"""
Exportiert die Gold-Mart-Tabellen aus DuckDB als CSV.
Die CSV-Dateien werden in data/gold/ gespeichert und von Power BI geladen.
"""

import logging
import os
import duckdb
import pandas as pd

# Logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# Konfiguration

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "dbt", "dev.duckdb")
OUTPUT_DIR = os.path.join(ROOT, "data", "gold")

MARTS = [
    "main_marts.fct_sales",
    "main_marts.fct_regional_performance",
    "main_marts.fct_delivery",
    "main_marts.fct_reviews",
]


def export_marts() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    con = duckdb.connect(DB_PATH, read_only=True)
    log.info("Verbunden mit DuckDB: %s", DB_PATH)

    for table in MARTS:
        table_name = table.split(".")[-1]
        output_path = os.path.join(OUTPUT_DIR, f"{table_name}.csv")

        try:
            df = con.execute(f"SELECT * FROM {table}").df()
            df.to_csv(output_path, index=False)
            log.info("Exportiert: %s (%d Zeilen) -> %s", table_name, len(df), output_path)
        except Exception as e:
            log.error("Fehler beim Export von %s: %s", table_name, e)

    con.close()
    log.info("Export abgeschlossen. Dateien in: %s", OUTPUT_DIR)


if __name__ == "__main__":
    export_marts()
