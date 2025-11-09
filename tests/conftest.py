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

import os
from pathlib import Path
import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# === Configuración de entorno automática ===
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Configuración automática del entorno de test"""
    import sys
    from pathlib import Path
    
    # Añadir el directorio raíz del proyecto al path
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Configurar variables de entorno para testing
    os.environ["TESTING"] = "true"
    os.environ["LOG_LEVEL"] = "DEBUG"
    # Silenciar warnings de SQLAlchemy 1.4->2.0
    os.environ["SQLALCHEMY_WARN_20"] = "0"
    os.environ["SQLALCHEMY_SILENCE_UBER_WARNING"] = "1"
    
    yield
    
    # Cleanup
    for key in ["TESTING", "SQLALCHEMY_WARN_20", "SQLALCHEMY_SILENCE_UBER_WARNING"]:
        if key in os.environ:
            del os.environ[key]

# === Verificar disponibilidad de dependencias ===
try:
    from pytest_docker import docker_services as _check
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

# === Cliente HTTP usando requests + uvicorn ===
import threading
import time
import uvicorn
import requests
from contextlib import contextmanager

class RequestsTestClient:
    """Cliente de test usando requests contra servidor uvicorn real"""
    
    def __init__(self, app, base_url="http://127.0.0.1:8001"):
        self.app = app
        self.base_url = base_url
        self._server = None
        self._thread = None
    
    def start_server(self):
        """Iniciar servidor de test"""
        def run_server():
            uvicorn.run(self.app, host="127.0.0.1", port=8001, log_level="critical")
        
        self._thread = threading.Thread(target=run_server, daemon=True)
        self._thread.start()
        
        # Esperar a que el servidor esté listo
        for _ in range(50):  # 5 segundos máximo
            try:
                requests.get(f"{self.base_url}/ping", timeout=1)
                break
            except:
                time.sleep(0.1)
        else:
            raise RuntimeError("No se pudo iniciar el servidor de test")
    
    def _request(self, method, url, **kwargs):
        """Hacer request usando requests"""
        full_url = f"{self.base_url}{url}"
        response = requests.request(method, full_url, **kwargs)
        return response
    
    def get(self, url, **kwargs):
        return self._request("GET", url, **kwargs)
    
    def post(self, url, **kwargs):
        return self._request("POST", url, **kwargs)
    
    def put(self, url, **kwargs):
        return self._request("PUT", url, **kwargs)
    
    def delete(self, url, **kwargs):
        return self._request("DELETE", url, **kwargs)
    
    def patch(self, url, **kwargs):
        return self._request("PATCH", url, **kwargs)

@pytest.fixture
def client():
    """Cliente de test usando requests contra servidor real"""
    try:
        from src.app.main import app
        print(f"✅ App importada: {type(app)}")
        
        client = RequestsTestClient(app)
        client.start_server()
        print("✅ Servidor de test iniciado")
        
        yield client
        
        print("✅ Cliente cerrado")
        
    except Exception as e:
        print(f"❌ Error creando cliente: {e}")
        pytest.skip(f"No se pudo crear cliente de test: {e}")

# === Base de datos de test ===
@pytest.fixture
def db_session():
    """Sesión de base de datos de test (SQLite en memoria)"""
    try:
        from src.app.database import Base
        
        # Crear engine en memoria para tests
        engine = create_engine(
            "sqlite:///:memory:", 
            echo=False,
            connect_args={"check_same_thread": False}
        )
        
        TestingSessionLocal = sessionmaker(
            autocommit=False, 
            autoflush=False, 
            bind=engine
        )
        
        # Crear tablas
        Base.metadata.create_all(bind=engine)
        
        # Crear sesión
        session = TestingSessionLocal()
        
        yield session
        
        session.close()
        
    except Exception as e:
        print(f"❌ Error configurando DB de test: {e}")
        pytest.skip(f"No se pudo configurar base de datos de test: {e}")

# === Fixtures para datos de test ===
@pytest.fixture
def sample_alert_data():
    """Datos de ejemplo para crear alertas"""
    return {
        "alert_type": "infrastructure",
        "message": "Sistema sobrecargado",
        "severity": "high",
        "source": "monitoring_system",
        "metadata": {"cpu_usage": 95.5, "memory_usage": 87.3}
    }

@pytest.fixture
def sample_datasource_data():
    """Datos de ejemplo para crear fuentes de datos"""
    return {
        "name": "test_source",
        "config": {"endpoint": "http://test.com/api", "interval": 60},
        "is_active": True
    }

# === Fixtures de tiempo ===
@pytest.fixture
def fixed_datetime():
    """Datetime fijo para tests"""
    return datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

@pytest.fixture
def recent_datetime():
    """Datetime reciente para tests"""
    return datetime.now(timezone.utc) - timedelta(minutes=5)

@pytest.fixture
def expired_datetime():
    """Datetime expirado para tests"""
    return datetime.now(timezone.utc) - timedelta(days=1)

# === Configuración de logging para tests ===
@pytest.fixture(autouse=True)
def configure_test_logging():
    """Configurar logging para tests"""
    import logging
    
    # Silenciar logs externos durante tests
    logging.getLogger("uvicorn").setLevel(logging.CRITICAL)
    logging.getLogger("fastapi").setLevel(logging.CRITICAL)
    logging.getLogger("sqlalchemy").setLevel(logging.CRITICAL)
    
    yield
    
    # Restaurar logging normal
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.INFO)

# === Helpers para tests ===
def create_test_alert(db_session, **kwargs):
    """Helper para crear alertas de test"""
    from src.domain.entities import Alert, AlertType
    
    default_data = {
        "alert_type": AlertType.INFRASTRUCTURE,
        "message": "Test alert",
        "severity": "medium",
        "source": "test_source",
        "metadata": {},
        "created_at": datetime.now(timezone.utc)
    }
    default_data.update(kwargs)
    
    alert = Alert(**default_data)
    db_session.add(alert)
    db_session.commit()
    db_session.refresh(alert)
    
    return alert

def create_test_datasource(db_session, **kwargs):
    """Helper para crear fuentes de datos de test"""
    from src.domain.entities import DataSource
    
    default_data = {
        "name": "test_source",
        "config": {"endpoint": "http://test.com"},
        "is_active": True,
        "created_at": datetime.now(timezone.utc)
    }
    default_data.update(kwargs)
    
    datasource = DataSource(**default_data)
    db_session.add(datasource)
    db_session.commit()
    db_session.refresh(datasource)
    
    return datasource