from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

DEFAULT_ARGS = {
    "owner": "music-charts",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="music_charts_etl",
    description="Pipeline completo de ingestao, transformacao e carga",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2026, 2, 26),
    schedule=None,
    catchup=False,
    tags=["etl", "music"],
) as dag:
    ingest = BashOperator(
        task_id="ingest_data",
        bash_command="cd /opt/airflow/project && python ingestion/run_ingestion.py",
    )

    transform = BashOperator(
        task_id="transform_data",
        bash_command="cd /opt/airflow/project && python etl/transform.py",
    )

    load = BashOperator(
        task_id="load_data",
        bash_command="cd /opt/airflow/project && python etl/load.py",
    )

    ingest >> transform >> load
