from datetime import datetime, timedelta

from sqlalchemy import Column, DateTime, Float, Integer, String

from app.database import Base


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    level = Column(String)
    type = Column(String)
    region = Column(String)
    status = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    latitude = Column(Float)  # Nueva columna para la latitud
    longitude = Column(Float)  # Nueva columna para la longitud
