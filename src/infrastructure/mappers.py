"""
Mappers para convertir entre entidades de dominio y modelos de base de datos
"""
from typing import Optional
from datetime import datetime

from ..domain.entities import Alert, AlertLevel, AlertStatus, AlertType, DataSource, DataSourceType
from ..app.models import Alert as AlertModel, DataSource as DataSourceModel

class AlertMapper:
    """Mapper para entidades Alert"""
    
    @staticmethod
    def to_domain(db_alert: AlertModel) -> Alert:
        """Convierte de modelo de BD a entidad de dominio"""
        return Alert(
            id=db_alert.id,
            title=db_alert.title,
            description=db_alert.description,
            level=AlertLevel(db_alert.level),
            type=AlertType(db_alert.type),
            region=db_alert.region,
            status=AlertStatus(db_alert.status),
            timestamp=db_alert.timestamp,
            expires_at=db_alert.expires_at,
            latitude=db_alert.latitude,
            longitude=db_alert.longitude,  
            source=db_alert.source,
            metadata=db_alert.metadata
        )
    
    @staticmethod
    def to_model(domain_alert: Alert) -> AlertModel:
        """Convierte de entidad de dominio a modelo de BD"""
        return AlertModel(
            id=domain_alert.id,
            title=domain_alert.title,
            description=domain_alert.description,
            level=domain_alert.level.value,
            type=domain_alert.type.value,
            region=domain_alert.region,
            status=domain_alert.status.value,
            timestamp=domain_alert.timestamp,
            expires_at=domain_alert.expires_at,
            latitude=domain_alert.latitude,
            longitude=domain_alert.longitude,
            source=domain_alert.source,
            metadata=domain_alert.metadata
        )
    
    @staticmethod
    def update_model_from_domain(db_alert: AlertModel, domain_alert: Alert) -> AlertModel:
        """Actualiza un modelo de BD con datos de entidad de dominio"""
        db_alert.title = domain_alert.title
        db_alert.description = domain_alert.description
        db_alert.level = domain_alert.level.value
        db_alert.type = domain_alert.type.value
        db_alert.region = domain_alert.region
        db_alert.status = domain_alert.status.value
        db_alert.expires_at = domain_alert.expires_at
        db_alert.latitude = domain_alert.latitude
        db_alert.longitude = domain_alert.longitude
        db_alert.source = domain_alert.source
        db_alert.metadata = domain_alert.metadata
        return db_alert

class DataSourceMapper:
    """Mapper para entidades DataSource"""
    
    @staticmethod
    def to_domain(db_source: DataSourceModel) -> DataSource:
        """Convierte de modelo de BD a entidad de dominio"""
        return DataSource(
            id=db_source.id,
            name=db_source.name,
            type=DataSourceType(db_source.type),
            url=db_source.url,
            is_active=db_source.is_active == "true",
            check_interval_minutes=db_source.check_interval_minutes,
            last_check=db_source.last_check,
            last_success=db_source.last_success,
            error_count=db_source.error_count,
            configuration=db_source.configuration
        )
    
    @staticmethod
    def to_model(domain_source: DataSource) -> DataSourceModel:
        """Convierte de entidad de dominio a modelo de BD"""
        return DataSourceModel(
            id=domain_source.id,
            name=domain_source.name,
            type=domain_source.type.value,
            url=domain_source.url,
            is_active="true" if domain_source.is_active else "false",
            check_interval_minutes=domain_source.check_interval_minutes,
            last_check=domain_source.last_check,
            last_success=domain_source.last_success,
            error_count=domain_source.error_count,
            configuration=domain_source.configuration
        )
    
    @staticmethod
    def update_model_from_domain(db_source: DataSourceModel, domain_source: DataSource) -> DataSourceModel:
        """Actualiza un modelo de BD con datos de entidad de dominio"""
        db_source.name = domain_source.name
        db_source.type = domain_source.type.value
        db_source.url = domain_source.url
        db_source.is_active = "true" if domain_source.is_active else "false"
        db_source.check_interval_minutes = domain_source.check_interval_minutes
        db_source.last_check = domain_source.last_check
        db_source.last_success = domain_source.last_success
        db_source.error_count = domain_source.error_count
        db_source.configuration = domain_source.configuration
        return db_source