import logging
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from .database import get_db
from .routers import alerts
from ..infrastructure.middleware import (
    LoggingMiddleware, 
    SecurityMiddleware, 
    HealthCheckMiddleware
)
from ..infrastructure.logging import logger

# from .auth import initialize_firebase

# # Inicializar Firebase
# initialize_firebase()

app = FastAPI(
    title="Weather Alerts API", 
    description="Gestión de alertas meteorológicas y otros tipos", 
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ================================
# MIDDLEWARE CONFIGURATION
# ================================

# 1. Health Check Middleware (más rápido, sin logging)
app.add_middleware(HealthCheckMiddleware)

# 2. Security Middleware
app.add_middleware(SecurityMiddleware, max_requests_per_minute=1000)

# 3. Logging Middleware (debe ir después de security)
app.add_middleware(LoggingMiddleware)

# 4. CORS Middleware (debe ir al final)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios exactos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================================
# STARTUP/SHUTDOWN EVENTS
# ================================

@app.on_event("startup")
async def startup_event():
    """Evento de inicio de la aplicación"""
    logger.info(
        "Alert Manager API starting up",
        event_type="application_startup",
        version="1.0.0",
        environment="development"  # Cambiar según entorno
    )

@app.on_event("shutdown")
async def shutdown_event():  
    """Evento de cierre de la aplicación"""
    logger.info(
        "Alert Manager API shutting down",
        event_type="application_shutdown"
    )

# ================================
# EXCEPTION HANDLERS
# ================================

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handler para errores de valor"""
    from ..infrastructure.logging import log_error
    
    log_error(
        error=exc,
        context="value_error_handler",
        request_path=str(request.url.path),
        request_method=request.method
    )
    
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "INVALID_VALUE",
                "message": str(exc),
                "type": "validation_error"
            }
        }
    )

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handler para errores 404"""
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": "NOT_FOUND",
                "message": f"Endpoint {request.url.path} no encontrado",
                "type": "not_found_error"
            }
        }
    )

# ================================
# ROUTERS
# ================================

app.include_router(alerts.router)

# ================================
# ROOT ENDPOINT
# ================================

@app.get("/")
async def root():
    """Endpoint raíz con información de la API"""
    from ..infrastructure.logging import log_api_request
    
    return {
        "message": "Alert Manager API",
        "version": "1.0.0",
        "description": "Sistema de gestión de alertas meteorológicas y otros tipos",
        "docs": "/docs",
        "health": "/alerts/health",
        "endpoints": {
            "alerts": "/alerts",
            "health": "/alerts/health"
        }
    }

@app.get("/metrics")
async def metrics():
    """Endpoint básico de métricas"""
    # Aquí podrías integrar Prometheus metrics en el futuro
    return {
        "service": "alert_manager",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": "unknown"  # Implementar contador de uptime
    }