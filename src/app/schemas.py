"""
Schemas modernos para la API - Alineados con el dominio
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field, validator

# Usar los enums del dominio
class AlertLevelSchema(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class AlertStatusSchema(str, Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    PENDING = "pending"
    CANCELLED = "cancelled"

class AlertTypeSchema(str, Enum):
    WEATHER = "weather"
    NATURAL_DISASTER = "natural_disaster"
    SECURITY = "security"
    HEALTH = "health"
    TRAFFIC = "traffic"
    INFRASTRUCTURE = "infrastructure"
    FIRE = "fire"
    OTHER = "other"

class DataSourceTypeSchema(str, Enum):
    WEATHER_API = "weather_api"
    NEWS_RSS = "news_rss"
    GOVERNMENT_API = "government_api"
    SENSOR_NETWORK = "sensor_network"
    SOCIAL_MEDIA = "social_media"

# === SCHEMAS PARA ALERTAS ===

class AlertCreateSchema(BaseModel):
    """Schema para crear una nueva alerta"""
    title: str = Field(..., min_length=1, max_length=255, description="Título de la alerta")
    description: str = Field(..., min_length=1, max_length=5000, description="Descripción detallada")
    level: AlertLevelSchema = Field(..., description="Nivel de severidad")
    type: AlertTypeSchema = Field(..., description="Tipo de alerta")
    region: str = Field(..., min_length=1, max_length=255, description="Región afectada")
    expires_at: Optional[datetime] = Field(None, description="Fecha de expiración (opcional)")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitud (-90 a 90)")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitud (-180 a 180)")
    source: Optional[str] = Field(None, max_length=255, description="Fuente que genera la alerta")
    extra_data: Optional[Dict[str, Any]] = Field(None, description="Datos adicionales en JSON")

    @validator('expires_at')
    def expires_at_must_be_future(cls, v):
        if v is None:
            return v
            
        # Obtener datetime actual en UTC
        now = datetime.now(timezone.utc)
        
        # Si v no tiene timezone, asumir UTC
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        
        # Comparar ambos con timezone
        if v <= now:
            raise ValueError('La fecha de expiración debe ser futura')
        return v

    class Config:
        schema_extra = {
            "example": {
                "title": "Alerta de tormenta",
                "description": "Se prevé tormenta intensa en la región",
                "level": "warning",
                "type": "weather",
                "region": "Madrid",
                "expires_at": "2024-12-31T23:59:59Z",
                "latitude": 40.4168,
                "longitude": -3.7038,
                "source": "api_meteorologia",
                "extra_data": {"intensity": "high"}
            }
        }

class AlertUpdateSchema(BaseModel):
    """Schema para actualizar una alerta existente"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1, max_length=5000)
    level: Optional[AlertLevelSchema] = Field(None)
    type: Optional[AlertTypeSchema] = Field(None)
    region: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[AlertStatusSchema] = Field(None)
    expires_at: Optional[datetime] = Field(None)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    source: Optional[str] = Field(None, max_length=255)
    extra_data: Optional[Dict[str, Any]] = Field(None)

    @validator('expires_at')
    def expires_at_must_be_future(cls, v):
        if v is None:
            return v
            
        # Obtener datetime actual en UTC
        now = datetime.now(timezone.utc)
        
        # Si v no tiene timezone, asumir UTC
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        
        # Comparar ambos con timezone
        if v <= now:
            raise ValueError('La fecha de expiración debe ser futura')
        return v

class AlertResponseSchema(BaseModel):
    """Schema para respuestas de alerta"""
    id: int
    title: str
    description: str
    level: str
    type: str
    region: str
    status: str
    timestamp: datetime
    expires_at: Optional[datetime] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None

    @staticmethod
    def from_domain(alert) -> "AlertResponseSchema":
        """Convierte una entidad de dominio a schema de respuesta"""
        return AlertResponseSchema(
            id=alert.id,
            title=alert.title,
            description=alert.description,
            level=alert.level.value if hasattr(alert.level, 'value') else str(alert.level),
            type=alert.type.value if hasattr(alert.type, 'value') else str(alert.type),
            region=alert.region,
            status=alert.status.value if hasattr(alert.status, 'value') else str(alert.status),
            timestamp=alert.timestamp,
            expires_at=alert.expires_at,
            latitude=alert.latitude,
            longitude=alert.longitude,
            source=alert.source,
            extra_data=alert.extra_data
        )

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "title": "Alerta de tormenta",
                "description": "Se prevé tormenta intensa en la región",
                "level": "warning",
                "type": "weather",
                "region": "Madrid",
                "status": "active",
                "timestamp": "2024-05-20T10:30:00Z",
                "expires_at": "2024-12-31T23:59:59Z",
                "latitude": 40.4168,
                "longitude": -3.7038,
                "source": "api_meteorologia",
                "extra_data": {"intensity": "high"}
            }
        }

# === FILTROS Y PAGINACIÓN ===

class AlertFilterSchema(BaseModel):
    """Schema para filtros de búsqueda"""
    level: Optional[AlertLevelSchema] = None
    type: Optional[AlertTypeSchema] = None
    region: Optional[str] = None
    status: Optional[AlertStatusSchema] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    active_only: bool = False
    high_priority_only: bool = False

class PaginatedAlertsResponse(BaseModel):
    """Schema para respuestas paginadas"""
    items: List[AlertResponseSchema]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool

# === HEALTH CHECK Y ESTADÍSTICAS ===

class HealthCheckSchema(BaseModel):
    """Schema para health check"""
    status: str
    timestamp: datetime
    database: Dict[str, Any]
    version: str
    environment: str

class StatisticsSchema(BaseModel):
    """Schema para estadísticas del sistema"""
    total_alerts: int
    active_alerts: int
    resolved_alerts: int
    by_level: Dict[str, int]
    by_region: Dict[str, int]
    by_type: Dict[str, int]

# === SCHEMAS PARA DATA SOURCES ===

class DataSourceCreateSchema(BaseModel):
    """Schema para crear fuente de datos"""
    name: str = Field(..., min_length=1, max_length=255)
    type: DataSourceTypeSchema
    url: str = Field(..., min_length=1, max_length=500)
    check_interval_minutes: int = Field(60, ge=1, le=10080)  # Entre 1 min y 1 semana
    configuration: Optional[Dict[str, Any]] = None

    @validator('url')
    def url_must_be_valid(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('La URL debe comenzar con http:// o https://')
        return v

    class Config:
        schema_extra = {
            "example": {
                "name": "API Meteorológica AEMET",
                "type": "weather_api",
                "url": "https://opendata.aemet.es/opendata/api",
                "check_interval_minutes": 30,
                "configuration": {"api_key": "your_api_key"}
            }
        }

class DataSourceResponseSchema(BaseModel):
    """Schema para respuesta de fuente de datos"""
    id: int
    name: str
    type: str
    url: str
    is_active: bool
    check_interval_minutes: int
    last_check: Optional[datetime] = None
    last_success: Optional[datetime] = None
    error_count: int
    configuration: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True