from airflow import DAG
from airflow.operators.python import ShortCircuitOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime
import os

WATCHED_FILE = "/opt/airflow/dags/points.json"
TIME_THRESHOLD_SECONDS = 60  # Cambios en el último minuto

def check_file_modified_recently(**kwargs):
    if not os.path.exists(WATCHED_FILE):
        print("Archivo no encontrado:", WATCHED_FILE)
        return False

    mtime = os.path.getmtime(WATCHED_FILE)
    now = datetime.now().timestamp()

    if now - mtime <= TIME_THRESHOLD_SECONDS:
        print("✅ Archivo modificado recientemente, triggering...")
        return True
    else:
        print("⏳ Archivo no ha sido modificado recientemente.")
        return False

with DAG(
    dag_id="monitor_points_json_change",
    start_date=datetime(2024, 1, 1),
    schedule_interval="* * * * *",  # cada minuto
    catchup=False,
    description="Monitorea si points.json cambió y lanza DAG de ingestión",
) as dag:

    check_modification = ShortCircuitOperator(
        task_id="check_modification",
        python_callable=check_file_modified_recently,
    )

    trigger_ingestion = TriggerDagRunOperator(
        task_id="trigger_ingestion_dag",
        trigger_dag_id="validate_and_insert_alert",
        execution_date="{{ execution_date }}",  # opcional
        wait_for_completion=False,
        poke_interval=10,
    )

    check_modification >> trigger_ingestion
