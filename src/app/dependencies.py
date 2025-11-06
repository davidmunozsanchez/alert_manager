"""
Dependencias para inyección en FastAPI
"""
from typing import Generator
from sqlalchemy.orm import Session

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
        yield db
    finally:
        db.close()

def get_alert_service(db: Session = Depends(get_db)) -> AlertService:
    """
    Dependency para obtener servicio de alertas
    """
    repository = SQLAlchemyAlertRepository(db)
    return AlertService(repository)

def get_data_source_service(db: Session = Depends(get_db)) -> DataSourceService:
    """
    Dependency para obtener servicio de fuentes de datos
    """
    repository = SQLAlchemyDataSourceRepository(db)
    return DataSourceService(repository)

# Import necesario para Depends
from fastapi import Depends