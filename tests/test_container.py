import pytest
import requests
import time
from sqlalchemy import create_engine

def test_postgres_connection():
    """Test PostgreSQL database connection"""
    try:
        engine = create_engine('postgresql://postgres:postgres@localhost:5432/alerts')
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            assert result.scalar() == 1
    except Exception as e:
        pytest.fail(f"Database connection failed: {e}")

def test_airflow_webserver():
    """Test Airflow webserver is running"""
    try:
        response = requests.get('http://localhost:8080/health')
        assert response.status_code == 200
    except requests.exceptions.ConnectionError:
        pytest.fail("Airflow webserver is not responding")

def test_web_service():
    """Test web service is running"""
    try:
        response = requests.get('http://localhost:8000/health')
        assert response.status_code == 200
    except requests.exceptions.ConnectionError:
        pytest.fail("Web service is not responding")

def test_airflow_scheduler():
    """Test Airflow scheduler is running"""
    try:
        result = requests.get('http://localhost:8080/api/v1/dags')
        assert result.status_code in [200, 401], "Scheduler API endpoint not available"
    except requests.exceptions.ConnectionError:
        pytest.fail("Airflow scheduler is not responding")