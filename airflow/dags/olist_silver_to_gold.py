from datetime import datetime, timedelta
import logging
import subprocess
import sys
import os

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


def validate_silver(**context) -> None:
    """Führt Great Expectations Silver Validation aus.

    Schlägt fehl wenn ein Check nicht besteht — dbt startet dann nicht.
    XCom: validation_status = 'passed'
    """
    log.info("Starte Great Expectations Silver Validation...")

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
            raise RuntimeError('Silver Validation fehlgeschlagen — dbt wird nicht gestartet.')

        log.info("Silver Validation erfolgreich: alle Checks bestanden.")
    except Exception as e:
        log.error("Fehler in validate_silver: %s", e)
        raise

    context['ti'].xcom_push(key='validation_status', value='passed')


def run_dbt(command: str, **context) -> None:
    """Führt einen dbt Befehl gegen Redshift (prod) aus.

    command: 'run' oder 'test'
    XCom: dbt_<command>_status = 'passed'
    """
    log.info("Starte dbt %s --target prod...", command)

    try:
        result = subprocess.run(
            ['dbt', command, '--no-partial-parse', '--target', 'prod', '--profiles-dir', f'{ROOT}/dbt'],
            cwd=f'{ROOT}/dbt',
            capture_output=True,
            text=True,
            env={
                **os.environ,
                'REDSHIFT_PASSWORD': os.environ['REDSHIFT_PASSWORD'],
                # Lineage-Events an Marquez senden (läuft im selben Docker-Netzwerk)
                'OPENLINEAGE_URL': 'http://marquez:5000',
                'OPENLINEAGE_NAMESPACE': 'olist-dbt',
            },
        )
        log.info(result.stdout)

        if result.returncode != 0:
            log.error(result.stderr)
            raise RuntimeError(f'dbt {command} fehlgeschlagen.')

        log.info("dbt %s erfolgreich abgeschlossen.", command)
    except Exception as e:
        log.error("Fehler in dbt %s: %s", command, e)
        raise

    context['ti'].xcom_push(key=f'dbt_{command}_status', value='passed')


with DAG(
    dag_id='olist_silver_to_gold',
    default_args=default_args,
    description='Validiert Silver Layer (GE) und baut Gold Layer (dbt gegen Redshift)',
    schedule_interval=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['silver', 'gold', 'olist', 'dbt'],
    doc_md="""
    ## olist_silver_to_gold

    Wird von olist_bronze_upload getriggert nachdem Silver-Dateien in S3 vorliegen.

    1. wait_for_silver_orders: S3KeySensor bestätigt Silver-Daten (reschedule mode)
    2. validate_silver: Great Expectations prüft 42 Checks auf Silver Layer
       - XCom: validation_status = 'passed'
    3. TaskGroup dbt_gold:
       - dbt_run: baut 14 Modelle in Redshift
         - XCom: dbt_run_status = 'passed'
       - dbt_test: führt 42 Tests aus
         - XCom: dbt_test_status = 'passed'

    Power BI verbindet sich direkt per ODBC mit Redshift — kein CSV Export nötig.
    """,
) as dag:

    # Sensor: sicherstellt dass Silver-Daten wirklich vorhanden sind
    # bevor GE und dbt starten (defensiv, da DAG extern getriggert wird)
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
