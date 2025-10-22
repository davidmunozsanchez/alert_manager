import pytest
import requests
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    return str(pytestconfig.rootdir / "docker/docker-compose.yml")

@pytest.fixture(scope="session")
def postgres_service(docker_services):
    """Ensure that Postgres service is up and responsive."""
    port = docker_services.port_for("db", 5432)
    url = f"postgresql://postgres:postgres@localhost:{port}/alerts"
    engine = create_engine(url)
    docker_services.wait_until_responsive(
        timeout=60.0,
        pause=1,
        check=lambda: _is_postgres_responsive(engine)
    )
    return port

@pytest.fixture(scope="session")
def airflow_service(docker_services):
    """Ensure that Airflow service is up and responsive."""
    port = docker_services.port_for("airflow-webserver", 8080)
    url = f"http://localhost:{port}/health"
    docker_services.wait_until_responsive(
        timeout=120.0,
        pause=2,
        check=lambda: _is_airflow_responsive(url)
    )
    return port

def _is_postgres_responsive(engine):
    try:
        with engine.connect() as conn:
            return conn.execute("SELECT 1").scalar() == 1
    except OperationalError:
        return False

def _is_airflow_responsive(url):
    try:
        response = requests.get(url)
        return response.status_code == 200
    except requests.ConnectionError:
        return False