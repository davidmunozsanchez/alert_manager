# tests/conftest.py
import pytest
import os
import requests
from sqlalchemy import create_engine

# --- CONFIGURACIÓN DE RUTAS Y POLÍTICAS DE LIMPIEZA ---

@pytest.fixture(scope="session")
def docker_compose_file(request):
    """
    Define la ruta al archivo docker-compose.yml.
    
    ASUME: La estructura es: 
    - proyecto/
        - docker/
            - docker-compose.yml  <-- Archivo
        - tests/
            - conftest.py         <-- Este archivo
            - test_services.py
    """
    # Se añade 'docker' a la ruta para apuntar a la carpeta correcta
    return os.path.join(os.path.dirname(__file__), '..', 'docker', 'docker-compose.yml')


@pytest.fixture(scope="session")
def docker_cleanup():
    """Política de limpieza: detiene y elimina contenedores al finalizar."""
    return 'down' 


@pytest.fixture(scope="session")
def docker_setup():
    """Comandos adicionales antes de levantar los contenedores (opcional)."""
    return None 

# -------------------------------------------------------------------
# --- FIXTURE CLAVE: wait_for_services (CORRIGE EL ERROR) ---
# -------------------------------------------------------------------

@pytest.fixture(scope="session")
def wait_for_services():
    """
    Define la función de chequeo de salud para cada servicio. 
    Asegura que los servicios estén listos ANTES de que se ejecuten los tests.
    """
    
    def wait_for_postgres(ip, port):
        """Intenta conectar a PostgreSQL para verificar que está listo."""
        try:
            db_url = f'postgresql://postgres:postgres@{ip}:{port}/alerts'
            engine = create_engine(db_url, connect_args={'connect_timeout': 5})
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            return True 
        except Exception:
            return False 

    def wait_for_airflow_webserver(ip, port):
        """Comprueba el endpoint /health de Airflow."""
        try:
            url = f'http://{ip}:{port}/health'
            response = requests.get(url, timeout=5) 
            return response.status_code == 200 
        except requests.exceptions.RequestException:
            return False

    def wait_for_web_service(ip, port):
        """Comprueba el servicio Python/Uvicorn en el puerto 8000."""
        try:
            url = f'http://{ip}:{port}'
            response = requests.get(url, timeout=5)
            return response.status_code in [200, 404] 
        except requests.exceptions.RequestException:
            return False

    return {
        # Mapeo: "nombre_servicio": (puerto_interno, función_de_chequeo)
        "db": (5432, wait_for_postgres),
        "airflow-webserver": (8080, wait_for_airflow_webserver),
        "web": (8000, wait_for_web_service),
    }

# --- FIXTURES DE PUERTOS PARA ACCESO DIRECTO EN LOS TESTS ---

@pytest.fixture(scope="session")
def postgres_port(docker_services):
    """Devuelve el puerto mapeado para el servicio 'db'."""
    return docker_services.port_for("db", 5432)

@pytest.fixture(scope="session")
def airflow_webserver_port(docker_services):
    """Devuelve el puerto mapeado para Airflow Webserver."""
    return docker_services.port_for("airflow-webserver", 8080)

@pytest.fixture(scope="session")
def web_service_port(docker_services):
    """Devuelve el puerto mapeado para el servicio web."""
    return docker_services.port_for("web", 8000)