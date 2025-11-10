"""
Capa de Aplicación (Application Layer)

Esta capa contiene:
- FastAPI application y configuración
- Routers y endpoints REST
- Esquemas de validación (Pydantic)  
- Dependencias e inyección de dependencias
- Modelos de base de datos (SQLAlchemy)
- Configuración de persistencia
"""

# Imports principales
from .main import app
from .database import get_db, SessionLocal
from .schemas import (
    AlertCreateSchema,
    AlertResponseSchema, 
    AlertUpdateSchema,
    AlertLevelSchema,
    AlertTypeSchema,
    AlertStatusSchema
)

__all__ = [
    "app",
    "get_db", 
    "SessionLocal",
    "AlertCreateSchema",
    "AlertResponseSchema",
    "AlertUpdateSchema", 
    "AlertLevelSchema",
    "AlertTypeSchema",
    "AlertStatusSchema"
]