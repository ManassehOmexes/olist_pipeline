import sys
import logging
import boto3
import pandas as pd
from awsglue.utils import getResolvedOptions
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'source_bucket', 'target_bucket'])

SOURCE_BUCKET = args['source_bucket']
TARGET_BUCKET = args['target_bucket']


def read_csv_from_s3(bucket: str, table_name: str) -> pd.DataFrame:
    """Liest eine CSV Datei aus dem Bronze Layer via boto3."""
    import io
    key = f"bronze/{table_name}/{table_name}.csv"
    s3_client = boto3.client('s3')
    response = s3_client.get_object(Bucket=bucket, Key=key)
    return pd.read_csv(io.BytesIO(response['Body'].read()))


def write_parquet_to_s3(df: pd.DataFrame, bucket: str, table_name: str) -> None:
    """Schreibt einen DataFrame als Parquet in den Silver Layer via boto3."""
    import io
    key = f"silver/{table_name}/{table_name}.parquet"
    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False)
    buffer.seek(0)
    s3_client = boto3.client('s3')
    s3_client.put_object(Bucket=bucket, Key=key, Body=buffer.getvalue())
    log.info("Geschrieben: s3://%s/%s (%d Zeilen)", bucket, key, len(df))


def transform_orders(df: pd.DataFrame) -> pd.DataFrame:
    """Bronze → Silver: olist_orders_dataset"""
    timestamp_cols = [
        'order_purchase_timestamp',
        'order_approved_at',
        'order_delivered_carrier_date',
        'order_delivered_customer_date',
        'order_estimated_delivery_date'
    ]
    for col in timestamp_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    return df


def transform_order_items(df: pd.DataFrame) -> pd.DataFrame:
    """Bronze → Silver: olist_order_items_dataset"""
    df['shipping_limit_date'] = pd.to_datetime(df['shipping_limit_date'], errors='coerce')
    return df


def transform_products(df: pd.DataFrame) -> pd.DataFrame:
    """Bronze → Silver: olist_products_dataset"""
    df['product_category_name'] = df['product_category_name'].fillna('unknown')
    return df


def transform_reviews(df: pd.DataFrame) -> pd.DataFrame:
    """Bronze → Silver: olist_order_reviews_dataset"""
    timestamp_cols = ['review_creation_date', 'review_answer_timestamp']
    for col in timestamp_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    return df


def transform_default(df: pd.DataFrame) -> pd.DataFrame:
    """Tabellen ohne spezifische Transformation."""
    return df


TABLES = {
    'olist_orders_dataset':              transform_orders,
    'olist_order_items_dataset':         transform_order_items,
    'olist_order_payments_dataset':      transform_default,
    'olist_order_reviews_dataset':       transform_reviews,
    'olist_customers_dataset':           transform_default,
    'olist_sellers_dataset':             transform_default,
    'olist_products_dataset':            transform_products,
    'olist_geolocation_dataset':         transform_default,
    'product_category_name_translation': transform_default,
}


if __name__ == '__main__':
    log.info("Glue Job gestartet: %s", datetime.now())

    for table_name, transform_fn in TABLES.items():
        try:
            log.info("Verarbeite: %s", table_name)
            df = read_csv_from_s3(SOURCE_BUCKET, table_name)
            df = transform_fn(df)
            write_parquet_to_s3(df, TARGET_BUCKET, table_name)
        except Exception as e:
            log.error("Fehler bei %s: %s", table_name, e)
            raise

    log.info("Glue Job abgeschlossen: %s", datetime.now())
