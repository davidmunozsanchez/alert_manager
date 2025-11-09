"""
Sistema de logging nativo con logger estándar de Python
"""
import json
import logging
import logging.handlers
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar
from pathlib import Path
import os

# Context variables para tracking
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)

class ContextFilter(logging.Filter):
    """Filtro que añade información de contexto a los logs"""
    
    def filter(self, record):
        # Añadir context variables
        record.request_id = request_id_var.get()
        record.user_id = user_id_var.get()
        return True

class JSONFormatter(logging.Formatter):
    """Formatter JSON personalizado"""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage()
        }
        
        # Añadir contexto
        if hasattr(record, 'request_id') and record.request_id:
            log_data["request_id"] = record.request_id
        
        if hasattr(record, 'user_id') and record.user_id:
            log_data["user_id"] = record.user_id
        
        # Añadir campos extra si existen
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info', 
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated', 
                          'thread', 'threadName', 'processName', 'process', 'message', 
                          'request_id', 'user_id']:
                log_data[key] = value
        
        # Añadir excepción si existe
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, default=str, ensure_ascii=False)

def setup_logging(environment: str = "development"):
    """Configura logging estándar según el entorno"""
    
    # Crear directorio de logs
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Obtener logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if environment == "development" else logging.INFO)
    
    # Limpiar handlers existentes
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Filtro de contexto
    context_filter = ContextFilter()
    
    if environment == "development":
        # Handler de consola para desarrollo
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(context_filter)
        root_logger.addHandler(console_handler)
    
    # Handler JSON para archivo general
    json_handler = logging.handlers.RotatingFileHandler(
        log_dir / "alert_manager.json",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    json_handler.setLevel(logging.INFO)
    json_formatter = JSONFormatter()
    json_handler.setFormatter(json_formatter)
    json_handler.addFilter(context_filter)
    root_logger.addHandler(json_handler)
    
    # Handler solo para errores
    error_handler = logging.handlers.RotatingFileHandler(
        log_dir / "errors.json",
        maxBytes=5*1024*1024,  # 5MB
        backupCount=10
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(json_formatter)
    error_handler.addFilter(context_filter)
    root_logger.addHandler(error_handler)

def get_logger(name: str = None) -> logging.Logger:
    """Obtener logger con nombre específico"""
    return logging.getLogger(name or __name__)

# Logger global para el módulo
logger = get_logger("alert_manager")

# Funciones de conveniencia
def log_api_request(method: str, path: str, status_code: int, duration_ms: float, **extra):
    """Log de API request"""
    logger.info(
        f"API {method} {path} - {status_code} ({duration_ms:.2f}ms)",
        extra={
            "event_type": "api_request",
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            **extra
        }
    )

def log_business_operation(operation: str, entity_type: str, entity_id: Optional[str] = None, **extra):
    """Log de operación de negocio"""
    logger.info(
        f"Business: {operation} {entity_type}",
        extra={
            "event_type": "business_operation",
            "operation": operation,
            "entity_type": entity_type,
            "entity_id": entity_id,
            **extra
        }
    )

def log_data_source_check(source_name: str, success: bool, alerts_created: int = 0, **extra):
    """Log de verificación de fuente de datos"""
    status = "success" if success else "failed"
    logger.info(
        f"DataSource {source_name} - {status} ({alerts_created} alerts)",
        extra={
            "event_type": "data_source_check",
            "source_name": source_name,
            "success": success,
            "alerts_created": alerts_created,
            **extra
        }
    )

def log_airflow_task(dag_id: str, task_id: str, state: str, **extra):
    """Log de tarea Airflow"""
    logger.info(
        f"Airflow {dag_id}.{task_id} - {state}",
        extra={
            "event_type": "airflow_task",
            "dag_id": dag_id,
            "task_id": task_id,
            "state": state,
            **extra
        }
    )

def log_error(error: Exception, context: str, **extra):
    """Log de error con contexto completo"""
    logger.error(
        f"Error in {context}: {str(error)}",
        extra={
            "event_type": "error",
            "error_type": type(error).__name__,
            "context": context,
            **extra
        },
        exc_info=True
    )

def log_security_event(event_type: str, description: str, **extra):
    """Log de evento de seguridad"""
    logger.warning(
        f"Security: {event_type} - {description}",
        extra={
            "event_type": "security",
            "security_event_type": event_type,
            "description": description,
            **extra
        }
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

# Configurar logging automáticamente
environment = os.getenv("ENVIRONMENT", "development")
setup_logging(environment)