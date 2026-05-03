"""
Deployt Airbyte Source, Destination und Connection per API.
Idempotent: bestehende Ressourcen werden wiederverwendet, nicht neu erstellt.

Voraussetzung: pip install requests

Verwendung:
    python scripts/airbyte_deploy.py

Umgebungsvariablen:
    AIRBYTE_URL          Airbyte API Basis-URL (default: http://localhost:8006)
    AIRBYTE_USERNAME     Basic-Auth Benutzername (default: airbyte)
    AIRBYTE_PASSWORD     Basic-Auth Passwort (default: password)
    AWS_ACCESS_KEY_ID    Wird in den Configs als ${AWS_ACCESS_KEY_ID} referenziert
    AWS_SECRET_ACCESS_KEY
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
    """Ersetzt ${VAR}-Platzhalter in der Config durch Umgebungsvariablen."""
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
    resolved = _resolve_env_vars(config)
    payload = {
        "workspaceId": workspace_id,
        "name": resolved["name"],
        "sourceDefinitionId": resolved["sourceDefinitionId"],
        "connectionConfiguration": resolved["connectionConfiguration"],
    }
    result = _post("sources/create", payload)
    source_id = result["sourceId"]
    log.info("Source '%s' erstellt: %s", resolved["name"], source_id)
    return source_id


def find_destination(workspace_id: str, name: str) -> Optional[str]:
    result = _post("destinations/list", {"workspaceId": workspace_id})
    for dest in result.get("destinations", []):
        if dest["name"] == name:
            log.info("Destination '%s' existiert bereits: %s", name, dest["destinationId"])
            return dest["destinationId"]
    return None


def create_destination(workspace_id: str, config: dict) -> str:
    resolved = _resolve_env_vars(config)
    payload = {
        "workspaceId": workspace_id,
        "name": resolved["name"],
        "destinationDefinitionId": resolved["destinationDefinitionId"],
        "connectionConfiguration": resolved["connectionConfiguration"],
    }
    result = _post("destinations/create", payload)
    dest_id = result["destinationId"]
    log.info("Destination '%s' erstellt: %s", resolved["name"], dest_id)
    return dest_id


def find_connection(workspace_id: str, name: str) -> Optional[str]:
    result = _post("connections/list", {"workspaceId": workspace_id})
    for conn in result.get("connections", []):
        if conn["name"] == name:
            log.info("Connection '%s' existiert bereits: %s", name, conn["connectionId"])
            return conn["connectionId"]
    return None


def create_connection(source_id: str, destination_id: str, config: dict) -> str:
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


def deploy() -> None:
    log.info("Airbyte Deploy gestartet — Ziel: %s", AIRBYTE_URL)

    source_config = json.loads((CONNECTIONS_DIR / "source_s3_olist.json").read_text())
    destination_config = json.loads((CONNECTIONS_DIR / "destination_s3_bronze.json").read_text())
    connection_config = json.loads((CONNECTIONS_DIR / "connection_olist_to_bronze.json").read_text())

    workspace_id = get_workspace_id()

    source_id = find_source(workspace_id, source_config["name"])
    if source_id is None:
        source_id = create_source(workspace_id, source_config)

    destination_id = find_destination(workspace_id, destination_config["name"])
    if destination_id is None:
        destination_id = create_destination(workspace_id, destination_config)

    connection_id = find_connection(workspace_id, connection_config["name"])
    if connection_id is None:
        connection_id = create_connection(source_id, destination_id, connection_config)

    log.info("Deploy abgeschlossen in < 30s.")
    log.info("  Source:      %s", source_id)
    log.info("  Destination: %s", destination_id)
    log.info("  Connection:  %s", connection_id)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    try:
        deploy()
    except Exception as e:
        log.error("Deploy fehlgeschlagen: %s", e)
        sys.exit(1)
