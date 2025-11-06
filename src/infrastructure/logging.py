"""
Sistema de logging moderno con Loguru - CORREGIDO SIN COMPRESIÓN
"""
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar
from pathlib import Path

from loguru import logger

# Context variables para tracking
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)

def serialize_extra(record):
    """Serializa campos extra para JSON"""
    extra = record["extra"].copy()
    
    # Añadir context variables
    request_id = request_id_var.get()
    if request_id:
        extra["request_id"] = request_id
    
    user_id = user_id_var.get()
    if user_id:
        extra["user_id"] = user_id
    
    return extra

def setup_logging(environment: str = "development"):
    """Configura Loguru según el entorno"""
    
    # Remover handler por defecto
    logger.remove()
    
    if environment == "development":
        # Consola colorizada para desarrollo
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
            level="DEBUG",
            colorize=True,
            backtrace=True,
            diagnose=True
        )
    
    # Crear directorio de logs
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Archivo JSON estructurado (SIN compresión por ahora)
    logger.add(
        log_dir / "alert_manager.json",
        format=lambda record: json.dumps({
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name,
            "logger": record["name"],
            "module": record["module"],
            "function": record["function"], 
            "line": record["line"],
            "message": record["message"],
            **serialize_extra(record)
        }, default=str, ensure_ascii=False),
        level="INFO",
        rotation="10 MB",
        retention="7 days"
        # compression="gz"  ← REMOVIDO temporalmente
    )
    
    # Archivo solo para errores (SIN compresión)
    logger.add(
        log_dir / "errors.json",
        format=lambda record: json.dumps({
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name,
            "message": record["message"],
            "exception": record.get("exception"),
            **serialize_extra(record)
        }, default=str, ensure_ascii=False),
        level="ERROR",
        rotation="5 MB",
        retention="30 days",
        backtrace=True,
        diagnose=True
        # compression="gz"  ← REMOVIDO temporalmente
    )

# Funciones de conveniencia (mantienen la API anterior)
def log_api_request(method: str, path: str, status_code: int, duration_ms: float, **extra):
    """Log de API request"""
    logger.bind(**extra).info(
        f"API {method} {path} - {status_code} ({duration_ms:.2f}ms)",
        event_type="api_request",
        method=method,
        path=path,
        status_code=status_code,
        duration_ms=duration_ms
    )

def log_business_operation(operation: str, entity_type: str, entity_id: Optional[str] = None, **extra):
    """Log de operación de negocio"""
    logger.bind(**extra).info(
        f"Business: {operation} {entity_type}",
        event_type="business_operation",
        operation=operation,
        entity_type=entity_type,
        entity_id=entity_id
    )

def log_data_source_check(source_name: str, success: bool, alerts_created: int = 0, **extra):
    """Log de verificación de fuente de datos"""
    status = "success" if success else "failed"
    logger.bind(**extra).info(
        f"DataSource {source_name} - {status} ({alerts_created} alerts)",
        event_type="data_source_check",
        source_name=source_name,
        success=success,
        alerts_created=alerts_created
    )

def log_airflow_task(dag_id: str, task_id: str, state: str, **extra):
    """Log de tarea Airflow"""
    logger.bind(**extra).info(
        f"Airflow {dag_id}.{task_id} - {state}",
        event_type="airflow_task",
        dag_id=dag_id,
        task_id=task_id,
        state=state
    )

def log_error(error: Exception, context: str, **extra):
    """Log de error con contexto completo"""
    logger.bind(**extra).error(
        f"Error in {context}: {str(error)}",
        event_type="error",
        error_type=type(error).__name__,
        context=context
    )

def log_security_event(event_type: str, description: str, **extra):
    """Log de evento de seguridad"""
    logger.bind(**extra).warning(
        f"Security: {event_type} - {description}",
        event_type="security",
        security_event_type=event_type,
        description=description
    )

def set_request_context(request_id: str, user_id: Optional[str] = None):
    """Establece contexto de request"""
    request_id_var.set(request_id)
    if user_id:
        user_id_var.set(user_id)

def clear_request_context():
    """Limpia contexto de request"""
    request_id_var.set(None)
    user_id_var.set(None)

# Configurar según entorno (puedes cambiarlo)
import os
environment = os.getenv("ENVIRONMENT", "development")

# NO llamar setup_logging() automáticamente, mejor hacerlo manual
if __name__ != "__main__":
    setup_logging(environment)