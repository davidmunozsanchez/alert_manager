"""
Servicios del dominio - Lógica de negocio
"""
from typing import List, Optional
from datetime import datetime, timedelta

from .entities import Alert, AlertFilter, AlertLevel, AlertStatus, AlertType, DataSource
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
    
    def __init__(self, repository: AlertRepository):
        self._repository = repository
    
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
        
        Args:
            title: Título de la alerta
            description: Descripción detallada
            level: Nivel de severidad (info, warning, critical, emergency)
            type: Tipo de alerta (weather, security, etc.)
            region: Región afectada
            expires_at: Fecha de expiración (opcional)
            latitude: Latitud (opcional)
            longitude: Longitud (opcional)
            source: Fuente que generó la alerta (opcional)
            
        Returns:
            Alert: La alerta creada
            
        Raises:
            InvalidAlertDataException: Si los datos son inválidos
            DuplicateAlertException: Si ya existe una alerta similar
            InvalidAlertLevelException: Si el nivel es inválido
        """
        
        # Validar nivel
        try:
            alert_level = AlertLevel(level.lower())
        except ValueError:
            raise InvalidAlertLevelException(level)
        
        # Validar tipo
        try:
            alert_type = AlertType(type.lower())
        except ValueError:
            valid_types = [t.value for t in AlertType]
            raise InvalidAlertDataException("type", type, f"Tipos válidos: {valid_types}")
        
        # Validar datos obligatorios
        self._validate_required_fields(title, description, region)
        
        # Validar coordenadas si se proporcionan
        self._validate_coordinates(latitude, longitude)
        
        # Validar fecha de expiración
        self._validate_expiration_date(expires_at)
        
        # Verificar duplicados (regla de negocio)
        if self._repository.exists_by_title_and_region(title.strip(), region.strip()):
            raise DuplicateAlertException(title.strip(), region.strip())
        
        # Crear la alerta
        alert = Alert(
            id=None,
            title=title.strip(),
            description=description.strip(),
            level=alert_level,
            type=alert_type,
            region=region.strip(),
            status=AlertStatus.ACTIVE,
            timestamp=datetime.utcnow(),
            expires_at=expires_at,
            latitude=latitude,
            longitude=longitude,
            source=source
        )
        
        return self._repository.save(alert)
    
    def get_alert_by_id(self, alert_id: int) -> Alert:
        """
        Obtiene una alerta por ID
        
        Args:
            alert_id: ID de la alerta
            
        Returns:
            Alert: La alerta encontrada
            
        Raises:
            AlertNotFoundException: Si la alerta no existe
        """
        if alert_id <= 0:
            raise InvalidAlertDataException("alert_id", str(alert_id), "ID debe ser positivo")
            
        alert = self._repository.find_by_id(alert_id)
        if not alert:
            raise AlertNotFoundException(alert_id)
        return alert
    
    def get_all_alerts(self, filter: Optional[AlertFilter] = None) -> List[Alert]:
        """
        Obtiene todas las alertas con filtros opcionales
        
        Args:
            filter: Filtros a aplicar (opcional)
            
        Returns:
            List[Alert]: Lista de alertas
        """
        alerts = self._repository.find_all(filter)
        
        # Aplicar lógica de negocio: marcar alertas expiradas como inactivas
        self._process_expired_alerts(alerts)
        
        return alerts
    
    def update_alert_status(self, alert_id: int, new_status: str) -> Alert:
        """
        Actualiza el estado de una alerta
        
        Args:
            alert_id: ID de la alerta
            new_status: Nuevo estado
            
        Returns:
            Alert: La alerta actualizada
            
        Raises:
            AlertNotFoundException: Si la alerta no existe
            InvalidAlertStatusException: Si el estado es inválido
            AlertExpiredException: Si la alerta ha expirado
        """
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
        """
        Resuelve una alerta (cambia estado a RESOLVED)
        
        Args:
            alert_id: ID de la alerta
            
        Returns:
            Alert: La alerta resuelta
        """
        alert = self.get_alert_by_id(alert_id)
        
        if alert.is_expired():
            raise AlertExpiredException(alert_id)
        
        alert.resolve()  # Usa la lógica de la entidad
        return self._repository.save(alert)
    
    def delete_alert(self, alert_id: int) -> bool:
        """
        Elimina una alerta
        
        Args:
            alert_id: ID de la alerta
            
        Returns:
            bool: True si se eliminó, False si no existía
        """
        # Verificar que existe antes de eliminar
        self.get_alert_by_id(alert_id)
        return self._repository.delete(alert_id)
    
    def get_active_alerts(self, region: Optional[str] = None) -> List[Alert]:
        """
        Obtiene alertas activas, opcionalmente filtradas por región
        
        Args:
            region: Región a filtrar (opcional)
            
        Returns:
            List[Alert]: Lista de alertas activas
        """
        filter = AlertFilter(active_only=True, region=region)
        return self.get_all_alerts(filter)
    
    def get_critical_alerts(self) -> List[Alert]:
        """
        Obtiene alertas críticas y de emergencia activas
        
        Returns:
            List[Alert]: Lista de alertas críticas
        """
        critical_filter = AlertFilter(level=AlertLevel.CRITICAL, active_only=True)
        emergency_filter = AlertFilter(level=AlertLevel.EMERGENCY, active_only=True)
        
        critical_alerts = self.get_all_alerts(critical_filter)
        emergency_alerts = self.get_all_alerts(emergency_filter)
        
        # Combinar y ordenar por nivel de prioridad
        all_critical = critical_alerts + emergency_alerts
        return sorted(all_critical, key=lambda a: a.level.get_priority(), reverse=True)
    
    def get_alerts_by_region(self, region: str, active_only: bool = False) -> List[Alert]:
        """
        Obtiene alertas de una región específica
        
        Args:
            region: Región a buscar
            active_only: Solo alertas activas
            
        Returns:
            List[Alert]: Lista de alertas de la región
        """
        if not region or not region.strip():
            raise InvalidAlertDataException("region", region, "La región no puede estar vacía")
        
        filter = AlertFilter(region=region.strip(), active_only=active_only)
        return self.get_all_alerts(filter)
    
    def get_alert_statistics(self) -> dict:
        """
        Obtiene estadísticas de alertas
        
        Returns:
            dict: Estadísticas del sistema
        """
        stats = {}
        
        # Contar por estado
        for status in AlertStatus:
            stats[f"count_{status.value}"] = self._repository.count_by_status(status)
        
        # Alertas activas por nivel
        for level in AlertLevel:
            filter = AlertFilter(level=level, active_only=True)
            alerts = self.get_all_alerts(filter)
            stats[f"active_{level.value}"] = len(alerts)
        
        # Total general
        all_alerts = self.get_all_alerts()
        stats["total_alerts"] = len(all_alerts)
        
        # Alertas expiradas
        expired_alerts = self._repository.find_expired_active_alerts()
        stats["expired_active"] = len(expired_alerts)
        
        return stats
    
    def cleanup_expired_alerts(self) -> int:
        """
        Limpia alertas expiradas marcándolas como resueltas
        
        Returns:
            int: Número de alertas procesadas
        """
        expired_alerts = self._repository.find_expired_active_alerts()
        
        processed = 0
        for alert in expired_alerts:
            try:
                alert.status = AlertStatus.RESOLVED
                self._repository.save(alert)
                processed += 1
            except Exception:
                # Log error pero continúa con las demás
                continue
        
        return processed
    
    # Métodos privados de validación
    def _validate_required_fields(self, title: str, description: str, region: str):
        """Valida campos obligatorios"""
        if not title or not title.strip():
            raise InvalidAlertDataException("title", title, "El título no puede estar vacío")
        
        if not description or not description.strip():
            raise InvalidAlertDataException("description", description, "La descripción no puede estar vacía")
        
        if not region or not region.strip():
            raise InvalidAlertDataException("region", region, "La región no puede estar vacía")
        
        # Validar longitudes
        if len(title.strip()) > 255:
            raise InvalidAlertDataException("title", title, "El título no puede exceder 255 caracteres")
        
        if len(description.strip()) > 5000:
            raise InvalidAlertDataException("description", description, "La descripción no puede exceder 5000 caracteres")
    
    def _validate_coordinates(self, latitude: Optional[float], longitude: Optional[float]):
        """Valida coordenadas geográficas"""
        if latitude is not None and (latitude < -90 or latitude > 90):
            raise InvalidAlertDataException("latitude", str(latitude), "La latitud debe estar entre -90 y 90")
        
        if longitude is not None and (longitude < -180 or longitude > 180):
            raise InvalidAlertDataException("longitude", str(longitude), "La longitud debe estar entre -180 y 180")
    
    def _validate_expiration_date(self, expires_at: Optional[datetime]):
        """Valida fecha de expiración"""
        if expires_at and expires_at <= datetime.utcnow():
            raise InvalidAlertDataException("expires_at", str(expires_at), "La fecha de expiración debe ser futura")
    
    def _validate_status_transition(self, current_status: AlertStatus, new_status: AlertStatus):
        """Valida transiciones de estado permitidas"""
        # Reglas de negocio para transiciones de estado
        invalid_transitions = [
            (AlertStatus.RESOLVED, AlertStatus.ACTIVE),  # No se puede reactivar una alerta resuelta
            (AlertStatus.CANCELLED, AlertStatus.ACTIVE),  # No se puede reactivar una alerta cancelada
        ]
        
        if (current_status, new_status) in invalid_transitions:
            raise InvalidAlertStatusException(
                f"No se puede cambiar de {current_status.value} a {new_status.value}"
            )
    
    def _process_expired_alerts(self, alerts: List[Alert]):
        """Procesa alertas expiradas en una lista"""
        for alert in alerts:
            if alert.is_expired() and alert.status == AlertStatus.ACTIVE:
                # Marcar como resuelta automáticamente
                try:
                    alert.status = AlertStatus.RESOLVED
                    self._repository.save(alert)
                except Exception:
                    # Log error pero continúa
                    pass

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
        """
        Crea una nueva fuente de datos
        
        Args:
            name: Nombre único de la fuente
            type: Tipo de fuente (weather_api, news_rss, etc.)
            url: URL de la fuente
            check_interval_minutes: Intervalo de verificación en minutos
            configuration: Configuración adicional
            
        Returns:
            DataSource: La fuente de datos creada
        """
        # Validaciones
        if not name or not name.strip():
            raise InvalidAlertDataException("name", name, "El nombre no puede estar vacío")
        
        if not url or not url.strip():
            raise InvalidAlertDataException("url", url, "La URL no puede estar vacía")
        
        if check_interval_minutes < 5:
            raise InvalidAlertDataException("check_interval_minutes", str(check_interval_minutes), 
                                          "El intervalo mínimo es 5 minutos")
        
        from .entities import DataSourceType
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
        """
        Obtiene fuentes de datos listas para verificar
        
        Returns:
            List[DataSource]: Fuentes listas para verificar
        """
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