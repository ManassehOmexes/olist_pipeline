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

VOLUME_BASELINES: dict[str, int] = {
    'olist_orders_dataset':              99441,
    'olist_order_items_dataset':         112650,
    'olist_order_payments_dataset':      103886,
    'olist_order_reviews_dataset':       99224,
    'olist_customers_dataset':           99441,
    'olist_sellers_dataset':             3095,
    'olist_products_dataset':            32951,
    'olist_geolocation_dataset':         1000163,
    'product_category_name_translation': 71,
}

VOLUME_THRESHOLD = 0.70


def upload_to_s3(file_name: str, **context) -> str:
    """Uploads a CSV file to the S3 Bronze layer.

    Returns the S3 key — stored via XCom.
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
        log.info("Uploaded: %s → s3://%s/%s", local_path, bucket, s3_key)
    except Exception as e:
        log.error("Upload failed for %s: %s", file_name, e)
        raise

    context['ti'].xcom_push(key='s3_key', value=s3_key)
    return s3_key


def check_volume_anomaly(**context) -> None:
    """Compares CSV row counts against baseline. Sends SNS alert and raises exception on anomaly."""
    region = os.environ['AWS_DEFAULT_REGION']
    topic_arn = os.environ.get(
        'SNS_TOPIC_ARN',
        'arn:aws:sns:eu-central-1:710220507619:olist-alerts-dev',
    )
    anomalies: list[str] = []

    for file_name in CSV_FILES:
        table = file_name.replace('.csv', '')
        local_path = Path('/opt/airflow/data/raw') / file_name
        baseline = VOLUME_BASELINES[table]

        try:
            with open(local_path, 'r', encoding='utf-8') as f:
                row_count = sum(1 for _ in f) - 1  # subtract header
        except Exception as e:
            log.error("File not readable: %s — %s", local_path, e)
            anomalies.append(f"{table}: file not readable ({e})")
            continue

        ratio = row_count / baseline
        deviation_pct = (1 - ratio) * 100

        if ratio < VOLUME_THRESHOLD:
            msg = (
                f"{table}: expected ~{baseline:,}, found {row_count:,} "
                f"({deviation_pct:.1f}% below baseline)"
            )
            log.warning("ANOMALY — %s", msg)
            anomalies.append(msg)
        else:
            log.info("OK — %s: %s rows (%.1f%% of baseline)", table, f"{row_count:,}", ratio * 100)

    if anomalies:
        summary = "\n".join(anomalies)
        try:
            sns = boto3.client('sns', region_name=region)
            sns.publish(
                TopicArn=topic_arn,
                Subject='[olist] Bronze Volume Anomaly',
                Message=f"Volume anomalies detected:\n\n{summary}",
            )
            log.info("SNS alert sent to %s", topic_arn)
        except Exception as e:
            log.error("SNS publish failed: %s", e)

        raise RuntimeError(
            f"Volume anomaly check failed ({len(anomalies)} table(s)):\n{summary}"
        )


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
            raise RuntimeError("Bronze validation failed — Glue job will not start")
    except FileNotFoundError:
        log.error("validate_bronze.py not found at: %s", script)
        raise


def trigger_glue_job(**context) -> str:
    """Starts the Glue Bronze-to-Silver job.

    Returns the job run ID — stored via XCom.
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
        log.info("Glue job started: %s (run ID: %s)", job_name, run_id)
    except Exception as e:
        log.error("Failed to start Glue job: %s", e)
        raise

    context['ti'].xcom_push(key='glue_run_id', value=run_id)
    return run_id


with DAG(
    dag_id='olist_bronze_upload',
    default_args=default_args,
    description='Uploads Olist CSV raw data to S3 Bronze layer and triggers Glue job',
    schedule_interval='@once',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['bronze', 'olist', 's3'],
    doc_md="""
    ## olist_bronze_upload

    1. TaskGroup upload_bronze: Upload all 9 CSV files to S3 Bronze in parallel
       - XCom: s3_key stored per file
    2. check_volume_anomaly: Compare row counts of all CSVs against baseline (threshold 70%)
       - Anomaly → SNS alert + abort before GE validation
    3. validate_bronze: Great Expectations checks all CSVs on S3 (schema, PK, row count)
       - Fails → Glue will not start
    4. start_glue_job: Trigger Glue job Bronze → Silver
       - XCom: glue_run_id stored
    5. wait_for_silver: S3KeySensor waits until Silver Parquet appears (reschedule mode)
    6. trigger_silver_to_gold: DAG olist_silver_to_gold is triggered
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

    check_volume = PythonOperator(
        task_id='check_volume_anomaly',
        python_callable=check_volume_anomaly,
    )

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

    upload_group >> check_volume >> validate_bronze >> start_glue >> wait_for_silver >> trigger_silver_to_gold
