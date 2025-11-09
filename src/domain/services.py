"""
Servicios del dominio - Lógica de negocio
"""
from typing import List, Optional
from datetime import datetime, timedelta, timezone

from .entities import Alert, AlertFilter, AlertLevel, AlertStatus, AlertType, DataSource, DataSourceType
from .repositories import AlertRepository, DataSourceRepository
from .exceptions import (
    AlertNotFoundException,
    InvalidAlertDataException,
    DuplicateAlertException,
    AlertExpiredException,
    InvalidAlertLevelException,
    InvalidAlertStatusException,
    DataSourceException
)

class AlertService:
    """Servicio de dominio para gestión de alertas"""
    
    def __init__(self, repository: AlertRepository, data_source_repository: Optional[DataSourceRepository] = None):
        self._repository = repository
        self._data_source_repository = data_source_repository
    
    def create_alert(
        self,
        title: str,
        description: str,
        level: str,
        type: str,
        region: str,
        expires_at: Optional[datetime] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        source: Optional[str] = None
    ) -> Alert:
        """
        Crea una nueva alerta con validaciones de negocio
        """
        # Validar título
        if not title or len(title.strip()) < 3:
            raise InvalidAlertDataException("title", title, "El título debe tener al menos 3 caracteres")
        
        # Validar descripción
        if not description or len(description.strip()) < 5:
            raise InvalidAlertDataException("description", description, "La descripción debe tener al menos 5 caracteres")
        
        # Validar región
        if not region or len(region.strip()) < 2:
            raise InvalidAlertDataException("region", region, "La región debe tener al menos 2 caracteres")
        
        # Validar nivel
        try:
            alert_level = AlertLevel(level.lower())
        except ValueError:
            valid_levels = [l.value for l in AlertLevel]
            raise InvalidAlertDataException("level", level, f"Niveles válidos: {valid_levels}")
        
        # Validar tipo
        try:
            alert_type = AlertType(type.lower())
        except ValueError:
            valid_types = [t.value for t in AlertType]
            raise InvalidAlertDataException("type", type, f"Tipos válidos: {valid_types}")
        
        # Validar coordenadas si se proporcionan
        if latitude is not None and not (-90 <= latitude <= 90):
            raise InvalidAlertDataException("latitude", latitude, "La latitud debe estar entre -90 y 90")
        
        if longitude is not None and not (-180 <= longitude <= 180):
            raise InvalidAlertDataException("longitude", longitude, "La longitud debe estar entre -180 y 180")
        
        # Validar fecha de expiración con timezone-aware datetime
        now = datetime.now(timezone.utc)
        if expires_at:
            # Si expires_at no tiene timezone, asumir UTC
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            
            if expires_at <= now:
                raise InvalidAlertDataException("expires_at", expires_at, "La fecha de expiración debe ser futura")
        
        # Verificar duplicados (alertas similares en la misma región)
        existing_alerts = self._repository.find_by_title_and_region(title.strip(), region.strip())
        if existing_alerts:
            active_duplicate = next((a for a in existing_alerts if a.status == AlertStatus.ACTIVE), None)
            if active_duplicate:
                raise DuplicateAlertException(title, region)
        
        # Crear la alerta con timestamp UTC pero sin timezone (para compatibilidad con BD)
        alert = Alert(
            id=None,
            title=title.strip(),
            description=description.strip(),
            level=alert_level,
            type=alert_type,
            region=region.strip(),
            status=AlertStatus.ACTIVE,
            timestamp=now.replace(tzinfo=None),  # Guardar como naive UTC
            expires_at=expires_at.replace(tzinfo=None) if expires_at and expires_at.tzinfo else expires_at,
            latitude=latitude,
            longitude=longitude,
            source=source.strip() if source else None,
            extra_data={}
        )
        
        return self._repository.save(alert)
    
    def get_alert_by_id(self, alert_id: int) -> Alert:
        """Obtiene una alerta por su ID"""
        alert = self._repository.find_by_id(alert_id)
        if not alert:
            raise AlertNotFoundException(alert_id)
        return alert
    
    def get_all_alerts(self, filter: Optional[AlertFilter] = None) -> List[Alert]:
        """Obtiene todas las alertas con filtros opcionales"""
        if filter:
            return self._repository.find_by_filter(filter)
        else:
            return self._repository.find_all()
    
    def get_filtered_alerts(self, filter: AlertFilter) -> List[Alert]:
        """Obtiene alertas aplicando filtros específicos"""
        return self._repository.find_by_filter(filter)
    
    def process_expired_alerts(self) -> int:
        """Procesa alertas expiradas y las marca como resueltas"""
        expired_count = 0
        try:
            # Obtener alertas activas que han expirado
            all_active_alerts = self._repository.find_by_status(AlertStatus.ACTIVE)
            now = datetime.now(timezone.utc).replace(tzinfo=None)  # UTC naive para comparación
            
            for alert in all_active_alerts:
                if alert.expires_at and alert.expires_at <= now:
                    # Marcar como resuelta por expiración
                    alert.status = AlertStatus.RESOLVED
                    alert.extra_data = alert.extra_data or {}
                    alert.extra_data['resolved_reason'] = 'expired'
                    alert.extra_data['resolved_at'] = now.isoformat()
                    
                    self._repository.save(alert)
                    expired_count += 1
            
            return expired_count
            
        except Exception as e:
            # Log del error pero no fallar completamente
            print(f"Error processing expired alerts: {e}")
            return expired_count
    
    def update_alert_status(self, alert_id: int, new_status: str) -> Alert:
        """Actualiza el estado de una alerta"""
        alert = self.get_alert_by_id(alert_id)
        
        try:
            status = AlertStatus(new_status.lower())
        except ValueError:
            raise InvalidAlertStatusException(new_status)
        
        # Verificar si la alerta ha expirado
        if alert.is_expired():
            raise AlertExpiredException(alert_id)
        
        # Reglas de negocio para cambios de estado
        self._validate_status_transition(alert.status, status)
        
        alert.status = status
        return self._repository.save(alert)
    
    def resolve_alert(self, alert_id: int) -> Alert:
        """Resuelve una alerta (cambia estado a RESOLVED)"""
        alert = self.get_alert_by_id(alert_id)
        
        if alert.is_expired():
            raise AlertExpiredException(alert_id)
        
        alert.resolve()  # Usa la lógica de la entidad
        return self._repository.save(alert)
    
    def delete_alert(self, alert_id: int) -> bool:
        """Elimina una alerta"""
        alert = self.get_alert_by_id(alert_id)
        return self._repository.delete(alert.id)
    
    def get_alerts_by_region(self, region: str) -> List[Alert]:
        """Obtiene alertas por región"""
        return self._repository.find_by_region(region)
    
    def get_alerts_by_level(self, level: AlertLevel) -> List[Alert]:
        """Obtiene alertas por nivel de severidad"""
        return self._repository.find_by_level(level)
    
    def get_active_alerts(self) -> List[Alert]:
        """Obtiene solo las alertas activas"""
        return self._repository.find_by_status(AlertStatus.ACTIVE)
    
    def get_alert_statistics(self) -> dict:
        """Obtiene estadísticas generales de alertas"""
        all_alerts = self._repository.find_all()
        
        stats = {
            "total_alerts": len(all_alerts),
            "active_alerts": len([a for a in all_alerts if a.status == AlertStatus.ACTIVE]),
            "resolved_alerts": len([a for a in all_alerts if a.status == AlertStatus.RESOLVED]),
            "by_level": {},
            "by_region": {},
            "by_type": {}
        }
        
        # Estadísticas por nivel
        for level in AlertLevel:
            stats["by_level"][level.value] = len([a for a in all_alerts if a.level == level])
        
        # Estadísticas por región
        regions = set(alert.region for alert in all_alerts)
        for region in regions:
            stats["by_region"][region] = len([a for a in all_alerts if a.region == region])
        
        # Estadísticas por tipo
        for alert_type in AlertType:
            stats["by_type"][alert_type.value] = len([a for a in all_alerts if a.type == alert_type])
        
        return stats
    
    def _validate_status_transition(self, current: AlertStatus, new: AlertStatus):
        """Valida las transiciones de estado permitidas"""
        # Definir transiciones válidas
        valid_transitions = {
            AlertStatus.PENDING: [AlertStatus.ACTIVE, AlertStatus.CANCELLED],
            AlertStatus.ACTIVE: [AlertStatus.RESOLVED, AlertStatus.CANCELLED],
            AlertStatus.RESOLVED: [],  # Los resueltos no pueden cambiar
            AlertStatus.CANCELLED: []  # Los cancelados no pueden cambiar
        }
        
        if new not in valid_transitions.get(current, []):
            raise InvalidAlertStatusException(
                f"No se puede cambiar de {current.value} a {new.value}"
            )


class DataSourceService:
    """Servicio para gestión de fuentes de datos automáticas"""
    
    def __init__(self, repository: DataSourceRepository):
        self._repository = repository
    
    def create_data_source(
        self,
        name: str,
        type: str,
        url: str,
        check_interval_minutes: int = 60,
        configuration: Optional[dict] = None
    ) -> DataSource:
        """Crear nueva fuente de datos"""
        # Validaciones
        if not name or len(name.strip()) < 3:
            raise InvalidAlertDataException("name", name, "El nombre debe tener al menos 3 caracteres")
        
        if not url or not url.strip().startswith(('http://', 'https://')):
            raise InvalidAlertDataException("url", url, "La URL debe ser válida y comenzar con http:// o https://")
        
        if check_interval_minutes < 1:
            raise InvalidAlertDataException("check_interval_minutes", check_interval_minutes, "El intervalo debe ser mayor a 0")
        
        try:
            source_type = DataSourceType(type.lower())
        except ValueError:
            valid_types = [t.value for t in DataSourceType]
            raise InvalidAlertDataException("type", type, f"Tipos válidos: {valid_types}")
        
        # Crear fuente de datos
        data_source = DataSource(
            id=None,
            name=name.strip(),
            type=source_type,
            url=url.strip(),
            is_active=True,
            check_interval_minutes=check_interval_minutes,
            configuration=configuration
        )
        
        return self._repository.save(data_source)
    
    def get_sources_ready_for_check(self) -> List[DataSource]:
        """Obtiene fuentes de datos listas para verificar"""
        return self._repository.find_ready_for_check()
    
    def mark_source_success(self, source_id: int) -> DataSource:
        """Marca una fuente como exitosa"""
        source = self._repository.find_by_id(source_id)
        if not source:
            raise DataSourceException(f"source_id_{source_id}", "Fuente no encontrada")
        
        source.mark_success()
        return self._repository.save(source)
    
    def mark_source_error(self, source_id: int) -> DataSource:
        """Marca una fuente con error"""
        source = self._repository.find_by_id(source_id)
        if not source:
            raise DataSourceException(f"source_id_{source_id}", "Fuente no encontrada")
        
        source.mark_error()
        return self._repository.save(source)