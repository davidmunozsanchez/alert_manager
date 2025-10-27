from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field, validator


# Enum para el nivel de alerta
class AlertLevel(str, Enum):
    baja = "baja"
    media = "media"
    alta = "alta"
    muy_alta = "muy alta"


class AlertLevel(str, Enum):
    baja = "baja"
    media = "media"
    alta = "alta"
    muy_alta = "muy alta"


class AlertCreate(BaseModel):
    title: str
    description: str
    level: AlertLevel
    type: str
    region: str
    status: str
    expires_at: datetime
    latitude: float  # Nueva propiedad para la latitud
    longitude: float  # Nueva propiedad para la longitud


class Alert(BaseModel):
    id: int
    title: str
    description: str
    level: AlertLevel
    type: str
    region: str
    status: str
    expires_at: datetime
    timestamp: datetime
    latitude: float  # Nueva propiedad para la latitud
    longitude: float  # Nueva propiedad para la longitud

    class Config:
        orm_mode = True
