"""
Entidades del dominio de negocio - CORREGIDO
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"
    
    def get_priority(self) -> int:
        """Retorna la prioridad numérica del nivel"""
        priorities = {
            AlertLevel.INFO: 1,
            AlertLevel.WARNING: 2,
            AlertLevel.CRITICAL: 3,
            AlertLevel.EMERGENCY: 4
        }
        return priorities[self]

class AlertStatus(Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    PENDING = "pending"
    CANCELLED = "cancelled"

class AlertType(Enum):
    WEATHER = "weather"
    NATURAL_DISASTER = "natural_disaster"
    SECURITY = "security"
    HEALTH = "health"
    TRAFFIC = "traffic"
    OTHER = "other"

class DataSourceType(Enum):
    """Tipos de fuentes de datos automáticas"""
    WEATHER_API = "weather_api"
    NEWS_RSS = "news_rss"
    GOVERNMENT_API = "government_api"
    SENSOR_NETWORK = "sensor_network"
    SOCIAL_MEDIA = "social_media"

@dataclass
class Alert:
    """Entidad del dominio para representar una alerta"""
    id: Optional[int]
    title: str
    description: str
    level: AlertLevel
    type: AlertType
    region: str
    status: AlertStatus
    timestamp: datetime
    expires_at: Optional[datetime]
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source: Optional[str] = None  # Fuente que generó la alerta
    extra_data: Optional[Dict[str, Any]] = None  # ← CAMBIO: metadata → extra_data
    
    def is_expired(self) -> bool:
        """Verifica si la alerta ha expirado"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def is_active(self) -> bool:
        """Verifica si la alerta está activa"""
        return self.status == AlertStatus.ACTIVE and not self.is_expired()
    
    def can_be_resolved(self) -> bool:
        """Verifica si la alerta puede ser resuelta"""
        return self.status in [AlertStatus.ACTIVE, AlertStatus.PENDING]
    
    def resolve(self) -> None:
        """Resuelve la alerta"""
        from .exceptions import InvalidAlertStatusException
        if not self.can_be_resolved():
            raise InvalidAlertStatusException(f"No se puede resolver una alerta en estado {self.status.value}")
        self.status = AlertStatus.RESOLVED
    
    def is_high_priority(self) -> bool:
        """Verifica si es una alerta de alta prioridad"""
        return self.level in [AlertLevel.CRITICAL, AlertLevel.EMERGENCY]
    
    def get_coordinates(self) -> Optional[tuple[float, float]]:
        """Retorna las coordenadas como tupla"""
        if self.latitude is not None and self.longitude is not None:
            return (self.latitude, self.longitude)
        return None

@dataclass
class AlertFilter:
    """Filtro para búsqueda de alertas"""
    level: Optional[AlertLevel] = None
    type: Optional[AlertType] = None
    region: Optional[str] = None
    status: Optional[AlertStatus] = None
    active_only: bool = False
    high_priority_only: bool = False
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    
    def matches(self, alert: Alert) -> bool:
        """Verifica si una alerta coincide con los filtros"""
        if self.level and alert.level != self.level:
            return False
        if self.type and alert.type != self.type:
            return False
        if self.region and alert.region.lower() != self.region.lower():
            return False
        if self.status and alert.status != self.status:
            return False
        if self.active_only and not alert.is_active():
            return False
        if self.high_priority_only and not alert.is_high_priority():
            return False
        if self.from_date and alert.timestamp < self.from_date:
            return False
        if self.to_date and alert.timestamp > self.to_date:
            return False
        return True

@dataclass
class DataSource:
    """Entidad para representar una fuente de datos automática"""
    id: Optional[int]
    name: str
    type: DataSourceType
    url: str
    is_active: bool
    check_interval_minutes: int
    last_check: Optional[datetime] = None
    last_success: Optional[datetime] = None
    error_count: int = 0
    config_data: Optional[Dict[str, Any]] = None  # ← CAMBIO: configuration → config_data
    
    def can_be_checked(self) -> bool:
        """Verifica si la fuente puede ser verificada"""
        if not self.is_active:
            return False
        if self.last_check is None:
            return True
        
        next_check = self.last_check.timestamp() + (self.check_interval_minutes * 60)
        return datetime.utcnow().timestamp() >= next_check
    
    def mark_success(self) -> None:
        """Marca la verificación como exitosa"""
        self.last_check = datetime.utcnow()
        self.last_success = self.last_check
        self.error_count = 0
    
    def mark_error(self) -> None:
        """Marca la verificación como fallida"""
        self.last_check = datetime.utcnow()
        self.error_count += 1
    
    def is_healthy(self) -> bool:
        """Verifica si la fuente está saludable"""
        return self.error_count < 5 and self.is_active

@dataclass
class AirflowTaskStatus:
    """Estado de una tarea de Airflow"""
    task_id: str
    dag_id: str
    execution_date: datetime
    state: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    duration: Optional[float] = None
    
    def is_running(self) -> bool:
        """Verifica si la tarea está ejecutándose"""
        return self.state in ["running", "up_for_retry"]
    
    def is_successful(self) -> bool:
        """Verifica si la tarea fue exitosa"""
        return self.state == "success"
    
    def is_failed(self) -> bool:
        """Verifica si la tarea falló"""
        return self.state in ["failed", "up_for_reschedule"]