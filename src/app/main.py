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
    
    # Inicializar base de datos
    try:
        from .database import engine, Base, wait_for_postgres
        
        logger.info("Waiting for PostgreSQL to be ready...")
        if wait_for_postgres():
            logger.info("Creating database tables...")
            Base.metadata.create_all(bind=engine)
            logger.info("✅ Database tables created successfully")
        else:
            logger.error("❌ Failed to connect to PostgreSQL")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")

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
        "timestamp": datetime.utcnow().isoformat(),
        "environment": environment,
        "health_check": "/alerts/health"
    }

@app.get("/ping")
async def ping():
    """Endpoint de ping simple para verificar que el servicio responde"""
    return {
        "status": "healthy",
        "service": "alert_manager",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": environment
    }

@app.get("/debug/simple")
async def debug_simple():
    """Endpoint de debug simple"""
    return {
        "debug": True,
        "message": "Debug endpoint working",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": environment,
        "process_id": os.getpid(),
        "memory_usage": "unknown"  # Placeholder
    }

@app.get("/debug/headers")
async def debug_headers(request: Request):
    """Endpoint para debug de headers"""
    return {
        "debug": True,
        "headers": dict(request.headers),
        "method": request.method,
        "url": str(request.url),
        "client": request.client.host if request.client else None,
        "timestamp": datetime.utcnow().isoformat()
    }
@app.get("/test-logs")
async def test_logs():
    """Endpoint específico para probar logs en Seq"""
    test_id = int(time.time())
    
    # Log de información
    logger.info("🧪 Test log INFO level", extra={
        "test_id": test_id,
        "log_level": "info",
        "endpoint": "/test-logs"
    })
    
    # Log de warning
    logger.warning("⚠️ Test log WARNING level", extra={
        "test_id": test_id,
        "log_level": "warning",
        "endpoint": "/test-logs"
    })
    
    # Log de error (para pruebas)
    logger.error("❌ Test log ERROR level", extra={
        "test_id": test_id,
        "log_level": "error",
        "endpoint": "/test-logs"
    })
    
    return {
        "message": "Logs de prueba enviados",
        "test_id": test_id,
        "timestamp": datetime.utcnow().isoformat(),
        "seq_url": os.getenv("SEQ_URL", "No configurado")
    }
@app.get("/debug/env")
async def debug_env():
    """Endpoint para debug de variables de entorno (solo desarrollo)"""
    if environment != "development":
        return {"error": "Debug endpoint only available in development"}
    
    safe_vars = {
        key: value for key, value in os.environ.items()
        if not any(secret in key.upper() for secret in ['PASSWORD', 'SECRET', 'KEY', 'TOKEN'])
    }
    
    return {
        "debug": True,
        "environment_variables": safe_vars,
        "timestamp": datetime.utcnow().isoformat()
    }

# ================================
# MANEJO DE ERRORES GLOBAL
# ================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Manejo global de excepciones"""
    logger.error(
        f"Unhandled exception in {request.method} {request.url.path}",
        extra={
            "event_type": "unhandled_exception",
            "method": request.method,
            "path": request.url.path,
            "error_type": type(exc).__name__,
            "error_message": str(exc)
        },
        exc_info=True
    )
    
    if environment == "development":
        return {
            "error": "Internal server error",
            "detail": str(exc),
            "type": type(exc).__name__,
            "timestamp": datetime.utcnow().isoformat()
        }
    else:
        return {
            "error": "Internal server error",
            "timestamp": datetime.utcnow().isoformat()
        }

# ================================
# INFORMACIÓN DE LA APLICACIÓN
# ================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=environment == "development",
        log_level="debug" if environment == "development" else "info"
    )