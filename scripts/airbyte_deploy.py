"""
Deployt Airbyte Pipelines per API — deklarativ, idempotent, upsert-fähig.

Jede Pipeline besteht aus drei Dateien in airbyte/connections/:
    source_<pipeline>.json
    connection_<pipeline>_to_bronze.json
    destination_s3_bronze.json   (geteilt, einmal pro Environment)

Verhalten (Upsert):
    - Ressource existiert nicht  → wird erstellt
    - Ressource existiert, Config hat sich geändert → wird aktualisiert
    - Ressource existiert, Config identisch          → wird übersprungen (kein API-Call)
    - Connection verweist auf falsche IDs            → wird aktualisiert

Voraussetzung: pip install requests

Verwendung:
    # Alle Pipelines deployen
    python scripts/airbyte_deploy.py

    # Einzelne Pipeline deployen
    python scripts/airbyte_deploy.py shopify

    # Dry-Run: zeigt Plan ohne Änderungen
    python scripts/airbyte_deploy.py --dry-run
    python scripts/airbyte_deploy.py shopify --dry-run

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
    """Ersetzt ${VAR}-Platzhalter durch Umgebungsvariablen."""
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


def _configs_equal(desired: dict, actual: dict) -> bool:
    """Prüft ob zwei connectionConfiguration-Dicts inhaltlich identisch sind.

    Ignoriert Felder die Airbyte intern hinzufügt (z.B. _type, airbyte_*).
    """
    def _strip_internal(d: dict) -> dict:
        return {k: v for k, v in d.items() if not k.startswith("_") and not k.startswith("airbyte_")}

    return _strip_internal(desired) == _strip_internal(actual)


def get_workspace_id() -> str:
    result = _post("workspaces/list", {})
    workspaces = result.get("workspaces", [])
    if not workspaces:
        raise RuntimeError("Kein Airbyte-Workspace gefunden — ist Airbyte gestartet?")
    workspace_id = workspaces[0]["workspaceId"]
    log.info("Workspace: %s", workspace_id)
    return workspace_id


def upsert_source(workspace_id: str, config: dict, dry_run: bool = False) -> str:
    """Erstellt die Source oder aktualisiert sie wenn die Config abweicht."""
    result = _post("sources/list", {"workspaceId": workspace_id})
    for source in result.get("sources", []):
        if source["name"] == config["name"]:
            source_id = source["sourceId"]
            if _configs_equal(config["connectionConfiguration"], source.get("connectionConfiguration", {})):
                log.info("Source '%s' unverändert — kein Update nötig", config["name"])
            else:
                log.info("Source '%s' hat Config-Drift — wird aktualisiert", config["name"])
                if not dry_run:
                    _post("sources/update", {
                        "sourceId": source_id,
                        "name": config["name"],
                        "connectionConfiguration": config["connectionConfiguration"],
                    })
            return source_id

    log.info("Source '%s' nicht gefunden — wird erstellt", config["name"])
    if dry_run:
        return "dry-run-source-id"
    result = _post("sources/create", {
        "workspaceId": workspace_id,
        "name": config["name"],
        "sourceDefinitionId": config["sourceDefinitionId"],
        "connectionConfiguration": config["connectionConfiguration"],
    })
    source_id = result["sourceId"]
    log.info("Source '%s' erstellt: %s", config["name"], source_id)
    return source_id


def upsert_destination(workspace_id: str, config: dict, dry_run: bool = False) -> str:
    """Erstellt die Destination oder aktualisiert sie wenn die Config abweicht."""
    result = _post("destinations/list", {"workspaceId": workspace_id})
    for dest in result.get("destinations", []):
        if dest["name"] == config["name"]:
            dest_id = dest["destinationId"]
            if _configs_equal(config["connectionConfiguration"], dest.get("connectionConfiguration", {})):
                log.info("Destination '%s' unverändert — kein Update nötig", config["name"])
            else:
                log.info("Destination '%s' hat Config-Drift — wird aktualisiert", config["name"])
                if not dry_run:
                    _post("destinations/update", {
                        "destinationId": dest_id,
                        "name": config["name"],
                        "connectionConfiguration": config["connectionConfiguration"],
                    })
            return dest_id

    log.info("Destination '%s' nicht gefunden — wird erstellt", config["name"])
    if dry_run:
        return "dry-run-destination-id"
    result = _post("destinations/create", {
        "workspaceId": workspace_id,
        "name": config["name"],
        "destinationDefinitionId": config["destinationDefinitionId"],
        "connectionConfiguration": config["connectionConfiguration"],
    })
    dest_id = result["destinationId"]
    log.info("Destination '%s' erstellt: %s", config["name"], dest_id)
    return dest_id


def upsert_connection(
    source_id: str,
    destination_id: str,
    config: dict,
    dry_run: bool = False,
) -> str:
    """Erstellt die Connection oder aktualisiert sie wenn Config oder IDs abweichen."""
    result = _post("connections/list", {"sourceId": source_id})
    for conn in result.get("connections", []):
        if conn["name"] == config["name"]:
            conn_id = conn["connectionId"]
            ids_match = (
                conn.get("sourceId") == source_id
                and conn.get("destinationId") == destination_id
            )
            catalog_match = conn.get("syncCatalog") == config["syncCatalog"]
            schedule_match = (
                conn.get("scheduleType") == config["scheduleType"]
                and conn.get("scheduleData") == config.get("scheduleData")
            )
            if ids_match and catalog_match and schedule_match:
                log.info("Connection '%s' unverändert — kein Update nötig", config["name"])
            else:
                reasons = []
                if not ids_match:
                    reasons.append("Source/Destination-IDs")
                if not catalog_match:
                    reasons.append("syncCatalog")
                if not schedule_match:
                    reasons.append("Schedule")
                log.info("Connection '%s' hat Drift (%s) — wird aktualisiert", config["name"], ", ".join(reasons))
                if not dry_run:
                    _post("connections/update", {
                        "connectionId": conn_id,
                        "sourceId": source_id,
                        "destinationId": destination_id,
                        "name": config["name"],
                        "syncCatalog": config["syncCatalog"],
                        "scheduleType": config["scheduleType"],
                        "scheduleData": config.get("scheduleData"),
                        "status": config["status"],
                    })
            return conn_id

    log.info("Connection '%s' nicht gefunden — wird erstellt", config["name"])
    if dry_run:
        return "dry-run-connection-id"
    result = _post("connections/create", {
        "sourceId": source_id,
        "destinationId": destination_id,
        "name": config["name"],
        "syncCatalog": config["syncCatalog"],
        "scheduleType": config["scheduleType"],
        "scheduleData": config.get("scheduleData"),
        "status": config["status"],
    })
    conn_id = result["connectionId"]
    log.info("Connection '%s' erstellt: %s", config["name"], conn_id)
    return conn_id


def deploy_pipeline(pipeline: str, workspace_id: str, dry_run: bool = False) -> None:
    """Deployt eine einzelne Pipeline (Source + Destination + Connection) per Upsert."""
    source_file = CONNECTIONS_DIR / f"source_{pipeline}.json"
    connection_file = CONNECTIONS_DIR / f"connection_{pipeline}_to_bronze.json"
    destination_file = CONNECTIONS_DIR / "destination_s3_bronze.json"

    if not source_file.exists():
        raise FileNotFoundError(f"Source-Config nicht gefunden: {source_file.name}")
    if not connection_file.exists():
        raise FileNotFoundError(f"Connection-Config nicht gefunden: {connection_file.name}")

    source_config = _resolve_env_vars(json.loads(source_file.read_text()))
    destination_config = _resolve_env_vars(json.loads(destination_file.read_text()))
    connection_config = _resolve_env_vars(json.loads(connection_file.read_text()))

    source_id = upsert_source(workspace_id, source_config, dry_run)
    destination_id = upsert_destination(workspace_id, destination_config, dry_run)
    upsert_connection(source_id, destination_id, connection_config, dry_run)

    log.info(
        "%sPipeline '%s' — source: %s | dest: %s",
        "[DRY-RUN] " if dry_run else "",
        pipeline,
        source_id,
        destination_id,
    )


def deploy(pipeline: Optional[str] = None, dry_run: bool = False) -> None:
    """Einstiegspunkt: deployt eine oder alle Pipelines per Upsert."""
    if dry_run:
        log.info("=== DRY-RUN — keine Änderungen werden durchgeführt ===")
    log.info("Airbyte Deploy gestartet — Ziel: %s", AIRBYTE_URL)
    workspace_id = get_workspace_id()

    if pipeline:
        deploy_pipeline(pipeline, workspace_id, dry_run)
    else:
        source_files = sorted(CONNECTIONS_DIR.glob("source_*.json"))
        pipelines = [f.stem.removeprefix("source_") for f in source_files]
        if not pipelines:
            raise RuntimeError(f"Keine source_*.json Dateien in {CONNECTIONS_DIR}")
        log.info("Gefundene Pipelines: %s", pipelines)
        for p in pipelines:
            deploy_pipeline(p, workspace_id, dry_run)

    log.info("%sDeploy abgeschlossen.", "[DRY-RUN] " if dry_run else "")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    dry_run_flag = "--dry-run" in sys.argv[1:]
    pipeline_arg = args[0] if args else None
    try:
        deploy(pipeline_arg, dry_run=dry_run_flag)
    except Exception as e:
        log.error("Deploy fehlgeschlagen: %s", e)
        sys.exit(1)
