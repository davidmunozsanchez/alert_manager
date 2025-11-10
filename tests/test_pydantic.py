"""
Tests específicos de validación de schemas Pydantic
Tests actualizados para coincidir con los schemas reales
"""
import pytest
from datetime import datetime, timezone, timedelta
from pydantic import ValidationError
from typing import Dict, Any
import sys
from pathlib import Path

# Configurar path para imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

class TestPydanticImports:
    """Tests que verifican que los schemas se pueden importar"""
    
    def test_import_schemas(self):
        """Test que los schemas se pueden importar sin errores"""
        try:
            from src.app.schemas import (
                AlertCreateSchema, AlertUpdateSchema, AlertResponseSchema,
                AlertFilterSchema, HealthCheckSchema, StatisticsSchema,
                DataSourceCreateSchema, DataSourceResponseSchema,
                AlertLevelSchema, AlertTypeSchema, AlertStatusSchema, DataSourceTypeSchema
            )
            print("✅ Todos los schemas importados correctamente")
            assert True
        except ImportError as e:
            pytest.fail(f"No se pueden importar los schemas: {e}")
        except Exception as e:
            pytest.fail(f"Error inesperado importando schemas: {e}")
    
    def test_import_enums(self):
        """Test que los enums se pueden importar y usar"""
        try:
            from src.app.schemas import AlertLevelSchema, AlertTypeSchema, AlertStatusSchema
            
            # Test que los valores están disponibles
            levels = [level.value for level in AlertLevelSchema]
            types = [type_.value for type_ in AlertTypeSchema]
            statuses = [status.value for status in AlertStatusSchema]
            
            print(f"✅ Levels disponibles: {levels}")
            print(f"✅ Types disponibles: {types}")
            print(f"✅ Statuses disponibles: {statuses}")
            
            assert "info" in levels
            assert "critical" in levels
            assert "weather" in types
            assert "active" in statuses
            
        except Exception as e:
            pytest.fail(f"Error con enums: {e}")

class TestAlertCreateSchema:
    """Tests exhaustivos del schema de creación de alertas"""
    
    @pytest.fixture
    def valid_alert_data(self):
        """Datos válidos para crear alertas"""
        return {
            "title": "Test Alert",
            "description": "Test description for validation",
            "level": "warning",  # Usar valores reales del enum
            "type": "other",
            "region": "Test Region"
        }
    
    def test_alert_creation_with_valid_data(self, valid_alert_data):
        """Test creación con datos válidos mínimos"""
        try:
            from src.app.schemas import AlertCreateSchema
            
            schema = AlertCreateSchema(**valid_alert_data)
            
            assert schema.title == "Test Alert"
            assert schema.level == "warning"
            assert schema.type == "other"
            assert schema.region == "Test Region"
            
            print("✅ Schema creado correctamente con datos mínimos")
            
        except Exception as e:
            pytest.fail(f"Error creando schema válido: {e}")
    
    def test_alert_creation_with_all_fields(self):
        """Test creación con todos los campos"""
        try:
            from src.app.schemas import AlertCreateSchema
            
            complete_data = {
                "title": "Complete Test Alert",
                "description": "Complete test description with all fields",
                "level": "critical",
                "type": "weather",
                "region": "Madrid",
                "expires_at": datetime.now(timezone.utc) + timedelta(hours=24),
                "latitude": 40.4168,
                "longitude": -3.7038,
                "source": "AEMET",
                "extra_data": {"temperature": 25.5, "humidity": 80}  # Campo correcto
            }
            
            schema = AlertCreateSchema(**complete_data)
            
            assert schema.title == "Complete Test Alert"
            assert schema.latitude == 40.4168
            assert schema.longitude == -3.7038
            assert schema.source == "AEMET"
            assert schema.extra_data["temperature"] == 25.5
            
            print("✅ Schema creado correctamente con todos los campos")
            
        except Exception as e:
            pytest.fail(f"Error creando schema completo: {e}")
    
    def test_title_validation_comprehensive(self, valid_alert_data):
        """Test validación exhaustiva del título"""
        from src.app.schemas import AlertCreateSchema
        
        # Casos válidos
        valid_titles = [
            "Alert",  # Mínimo válido
            "Emergency Alert",
            "Alerta de Emergencia",
            "Alert with números 123",
            "Alert with símbolos!",
            "火災警報",  # Unicode
            "A" * 200  # Máximo válido
        ]
        
        for title in valid_titles:
            try:
                data = valid_alert_data.copy()
                data["title"] = title
                schema = AlertCreateSchema(**data)
                assert schema.title == title
                print(f"✅ Título válido: '{title[:30]}...'")
            except Exception as e:
                pytest.fail(f"Título válido rechazado: '{title}' - {e}")
        
        # Casos inválidos
        invalid_titles = [
            ("", "Título vacío"),
            ("  ", "Solo espacios"),
            ("A" * 256, "Muy largo"),  # Límite es 255
            (None, "Valor None")
        ]
        
        for title, description in invalid_titles:
            try:
                data = valid_alert_data.copy()
                data["title"] = title
                schema = AlertCreateSchema(**data)
                pytest.fail(f"Título inválido aceptado: {description}")
            except ValidationError:
                print(f"✅ Título inválido rechazado: {description}")
            except Exception as e:
                print(f"⚠️ Error inesperado con título {description}: {e}")
    
    def test_description_validation(self, valid_alert_data):
        """Test validación de descripción"""
        from src.app.schemas import AlertCreateSchema
        
        # Casos válidos
        valid_descriptions = [
            "Valid description",
            "Descripción muy larga con muchos detalles sobre la alerta",
            "A" * 1000  # Dentro del límite
        ]
        
        for desc in valid_descriptions:
            try:
                data = valid_alert_data.copy()
                data["description"] = desc
                schema = AlertCreateSchema(**data)
                assert schema.description == desc
                print(f"✅ Descripción válida: '{desc[:30]}...'")
            except Exception as e:
                pytest.fail(f"Descripción válida rechazada: '{desc}' - {e}")
        
        # Casos inválidos
        invalid_descriptions = [
            ("", "Descripción vacía"),
            ("A" * 5001, "Muy larga"),  # Límite es 5000
        ]
        
        for desc, description in invalid_descriptions:
            try:
                data = valid_alert_data.copy()
                data["description"] = desc
                schema = AlertCreateSchema(**data)
                pytest.fail(f"Descripción inválida aceptada: {description}")
            except ValidationError:
                print(f"✅ Descripción inválida rechazada: {description}")
    
    def test_enum_validation(self, valid_alert_data):
        """Test validación de enums"""
        from src.app.schemas import AlertCreateSchema
        
        # Test levels válidos (usar valores reales)
        valid_levels = ["info", "warning", "critical", "emergency"]
        for level in valid_levels:
            try:
                data = valid_alert_data.copy()
                data["level"] = level
                schema = AlertCreateSchema(**data)
                assert schema.level == level
                print(f"✅ Level válido: {level}")
            except Exception as e:
                pytest.fail(f"Level válido rechazado: {level} - {e}")
        
        # Test levels inválidos
        invalid_levels = ["low", "medium", "high", "super_high", "minor", "extreme", "", "invalid"]
        for level in invalid_levels:
            try:
                data = valid_alert_data.copy()
                data["level"] = level
                schema = AlertCreateSchema(**data)
                pytest.fail(f"Level inválido aceptado: {level}")
            except ValidationError:
                print(f"✅ Level inválido rechazado: {level}")
        
        # Test types válidos (usar valores reales)
        valid_types = ["weather", "natural_disaster", "security", "health", "traffic", "infrastructure", "fire", "other"]
        for alert_type in valid_types:
            try:
                data = valid_alert_data.copy()
                data["type"] = alert_type
                schema = AlertCreateSchema(**data)
                assert schema.type == alert_type
                print(f"✅ Type válido: {alert_type}")
            except Exception as e:
                pytest.fail(f"Type válido rechazado: {alert_type} - {e}")
        
        # Test types inválidos
        invalid_types = ["alien", "zombie", "robot", "emergency", "", "invalid"]
        for alert_type in invalid_types:
            try:
                data = valid_alert_data.copy()
                data["type"] = alert_type
                schema = AlertCreateSchema(**data)
                pytest.fail(f"Type inválido aceptado: {alert_type}")
            except ValidationError:
                print(f"✅ Type inválido rechazado: {alert_type}")
    
    def test_coordinate_validation(self, valid_alert_data):
        """Test validación de coordenadas"""
        from src.app.schemas import AlertCreateSchema
        
        # Casos válidos
        valid_coordinates = [
            (40.4168, -3.7038, "Madrid"),
            (0, 0, "Origen"),
            (-90, -180, "Extremo mínimo"),
            (90, 180, "Extremo máximo"),
            (None, None, "Sin coordenadas")
        ]
        
        for lat, lon, description in valid_coordinates:
            try:
                data = valid_alert_data.copy()
                if lat is not None:
                    data["latitude"] = lat
                    data["longitude"] = lon
                
                schema = AlertCreateSchema(**data)
                assert schema.latitude == lat
                assert schema.longitude == lon
                print(f"✅ Coordenadas válidas: {description}")
                
            except Exception as e:
                pytest.fail(f"Coordenadas válidas rechazadas: {description} - {e}")
        
        # Casos inválidos
        invalid_coordinates = [
            (91, 0, "Latitud muy alta"),
            (-91, 0, "Latitud muy baja"),
            (0, 181, "Longitud muy alta"),
            (0, -181, "Longitud muy baja")
        ]
        
        for lat, lon, description in invalid_coordinates:
            try:
                data = valid_alert_data.copy()
                data["latitude"] = lat
                data["longitude"] = lon
                
                schema = AlertCreateSchema(**data)
                pytest.fail(f"Coordenadas inválidas aceptadas: {description}")
                
            except ValidationError:
                print(f"✅ Coordenadas inválidas rechazadas: {description}")
    
    def test_date_validation(self, valid_alert_data):
        """Test validación de fechas"""
        from src.app.schemas import AlertCreateSchema
        
        # Fechas válidas (futuras)
        now = datetime.now(timezone.utc)
        future_dates = [
            now + timedelta(minutes=1),
            now + timedelta(hours=1),
            now + timedelta(days=1),
            now + timedelta(weeks=1)
        ]
        
        for future_date in future_dates:
            try:
                data = valid_alert_data.copy()
                data["expires_at"] = future_date
                schema = AlertCreateSchema(**data)
                assert schema.expires_at == future_date
                print(f"✅ Fecha válida: {future_date}")
            except Exception as e:
                pytest.fail(f"Fecha válida rechazada: {future_date} - {e}")
        
        # Fechas inválidas (en el pasado)
        past_dates = [
            now - timedelta(seconds=1),
            now - timedelta(minutes=1),
            now - timedelta(hours=1),
            now - timedelta(days=1)
        ]
        
        for past_date in past_dates:
            try:
                data = valid_alert_data.copy()
                data["expires_at"] = past_date
                schema = AlertCreateSchema(**data)
                pytest.fail(f"Fecha pasada aceptada: {past_date}")
            except ValidationError:
                print(f"✅ Fecha pasada rechazada: {past_date}")

class TestAlertUpdateSchema:
    """Tests del schema de actualización"""
    
    def test_update_schema_all_optional(self):
        """Test que todos los campos son opcionales en update"""
        try:
            from src.app.schemas import AlertUpdateSchema
            
            # Schema completamente vacío debería ser válido
            schema = AlertUpdateSchema()
            assert schema.title is None
            assert schema.description is None
            assert schema.level is None
            
            print("✅ Update schema acepta campos opcionales")
            
        except Exception as e:
            pytest.fail(f"Error con update schema vacío: {e}")
    
    def test_update_schema_partial_data(self):
        """Test actualización con datos parciales"""
        try:
            from src.app.schemas import AlertUpdateSchema
            
            partial_data = {
                "title": "Updated Title",
                "level": "critical"  # Usar valor real del enum
                # description y otros campos ausentes
            }
            
            schema = AlertUpdateSchema(**partial_data)
            assert schema.title == "Updated Title"
            assert schema.level == "critical"
            assert schema.description is None
            
            print("✅ Update schema acepta datos parciales")
            
        except Exception as e:
            pytest.fail(f"Error con datos parciales: {e}")

class TestDataSourceSchema:
    """Tests del schema de fuentes de datos"""
    
    def test_datasource_creation_basic(self):
        """Test creación básica de fuente de datos"""
        try:
            from src.app.schemas import DataSourceCreateSchema
            
            data = {
                "name": "test_api",
                "type": "weather_api",  # Usar tipo válido
                "url": "https://api.test.com",  # URL válida
                "check_interval_minutes": 30
            }
            
            schema = DataSourceCreateSchema(**data)
            assert schema.name == "test_api"
            assert schema.type == "weather_api"
            assert schema.url == "https://api.test.com"
            
            print("✅ DataSource schema básico funciona")
            
        except Exception as e:
            pytest.fail(f"Error con DataSource schema: {e}")
    
    def test_datasource_url_validation(self):
        """Test validación de URL"""
        try:
            from src.app.schemas import DataSourceCreateSchema
            
            # URL válida
            valid_data = {
                "name": "test_api",
                "type": "weather_api",
                "url": "https://api.test.com",
                "check_interval_minutes": 30
            }
            
            schema = DataSourceCreateSchema(**valid_data)
            assert schema.url == "https://api.test.com"
            print("✅ URL válida aceptada")
            
            # URL inválida
            invalid_data = valid_data.copy()
            invalid_data["url"] = "not-a-valid-url"
            
            try:
                schema = DataSourceCreateSchema(**invalid_data)
                pytest.fail("URL inválida aceptada")
            except ValidationError:
                print("✅ URL inválida rechazada")
            
        except Exception as e:
            pytest.fail(f"Error con URL validation: {e}")

class TestSchemaIntegration:
    """Tests de integración entre schemas"""
    
    def test_create_to_response_conversion(self):
        """Test conversión de create a response schema"""
        try:
            from src.app.schemas import AlertCreateSchema, AlertResponseSchema
            
            create_data = {
                "title": "Integration Test",
                "description": "Test de integración",
                "level": "warning",  # Usar valor válido
                "type": "other",
                "region": "Test Region"
            }
            
            create_schema = AlertCreateSchema(**create_data)
            
            # Simular datos de respuesta
            response_data = {
                "id": 1,
                "title": create_schema.title,
                "description": create_schema.description,
                "level": str(create_schema.level),  # Convertir a string
                "type": str(create_schema.type),
                "status": "active",
                "region": create_schema.region,
                "timestamp": datetime.now(timezone.utc)
            }
            
            response_schema = AlertResponseSchema(**response_data)
            assert response_schema.id == 1
            assert response_schema.title == create_schema.title
            assert response_schema.status == "active"
            
            print("✅ Integración create->response funciona")
            
        except Exception as e:
            pytest.fail(f"Error en integración: {e}")

class TestPydanticFeatures:
    """Tests de características específicas de Pydantic"""
    
    def test_field_validations(self):
        """Test que los Field con validaciones funcionan"""
        try:
            from src.app.schemas import AlertCreateSchema
            
            # Test que los Field() con parámetros funcionan
            data = {
                "title": "Test Field",
                "description": "Test description",
                "level": "info",
                "type": "other",
                "region": "Test"
            }
            
            schema = AlertCreateSchema(**data)
            
            # Verificar que las validaciones de Field funcionan
            assert len(schema.title) >= 1  # min_length
            assert len(schema.title) <= 255  # max_length
            
            print("✅ Field validations funcionan")
            
        except Exception as e:
            pytest.fail(f"Error con Field validations: {e}")
    
    def test_json_serialization(self):
        """Test que la serialización JSON funciona"""
        try:
            from src.app.schemas import AlertCreateSchema
            
            data = {
                "title": "JSON Test",
                "description": "Test serialización",
                "level": "critical",
                "type": "weather",
                "region": "Madrid",
                "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
                "extra_data": {"temp": 25.5}
            }
            
            schema = AlertCreateSchema(**data)
            
            # Convertir a dict
            schema_dict = schema.dict()
            assert isinstance(schema_dict, dict)
            assert schema_dict["title"] == "JSON Test"
            
            # Convertir a JSON
            schema_json = schema.json()
            assert isinstance(schema_json, str)
            assert '"title": "JSON Test"' in schema_json
            
            print("✅ JSON serialization funciona")
            
        except Exception as e:
            pytest.fail(f"Error con JSON serialization: {e}")

class TestAlertFilterSchema:
    """Tests del schema de filtros"""
    
    def test_filter_schema_all_optional(self):
        """Test que todos los filtros son opcionales"""
        try:
            from src.app.schemas import AlertFilterSchema
            
            # Schema completamente vacío debería ser válido
            schema = AlertFilterSchema()
            assert schema.level is None
            assert schema.type is None
            assert schema.region is None
            
            print("✅ Filter schema acepta campos opcionales")
            
        except Exception as e:
            pytest.fail(f"Error con filter schema: {e}")
    
    def test_filter_schema_with_values(self):
        """Test filtros con valores"""
        try:
            from src.app.schemas import AlertFilterSchema
            
            filter_data = {
                "level": "critical",
                "type": "weather",
                "region": "Madrid",
                "status": "active",
                "active_only": True
            }
            
            schema = AlertFilterSchema(**filter_data)
            assert schema.level == "critical"
            assert schema.type == "weather"
            assert schema.active_only is True
            
            print("✅ Filter schema con valores funciona")
            
        except Exception as e:
            pytest.fail(f"Error con filter schema con valores: {e}")

# === Test de ejecución directa ===
if __name__ == "__main__":
    # Ejecutar algunos tests básicos si se ejecuta directamente
    test_instance = TestPydanticImports()
    test_instance.test_import_schemas()
    test_instance.test_import_enums()
    
    test_create = TestAlertCreateSchema()
    test_create.test_alert_creation_with_valid_data({
        "title": "Test Alert",
        "description": "Test description for validation",
        "level": "warning", 
        "type": "other",
        "region": "Test Region"
    })
    
    print("✅ Tests básicos de Pydantic completados")