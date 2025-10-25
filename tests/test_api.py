"""
Tests completos para la API de Alert Manager
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import os

# Importar la app y dependencias
from src.app.main import app
from src.app.database import Base, get_db
from src.app.models import Alert, User
from src.app.auth import get_password_hash, create_access_token

# Configuración de base de datos de test
SQLALCHEMY_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/alerts_test"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Crea una sesión de base de datos limpia para cada test"""
    # Crear todas las tablas
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Limpiar todas las tablas después del test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Cliente de test con base de datos mockeada"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Crea un usuario de prueba"""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Headers de autenticación para requests"""
    access_token = create_access_token(data={"sub": test_user.username})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def sample_alert_data():
    """Datos de ejemplo para crear una alerta"""
    return {
        "title": "Test Alert",
        "description": "This is a test alert",
        "level": "warning",
        "type": "weather",
        "region": "Test Region",
        "status": "active",
        "latitude": 40.4168,
        "longitude": -3.7038,
        "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
    }


# ============================================================================
# TESTS DE HEALTH CHECK
# ============================================================================

class TestHealthCheck:
    """Tests para el endpoint de health check"""
    
    def test_health_check(self, client):
        """Test que el health check retorna 200"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_health_check_with_db(self, client, db_session):
        """Test que el health check verifica la conexión a DB"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["database"] == "connected"


# ============================================================================
# TESTS DE AUTENTICACIÓN
# ============================================================================

class TestAuthentication:
    """Tests para endpoints de autenticación"""
    
    def test_create_user(self, client):
        """Test crear un nuevo usuario"""
        response = client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "newpassword123"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "new@example.com"
        assert "id" in data
        assert "hashed_password" not in data
    
    def test_create_duplicate_user(self, client, test_user):
        """Test que no se puede crear usuario duplicado"""
        response = client.post(
            "/auth/register",
            json={
                "username": test_user.username,
                "email": "different@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_login_success(self, client, test_user):
        """Test login exitoso"""
        response = client.post(
            "/auth/token",
            data={
                "username": "testuser",
                "password": "testpassword"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_wrong_password(self, client, test_user):
        """Test login con contraseña incorrecta"""
        response = client.post(
            "/auth/token",
            data={
                "username": "testuser",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
    
    def test_login_nonexistent_user(self, client):
        """Test login con usuario inexistente"""
        response = client.post(
            "/auth/token",
            data={
                "username": "nonexistent",
                "password": "password123"
            }
        )
        assert response.status_code == 401
    
    def test_get_current_user(self, client, test_user, auth_headers):
        """Test obtener usuario actual autenticado"""
        response = client.get("/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email
    
    def test_unauthorized_access(self, client):
        """Test acceso sin autenticación"""
        response = client.get("/auth/me")
        assert response.status_code == 401


# ============================================================================
# TESTS DE CRUD DE ALERTAS
# ============================================================================

class TestAlertsCRUD:
    """Tests para operaciones CRUD de alertas"""
    
    def test_create_alert(self, client, auth_headers, sample_alert_data):
        """Test crear una nueva alerta"""
        response = client.post(
            "/alerts/",
            json=sample_alert_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_alert_data["title"]
        assert data["level"] == sample_alert_data["level"]
        assert "id" in data
        assert "timestamp" in data
    
    def test_create_alert_unauthorized(self, client, sample_alert_data):
        """Test que crear alerta requiere autenticación"""
        response = client.post("/alerts/", json=sample_alert_data)
        assert response.status_code == 401
    
    def test_create_alert_invalid_data(self, client, auth_headers):
        """Test crear alerta con datos inválidos"""
        response = client.post(
            "/alerts/",
            json={"title": "Invalid"},  # Faltan campos requeridos
            headers=auth_headers
        )
        assert response.status_code == 422
    
    def test_get_alerts_list(self, client, auth_headers, db_session):
        """Test obtener lista de alertas"""
        # Crear algunas alertas de prueba
        for i in range(3):
            alert = Alert(
                title=f"Alert {i}",
                description=f"Description {i}",
                level="info",
                type="test",
                region="Test",
                status="active",
                latitude=40.0,
                longitude=-3.0,
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            db_session.add(alert)
        db_session.commit()
        
        response = client.get("/alerts/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all("title" in alert for alert in data)
    
    def test_get_alert_by_id(self, client, auth_headers, db_session):
        """Test obtener alerta específica por ID"""
        alert = Alert(
            title="Specific Alert",
            description="Test",
            level="warning",
            type="test",
            region="Test",
            status="active",
            latitude=40.0,
            longitude=-3.0,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)
        
        response = client.get(f"/alerts/{alert.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == alert.id
        assert data["title"] == "Specific Alert"
    
    def test_get_nonexistent_alert(self, client, auth_headers):
        """Test obtener alerta que no existe"""
        response = client.get("/alerts/99999", headers=auth_headers)
        assert response.status_code == 404
    
    def test_update_alert(self, client, auth_headers, db_session):
        """Test actualizar una alerta"""
        alert = Alert(
            title="Original Title",
            description="Test",
            level="info",
            type="test",
            region="Test",
            status="active",
            latitude=40.0,
            longitude=-3.0,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)
        
        update_data = {
            "title": "Updated Title",
            "status": "resolved"
        }
        
        response = client.put(
            f"/alerts/{alert.id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["status"] == "resolved"
    
    def test_delete_alert(self, client, auth_headers, db_session):
        """Test eliminar una alerta"""
        alert = Alert(
            title="To Delete",
            description="Test",
            level="info",
            type="test",
            region="Test",
            status="active",
            latitude=40.0,
            longitude=-3.0,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)
        
        response = client.delete(f"/alerts/{alert.id}", headers=auth_headers)
        assert response.status_code == 204
        
        # Verificar que fue eliminada
        response = client.get(f"/alerts/{alert.id}", headers=auth_headers)
        assert response.status_code == 404


# ============================================================================
# TESTS DE FILTROS Y BÚSQUEDA
# ============================================================================

class TestAlertsFiltering:
    """Tests para filtrado y búsqueda de alertas"""
    
    @pytest.fixture(autouse=True)
    def setup_alerts(self, db_session):
        """Crear alertas de prueba con diferentes atributos"""
        alerts_data = [
            {"title": "Fire Alert", "level": "critical", "type": "fire", "region": "North", "status": "active"},
            {"title": "Weather Warning", "level": "warning", "type": "weather", "region": "South", "status": "active"},
            {"title": "Flood Alert", "level": "warning", "type": "flood", "region": "North", "status": "resolved"},
            {"title": "Info Notice", "level": "info", "type": "general", "region": "East", "status": "active"},
        ]
        
        for data in alerts_data:
            alert = Alert(
                title=data["title"],
                description="Test description",
                level=data["level"],
                type=data["type"],
                region=data["region"],
                status=data["status"],
                latitude=40.0,
                longitude=-3.0,
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            db_session.add(alert)
        db_session.commit()
    
    def test_filter_by_level(self, client, auth_headers):
        """Test filtrar alertas por nivel"""
        response = client.get("/alerts/?level=warning", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(alert["level"] == "warning" for alert in data)
    
    def test_filter_by_type(self, client, auth_headers):
        """Test filtrar alertas por tipo"""
        response = client.get("/alerts/?type=fire", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["type"] == "fire"
    
    def test_filter_by_status(self, client, auth_headers):
        """Test filtrar alertas por estado"""
        response = client.get("/alerts/?status=active", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all(alert["status"] == "active" for alert in data)
    
    def test_filter_by_region(self, client, auth_headers):
        """Test filtrar alertas por región"""
        response = client.get("/alerts/?region=North", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(alert["region"] == "North" for alert in data)
    
    def test_multiple_filters(self, client, auth_headers):
        """Test combinar múltiples filtros"""
        response = client.get(
            "/alerts/?level=warning&status=active",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["level"] == "warning"
        assert data[0]["status"] == "active"
    
    def test_pagination(self, client, auth_headers):
        """Test paginación de resultados"""
        response = client.get("/alerts/?skip=0&limit=2", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2
    
    def test_search_by_title(self, client, auth_headers):
        """Test búsqueda por título"""
        response = client.get("/alerts/?search=Fire", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any("Fire" in alert["title"] for alert in data)


# ============================================================================
# TESTS DE VALIDACIÓN
# ============================================================================

class TestValidation:
    """Tests para validación de datos"""
    
    def test_invalid_coordinates(self, client, auth_headers):
        """Test que las coordenadas se validan correctamente"""
        invalid_data = {
            "title": "Test",
            "description": "Test",
            "level": "info",
            "type": "test",
            "region": "Test",
            "status": "active",
            "latitude": 200.0,  # Inválido
            "longitude": -3.0,
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
        response = client.post("/alerts/", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422
    
    def test_invalid_level(self, client, auth_headers):
        """Test que el nivel de alerta es validado"""
        invalid_data = {
            "title": "Test",
            "description": "Test",
            "level": "invalid_level",
            "type": "test",
            "region": "Test",
            "status": "active",
            "latitude": 40.0,
            "longitude": -3.0,
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
        response = client.post("/alerts/", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422
    
    def test_expired_alert(self, client, auth_headers):
        """Test que se puede crear alerta con fecha de expiración pasada"""
        past_data = {
            "title": "Expired Alert",
            "description": "Test",
            "level": "info",
            "type": "test",
            "region": "Test",
            "status": "expired",
            "latitude": 40.0,
            "longitude": -3.0,
            "expires_at": (datetime.utcnow() - timedelta(hours=24)).isoformat()
        }
        response = client.post("/alerts/", json=past_data, headers=auth_headers)
        # Depende de tu lógica de negocio
        assert response.status_code in [201, 422]


# ============================================================================
# TESTS DE ESTADÍSTICAS
# ============================================================================

class TestStatistics:
    """Tests para endpoints de estadísticas"""
    
    @pytest.fixture(autouse=True)
    def setup_alerts(self, db_session):
        """Crear alertas de prueba"""
        for i in range(10):
            alert = Alert(
                title=f"Alert {i}",
                description="Test",
                level=["info", "warning", "critical"][i % 3],
                type="test",
                region=["North", "South"][i % 2],
                status=["active", "resolved"][i % 2],
                latitude=40.0,
                longitude=-3.0,
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            db_session.add(alert)
        db_session.commit()
    
    def test_get_statistics(self, client, auth_headers):
        """Test obtener estadísticas de alertas"""
        response = client.get("/alerts/stats/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "by_level" in data
        assert "by_status" in data
        assert data["total"] == 10
    
    def test_get_stats_by_region(self, client, auth_headers):
        """Test estadísticas por región"""
        response = client.get("/alerts/stats/?region=North", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5


# ============================================================================
# TESTS DE PERFORMANCE
# ============================================================================

@pytest.mark.slow
class TestPerformance:
    """Tests de rendimiento"""
    
    def test_bulk_create(self, client, auth_headers, db_session):
        """Test crear múltiples alertas"""
        alerts_data = []
        for i in range(100):
            alerts_data.append({
                "title": f"Bulk Alert {i}",
                "description": "Test",
                "level": "info",
                "type": "test",
                "region": "Test",
                "status": "active",
                "latitude": 40.0,
                "longitude": -3.0,
                "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
            })
        
        import time
        start = time.time()
        
        for alert_data in alerts_data:
            response = client.post("/alerts/", json=alert_data, headers=auth_headers)
            assert response.status_code == 201
        
        end = time.time()
        duration = end - start
        
        print(f"\n⏱️  Created 100 alerts in {duration:.2f}s")
        assert duration < 30, "Bulk creation took too long"
    
    def test_list_large_dataset(self, client, auth_headers, db_session):
        """Test listar alertas con dataset grande"""
        # Crear 1000 alertas
        for i in range(1000):
            alert = Alert(
                title=f"Alert {i}",
                description="Test",
                level="info",
                type="test",
                region="Test",
                status="active",
                latitude=40.0,
                longitude=-3.0,
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            db_session.add(alert)
        db_session.commit()
        
        import time
        start = time.time()
        
        response = client.get("/alerts/?limit=100", headers=auth_headers)
        
        end = time.time()
        duration = end - start
        
        assert response.status_code == 200
        print(f"\n⏱️  Retrieved 100 alerts from 1000 in {duration:.2f}s")
        assert duration < 5, "Query took too long"


# ============================================================================
# TESTS DE INTEGRACIÓN
# ============================================================================

@pytest.mark.integration
class TestIntegration:
    """Tests de integración end-to-end"""
    
    def test_complete_alert_lifecycle(self, client, db_session):
        """Test ciclo de vida completo de una alerta"""
        # 1. Registrar usuario
        register_response = client.post(
            "/auth/register",
            json={
                "username": "lifecycle_user",
                "email": "lifecycle@example.com",
                "password": "password123"
            }
        )
        assert register_response.status_code == 201
        
        # 2. Login
        login_response = client.post(
            "/auth/token",
            data={
                "username": "lifecycle_user",
                "password": "password123"
            }
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Crear alerta
        alert_data = {
            "title": "Lifecycle Alert",
            "description": "Testing full lifecycle",
            "level": "warning",
            "type": "test",
            "region": "Test",
            "status": "active",
            "latitude": 40.0,
            "longitude": -3.0,
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
        create_response = client.post("/alerts/", json=alert_data, headers=headers)
        assert create_response.status_code == 201
        alert_id = create_response.json()["id"]
        
        # 4. Obtener alerta
        get_response = client.get(f"/alerts/{alert_id}", headers=headers)
        assert get_response.status_code == 200
        assert get_response.json()["title"] == "Lifecycle Alert"
        
        # 5. Actualizar alerta
        update_response = client.put(
            f"/alerts/{alert_id}",
            json={"status": "resolved"},
            headers=headers
        )
        assert update_response.status_code == 200
        assert update_response.json()["status"] == "resolved"
        
        # 6. Eliminar alerta
        delete_response = client.delete(f"/alerts/{alert_id}", headers=headers)
        assert delete_response.status_code == 204
        
        # 7. Verificar eliminación
        final_get = client.get(f"/alerts/{alert_id}", headers=headers)
        assert final_get.status_code == 404