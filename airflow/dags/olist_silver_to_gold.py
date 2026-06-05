from datetime import datetime, timedelta
import json
import logging
import subprocess
import sys
import os

import boto3

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor
from airflow.utils.task_group import TaskGroup

log = logging.getLogger(__name__)

default_args = {
    'owner': 'olist',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

ROOT = '/opt/airflow'


def _get_redshift_password() -> str:
    project = os.environ.get('PROJECT', 'olist')
    environment = os.environ.get('ENVIRONMENT', 'dev')
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(
        SecretId=f"{project}/redshift/admin-password/{environment}"
    )
    return json.loads(response['SecretString'])['password']


def validate_silver(**context) -> None:
    """Runs Great Expectations Silver validation.

    Fails if any check does not pass — dbt will not start.
    XCom: validation_status = 'passed'
    """
    log.info("Starting Great Expectations Silver validation...")

    try:
        result = subprocess.run(
            [sys.executable, 'great_expectations/validate_silver.py'],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        log.info(result.stdout)

        if result.returncode != 0:
            log.error(result.stderr)
            raise RuntimeError('Silver validation failed — dbt will not start.')

        log.info("Silver validation successful: all checks passed.")
    except Exception as e:
        log.error("Error in validate_silver: %s", e)
        raise

    context['ti'].xcom_push(key='validation_status', value='passed')


def run_dbt(command: str, **context) -> None:
    """Runs a dbt command against Redshift (prod).

    command: 'run' or 'test'
    XCom: dbt_<command>_status = 'passed'
    """
    log.info("Starting dbt %s --target prod...", command)

    try:
        result = subprocess.run(
            ['dbt', command, '--no-partial-parse', '--target', 'prod', '--profiles-dir', f'{ROOT}/dbt'],
            cwd=f'{ROOT}/dbt',
            capture_output=True,
            text=True,
            env={
                **os.environ,
                'REDSHIFT_PASSWORD': _get_redshift_password(),
                # Send lineage events to Marquez (running in same Docker network)
                'OPENLINEAGE_URL': 'http://marquez:5000',
                'OPENLINEAGE_NAMESPACE': 'olist-dbt',
            },
        )
        log.info(result.stdout)

        if result.returncode != 0:
            log.error(result.stderr)
            raise RuntimeError(f'dbt {command} failed.')

        log.info("dbt %s completed successfully.", command)
    except Exception as e:
        log.error("Error in dbt %s: %s", command, e)
        raise

    context['ti'].xcom_push(key=f'dbt_{command}_status', value='passed')


with DAG(
    dag_id='olist_silver_to_gold',
    default_args=default_args,
    description='Validates Silver layer (GE) and builds Gold layer (dbt against Redshift)',
    schedule_interval=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['silver', 'gold', 'olist', 'dbt'],
    doc_md="""
    ## olist_silver_to_gold

    Triggered by olist_bronze_upload once Silver files are available in S3.

    1. wait_for_silver_orders: S3KeySensor confirms Silver data (reschedule mode)
    2. validate_silver: Great Expectations runs 42 checks on Silver layer
       - XCom: validation_status = 'passed'
    3. TaskGroup dbt_gold:
       - dbt_run: builds 14 models in Redshift
         - XCom: dbt_run_status = 'passed'
       - dbt_test: runs 42 tests
         - XCom: dbt_test_status = 'passed'

    Power BI connects directly via ODBC to Redshift — no CSV export required.
    """,
) as dag:

    # Sensor: ensures Silver data is actually present before GE and dbt start
    # (defensive check, since this DAG is triggered externally)
    wait_for_silver_orders = S3KeySensor(
        task_id='wait_for_silver_orders',
        bucket_name=os.environ.get('S3_BUCKET', 'olist-data-lake-dev'),
        bucket_key='silver/olist_orders_dataset/olist_orders_dataset.parquet',
        aws_conn_id='aws_default',
        poke_interval=30,
        timeout=300,
        mode='reschedule',
    )

    with TaskGroup(group_id='validate_silver') as validate_group:
        validate = PythonOperator(
            task_id='validate_silver',
            python_callable=validate_silver,
        )

    with TaskGroup(group_id='dbt_gold') as dbt_group:

        dbt_run = PythonOperator(
            task_id='dbt_run',
            python_callable=run_dbt,
            op_kwargs={'command': 'run'},
        )

        dbt_test = PythonOperator(
            task_id='dbt_test',
            python_callable=run_dbt,
            op_kwargs={'command': 'test'},
        )

        dbt_run >> dbt_test

    wait_for_silver_orders >> validate_group >> dbt_group
