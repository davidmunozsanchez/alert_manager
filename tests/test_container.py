# tests/test_integration.py
import pytest
import requests
from sqlalchemy import create_engine
import time

# --- Constantes de Acceso (Usando los puertos fijos de docker-compose) ---
DB_URL = 'postgresql://postgres:postgres@localhost:5432/alerts'
AIRFLOW_URL = 'http://localhost:8080/health'
WEB_URL = 'http://localhost:8000'

MAX_RETRIES = 15  # Máximo de intentos para esperar a los servicios (ajustar si es necesario)
RETRY_DELAY = 5   # Retraso en segundos entre reintentos

# --- Funciones de Utilidad (para reintentos) ---

def wait_for_service(check_func, service_name):
    """Espera que una función de chequeo sea True."""
    for i in range(MAX_RETRIES):
        try:
            if check_func():
                print(f"🟢 Servicio {service_name} listo después de {i+1} intentos.")
                return
            else:
                raise Exception("El chequeo devolvió False.")
        except Exception as e:
            if i < MAX_RETRIES - 1:
                print(f"⏳ {service_name} no está listo. Reintentando en {RETRY_DELAY}s... ({i+1}/{MAX_RETRIES})")
                time.sleep(RETRY_DELAY)
            else:
                pytest.fail(f"🔴 Fallo al conectar con {service_name} después de {MAX_RETRIES} intentos: {e}")

# --- Tests ---

def test_01_wait_for_database():
    """Espera y verifica la conexión a PostgreSQL antes de otros tests."""
    def check_db():
        engine = create_engine(DB_URL, connect_args={'connect_timeout': 3})
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            return result.scalar() == 1
    
    wait_for_service(check_db, "PostgreSQL DB")
    # Este test solo asegura que la DB está viva para los siguientes tests.

def test_02_web_service_is_responsive():
    """Verifica que el servicio 'web' (Uvicorn) está vivo."""
    def check_web():
        response = requests.get(WEB_URL, timeout=5)
        return response.status_code in [200, 404]
    
    # El servicio 'web' tiene dependencia en 'db' en docker-compose, así que debería arrancar después
    wait_for_service(check_web, "Web Service")
    

def test_03_airflow_webserver_health():
    """Verifica que el endpoint /health del servidor web de Airflow responde con 200."""
    def check_airflow():
        response = requests.get(AIRFLOW_URL, timeout=5)
        return response.status_code == 200
        
    wait_for_service(check_airflow, "Airflow Webserver")