"""
Alert Manager - Sistema de Gestión de Alertas

Microservicio para gestión de alertas con arquitectura limpia (Clean Architecture).
"""

__version__ = "1.0.0"
__author__ = "David Muñoz"
__description__ = "Sistema de gestión de alertas con FastAPI y arquitectura limpia"

# Configuración del servicio
SERVICE_CONFIG = {
    "name": "alert_manager",
    "version": __version__,
    "description": __description__,
    "environment": "development",
    "api_prefix": "/api/v1"
}

# Exports principales
from .app.main import app

__all__ = ["app", "SERVICE_CONFIG", "__version__"]