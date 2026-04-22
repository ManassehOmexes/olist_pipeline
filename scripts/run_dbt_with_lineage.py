"""
Führt dbt run + dbt test aus und sendet Lineage-Events an Marquez.

Voraussetzung: pip install openlineage-dbt openlineage-integration-common

Verwendung:
    python scripts/run_dbt_with_lineage.py --target dev
    python scripts/run_dbt_with_lineage.py --target prod
"""

import argparse
import logging
import subprocess
import sys
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

MARQUEZ_URL = os.environ.get("MARQUEZ_URL", "http://localhost:5000")
DBT_DIR = os.path.join(os.path.dirname(__file__), "..", "dbt")

# OpenLineage überträgt Lineage-Daten über Umgebungsvariablen
OPENLINEAGE_ENV = {
    **os.environ,
    "OPENLINEAGE_URL": MARQUEZ_URL,
    "OPENLINEAGE_NAMESPACE": "olist-dbt",
}


def run(command: list[str], target: str) -> None:
    log.info("Starte: %s (target=%s)", " ".join(command), target)
    try:
        result = subprocess.run(
            command + ["--target", target],
            cwd=DBT_DIR,
            env=OPENLINEAGE_ENV,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Befehl fehlgeschlagen: {' '.join(command)}")
        log.info("Erfolgreich: %s", " ".join(command))
    except Exception as e:
        log.error("Fehler: %s", e)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="dbt mit OpenLineage Lineage-Tracking ausführen")
    parser.add_argument("--target", default="dev", choices=["dev", "prod"], help="dbt target (dev=DuckDB, prod=Redshift)")
    args = parser.parse_args()

    log.info("Lineage-Events werden gesendet an: %s", MARQUEZ_URL)
    log.info("Namespace: olist-dbt | Target: %s", args.target)

    run(["dbt", "run", "--no-partial-parse"], args.target)
    run(["dbt", "test", "--no-partial-parse"], args.target)

    log.info("Fertig — Lineage-Graph sichtbar unter http://localhost:3000")


if __name__ == "__main__":
    main()
