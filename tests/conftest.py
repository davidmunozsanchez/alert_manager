import pytest
from pytest_docker.plugin import get_docker_services

@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    return str(pytestconfig.rootdir / "docker/docker-compose.yml")

@pytest.fixture(scope="session")
def docker_services(docker_compose_file):
    """Start all services from docker-compose."""
    return get_docker_services(docker_compose_file)

@pytest.fixture(scope="session")
def postgres_service(docker_services):
    """Ensure that Postgres service is up and responsive."""
    port = docker_services.port_for("db", 5432)
    docker_services.wait_until_responsive(
        timeout=30.0,
        pause=0.1,
        check=lambda: docker_services.port_for("db", 5432) is not None
    )
    return port

@pytest.fixture(scope="session")
def airflow_service(docker_services):
    """Ensure that Airflow service is up and responsive."""
    port = docker_services.port_for("airflow-webserver", 8080)
    docker_services.wait_until_responsive(
        timeout=30.0,
        pause=0.1,
        check=lambda: docker_services.port_for("airflow-webserver", 8080) is not None
    )
    return port