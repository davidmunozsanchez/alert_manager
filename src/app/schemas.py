"""
Schemas modernos para la API - Alineados con el dominio
"""
from datetime import datetime
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
        if v and v <= datetime.utcnow():
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
                "expires_at": "2024-12-31T23:59:59",
                "latitude": 40.4168,
                "longitude": -3.7038,
                "source": "weather_api"
            }
        }

class AlertUpdateSchema(BaseModel):
    """Schema para actualizar una alerta"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1, max_length=5000)
    level: Optional[AlertLevelSchema] = None
    type: Optional[AlertTypeSchema] = None
    region: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[AlertStatusSchema] = None
    expires_at: Optional[datetime] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    source: Optional[str] = Field(None, max_length=255)
    extra_data: Optional[Dict[str, Any]] = None

class AlertResponseSchema(BaseModel):
    """Schema para respuesta de alerta"""
    id: int
    title: str
    description: str
    level: AlertLevelSchema
    type: AlertTypeSchema
    region: str
    status: AlertStatusSchema
    timestamp: datetime
    expires_at: Optional[datetime]
    latitude: Optional[float]
    longitude: Optional[float]
    source: Optional[str]
    extra_data: Optional[Dict[str, Any]]
    
    # Campos calculados
    is_active: bool
    is_expired: bool
    is_high_priority: bool

    @classmethod
    def from_domain(cls, alert) -> "AlertResponseSchema":
        """Convierte una entidad de dominio a schema de respuesta"""
        return cls(
            id=alert.id,
            title=alert.title,
            description=alert.description,
            level=alert.level.value,
            type=alert.type.value,
            region=alert.region,
            status=alert.status.value,
            timestamp=alert.timestamp,
            expires_at=alert.expires_at,
            latitude=alert.latitude,
            longitude=alert.longitude,
            source=alert.source,
            extra_data=alert.extra_data,
            is_active=alert.is_active(),
            is_expired=alert.is_expired(),
            is_high_priority=alert.is_high_priority()
        )

    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "title": "Alerta de tormenta",
                "description": "Se prevé tormenta intensa en la región",
                "level": "warning",
                "type": "weather",
                "region": "Madrid",
                "status": "active",
                "timestamp": "2024-11-06T10:00:00",
                "expires_at": "2024-12-31T23:59:59",
                "latitude": 40.4168,
                "longitude": -3.7038,
                "source": "weather_api",
                "is_active": True,
                "is_expired": False,
                "is_high_priority": False
            }
        }

# === SCHEMAS PARA FUENTES DE DATOS ===

class DataSourceCreateSchema(BaseModel):
    """Schema para crear fuente de datos"""
    name: str = Field(..., min_length=1, max_length=255, description="Nombre único")
    type: DataSourceTypeSchema = Field(..., description="Tipo de fuente")
    url: str = Field(..., min_length=1, max_length=500, description="URL de la fuente")
    check_interval_minutes: int = Field(60, ge=5, description="Intervalo de verificación en minutos")
    config_data: Optional[Dict[str, Any]] = Field(None, description="Configuración adicional")

class DataSourceResponseSchema(BaseModel):
    """Schema para respuesta de fuente de datos"""
    id: int
    name: str
    type: DataSourceTypeSchema
    url: str
    is_active: bool
    check_interval_minutes: int
    last_check: Optional[datetime]
    last_success: Optional[datetime]
    error_count: int
    config_data: Optional[Dict[str, Any]]
    is_healthy: bool

    @classmethod
    def from_domain(cls, data_source) -> "DataSourceResponseSchema":
        """Convierte una entidad de dominio a schema de respuesta"""
        return cls(
            id=data_source.id,
            name=data_source.name,
            type=data_source.type.value,
            url=data_source.url,
            is_active=data_source.is_active,
            check_interval_minutes=data_source.check_interval_minutes,
            last_check=data_source.last_check,
            last_success=data_source.last_success,
            error_count=data_source.error_count,
            config_data=data_source.config_data,
            is_healthy=data_source.is_healthy()
        )

# === SCHEMAS PARA FILTROS Y BÚSQUEDAS ===

class AlertFilterSchema(BaseModel):
    """Schema para filtros de búsqueda de alertas"""
    level: Optional[AlertLevelSchema] = None
    type: Optional[AlertTypeSchema] = None
    region: Optional[str] = None
    status: Optional[AlertStatusSchema] = None
    active_only: bool = False
    high_priority_only: bool = False
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None

# === SCHEMAS PARA RESPUESTAS GENERALES ===

class HealthCheckSchema(BaseModel):
    """Schema para health check"""
    status: str
    timestamp: datetime
    database: Dict[str, Any]
    version: str
    environment: str

class ErrorResponseSchema(BaseModel):
    """Schema para respuestas de error"""
    error: Dict[str, Any]

class StatisticsSchema(BaseModel):
    """Schema para estadísticas"""
    total_alerts: int
    count_active: int
    count_resolved: int
    count_pending: int
    count_cancelled: int
    active_info: int
    active_warning: int
    active_critical: int
    active_emergency: int
    expired_active: int

# === SCHEMAS PARA PAGINACIÓN ===

class PaginatedResponse(BaseModel):
    """Schema base para respuestas paginadas"""
    items: List[Any]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool

class PaginatedAlertsResponse(BaseModel):
    """Schema para respuesta paginada de alertas"""
    items: List[AlertResponseSchema]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool