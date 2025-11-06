import os
from datetime import datetime

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from loguru import logger

from .database import get_db
from .routers import alerts
from ..infrastructure.middleware import (
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware, 
    HealthCheckMiddleware,
    limiter
)

# Configurar entorno
environment = os.getenv("ENVIRONMENT", "development")

app = FastAPI(
    title="Alert Manager API",
    description="Sistema moderno de gestión de alertas meteorológicas",
    version="1.0.0",
    docs_url="/docs" if environment == "development" else None,  # Ocultar docs en producción
    redoc_url="/redoc" if environment == "development" else None
)

# Rate limiter global
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ================================
# MIDDLEWARE STACK (orden importa)
# ================================

# 1. Health check (más rápido)
app.add_middleware(HealthCheckMiddleware)

# 2. Security headers
app.add_middleware(SecurityHeadersMiddleware)

# 3. Request logging (después de security)
app.add_middleware(RequestLoggingMiddleware)

# 4. CORS (al final)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if environment == "development" else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# ================================
# EVENTOS DE APLICACIÓN
# ================================

@app.on_event("startup")
async def startup_event():
    """Evento de inicio"""
    logger.info(
        "🚀 Alert Manager API starting up",
        event_type="application_startup",
        version="1.0.0",
        environment=environment,
        python_version=f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}"
    )

@app.on_event("shutdown")
async def shutdown_event():
    """Evento de cierre"""
    logger.info(
        "🛑 Alert Manager API shutting down",
        event_type="application_shutdown"
    )

# ================================
# ROUTERS
# ================================

app.include_router(alerts.router)

# ================================
# ENDPOINTS GLOBALES
# ================================

@app.get("/")
@limiter.limit("100/minute")
async def root(request: Request):
    """Endpoint raíz con información de la API"""
    return {
        "service": "Alert Manager API",
        "version": "1.0.0",
        "status": "running",
        "environment": environment,
        "timestamp": datetime.utcnow().isoformat(),
        "docs": "/docs" if environment == "development" else "disabled",
        "health": "/alerts/health"
    }

@app.get("/ping")
async def ping():
    """Ping simple para load balancers"""
    return {"ping": "pong", "timestamp": time.time()}

@app.get("/metrics")
@limiter.limit("10/minute")
async def metrics(request: Request):
    """Métricas básicas (expandir con Prometheus después)"""
    return {
        "service": "alert_manager",
        "status": "running",
        "uptime": "unknown",  # Implementar contador
        "environment": environment,
        "requests_processed": "unknown"  # Implementar contador
    }