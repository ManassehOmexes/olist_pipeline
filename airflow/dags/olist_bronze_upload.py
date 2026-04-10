from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import boto3
import os
from pathlib import Path

default_args = {
    'owner': 'olist',
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

def upload_to_s3(file_name: str) -> None:
    """Lädt eine CSV Datei in den S3 Bronze Layer hoch."""
    
    bucket = os.environ['S3_BUCKET']
    region = os.environ['AWS_DEFAULT_REGION']
    s3_client = boto3.client('s3', region_name=region)
    
    local_path = Path('/opt/airflow/data/raw') / file_name
    s3_key = f"bronze/{file_name.replace('.csv', '')}/{file_name}"
    
    s3_client.upload_file(
        Filename=str(local_path),
        Bucket=bucket,
        Key=s3_key,
    )
    print(f"Hochgeladen: {local_path} → s3://{bucket}/{s3_key}")

with DAG(
    dag_id='olist_bronze_upload',
    default_args=default_args,
    description='Lädt Olist CSV Rohdaten nach S3 Bronze Layer',
    schedule_interval='@once',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['bronze', 'olist', 's3'],
    doc_md="""
    ## olist_bronze_upload
    Liest alle CSV Dateien aus data/raw/ und lädt sie in den S3 Bronze Layer.
    Pfadschema: s3://<bucket>/bronze/<tabellenname>/
    """,
) as dag:

    csv_files = [
        'olist_orders_dataset.csv',
        'olist_order_items_dataset.csv',
        'olist_order_payments_dataset.csv',
        'olist_order_reviews_dataset.csv',
        'olist_customers_dataset.csv',
        'olist_sellers_dataset.csv',
        'olist_products_dataset.csv',
        'olist_geolocation_dataset.csv',
        'product_category_name_translation.csv',
    ]

    upload_tasks = [
        PythonOperator(
            task_id=f"upload_{f.replace('.csv', '')}",
            python_callable=upload_to_s3,
            op_kwargs={'file_name': f},
        )
        for f in csv_files
    ]

    upload_tasks
