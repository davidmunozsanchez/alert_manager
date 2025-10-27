# tests/test_crud.py

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

os.environ["TESTING"] = "1"

from app.database import Base
from app.models import Alert
from app.schemas import AlertCreate, AlertLevel
from app import crud

@pytest.fixture(scope="function")
def test_db():
    """Crea una base de datos SQLite en memoria para cada test"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    
    yield db
    
    db.close()



@pytest.fixture
def sample_alert_data():
    """Datos de ejemplo para tests"""
    return {
        "title": "Tormenta severa",
        "description": "Fuertes lluvias y vientos",
        "level": AlertLevel.alta,
        "type": "meteorológica",
        "region": "Madrid",
        "status": "activo",
        "expires_at": datetime.utcnow() + timedelta(hours=6),
        "latitude": 40.4168,
        "longitude": -3.7038
    }


# ========================================
# TESTS TDD: Create Alert
# ========================================

def test_create_alert_success(test_db, sample_alert_data):
    """Test: Crear una alerta válida debe retornar la alerta con ID"""
    alert_create = AlertCreate(**sample_alert_data)
    
    result = crud.create_alert(test_db, alert_create)
    
    assert result.id is not None
    assert result.title == sample_alert_data["title"]
    assert result.level == sample_alert_data["level"]
    assert result.status == "activo"
    assert result.timestamp is not None


def test_create_alert_persists_in_db(test_db, sample_alert_data):
    """Test: Alerta creada debe persistir en la base de datos"""
    alert_create = AlertCreate(**sample_alert_data)
    
    created_alert = crud.create_alert(test_db, alert_create)
    
    # Verificar que existe en DB
    db_alert = test_db.query(Alert).filter(Alert.id == created_alert.id).first()
    assert db_alert is not None
    assert db_alert.title == sample_alert_data["title"]


def test_create_alert_with_coordinates(test_db, sample_alert_data):
    """Test: Alerta debe incluir coordenadas geográficas"""
    alert_create = AlertCreate(**sample_alert_data)
    
    result = crud.create_alert(test_db, alert_create)
    
    assert result.latitude == pytest.approx(40.4168, abs=0.001)
    assert result.longitude == pytest.approx(-3.7038, abs=0.001)


# ========================================
# TESTS TDD: Get Alerts
# ========================================

def test_get_alerts_empty_database(test_db):
    """Test: Consultar alertas en BD vacía debe retornar lista vacía"""
    result = crud.get_alerts(test_db)
    
    assert result == []


def test_get_alerts_returns_all(test_db, sample_alert_data):
    """Test: get_alerts debe retornar todas las alertas activas"""
    # Crear 3 alertas
    for i in range(3):
        data = sample_alert_data.copy()
        data["title"] = f"Alerta {i}"
        crud.create_alert(test_db, AlertCreate(**data))
    
    result = crud.get_alerts(test_db)
    
    assert len(result) == 3


def test_get_alerts_pagination(test_db, sample_alert_data):
    """Test: Paginación debe limitar resultados correctamente"""
    # Crear 10 alertas
    for i in range(10):
        data = sample_alert_data.copy()
        data["title"] = f"Alerta {i}"
        crud.create_alert(test_db, AlertCreate(**data))
    
    # Primera página (skip=0, limit=5)
    page1 = crud.get_alerts(test_db, skip=0, limit=5)
    assert len(page1) == 5
    
    # Segunda página (skip=5, limit=5)
    page2 = crud.get_alerts(test_db, skip=5, limit=5)
    assert len(page2) == 5
    
    # Páginas no deben solaparse
    page1_ids = {a.id for a in page1}
    page2_ids = {a.id for a in page2}
    assert page1_ids.isdisjoint(page2_ids)


def test_get_alerts_auto_expires(test_db, sample_alert_data):
    """Test: Alertas expiradas deben cambiar automáticamente a 'inactivo'"""
    # Crear alerta expirada (expires_at en el pasado)
    data = sample_alert_data.copy()
    data["expires_at"] = datetime.utcnow() - timedelta(hours=1)
    data["status"] = "activo"
    
    created = crud.create_alert(test_db, AlertCreate(**data))
    assert created.status == "activo"  # Aún activo al crear
    
    # Llamar get_alerts (debe actualizar status)
    crud.get_alerts(test_db)
    
    # Verificar que ahora está inactivo
    test_db.refresh(created)
    assert created.status == "inactivo"


# ========================================
# TESTS TDD: Get Alerts by Community
# ========================================

def test_get_alerts_by_community_filter_by_region(test_db, sample_alert_data):
    """Test: Filtrar por comunidad debe retornar solo alertas de esa región"""
    # Crear alertas de diferentes regiones
    madrid_data = sample_alert_data.copy()
    madrid_data["region"] = "Madrid"
    madrid_data["title"] = "Alerta Madrid"
    
    barcelona_data = sample_alert_data.copy()
    barcelona_data["region"] = "Barcelona"
    barcelona_data["title"] = "Alerta Barcelona"
    
    crud.create_alert(test_db, AlertCreate(**madrid_data))
    crud.create_alert(test_db, AlertCreate(**barcelona_data))
    
    # Filtrar por Madrid
    result = crud.get_alerts_by_community(test_db, community_name="Madrid")
    
    assert len(result) == 1
    assert result[0].region == "Madrid"


def test_get_alerts_by_community_filter_by_type(test_db, sample_alert_data):
    """Test: Filtrar por tipo debe retornar solo alertas de ese tipo"""
    # Crear alertas de diferentes tipos
    weather_data = sample_alert_data.copy()
    weather_data["type"] = "meteorológica"
    
    traffic_data = sample_alert_data.copy()
    traffic_data["type"] = "tráfico"
    
    crud.create_alert(test_db, AlertCreate(**weather_data))
    crud.create_alert(test_db, AlertCreate(**traffic_data))
    
    result = crud.get_alerts_by_community(test_db, type="meteorológica")
    
    assert len(result) == 1
    assert result[0].type == "meteorológica"


def test_get_alerts_by_community_multiple_filters(test_db, sample_alert_data):
    """Test: Múltiples filtros deben aplicarse con AND lógico"""
    # Crear alertas con diferentes combinaciones
    alert1 = sample_alert_data.copy()
    alert1["region"] = "Madrid"
    alert1["type"] = "meteorológica"
    alert1["level"] = AlertLevel.alta
    
    alert2 = sample_alert_data.copy()
    alert2["region"] = "Madrid"
    alert2["type"] = "tráfico"
    alert2["level"] = AlertLevel.alta
    
    alert3 = sample_alert_data.copy()
    alert3["region"] = "Barcelona"
    alert3["type"] = "meteorológica"
    alert3["level"] = AlertLevel.alta
    
    crud.create_alert(test_db, AlertCreate(**alert1))
    crud.create_alert(test_db, AlertCreate(**alert2))
    crud.create_alert(test_db, AlertCreate(**alert3))
    
    # Filtrar: Madrid + meteorológica + alta
    result = crud.get_alerts_by_community(
        test_db,
        community_name="Madrid",
        type="meteorológica",
        priority="alta"
    )
    
    assert len(result) == 1
    assert result[0].region == "Madrid"
    assert result[0].type == "meteorológica"


def test_get_alerts_by_community_case_insensitive(test_db, sample_alert_data):
    """Test: Filtro de región debe ser case-insensitive"""
    data = sample_alert_data.copy()
    data["region"] = "Comunidad de Madrid"
    
    crud.create_alert(test_db, AlertCreate(**data))
    
    # Buscar con diferentes casos
    result1 = crud.get_alerts_by_community(test_db, community_name="madrid")
    result2 = crud.get_alerts_by_community(test_db, community_name="MADRID")
    result3 = crud.get_alerts_by_community(test_db, community_name="Madrid")
    
    assert len(result1) == 1
    assert len(result2) == 1
    assert len(result3) == 1


# ========================================
# TESTS TDD: Get Inactive Alerts
# ========================================

def test_get_inactive_alerts_only_returns_inactive(test_db, sample_alert_data):
    """Test: Debe retornar solo alertas con status='inactivo'"""
    # Crear alertas activas e inactivas
    active_data = sample_alert_data.copy()
    active_data["status"] = "activo"
    
    inactive_data = sample_alert_data.copy()
    inactive_data["status"] = "inactivo"
    
    crud.create_alert(test_db, AlertCreate(**active_data))
    crud.create_alert(test_db, AlertCreate(**inactive_data))
    
    result = crud.get_inactive_alerts(test_db)
    
    assert len(result) == 1
    assert result[0].status == "inactivo"


# ========================================
# TESTS TDD: Reactivate Alert
# ========================================

def test_reactivate_alert_changes_status(test_db, sample_alert_data):
    """Test: Reactivar alerta debe cambiar status a 'activo'"""
    data = sample_alert_data.copy()
    data["status"] = "inactivo"
    
    alert = crud.create_alert(test_db, AlertCreate(**data))
    assert alert.status == "inactivo"
    
    reactivated = crud.reactivate_alert(test_db, alert.id)
    
    assert reactivated.status == "activo"


def test_reactivate_alert_persists_change(test_db, sample_alert_data):
    """Test: Reactivación debe persistir en base de datos"""
    data = sample_alert_data.copy()
    data["status"] = "inactivo"
    
    alert = crud.create_alert(test_db, AlertCreate(**data))
    crud.reactivate_alert(test_db, alert.id)
    
    # Consultar directamente la BD
    db_alert = test_db.query(Alert).filter(Alert.id == alert.id).first()
    assert db_alert.status == "activo"


def test_reactivate_nonexistent_alert(test_db):
    """Test: Reactivar alerta inexistente debe retornar None"""
    result = crud.reactivate_alert(test_db, 99999)
    
    assert result is None


# ========================================
# TESTS TDD: Deactivate Alert
# ========================================

def test_deactivate_alert_changes_status(test_db, sample_alert_data):
    """Test: Desactivar alerta debe cambiar status a 'inactivo'"""
    alert = crud.create_alert(test_db, AlertCreate(**sample_alert_data))
    assert alert.status == "activo"
    
    deactivated = crud.deactivate_alert(test_db, alert.id)
    
    assert deactivated.status == "inactivo"


def test_deactivate_alert_persists_change(test_db, sample_alert_data):
    """Test: Desactivación debe persistir en base de datos"""
    alert = crud.create_alert(test_db, AlertCreate(**sample_alert_data))
    crud.deactivate_alert(test_db, alert.id)
    
    db_alert = test_db.query(Alert).filter(Alert.id == alert.id).first()
    assert db_alert.status == "inactivo"


# ========================================
# TESTS TDD: Edge Cases
# ========================================

def test_create_alert_with_very_long_description(test_db, sample_alert_data):
    """Test: Descripción muy larga debe manejarse correctamente"""
    data = sample_alert_data.copy()
    data["description"] = "x" * 10000  # 10k caracteres
    
    result = crud.create_alert(test_db, AlertCreate(**data))
    
    assert len(result.description) == 10000


def test_get_alerts_with_limit_zero(test_db, sample_alert_data):
    """Test: limit=0 debe retornar lista vacía"""
    crud.create_alert(test_db, AlertCreate(**sample_alert_data))
    
    result = crud.get_alerts(test_db, limit=0)
    
    assert result == []


def test_alerts_ordered_by_creation_time(test_db, sample_alert_data):
    """Test: Alertas deben retornarse en orden de creación (implícito por ID)"""
    import time
    
    ids = []
    for i in range(3):
        data = sample_alert_data.copy()
        data["title"] = f"Alerta {i}"
        alert = crud.create_alert(test_db, AlertCreate(**data))
        ids.append(alert.id)
        time.sleep(0.01)  # Pequeño delay
    
    result = crud.get_alerts(test_db)
    result_ids = [a.id for a in result]
    
    # IDs deben estar en orden ascendente
    assert result_ids == sorted(result_ids)