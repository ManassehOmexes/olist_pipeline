from datetime import datetime, timedelta
from pathlib import Path
import logging
import os
import subprocess
import sys

import boto3
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor
from airflow.utils.task_group import TaskGroup

log = logging.getLogger(__name__)

default_args = {
    'owner': 'olist',
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

CSV_FILES = [
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


def upload_to_s3(file_name: str, **context) -> str:
    """Lädt eine CSV Datei in den S3 Bronze Layer hoch.

    Gibt den S3-Key zurück — wird via XCom gespeichert.
    """
    bucket = os.environ['S3_BUCKET']
    region = os.environ['AWS_DEFAULT_REGION']
    local_path = Path('/opt/airflow/data/raw') / file_name
    s3_key = f"bronze/{file_name.replace('.csv', '')}/{file_name}"

    try:
        s3_client = boto3.client('s3', region_name=region)
        s3_client.upload_file(
            Filename=str(local_path),
            Bucket=bucket,
            Key=s3_key,
        )
        log.info("Hochgeladen: %s → s3://%s/%s", local_path, bucket, s3_key)
    except Exception as e:
        log.error("Upload fehlgeschlagen für %s: %s", file_name, e)
        raise

    context['ti'].xcom_push(key='s3_key', value=s3_key)
    return s3_key


def run_bronze_validation(**context) -> None:
    script = '/opt/airflow/great_expectations/validate_bronze.py'
    try:
        result = subprocess.run(
            [sys.executable, script],
            capture_output=True,
            text=True,
            env=os.environ.copy(),
        )
        if result.stdout:
            log.info(result.stdout.strip())
        if result.returncode != 0:
            log.error(result.stderr.strip())
            raise RuntimeError("Bronze Validation fehlgeschlagen — Glue Job wird nicht gestartet")
    except FileNotFoundError:
        log.error("validate_bronze.py nicht gefunden unter: %s", script)
        raise


def trigger_glue_job(**context) -> str:
    """Startet den Glue Bronze-to-Silver Job.

    Gibt die Job-Run-ID zurück — wird via XCom gespeichert.
    """
    region = os.environ['AWS_DEFAULT_REGION']
    job_name = 'olist-bronze-to-silver-dev'

    try:
        glue_client = boto3.client('glue', region_name=region)
        response = glue_client.start_job_run(
            JobName=job_name,
            Arguments={
                '--source_bucket': os.environ['S3_BUCKET'],
                '--target_bucket': os.environ['S3_BUCKET'],
            },
        )
        run_id = response['JobRunId']
        log.info("Glue Job gestartet: %s (Run ID: %s)", job_name, run_id)
    except Exception as e:
        log.error("Glue Job konnte nicht gestartet werden: %s", e)
        raise

    context['ti'].xcom_push(key='glue_run_id', value=run_id)
    return run_id


with DAG(
    dag_id='olist_bronze_upload',
    default_args=default_args,
    description='Lädt Olist CSV Rohdaten nach S3 Bronze Layer und startet Glue Job',
    schedule_interval='@once',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['bronze', 'olist', 's3'],
    doc_md="""
    ## olist_bronze_upload

    1. TaskGroup upload_bronze: Alle 9 CSV Dateien parallel nach S3 Bronze hochladen
       - XCom: s3_key pro Datei gespeichert
    2. validate_bronze: Great Expectations prüft alle CSVs auf S3 (Struktur, PK, Row Count)
       - Schlägt fehl → Glue wird nicht gestartet
    3. start_glue_job: Glue Job Bronze → Silver triggern
       - XCom: glue_run_id gespeichert
    4. wait_for_silver: S3KeySensor wartet bis Silver-Parquet erscheint (reschedule mode)
    5. trigger_silver_to_gold: DAG olist_silver_to_gold wird gestartet
    """,
) as dag:

    with TaskGroup(group_id='upload_bronze') as upload_group:
        upload_tasks = [
            PythonOperator(
                task_id=f"upload_{f.replace('.csv', '')}",
                python_callable=upload_to_s3,
                op_kwargs={'file_name': f},
            )
            for f in CSV_FILES
        ]

    validate_bronze = PythonOperator(
        task_id='validate_bronze',
        python_callable=run_bronze_validation,
    )

    start_glue = PythonOperator(
        task_id='start_glue_job',
        python_callable=trigger_glue_job,
    )

    wait_for_silver = S3KeySensor(
        task_id='wait_for_silver',
        bucket_name=os.environ.get('S3_BUCKET', 'olist-data-lake-dev'),
        bucket_key='silver/olist_orders_dataset/olist_orders_dataset.parquet',
        aws_conn_id='aws_default',
        poke_interval=30,
        timeout=600,
        mode='reschedule',
    )

    trigger_silver_to_gold = TriggerDagRunOperator(
        task_id='trigger_silver_to_gold',
        trigger_dag_id='olist_silver_to_gold',
        wait_for_completion=False,
    )

    upload_group >> validate_bronze >> start_glue >> wait_for_silver >> trigger_silver_to_gold
