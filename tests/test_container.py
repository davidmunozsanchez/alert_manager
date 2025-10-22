# tests/test_services.py
import pytest
import requests
from sqlalchemy import create_engine
import time

# Las fixtures usadas (docker_ip, postgres_port, etc.) se definen en conftest.py

def test_postgres_connection(docker_ip, postgres_port):
    """Verifica que la base de datos 'db' esté accesible y pueda ejecutar una consulta."""
    
    # Usa docker_ip (IP del host) y el puerto dinámico
    db_url = f'postgresql://postgres:postgres@{docker_ip}:{postgres_port}/alerts'
    
    max_retries = 5
    for i in range(max_retries):
        try:
            # 1. Crea el motor de SQLAlchemy
            engine = create_engine(db_url)
            
            # 2. Intenta la conexión y ejecuta una consulta simple (SELECT 1)
            with engine.connect() as conn:
                result = conn.execute("SELECT 1")
                assert result.scalar() == 1
                print(f"\n✅ Conexión a PostgreSQL exitosa en {docker_ip}:{postgres_port}.")
                return
        except Exception as e:
            if i < max_retries - 1:
                # La DB puede estar levantada pero no lista para conexiones
                print(f"PostgreSQL aún no está listo. Reintentando en 5s... ({i+1}/{max_retries})")
                time.sleep(5)
            else:
                pytest.fail(f"🔴 Fallo en la conexión a PostgreSQL después de {max_retries} intentos: {e}")


def test_airflow_webserver_health(docker_ip, airflow_webserver_port):
    """Verifica que el endpoint /health del servidor web de Airflow responde con 200."""
    
    # Airflow requiere un tiempo largo para inicializarse
    url = f'http://{docker_ip}:{airflow_webserver_port}/health'
    
    max_retries = 10
    for i in range(max_retries):
        try:
            # 1. Realiza una solicitud GET
            response = requests.get(url, timeout=10)
            
            # 2. Verifica que la respuesta sea 200 (OK)
            assert response.status_code == 200
            print(f"\n✅ Airflow Webserver respondió con código {response.status_code} en {url}.")
            return
        except requests.exceptions.RequestException as e:
            if i < max_retries - 1:
                print(f"Airflow Webserver aún no responde. Reintentando en 5s... ({i+1}/{max_retries})")
                time.sleep(5)
            else:
                pytest.fail(f"🔴 Fallo al conectar o recibir respuesta de Airflow Webserver después de {max_retries} intentos: {e}")


def test_web_service_is_responsive(docker_ip, web_service_port):
    """Verifica que tu servicio 'web' (Uvicorn) es accesible en la raíz."""
    
    url = f'http://{docker_ip}:{web_service_port}'
    print(f"\nComprobando servicio web en: {url}")

    # Tu servicio web ya pasó la espera inicial en la fixture 'web_service_port'
    try:
        response = requests.get(url, timeout=5)
        
        # 1. Verifica que el servicio está vivo (200 OK o 404 Not Found, si no hay ruta en la raíz)
        assert response.status_code in [200, 404]
        print(f"✅ Servicio 'web' respondió con código {response.status_code}.")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"🔴 Fallo al conectar con el servicio web {url}: {e}")