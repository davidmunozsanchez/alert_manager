import os
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def docker_compose_command():
    if os.getenv("GITHUB_ACTIONS") or os.getenv("CI"):
        return "docker compose"
    return "docker-compose"


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    root = Path(pytestconfig.rootdir)
    return str(root / "docker" / "docker-compose.yml")


@pytest.fixture(scope="session")
def wait_for(docker_services, timeout=180.0, pause=3.0):
    """Helper para esperar con backoff"""

    def _wait(check, timeout=timeout, pause=pause):
        def check_with_exception_handling():
            try:
                return check()
            except Exception:
                return False

        docker_services.wait_until_responsive(timeout=timeout, pause=pause, check=check_with_exception_handling)

    return _wait


@pytest.fixture(scope="session")
def db_dsn(docker_services, docker_ip):
    """DSN para conectar a PostgreSQL usando las mismas variables que docker-compose"""
    port = docker_services.port_for("db", 5432)
    
    # Usar las mismas variables de entorno que docker-compose.yml
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_password = os.getenv("POSTGRES_PASSWORD", "postgres") 
    db_name = os.getenv("POSTGRES_DB", "alerts")
    
    return f"postgresql://{db_user}:{db_password}@{docker_ip}:{port}/{db_name}"


@pytest.fixture(scope="session")
def airflow_url(docker_services, docker_ip):
    """URL para Airflow webserver"""
    port = docker_services.port_for("airflow-webserver", 8080)
    return f"http://{docker_ip}:{port}/health"


@pytest.fixture(scope="session")
def web_url(docker_services, docker_ip):
    """URL para el servicio web/API"""
    port = docker_services.port_for("web", 8000)
    return f"http://{docker_ip}:{port}"


@pytest.fixture(scope="session")
def web_health_url(web_url):
    """URL del health check del servicio web"""
    return f"{web_url}/alerts/health"
