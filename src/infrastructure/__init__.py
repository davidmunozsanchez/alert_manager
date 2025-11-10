"""
Infraestructura completa con repositories
"""
from .logging import (
    log_api_request, 
    log_business_operation, 
    log_error,
    log_data_source_check,
    log_airflow_task,
    log_security_event,
    set_request_context,
    clear_request_context,
    setup_logging
)

# Importar repositories y mappers
from .repositories import SQLAlchemyAlertRepository, SQLAlchemyDataSourceRepository
from .mappers import AlertMapper, DataSourceMapper

# Intentar importar middleware
try:
    from .middleware import (
        RequestLoggingMiddleware, 
        SecurityHeadersMiddleware, 
        HealthCheckMiddleware,
        RateLimitMiddleware,
        global_limiter
    )
    middleware_available = True
    # Alias para compatibilidad
    limiter = global_limiter
except ImportError as e:
    print(f"⚠️  Middleware no disponible: {e}")
    middleware_available = False
    RequestLoggingMiddleware = None
    SecurityHeadersMiddleware = None
    HealthCheckMiddleware = None
    RateLimitMiddleware = None
    global_limiter = None
    limiter = None

__all__ = [
    # Logger principal
    "logger",
    # Funciones de logging
    "log_api_request",
    "log_business_operation", 
    "log_error",
    "log_data_source_check",
    "log_airflow_task",
    "log_security_event",
    "set_request_context",
    "clear_request_context",
    "setup_logging",
    # Repositories
    "SQLAlchemyAlertRepository",
    "SQLAlchemyDataSourceRepository",
    # Mappers
    "AlertMapper",
    "DataSourceMapper",
]

if middleware_available:
    __all__.extend([
        "RequestLoggingMiddleware",
        "SecurityHeadersMiddleware", 
        "HealthCheckMiddleware",
        "RateLimitMiddleware",
        "global_limiter",
        "limiter",
    ])