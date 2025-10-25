import json
import os
import traceback
from datetime import datetime

import psycopg2
from airflow import DAG
from airflow.operators.python import PythonOperator


def validate_and_insert():
    try:
        print("Iniciando validación e inserción de alertas...")

        json_path = "/opt/airflow/dags/points.json"
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"El archivo no existe: {json_path}")

        required_fields = ["title", "description", "level", "type", "region", "status", "expires_at", "latitude", "longitude"]

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            data = [data]

        for idx, alert in enumerate(data):
            for field in required_fields:
                if field not in alert:
                    raise ValueError(f"El punto {idx} no tiene el campo requerido: {field}")
            if not (-90 <= alert["latitude"] <= 90):
                raise ValueError(f"Latitud fuera de rango en punto {idx}")
            if not (-180 <= alert["longitude"] <= 180):
                raise ValueError(f"Longitud fuera de rango en punto {idx}")

        print(f"Validación completada: {len(data)} alertas válidas.")

        # Insertar en PostgreSQL
        conn = psycopg2.connect(dbname="alerts", user="postgres", password="postgres", host="db", port=5432)
        cur = conn.cursor()
        for alert in data:
            cur.execute(
                """
                INSERT INTO alerts (
                    title, description, level, type, region, status,
                    expires_at, timestamp, latitude, longitude
                ) VALUES (
                    %(title)s, %(description)s, %(level)s, %(type)s, %(region)s, %(status)s,
                    %(expires_at)s, NOW(), %(latitude)s, %(longitude)s
                )
            """,
                alert,
            )
        conn.commit()
        cur.close()
        conn.close()

        print("Inserción completada correctamente en la base de datos.")

    except Exception as e:
        print("❌ Error durante la ejecución del DAG:")
        traceback.print_exc()
        raise  # Para que Airflow registre el fallo y lo muestre en UI/logs


with DAG(
    dag_id="validate_and_insert_alert",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    description="Valida alertas y las inserta en PostgreSQL",
) as dag:
    task = PythonOperator(task_id="validate_and_insert", python_callable=validate_and_insert)
