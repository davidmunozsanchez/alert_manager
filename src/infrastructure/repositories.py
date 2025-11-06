"""
Implementación de repositorios usando SQLAlchemy
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime

from ..domain.entities import Alert, AlertFilter, AlertLevel, AlertStatus, AlertType, DataSource
from ..domain.repositories import AlertRepository, DataSourceRepository
from ..app.models import Alert as AlertModel, DataSource as DataSourceModel
from .mappers import AlertMapper, DataSourceMapper
from .logging import log_business_operation, log_error

class SQLAlchemyAlertRepository(AlertRepository):
    """Implementación del repositorio de alertas usando SQLAlchemy"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def save(self, alert: Alert) -> Alert:
        """Guarda una alerta en la base de datos"""
        try:
            if alert.id is None:
                # Nueva alerta
                db_alert = AlertMapper.to_model(alert)
                self.db.add(db_alert)
                self.db.commit()
                self.db.refresh(db_alert)
                
                # Actualizar el ID en la entidad de dominio
                alert.id = db_alert.id
                
                log_business_operation(
                    operation="create",
                    entity_type="alert",
                    entity_id=str(alert.id),
                    title=alert.title,
                    level=alert.level.value,
                    region=alert.region
                )
            else:
                # Actualizar alerta existente
                db_alert = self.db.query(AlertModel).filter(AlertModel.id == alert.id).first()
                if db_alert:
                    AlertMapper.update_model_from_domain(db_alert, alert)
                    self.db.commit()
                    
                    log_business_operation(
                        operation="update",
                        entity_type="alert",
                        entity_id=str(alert.id),
                        status=alert.status.value
                    )
                else:
                    raise ValueError(f"Alert with ID {alert.id} not found for update")
            
            return alert
            
        except Exception as e:
            self.db.rollback()
            log_error(e, "save_alert", alert_id=alert.id)
            raise
    
    def find_by_id(self, alert_id: int) -> Optional[Alert]:
        """Busca una alerta por ID"""
        try:
            db_alert = self.db.query(AlertModel).filter(AlertModel.id == alert_id).first()
            if db_alert:
                return AlertMapper.to_domain(db_alert)
            return None
        except Exception as e:
            log_error(e, "find_alert_by_id", alert_id=alert_id)
            raise
    
    def find_all(self, filter: Optional[AlertFilter] = None) -> List[Alert]:
        """Busca todas las alertas con filtros opcionales"""
        try:
            query = self.db.query(AlertModel)
            
            if filter:
                # Aplicar filtros
                if filter.level:
                    query = query.filter(AlertModel.level == filter.level.value)
                
                if filter.type:
                    query = query.filter(AlertModel.type == filter.type.value)
                
                if filter.region:
                    query = query.filter(AlertModel.region.ilike(f"%{filter.region}%"))
                
                if filter.status:
                    query = query.filter(AlertModel.status == filter.status.value)
                
                if filter.from_date:
                    query = query.filter(AlertModel.timestamp >= filter.from_date)
                
                if filter.to_date:
                    query = query.filter(AlertModel.timestamp <= filter.to_date)
                
                if filter.active_only:
                    query = query.filter(
                        and_(
                            AlertModel.status == AlertStatus.ACTIVE.value,
                            or_(
                                AlertModel.expires_at.is_(None),
                                AlertModel.expires_at > datetime.utcnow()
                            )
                        )
                    )
                
                if filter.high_priority_only:
                    query = query.filter(
                        AlertModel.level.in_([
                            AlertLevel.CRITICAL.value,
                            AlertLevel.EMERGENCY.value
                        ])
                    )
            
            # Ordenar por timestamp descendente (más recientes primero)
            query = query.order_by(AlertModel.timestamp.desc())
            
            db_alerts = query.all()
            domain_alerts = [AlertMapper.to_domain(db_alert) for db_alert in db_alerts]
            
            log_business_operation(
                operation="find_all",
                entity_type="alert",
                results_count=len(domain_alerts),
                filter_applied=filter is not None
            )
            
            return domain_alerts
            
        except Exception as e:
            log_error(e, "find_all_alerts")
            raise
    
    def delete(self, alert_id: int) -> bool:
        """Elimina una alerta"""
        try:
            db_alert = self.db.query(AlertModel).filter(AlertModel.id == alert_id).first()
            if db_alert:
                self.db.delete(db_alert)
                self.db.commit()
                
                log_business_operation(
                    operation="delete",
                    entity_type="alert",
                    entity_id=str(alert_id)
                )
                return True
            return False
            
        except Exception as e:
            self.db.rollback()
            log_error(e, "delete_alert", alert_id=alert_id)
            raise
    
    def exists_by_title_and_region(self, title: str, region: str) -> bool:
        """Verifica si existe una alerta con título y región específicos"""
        try:
            count = self.db.query(AlertModel).filter(
                and_(
                    AlertModel.title.ilike(f"%{title}%"),
                    AlertModel.region.ilike(f"%{region}%"),
                    AlertModel.status.in_([
                        AlertStatus.ACTIVE.value,
                        AlertStatus.PENDING.value
                    ])
                )
            ).count()
            
            return count > 0
            
        except Exception as e:
            log_error(e, "check_duplicate_alert", title=title, region=region)
            raise
    
    def count_by_status(self, status: AlertStatus) -> int:
        """Cuenta alertas por estado"""
        try:
            return self.db.query(AlertModel).filter(
                AlertModel.status == status.value
            ).count()
        except Exception as e:
            log_error(e, "count_by_status", status=status.value)
            raise
    
    def find_expired_active_alerts(self) -> List[Alert]:
        """Encuentra alertas activas que han expirado"""
        try:
            db_alerts = self.db.query(AlertModel).filter(
                and_(
                    AlertModel.status == AlertStatus.ACTIVE.value,
                    AlertModel.expires_at.is_not(None),
                    AlertModel.expires_at < datetime.utcnow()
                )
            ).all()
            
            return [AlertMapper.to_domain(db_alert) for db_alert in db_alerts]
            
        except Exception as e:
            log_error(e, "find_expired_alerts")
            raise

class SQLAlchemyDataSourceRepository(DataSourceRepository):
    """Implementación del repositorio de fuentes de datos usando SQLAlchemy"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def save(self, data_source: DataSource) -> DataSource:
        """Guarda una fuente de datos"""
        try:
            if data_source.id is None:
                # Nueva fuente
                db_source = DataSourceMapper.to_model(data_source)
                self.db.add(db_source)
                self.db.commit()
                self.db.refresh(db_source)
                
                data_source.id = db_source.id
                
                log_business_operation(
                    operation="create",
                    entity_type="data_source",
                    entity_id=str(data_source.id),
                    name=data_source.name,
                    type=data_source.type.value
                )
            else:
                # Actualizar fuente existente
                db_source = self.db.query(DataSourceModel).filter(DataSourceModel.id == data_source.id).first()
                if db_source:
                    DataSourceMapper.update_model_from_domain(db_source, data_source)
                    self.db.commit()
                    
                    log_business_operation(
                        operation="update",
                        entity_type="data_source",
                        entity_id=str(data_source.id),
                        name=data_source.name
                    )
                else:
                    raise ValueError(f"DataSource with ID {data_source.id} not found for update")
            
            return data_source
            
        except Exception as e:
            self.db.rollback()
            log_error(e, "save_data_source", source_id=data_source.id)
            raise
    
    def find_by_id(self, source_id: int) -> Optional[DataSource]:
        """Busca una fuente de datos por ID"""
        try:
            db_source = self.db.query(DataSourceModel).filter(DataSourceModel.id == source_id).first()
            if db_source:
                return DataSourceMapper.to_domain(db_source)
            return None
        except Exception as e:
            log_error(e, "find_data_source_by_id", source_id=source_id)
            raise
    
    def find_all_active(self) -> List[DataSource]:
        """Busca todas las fuentes de datos activas"""
        try:
            db_sources = self.db.query(DataSourceModel).filter(
                DataSourceModel.is_active == "true"
            ).all()
            
            return [DataSourceMapper.to_domain(db_source) for db_source in db_sources]
            
        except Exception as e:
            log_error(e, "find_all_active_data_sources")
            raise
    
    def find_ready_for_check(self) -> List[DataSource]:
        """Busca fuentes de datos listas para verificar"""
        try:
            all_sources = self.find_all_active()
            ready_sources = [source for source in all_sources if source.can_be_checked()]
            
            log_business_operation(
                operation="find_ready_for_check",
                entity_type="data_source",
                ready_count=len(ready_sources),
                total_active=len(all_sources)
            )
            
            return ready_sources
            
        except Exception as e:
            log_error(e, "find_ready_for_check_data_sources")
            raise