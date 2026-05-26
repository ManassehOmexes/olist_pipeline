"""
Great Expectations - Bronze Layer Validation
Läuft nach S3-Upload, vor Glue (Bronze → Silver).
Prüft Struktur und Vollständigkeit der CSV-Dateien auf S3 Bronze.
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
    ExpectColumnValuesToBeUnique,
    ExpectColumnValuesToNotBeNull,
    ExpectTableRowCountToBeBetween,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

BUCKET = os.environ["S3_BUCKET"]
REGION = os.environ["AWS_DEFAULT_REGION"]

BRONZE_TABLES = {
    "olist_orders_dataset":              "bronze/olist_orders_dataset/olist_orders_dataset.csv",
    "olist_order_items_dataset":         "bronze/olist_order_items_dataset/olist_order_items_dataset.csv",
    "olist_order_payments_dataset":      "bronze/olist_order_payments_dataset/olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset":       "bronze/olist_order_reviews_dataset/olist_order_reviews_dataset.csv",
    "olist_customers_dataset":           "bronze/olist_customers_dataset/olist_customers_dataset.csv",
    "olist_sellers_dataset":             "bronze/olist_sellers_dataset/olist_sellers_dataset.csv",
    "olist_products_dataset":            "bronze/olist_products_dataset/olist_products_dataset.csv",
    "olist_geolocation_dataset":         "bronze/olist_geolocation_dataset/olist_geolocation_dataset.csv",
    "product_category_name_translation": "bronze/product_category_name_translation/product_category_name_translation.csv",
}


def _load_csv_from_s3(bucket: str, key: str) -> pd.DataFrame:
    s3 = boto3.client(
        "s3",
        region_name=REGION,
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    )
    response = s3.get_object(Bucket=bucket, Key=key)
    return pd.read_csv(io.BytesIO(response["Body"].read()))


def _suite_orders() -> ExpectationSuite:
    suite = ExpectationSuite(name="bronze_orders_suite")
    suite.add_expectation(ExpectTableRowCountToBeBetween(min_value=90_000, max_value=200_000))
    suite.add_expectation(ExpectColumnValuesToNotBeNull(column="order_id"))
    suite.add_expectation(ExpectColumnValuesToBeUnique(column="order_id"))
    suite.add_expectation(ExpectColumnValuesToNotBeNull(column="customer_id"))
    return suite


def _suite_order_items() -> ExpectationSuite:
    suite = ExpectationSuite(name="bronze_order_items_suite")
    suite.add_expectation(ExpectTableRowCountToBeBetween(min_value=100_000, max_value=200_000))
    suite.add_expectation(ExpectColumnValuesToNotBeNull(column="order_id"))
    suite.add_expectation(ExpectColumnValuesToNotBeNull(column="product_id"))
    suite.add_expectation(ExpectColumnValuesToNotBeNull(column="seller_id"))
    return suite


def _suite_order_payments() -> ExpectationSuite:
    suite = ExpectationSuite(name="bronze_order_payments_suite")
    suite.add_expectation(ExpectTableRowCountToBeBetween(min_value=100_000, max_value=200_000))
    suite.add_expectation(ExpectColumnValuesToNotBeNull(column="order_id"))
    suite.add_expectation(ExpectColumnValuesToNotBeNull(column="payment_type"))
    return suite


def _suite_order_reviews() -> ExpectationSuite:
    suite = ExpectationSuite(name="bronze_order_reviews_suite")
    suite.add_expectation(ExpectColumnValuesToNotBeNull(column="review_id"))
    suite.add_expectation(ExpectColumnValuesToNotBeNull(column="order_id"))
    return suite


def _suite_customers() -> ExpectationSuite:
    suite = ExpectationSuite(name="bronze_customers_suite")
    suite.add_expectation(ExpectColumnValuesToNotBeNull(column="customer_id"))
    suite.add_expectation(ExpectColumnValuesToBeUnique(column="customer_id"))
    suite.add_expectation(ExpectColumnValuesToNotBeNull(column="customer_state"))
    return suite


def _suite_sellers() -> ExpectationSuite:
    suite = ExpectationSuite(name="bronze_sellers_suite")
    suite.add_expectation(ExpectColumnValuesToNotBeNull(column="seller_id"))
    suite.add_expectation(ExpectColumnValuesToBeUnique(column="seller_id"))
    return suite


def _suite_products() -> ExpectationSuite:
    suite = ExpectationSuite(name="bronze_products_suite")
    suite.add_expectation(ExpectColumnValuesToNotBeNull(column="product_id"))
    suite.add_expectation(ExpectColumnValuesToBeUnique(column="product_id"))
    return suite


def _suite_geolocation() -> ExpectationSuite:
    suite = ExpectationSuite(name="bronze_geolocation_suite")
    suite.add_expectation(ExpectTableRowCountToBeBetween(min_value=1_000, max_value=2_000_000))
    suite.add_expectation(ExpectColumnValuesToNotBeNull(column="geolocation_zip_code_prefix"))
    return suite


def _suite_translations() -> ExpectationSuite:
    suite = ExpectationSuite(name="bronze_translations_suite")
    suite.add_expectation(ExpectTableRowCountToBeBetween(min_value=50, max_value=500))
    suite.add_expectation(ExpectColumnValuesToNotBeNull(column="product_category_name"))
    return suite


_SUITES = {
    "olist_orders_dataset":              _suite_orders,
    "olist_order_items_dataset":         _suite_order_items,
    "olist_order_payments_dataset":      _suite_order_payments,
    "olist_order_reviews_dataset":       _suite_order_reviews,
    "olist_customers_dataset":           _suite_customers,
    "olist_sellers_dataset":             _suite_sellers,
    "olist_products_dataset":            _suite_products,
    "olist_geolocation_dataset":         _suite_geolocation,
    "product_category_name_translation": _suite_translations,
}


def _validate_table(context, table_name: str, s3_key: str) -> bool:
    log.info("Validiere Bronze: %s", table_name)
    try:
        df = _load_csv_from_s3(BUCKET, s3_key)
    except Exception as e:
        log.error("Fehler beim Laden von S3 (%s): %s", s3_key, e)
        return False

    log.info("  Zeilen: %s  |  Spalten: %s", f"{len(df):,}", len(df.columns))

    try:
        suite = _SUITES[table_name]()
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
                log.warning("    FAIL: %s - %s", r.expectation_config.type, r.result)

    return result.success


def validate_all_bronze() -> bool:
    """Validiert alle Bronze-CSVs auf S3. Gibt True zurück wenn alle Checks bestanden."""
    context = gx.get_context(mode="ephemeral")
    all_passed = True
    for table_name, s3_key in BRONZE_TABLES.items():
        try:
            passed = _validate_table(context, table_name, s3_key)
        except Exception as e:
            log.error("Unerwarteter Fehler bei %s: %s", table_name, e)
            passed = False
        if not passed:
            all_passed = False
    return all_passed


def main() -> None:
    all_passed = validate_all_bronze()
    if all_passed:
        log.info("BRONZE VALIDATION: alle Checks bestanden. Glue kann starten.")
        sys.exit(0)
    else:
        log.error("BRONZE VALIDATION: Fehler gefunden. Glue wird nicht gestartet.")
        sys.exit(1)


if __name__ == "__main__":
    main()
