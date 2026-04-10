"""
Great Expectations — Silver Layer Validation
Läuft nach Glue (Bronze→Silver), vor dbt (Silver→Gold).
Prüft Datenqualität der Parquet-Dateien auf S3.
"""

import io
import logging
import os
import sys

import boto3
import great_expectations as gx
import pandas as pd
from great_expectations.core.expectation_suite import ExpectationSuite
from great_expectations.expectations import (
    ExpectColumnValuesToBeBetween,
    ExpectColumnValuesToBeInSet,
    ExpectColumnValuesToBeUnique,
    ExpectColumnValuesToNotBeNull,
    ExpectTableRowCountToBeBetween,
)

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Konfiguration ────────────────────────────────────────────────────────────

BUCKET = os.environ["S3_BUCKET"]
REGION = os.environ["AWS_DEFAULT_REGION"]

SILVER_TABLES = {
    "olist_orders_dataset":        "silver/olist_orders_dataset/olist_orders_dataset.parquet",
    "olist_order_items_dataset":   "silver/olist_order_items_dataset/olist_order_items_dataset.parquet",
    "olist_customers_dataset":     "silver/olist_customers_dataset/olist_customers_dataset.parquet",
    "olist_products_dataset":      "silver/olist_products_dataset/olist_products_dataset.parquet",
    "olist_order_reviews_dataset": "silver/olist_order_reviews_dataset/olist_order_reviews_dataset.parquet",
}


# ── S3 Hilfsfunktion ─────────────────────────────────────────────────────────

def load_parquet_from_s3(bucket: str, key: str) -> pd.DataFrame:
    """Liest eine Parquet-Datei von S3 in einen Pandas DataFrame."""
    s3 = boto3.client(
        "s3",
        region_name=REGION,
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    )
    response = s3.get_object(Bucket=bucket, Key=key)
    return pd.read_parquet(io.BytesIO(response["Body"].read()))


# ── Expectation Suites ───────────────────────────────────────────────────────

def suite_orders() -> ExpectationSuite:
    suite = ExpectationSuite(name="orders_suite")
    suite.add_expectation(ExpectTableRowCountToBeBetween(min_value=90_000, max_value=200_000))
    suite.add_expectation(ExpectColumnValuesToNotBeNull(column="order_id"))
    suite.add_expectation(ExpectColumnValuesToBeUnique(column="order_id"))
    suite.add_expectation(ExpectColumnValuesToNotBeNull(column="customer_id"))
    suite.add_expectation(ExpectColumnValuesToBeInSet(
        column="order_status",
        value_set=["delivered", "shipped", "canceled", "processing",
                   "invoiced", "unavailable", "created", "approved"],
    ))
    return suite


def suite_order_items() -> ExpectationSuite:
    suite = ExpectationSuite(name="order_items_suite")
    suite.add_expectation(ExpectTableRowCountToBeBetween(min_value=100_000, max_value=200_000))
    suite.add_expectation(ExpectColumnValuesToNotBeNull(column="order_id"))
    suite.add_expectation(ExpectColumnValuesToNotBeNull(column="product_id"))
    suite.add_expectation(ExpectColumnValuesToNotBeNull(column="seller_id"))
    suite.add_expectation(ExpectColumnValuesToBeBetween(column="price", min_value=0))
    suite.add_expectation(ExpectColumnValuesToBeBetween(column="freight_value", min_value=0))
    return suite


def suite_customers() -> ExpectationSuite:
    suite = ExpectationSuite(name="customers_suite")
    suite.add_expectation(ExpectColumnValuesToNotBeNull(column="customer_id"))
    suite.add_expectation(ExpectColumnValuesToBeUnique(column="customer_id"))
    suite.add_expectation(ExpectColumnValuesToNotBeNull(column="customer_state"))
    return suite


def suite_products() -> ExpectationSuite:
    suite = ExpectationSuite(name="products_suite")
    suite.add_expectation(ExpectColumnValuesToNotBeNull(column="product_id"))
    suite.add_expectation(ExpectColumnValuesToBeUnique(column="product_id"))
    return suite


def suite_reviews() -> ExpectationSuite:
    suite = ExpectationSuite(name="reviews_suite")
    suite.add_expectation(ExpectColumnValuesToNotBeNull(column="review_id"))
    suite.add_expectation(ExpectColumnValuesToNotBeNull(column="order_id"))
    suite.add_expectation(ExpectColumnValuesToBeBetween(column="review_score", min_value=1, max_value=5))
    return suite


SUITES = {
    "olist_orders_dataset":        suite_orders,
    "olist_order_items_dataset":   suite_order_items,
    "olist_customers_dataset":     suite_customers,
    "olist_products_dataset":      suite_products,
    "olist_order_reviews_dataset": suite_reviews,
}


# ── Validierung ──────────────────────────────────────────────────────────────

def validate_table(context, table_name: str, s3_key: str) -> bool:
    """Lädt eine Tabelle von S3 und validiert sie gegen die Expectation Suite."""
    log.info("Validiere: %s", table_name)

    try:
        df = load_parquet_from_s3(BUCKET, s3_key)
    except Exception as e:
        log.error("Fehler beim Laden von S3 (%s): %s", s3_key, e)
        return False

    log.info("  Zeilen: %s  |  Spalten: %s", f"{len(df):,}", len(df.columns))

    try:
        suite = SUITES[table_name]()
        datasource = context.data_sources.add_pandas(name=f"ds_{table_name}")
        data_asset = datasource.add_dataframe_asset(name=table_name)
        batch_definition = data_asset.add_batch_definition_whole_dataframe("batch")
        batch = batch_definition.get_batch(batch_parameters={"dataframe": df})
        result = batch.validate(suite)
    except Exception as e:
        log.error("Fehler bei der Validierung von %s: %s", table_name, e)
        return False

    total = len(result.results)
    failed = sum(1 for r in result.results if not r.success)

    if result.success:
        log.info("  PASS: %d/%d Expectations bestanden", total, total)
    else:
        log.warning("  FAIL: %d/%d Expectations fehlgeschlagen", failed, total)
        for r in result.results:
            if not r.success:
                log.warning("    ✗ %s — %s", r.expectation_config.type, r.result)

    return result.success


def main() -> None:
    context = gx.get_context(mode="ephemeral")

    all_passed = True
    for table_name, s3_key in SILVER_TABLES.items():
        try:
            passed = validate_table(context, table_name, s3_key)
        except Exception as e:
            log.error("Unerwarteter Fehler bei %s: %s", table_name, e)
            passed = False

        if not passed:
            all_passed = False

    if all_passed:
        log.info("SILVER VALIDATION: ALLE CHECKS BESTANDEN — dbt kann starten.")
        sys.exit(0)
    else:
        log.error("SILVER VALIDATION: FEHLER GEFUNDEN — dbt wird NICHT gestartet.")
        sys.exit(1)


if __name__ == "__main__":
    main()
