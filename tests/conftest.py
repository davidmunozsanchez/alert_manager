from pathlib import Path
import os
import pytest

@pytest.fixture(scope="session")
def docker_compose_command():
    # Forzar el uso de "docker compose" (v2) en GitHub Actions
    return "docker compose"

@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    # Usa el compose del proyecto
    root = Path(pytestconfig.rootdir)
    return str(root / "docker" / "docker-compose.yml")



@pytest.fixture(scope="session")
def wait_for(docker_services, timeout=180.0, pause=3.0):
    # Helper para esperar con backoff
    def _wait(check, timeout=timeout, pause=pause):
        def check_with_exception_handling():
            try:
                return check()
            except Exception:
                return False
        docker_services.wait_until_responsive(
            timeout=timeout, 
            pause=pause, 
            check=check_with_exception_handling
        )
    return _wait

@pytest.fixture(scope="session")
def db_dsn(docker_services, docker_ip):
    port = docker_services.port_for("db", 5432)
    return f"postgresql://postgres:postgres@{docker_ip}:{port}/alerts"

@pytest.fixture(scope="session")
def airflow_url(docker_services, docker_ip):
    port = docker_services.port_for("airflow-webserver", 8080)
    return f"http://{docker_ip}:{port}/health"

# @pytest.fixture(scope="session")
# def web_url(docker_services, docker_ip):
#     port = docker_services.port_for("web", 8000)
#     return f"http://{docker_ip}:{port}"