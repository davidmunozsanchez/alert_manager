import pytest
import requests
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

@pytest.fixture(scope="session")
def docker_compose_command() -> str:
    return "docker-compose"

# tests/conftest.py
import pytest
import os

# --- Fixtures Requeridas por pytest-docker ---

@pytest.fixture(scope="session")
def docker_compose_file(request):
    """
    Define la ruta al archivo docker-compose.yml.
    Asegúrate de que la ruta sea correcta desde donde se ejecuta pytest (generalmente la raíz).
    """
    # Usamos os.path.join para asegurar la compatibilidad de rutas
    return os.path.join(os.path.dirname(__file__), '..', 'docker', 'docker-compose.yml')


@pytest.fixture(scope="session")
def docker_cleanup():
    """
    Define el comportamiento de limpieza después de las pruebas.
    'stop' detiene contenedores, 'down' detiene y elimina (más limpio).
    """
    return 'down' # Detiene y elimina contenedores y redes. Puedes usar 'down --volumes' si es necesario.


@pytest.fixture(scope="session")
def docker_setup():
    """
    Define comandos de configuración previos a las pruebas (opcional).
    En tu caso, no es estrictamente necesario ya que start.sh se encarga de la espera.
    """
    return None # No se requiere configuración adicional por defecto.

# --- Fixture para esperar servicios (la clave para tu prueba) ---

# Usa la fixture built-in 'docker_ip' y 'docker_services' de pytest-docker
# Esta fixture usa 'docker_services' (que ahora se inicializa correctamente)
# para esperar a que un servicio esté listo antes de ejecutar una prueba.
@pytest.fixture(scope="session")
def wait_for_postgres(docker_ip, docker_services):
    """
    Espera a que el servicio 'db' esté listo antes de que comiencen las pruebas.
    """
    # Tu servicio 'db' está en el puerto 5432
    port = 5432
    
    # El método .wait_for_service() esperará automáticamente hasta que el puerto 5432 
    # del contenedor 'db' esté abierto y acepte conexiones.
    docker_services.wait_for_service("db", timeout=30.0) 
    
    # Si necesitas una prueba más exhaustiva (ejecutar un comando SQL), 
    # usa docker_services.wait_until_responsive() con una función de chequeo.
    
    return True # Indica que el servicio está listo