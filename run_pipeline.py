"""
Pipeline Runner: Silver Validation -> dbt run -> dbt test
Reihenfolge:
  1. Great Expectations prueft Silver-Daten auf S3
  2. Nur wenn alles erfolgreich: dbt run + dbt test
"""

import logging
import os
import subprocess
import sys

# Logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


# Hilfsfunktion

def run(cmd: list[str], cwd: str | None = None) -> int:
    """Fuehrt einen Shell-Befehl aus und gibt den Exit-Code zurueck."""
    log.info("Starte: %s", " ".join(cmd))
    try:
        result = subprocess.run(cmd, cwd=cwd)
        return result.returncode
    except FileNotFoundError as e:
        log.error("Befehl nicht gefunden: %s", e)
        return 1
    except Exception as e:
        log.error("Fehler beim Ausfuehren von '%s': %s", " ".join(cmd), e)
        return 1


# Pipeline

def main() -> None:
    root = os.path.dirname(os.path.abspath(__file__))
    dbt_dir = os.path.join(root, "dbt")

    # Schritt 1: Silver Validation
    log.info("Schritt 1: Great Expectations - Silver Validation")
    code = run([sys.executable, "great_expectations/validate_silver.py"], cwd=root)
    if code != 0:
        log.error("Pipeline abgebrochen: Datenqualitaet nicht erfuellt.")
        sys.exit(1)

    # Schritt 2: dbt run
    log.info("Schritt 2: dbt run")
    code = run(["dbt", "run", "--no-partial-parse"], cwd=dbt_dir)
    if code != 0:
        log.error("Pipeline abgebrochen: dbt run fehlgeschlagen.")
        sys.exit(1)

    # Schritt 3: dbt test
    log.info("Schritt 3: dbt test")
    code = run(["dbt", "test", "--no-partial-parse"], cwd=dbt_dir)
    if code != 0:
        log.error("Pipeline abgebrochen: dbt test fehlgeschlagen.")
        sys.exit(1)

    log.info("Pipeline erfolgreich abgeschlossen.")
    sys.exit(0)


if __name__ == "__main__":
    main()
