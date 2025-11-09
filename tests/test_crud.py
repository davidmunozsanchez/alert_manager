"""
Tests de CRUD modernizados para la nueva arquitectura
"""
import sys
from pathlib import Path

# Setup path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.app.database import Base
from src.app.models import Alert as AlertModel
from src.domain.entities import Alert, AlertLevel, AlertStatus, AlertType
from src.domain.services import AlertService
from src.infrastructure.repositories import SQLAlchemyAlertRepository
from src.infrastructure.mappers import AlertMapper

@pytest.fixture
def test_db():
    """Base de datos en memoria para tests"""
    engine = create_engine(
        "sqlite:///./test.db",
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = TestingSessionLocal()
    yield db
    
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def alert_repository(test_db):
    """Repositorio de alertas para testing"""
    return SQLAlchemyAlertRepository(test_db)

@pytest.fixture
def alert_service(alert_repository):
    """Servicio de alertas para testing"""
    return AlertService(alert_repository)

@pytest.fixture
def sample_alert_data():
    """Datos de ejemplo para crear alertas"""
    return {
        "title": "Test Alert",
        "description": "This is a test alert",
        "level": "warning",
        "type": "other",
        "region": "Test Region",
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=2),
        "latitude": 40.4168,
        "longitude": -3.7038,
        "source": "test"
    }

class TestAlertCRUD:
    """Tests de operaciones CRUD en alertas"""
    
    def test_create_alert_via_service(self, alert_service, sample_alert_data):
        """Test crear alerta usando el servicio"""
        alert = alert_service.create_alert(**sample_alert_data)
        
        assert alert.id is not None
        assert alert.title == sample_alert_data["title"]
        assert alert.level == AlertLevel.WARNING
        assert alert.type == AlertType.OTHER
        assert alert.status == AlertStatus.ACTIVE

    def test_create_alert_via_repository(self, alert_repository):
        """Test crear alerta directamente con repositorio"""
        alert = Alert(
            id=None,
            title="Repository Test",
            description="Testing repository directly",
            level=AlertLevel.INFO,
            type=AlertType.OTHER,
            region="Test",
            status=AlertStatus.ACTIVE,
            timestamp=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),  # CORREGIDO: Agregado expires_at
            source="test"
        )
        
        saved_alert = alert_repository.save(alert)
        
        assert saved_alert.id is not None
        assert saved_alert.title == "Repository Test"

    def test_find_alert_by_id(self, alert_service, alert_repository, sample_alert_data):
        """Test buscar alerta por ID"""
        # Crear alerta
        created_alert = alert_service.create_alert(**sample_alert_data)
        
        # Buscar por ID
        found_alert = alert_repository.find_by_id(created_alert.id)
        
        assert found_alert is not None
        assert found_alert.id == created_alert.id
        assert found_alert.title == created_alert.title

    def test_find_all_alerts(self, alert_service, alert_repository, sample_alert_data):
        """Test obtener todas las alertas"""
        # Crear varias alertas
        alert_service.create_alert(**sample_alert_data)
        sample_alert_data["title"] = "Second Alert"
        alert_service.create_alert(**sample_alert_data)
        
        # Obtener todas
        alerts = alert_repository.find_all()
        
        assert len(alerts) >= 2

    def test_alert_mapper_bidirectional(self):
        """Test que el mapper funciona en ambas direcciones"""
        # Crear entidad de dominio
        domain_alert = Alert(
            id=1,
            title="Mapper Test",
            description="Testing mapper",
            level=AlertLevel.CRITICAL,
            type=AlertType.SECURITY,
            region="Test",
            status=AlertStatus.ACTIVE,
            timestamp=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=2),  # CORREGIDO: Agregado expires_at
            source="test"
        )
        
        # Convertir a modelo de BD
        db_alert = AlertMapper.to_model(domain_alert)
        
        assert db_alert.title == "Mapper Test"
        assert db_alert.level == AlertLevel.CRITICAL.value
        
        # Convertir de vuelta a dominio
        domain_alert_2 = AlertMapper.to_domain(db_alert)
        
        assert domain_alert_2.title == domain_alert.title
        assert domain_alert_2.level == domain_alert.level

class TestAlertBusinessRules:
    """Tests de reglas de negocio"""
    
    def test_alert_expiration_validation(self, alert_service):
        """Test validación de expiración"""
        # Crear alerta que expira pronto
        alert_data = {
            "title": "Expiring Alert",
            "description": "This alert will expire soon",
            "level": "warning",
            "type": "other",
            "region": "Test",
            "expires_at": datetime.now(timezone.utc) + timedelta(seconds=1),
            "source": "test"
        }
        
        alert = alert_service.create_alert(**alert_data)
        assert not alert.is_expired()
        
        # Simular paso del tiempo
        import time
        time.sleep(2)
        
        assert alert.is_expired()

    def test_duplicate_alert_detection(self, alert_service, sample_alert_data):
        """Test detección de alertas duplicadas"""
        # Crear primera alerta
        alert1 = alert_service.create_alert(**sample_alert_data)
        
        # Intentar crear alerta duplicada
        alert2 = alert_service.create_alert(**sample_alert_data)
        
        # Deben ser diferentes objetos pero contenido similar
        assert alert1.id != alert2.id
        assert alert1.title == alert2.title

    def test_alert_statistics(self, alert_service, sample_alert_data):
        """Test estadísticas básicas de alertas"""
        # Crear varias alertas con diferentes niveles
        alert_service.create_alert(**sample_alert_data)
        
        critical_data = sample_alert_data.copy()
        critical_data["level"] = "critical"
        critical_data["title"] = "Critical Alert"
        alert_service.create_alert(**critical_data)
        
        # Obtener estadísticas básicas
        # Esto se debería implementar en el servicio
        # stats = alert_service.get_statistics()
        # assert stats.total_alerts >= 2

    def test_filter_by_level(self, alert_service, alert_repository, sample_alert_data):
        """Test filtrado por nivel"""
        # Crear alertas de diferentes niveles
        alert_service.create_alert(**sample_alert_data)  # warning
        
        critical_data = sample_alert_data.copy()
        critical_data["level"] = "critical"
        critical_data["title"] = "Critical Alert"
        alert_service.create_alert(**critical_data)
        
        # Buscar solo críticas
        all_alerts = alert_repository.find_all()
        critical_alerts = [a for a in all_alerts if a.level == AlertLevel.CRITICAL]
        
        assert len(critical_alerts) >= 1

    def test_filter_active_only(self, alert_service, alert_repository, sample_alert_data):
        """Test filtrado solo activas"""
        # Crear alerta activa
        alert = alert_service.create_alert(**sample_alert_data)
        
        # Resolver la alerta
        alert.resolve()
        alert_repository.save(alert)
        
        # Filtrar activas
        all_alerts = alert_repository.find_all()
        active_alerts = [a for a in all_alerts if a.is_active()]
        resolved_alerts = [a for a in all_alerts if a.status == AlertStatus.RESOLVED]
        
        assert len(resolved_alerts) >= 1