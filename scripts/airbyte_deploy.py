"""
Deployt Airbyte Pipelines per API — idempotent und generisch.

Jede Pipeline besteht aus drei Dateien in airbyte/connections/:
    source_<pipeline>.json
    connection_<pipeline>_to_bronze.json
    destination_s3_bronze.json   (geteilt, einmal pro Environment)

Idempotent: bestehende Ressourcen werden wiederverwendet, nicht neu erstellt.

Voraussetzung: pip install requests

Verwendung:
    # Alle Pipelines deployen (entdeckt source_*.json automatisch)
    python scripts/airbyte_deploy.py

    # Einzelne Pipeline deployen
    python scripts/airbyte_deploy.py shopify
    python scripts/airbyte_deploy.py olist
    python scripts/airbyte_deploy.py postgres

Umgebungsvariablen (Pflicht):
    AIRBYTE_URL            Airbyte API Basis-URL (default: http://localhost:8006)
    AIRBYTE_USERNAME       Basic-Auth Benutzername (default: airbyte)
    AIRBYTE_PASSWORD       Basic-Auth Passwort (default: password)
    AWS_ACCESS_KEY_ID      Für S3-Destination
    AWS_SECRET_ACCESS_KEY  Für S3-Destination

Kunden-spezifische Variablen (je nach Pipeline):
    CUSTOMER_ID            Eindeutiger Kundenbezeichner (z.B. "acme")
    SHOPIFY_SHOP           Shopify Shop-Domain (z.B. "acme.myshopify.com")
    SHOPIFY_API_PASSWORD   Shopify Admin API Access Token
    SHOPIFY_START_DATE     ISO 8601 Startdatum (z.B. "2023-01-01T00:00:00Z")
    POSTGRES_HOST          PostgreSQL Hostname
    POSTGRES_DATABASE      Datenbankname
    POSTGRES_USERNAME      Benutzername
    POSTGRES_PASSWORD      Passwort
"""

import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Optional

import requests

log = logging.getLogger(__name__)

AIRBYTE_URL = os.environ.get("AIRBYTE_URL", "http://localhost:8006")
AIRBYTE_USERNAME = os.environ.get("AIRBYTE_USERNAME", "airbyte")
AIRBYTE_PASSWORD = os.environ.get("AIRBYTE_PASSWORD", "password")
CONNECTIONS_DIR = Path(__file__).parent.parent / "airbyte" / "connections"


def _resolve_env_vars(config: dict) -> dict:
    """Ersetzt ${VAR}-Platzhalter durch Umgebungsvariablen.

    Secrets stehen nie im Config-File — nur als Platzhalter.
    Fehlt eine Variable, wird deploy() mit RuntimeError abgebrochen.
    """
    raw = json.dumps(config)

    def replacer(match: re.Match) -> str:
        var_name = match.group(1)
        value = os.environ.get(var_name)
        if value is None:
            raise RuntimeError(f"Umgebungsvariable '{var_name}' nicht gesetzt")
        return value

    return json.loads(re.sub(r"\$\{([^}]+)\}", replacer, raw))


def _post(path: str, body: dict) -> dict:
    url = f"{AIRBYTE_URL}/api/v1/{path}"
    try:
        response = requests.post(
            url,
            json=body,
            auth=(AIRBYTE_USERNAME, AIRBYTE_PASSWORD),
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as e:
        log.error("HTTP-Fehler %s bei %s: %s", e.response.status_code, path, e.response.text)
        raise
    except requests.RequestException as e:
        log.error("Verbindungsfehler bei %s: %s", path, e)
        raise


def get_workspace_id() -> str:
    result = _post("workspaces/list", {})
    workspaces = result.get("workspaces", [])
    if not workspaces:
        raise RuntimeError("Kein Airbyte-Workspace gefunden — ist Airbyte gestartet?")
    workspace_id = workspaces[0]["workspaceId"]
    log.info("Workspace: %s", workspace_id)
    return workspace_id


def find_source(workspace_id: str, name: str) -> Optional[str]:
    result = _post("sources/list", {"workspaceId": workspace_id})
    for source in result.get("sources", []):
        if source["name"] == name:
            log.info("Source '%s' existiert bereits: %s", name, source["sourceId"])
            return source["sourceId"]
    return None


def create_source(workspace_id: str, config: dict) -> str:
    """Erstellt eine neue Source. config muss bereits aufgelöst sein (keine ${VAR})."""
    payload = {
        "workspaceId": workspace_id,
        "name": config["name"],
        "sourceDefinitionId": config["sourceDefinitionId"],
        "connectionConfiguration": config["connectionConfiguration"],
    }
    result = _post("sources/create", payload)
    source_id = result["sourceId"]
    log.info("Source '%s' erstellt: %s", config["name"], source_id)
    return source_id


def find_destination(workspace_id: str, name: str) -> Optional[str]:
    result = _post("destinations/list", {"workspaceId": workspace_id})
    for dest in result.get("destinations", []):
        if dest["name"] == name:
            log.info("Destination '%s' existiert bereits: %s", name, dest["destinationId"])
            return dest["destinationId"]
    return None


def create_destination(workspace_id: str, config: dict) -> str:
    """Erstellt eine neue Destination. config muss bereits aufgelöst sein."""
    payload = {
        "workspaceId": workspace_id,
        "name": config["name"],
        "destinationDefinitionId": config["destinationDefinitionId"],
        "connectionConfiguration": config["connectionConfiguration"],
    }
    result = _post("destinations/create", payload)
    dest_id = result["destinationId"]
    log.info("Destination '%s' erstellt: %s", config["name"], dest_id)
    return dest_id


def find_connection(workspace_id: str, name: str) -> Optional[str]:
    result = _post("connections/list", {"workspaceId": workspace_id})
    for conn in result.get("connections", []):
        if conn["name"] == name:
            log.info("Connection '%s' existiert bereits: %s", name, conn["connectionId"])
            return conn["connectionId"]
    return None


def create_connection(source_id: str, destination_id: str, config: dict) -> str:
    """Erstellt eine neue Connection. config muss bereits aufgelöst sein."""
    payload = {
        "sourceId": source_id,
        "destinationId": destination_id,
        "name": config["name"],
        "syncCatalog": config["syncCatalog"],
        "scheduleType": config["scheduleType"],
        "scheduleData": config["scheduleData"],
        "status": config["status"],
    }
    result = _post("connections/create", payload)
    conn_id = result["connectionId"]
    log.info("Connection '%s' erstellt: %s", config["name"], conn_id)
    return conn_id


def deploy_pipeline(pipeline: str, workspace_id: str) -> None:
    """Deployt eine einzelne Pipeline (Source + Destination + Connection).

    Convention: source_<pipeline>.json + connection_<pipeline>_to_bronze.json
    Die Destination (destination_s3_bronze.json) ist für alle Pipelines geteilt.
    """
    source_file = CONNECTIONS_DIR / f"source_{pipeline}.json"
    connection_file = CONNECTIONS_DIR / f"connection_{pipeline}_to_bronze.json"
    destination_file = CONNECTIONS_DIR / "destination_s3_bronze.json"

    if not source_file.exists():
        raise FileNotFoundError(f"Source-Config nicht gefunden: {source_file.name}")
    if not connection_file.exists():
        raise FileNotFoundError(f"Connection-Config nicht gefunden: {connection_file.name}")

    # Alle Configs einmalig auflösen — ${VAR} → echter Wert aus Umgebung
    source_config = _resolve_env_vars(json.loads(source_file.read_text()))
    destination_config = _resolve_env_vars(json.loads(destination_file.read_text()))
    connection_config = _resolve_env_vars(json.loads(connection_file.read_text()))

    source_id = find_source(workspace_id, source_config["name"])
    if source_id is None:
        source_id = create_source(workspace_id, source_config)

    destination_id = find_destination(workspace_id, destination_config["name"])
    if destination_id is None:
        destination_id = create_destination(workspace_id, destination_config)

    # Connection zuletzt: benötigt source_id UND destination_id
    connection_id = find_connection(workspace_id, connection_config["name"])
    if connection_id is None:
        connection_id = create_connection(source_id, destination_id, connection_config)

    log.info(
        "Pipeline '%s' deployed — source: %s | dest: %s | conn: %s",
        pipeline,
        source_id,
        destination_id,
        connection_id,
    )


def deploy(pipeline: Optional[str] = None) -> None:
    """Einstiegspunkt: deployt eine oder alle Pipelines.

    Ohne Argument: entdeckt alle source_*.json in airbyte/connections/
    und deployt jede Pipeline. Idempotent — bereits existierende Ressourcen
    werden wiederverwendet.
    """
    log.info("Airbyte Deploy gestartet — Ziel: %s", AIRBYTE_URL)
    workspace_id = get_workspace_id()

    if pipeline:
        deploy_pipeline(pipeline, workspace_id)
    else:
        # Konvention: source_<name>.json = eine Pipeline
        source_files = sorted(CONNECTIONS_DIR.glob("source_*.json"))
        pipelines = [f.stem.removeprefix("source_") for f in source_files]
        if not pipelines:
            raise RuntimeError(f"Keine source_*.json Dateien in {CONNECTIONS_DIR}")
        log.info("Gefundene Pipelines: %s", pipelines)
        for p in pipelines:
            deploy_pipeline(p, workspace_id)

    log.info("Deploy abgeschlossen.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    # Optionaler Pipeline-Name als erstes CLI-Argument
    pipeline_arg = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        deploy(pipeline_arg)
    except Exception as e:
        log.error("Deploy fehlgeschlagen: %s", e)
        sys.exit(1)
