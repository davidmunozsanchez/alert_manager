import pytest
import requests
from sqlalchemy import create_engine

@pytest.mark.docker
def test_postgres_connection(postgres_service):
    """Test PostgreSQL connection"""
    engine = create_engine(f'postgresql://postgres:postgres@localhost:{postgres_service}/alerts')
    with engine.connect() as conn:
        result = conn.execute("SELECT 1")
        assert result.scalar() == 1

@pytest.mark.docker
def test_airflow_webserver(airflow_service):
    """Test Airflow webserver"""
    response = requests.get(f'http://localhost:{airflow_service}/health')
    assert response.status_code == 200