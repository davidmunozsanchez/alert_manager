"""
Dependencias para inyección en FastAPI
"""
from typing import Generator
from sqlalchemy.orm import Session
from fastapi import Depends  # ← MOVER ESTE IMPORT AL INICIO

from .database import SessionLocal
from ..domain.services import AlertService, DataSourceService
from ..infrastructure.repositories import SQLAlchemyAlertRepository, SQLAlchemyDataSourceRepository
from ..infrastructure.logging import logger

def get_db() -> Generator[Session, None, None]:
    """
    Dependency para obtener sesión de base de datos
    """
    db = SessionLocal()
    try:
        logger.debug("Database session created")
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()
        logger.debug("Database session closed")

def get_alert_service(db: Session = Depends(get_db)) -> AlertService:
    """
    Dependency para obtener servicio de alertas
    """
    try:
        repository = SQLAlchemyAlertRepository(db)
        service = AlertService(repository)
        logger.debug("Alert service created successfully")
        return service
    except Exception as e:
        logger.error(f"Error creating alert service: {e}")
        raise

def get_data_source_service(db: Session = Depends(get_db)) -> DataSourceService:
    """
    Dependency para obtener servicio de fuentes de datos
    """
    try:
        repository = SQLAlchemyDataSourceRepository(db)
        service = DataSourceService(repository)
        logger.debug("Data source service created successfully")
        return service
    except Exception as e:
        logger.error(f"Error creating data source service: {e}")
        raise

def get_alert_repository(db: Session = Depends(get_db)) -> SQLAlchemyAlertRepository:
    """
    Dependency para obtener repositorio de alertas directamente (para casos especiales)
    """
    return SQLAlchemyAlertRepository(db)

def get_data_source_repository(db: Session = Depends(get_db)) -> SQLAlchemyDataSourceRepository:
    """
    Dependency para obtener repositorio de fuentes de datos directamente
    """
    return SQLAlchemyDataSourceRepository(db)