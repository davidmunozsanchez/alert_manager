# tests/test_services.py
import pytest
import requests
from sqlalchemy import create_engine

# Las fixtures usadas (docker_ip, postgres_port, etc.) se importan automáticamente de conftest.py

def test_postgres_connection(docker_ip, postgres_port):
    """Verifica que la base de datos 'db' esté funcional."""
    
    db_url = f'postgresql://postgres:postgres@{docker_ip}:{postgres_port}/alerts'
    engine = create_engine(db_url)
    
    # La conexión debería ser inmediata porque conftest.py garantizó que está listo
    with engine.connect() as conn:
        result = conn.execute("SELECT 1")
        assert result.scalar() == 1


def test_airflow_webserver_health(docker_ip, airflow_webserver_port):
    """Verifica que el servidor web de Airflow responde con 200 en /health."""
    
    url = f'http://{docker_ip}:{airflow_webserver_port}/health'
    
    # La respuesta debería ser 200 porque conftest.py esperó ese estado
    response = requests.get(url, timeout=10)
    
    assert response.status_code == 200


def test_web_service_is_responsive(docker_ip, web_service_port):
    """Verifica que tu servicio 'web' (Uvicorn) está vivo."""
    
    url = f'http://{docker_ip}:{web_service_port}'
    
    response = requests.get(url, timeout=5)
    
    # Un 200 (OK) o 404 (Not Found) indican que Uvicorn está activo
    assert response.status_code in [200, 404]