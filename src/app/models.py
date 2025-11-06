from datetime import datetime
from sqlalchemy import Column, DateTime, Float, Integer, String, Text, JSON, Index
from app.database import Base

class Alert(Base):
    __tablename__ = "alerts"
    
    # Campos principales
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    level = Column(String(50), nullable=False, index=True)
    type = Column(String(50), nullable=False, index=True)
    region = Column(String(255), nullable=False, index=True)
    status = Column(String(50), nullable=False, index=True, default="active")
    
    # Fechas
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=True)
    
    # Ubicación geográfica
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Nuevos campos para arquitectura moderna
    source = Column(String(255), nullable=True)  # Fuente que generó la alerta
    metadata = Column(JSON, nullable=True)  # Datos adicionales en formato JSON
    
    # Índices compuestos para consultas frecuentes
    __table_args__ = (
        Index('idx_alert_status_level', 'status', 'level'),
        Index('idx_alert_region_status', 'region', 'status'),
        Index('idx_alert_timestamp_status', 'timestamp', 'status'),
        Index('idx_alert_expires_status', 'expires_at', 'status'),
    )

class DataSource(Base):
    __tablename__ = "data_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    type = Column(String(50), nullable=False, index=True)
    url = Column(String(500), nullable=False)
    is_active = Column(String(10), nullable=False, default="true", index=True)  # "true"/"false"
    check_interval_minutes = Column(Integer, nullable=False, default=60)
    last_check = Column(DateTime, nullable=True)
    last_success = Column(DateTime, nullable=True)
    error_count = Column(Integer, nullable=False, default=0)
    configuration = Column(JSON, nullable=True)
    
    # Índices para consultas frecuentes
    __table_args__ = (
        Index('idx_datasource_active_type', 'is_active', 'type'),
        Index('idx_datasource_last_check', 'last_check'),
    )