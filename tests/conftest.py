# tests/conftest.py
import pytest
import os
import time

# --- Fixtures de Configuración Global de pytest-docker ---

@pytest.fixture(scope="session")
def docker_compose_file(request):
    """Define la ruta al archivo docker-compose.yml."""
    # MODIFICA ESTA RUTA si tu docker-compose.yml no está en la raíz del proyecto
    # Asumimos que está en la raíz, o ajusta la ruta si es necesario:
    # return os.path.join(os.path.dirname(__file__), '..', 'docker-compose.yml') 
    
    # Si está en la carpeta raíz del proyecto
    return os.path.join(os.path.dirname(__file__), '..', './docker/docker-compose.yml')


@pytest.fixture(scope="session")
def docker_cleanup():
    """Define el comportamiento de limpieza: 'down' detiene y elimina."""
    return 'down' # Es la opción más limpia.


@pytest.fixture(scope="session")
def docker_setup():
    """Comandos adicionales antes de levantar los contenedores (opcional)."""
    return None 

# --- Fixtures de Puntos de Acceso (Espera de Servicios) ---

@pytest.fixture(scope="session")
def postgres_port(docker_services):
    """Espera a que el servicio 'db' esté listo y devuelve el puerto mapeado."""
    # 1. Espera a que el puerto 5432 del servicio 'db' abra
    docker_services.wait_for_service("db", timeout=60.0)
    # 2. Retorna el puerto público asignado al puerto 5432
    return docker_services.get_service_port("db", 5432)


@pytest.fixture(scope="session")
def airflow_webserver_port(docker_services):
    """Espera a que el servicio 'airflow-webserver' esté listo y devuelve el puerto mapeado."""
    # 1. Espera a que el puerto 8080 del servicio 'airflow-webserver' abra
    docker_services.wait_for_service("airflow-webserver", timeout=120.0) 
    # 2. Retorna el puerto público asignado al puerto 8080
    return docker_services.get_service_port("airflow-webserver", 8080)


@pytest.fixture(scope="session")
def web_service_port(docker_services):
    """Espera a que tu servicio 'web' (Uvicorn) esté listo y devuelve el puerto mapeado."""
    # 1. Espera a que el puerto 8000 del servicio 'web' abra
    # El timeout es más largo porque el 'start.sh' hace una espera interna (sleep 5 y wait_db)
    docker_services.wait_for_service("web", timeout=90.0)
    # 2. Retorna el puerto público asignado al puerto 8000
    return docker_services.get_service_port("web", 8000)