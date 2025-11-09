"""
Routers de la API REST

Contiene todos los endpoints organizados por funcionalidad:
- alerts: CRUD de alertas, health checks, estadísticas, debug
"""

from .alerts import router as alerts_router

__all__ = ["alerts_router"]