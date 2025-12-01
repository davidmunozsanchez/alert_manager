import os
import json
import requests
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

log = logging.getLogger(__name__)

# --- Helpers de normalización ---
def map_aemet_level(nivel: Optional[str]) -> str:
    mapping = {
        "rojo": "emergency",
        "naranja": "critical",
        "amarillo": "warning",
        "verde": "info",
    }
    if not nivel:
        return "info"
    return mapping.get(nivel.lower(), "info")

def normalize_aviso(aviso: Dict[str, Any]) -> Dict[str, Any]:
    """Normaliza un aviso AEMET al formato de la app."""
    return {
        "title": aviso.get("titulo") or aviso.get("denominacion") or "Aviso AEMET",
        "description": aviso.get("texto") or aviso.get("descripcion") or "",
        "level": map_aemet_level(aviso.get("nivel")),
        "type": "weather",
        "region": aviso.get("provincia") or aviso.get("comunidad") or aviso.get("zona") or "Desconocido",
        "timestamp": aviso.get("fecha") or datetime.now(timezone.utc).isoformat(),
        "expires_at": aviso.get("fechaFin") or aviso.get("fecha_fin") or None,
        "source": "AEMET",
    }

# --- Tasks ---
def fetch_and_store_aemet(**kwargs) -> str:
    """
    Llama a la API de AEMET y guarda un JSON normalizado en disco.
    Requiere la variable de entorno AEMET_API_KEY.
    """
    api_key = os.getenv("AEMET_API_KEY")
    if not api_key:
        raise RuntimeError("AEMET_API_KEY no está configurada en las variables de entorno")

    base_url = "https://opendata.aemet.es/opendata/api/avisos_cap"
    params = {"api_key": api_key}

    log.info("Consultando AEMET: %s", base_url)
    resp = requests.get(base_url, params=params, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    data_url = payload.get("datos")
    if not data_url:
        raise RuntimeError(f"Respuesta de AEMET no contiene 'datos': {payload}")

    data_resp = requests.get(data_url, timeout=30)
    data_resp.raise_for_status()
    raw = data_resp.json()

    normalized: List[Dict[str, Any]] = []
    for aviso in raw:
        try:
            normalized.append(normalize_aviso(aviso))
        except Exception as e:
            log.warning("Error normalizando aviso: %s - %s", e, aviso)

    out_dir = os.getenv("AIRFLOW_DATA_DIR", "/opt/airflow/data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "alerts_data.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(normalized, f, ensure_ascii=False, indent=2)

    log.info("Guardados %d avisos normalizados en %s", len(normalized), out_path)
    return out_path

def process_downloaded_alerts(**kwargs) -> None:
    """
    Lee el archivo generado y opcionalmente publica cada aviso en la API web.
    Si no está configurada WEB_API_URL, solo deja el archivo en disco.
    """
    out_dir = os.getenv("AIRFLOW_DATA_DIR", "/opt/airflow/data")
    path = os.path.join(out_dir, "alerts_data.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Archivo no encontrado: {path}")

    with open(path, "r", encoding="utf-8") as f:
        alerts = json.load(f)

    log.info("Procesando %d avisos desde %s", len(alerts), path)

    web_api = os.getenv("WEB_API_URL")
    if web_api:
        headers = {"Content-Type": "application/json"}
        sent = 0
        for a in alerts:
            try:
                r = requests.post(web_api, json=a, headers=headers, timeout=10)
                if r.status_code in (200, 201):
                    sent += 1
                else:
                    log.warning("Fallo al postear alerta: %s %s", r.status_code, r.text)
            except Exception as e:
                log.exception("Error enviando alerta a API: %s", e)
        log.info("Enviadas %d/%d alertas a %s", sent, len(alerts), web_api)
    else:
        log.info("WEB_API_URL no configurada: avisos guardados en disco en %s", path)

# --- DAG definition ---
default_args = {
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="aemet_alerts_ingestion",
    start_date=datetime(2024, 1, 1),
    schedule_interval="0 * * * *",  # cada hora
    catchup=False,
    description="Descarga avisos de AEMET Open Data, normaliza y los procesa",
    default_args=default_args,
) as dag:

    download_task = PythonOperator(
        task_id="fetch_and_store_aemet",
        python_callable=fetch_and_store_aemet,
        provide_context=True,
    )

    process_task = PythonOperator(
        task_id="process_downloaded_alerts",
        python_callable=process_downloaded_alerts,
        provide_context=True,
    )

    trigger_processing = TriggerDagRunOperator(
        task_id="trigger_alert_processing",
        trigger_dag_id="validate_and_insert_alert",  # DAG que procesa/inyecta las alertas en la BD
        execution_date="{{ execution_date }}",
        wait_for_completion=False,
        poke_interval=10,
    )

    download_task >> process_task >> trigger_processing