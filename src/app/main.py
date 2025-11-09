import os
import time
import logging
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .routers import alerts
from ..infrastructure.middleware import (
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware, 
    HealthCheckMiddleware,
    RateLimitMiddleware,
    global_limiter
)
from ..infrastructure.logging import get_logger

# Logger para main
logger = get_logger("main")

# Configurar entorno
environment = os.getenv("ENVIRONMENT", "development")

app = FastAPI(
    title="Alert Manager API",
    description="Sistema moderno de gestión de alertas con arquitectura por capas",
    version="1.0.0",
    docs_url="/docs" if environment == "development" else None,
    redoc_url="/redoc" if environment == "development" else None
)

# ================================
# MIDDLEWARE STACK (orden importa)
# ================================

# 1. Health check (más rápido)
app.add_middleware(HealthCheckMiddleware)

# 2. Security headers
app.add_middleware(SecurityHeadersMiddleware)

# 3. Rate limiting
app.add_middleware(RateLimitMiddleware, limiter=global_limiter)

# 4. Request logging
app.add_middleware(RequestLoggingMiddleware)

# 5. CORS (al final)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if environment == "development" else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# ================================
# EVENTOS DE APLICACIÓN
# ================================

@app.on_event("startup")
async def startup_event():
    """Evento de inicio"""
    logger.info(
        "Alert Manager API starting up",
        extra={
            "event_type": "application_startup",
            "version": "1.0.0",
            "environment": environment,
            "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
            "features": ["layered_architecture", "domain_services", "structured_logging", "native_rate_limiting"]
        }
    )

@app.on_event("shutdown")
async def shutdown_event():
    """Evento de cierre"""
    logger.info(
        "Alert Manager API shutting down",
        extra={"event_type": "application_shutdown"}
    )

# ================================
# ROUTERS
# ================================

app.include_router(alerts.router)

# ================================
# ENDPOINTS GLOBALES
# ================================

@app.get("/")
async def root():
    """Endpoint raíz con información de la API"""
    return {
        "service": "Alert Manager API",
        "version": "1.0.0",
        "status": "running",
        "environment": environment,
        "timestamp": datetime.utcnow().isoformat(),
        "architecture": "layered_microservice",
        "features": [
            "domain_driven_design",
            "clean_architecture", 
            "structured_logging",
            "native_rate_limiting",
            "input_validation",
            "error_handling"
        ],
        "endpoints": {
            "alerts": "/alerts",
            "health": "/alerts/health",
            "docs": "/docs" if environment == "development" else "disabled",
            "statistics": "/alerts/statistics/summary"
        },
        "rate_limit": {
            "requests_per_minute": global_limiter.max_requests,
            "window_seconds": global_limiter.time_window
        }
    }

@app.get("/ping")
async def ping():
    """Ping simple para load balancers"""
    return {"ping": "pong", "timestamp": time.time()}

@app.get("/version")
async def version():
    """Información de versión detallada"""
    return {
        "service": "alert_manager",
        "version": "1.0.0",
        "build": "hito3",
        "environment": environment,
        "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
        "architecture": {
            "pattern": "clean_architecture",
            "layers": ["api", "domain", "infrastructure"],
            "database": "postgresql",
            "logging": "standard_python",
            "rate_limiting": "native_memory"
        }
    }

@app.get("/rate-limit-status")
async def rate_limit_status(request: Request):
    """Información del rate limiting para debug"""
    from ..infrastructure.middleware import get_client_ip
    
    client_ip = get_client_ip(request)
    remaining = global_limiter.get_remaining(client_ip)
    
    return {
        "client_ip": client_ip,
        "limit": global_limiter.max_requests,
        "window_seconds": global_limiter.time_window,
        "remaining": remaining,
        "reset_at": int(time.time()) + global_limiter.time_window
    }