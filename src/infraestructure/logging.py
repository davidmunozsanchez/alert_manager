"""
Sistema de logging para la API
"""
import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar
from pathlib import Path
import traceback

# Context variables para tracking de requests
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)

class StructuredFormatter(logging.Formatter):
    """
    Formatter que produce logs estructurados en JSON
    """
    
    def format(self, record: logging.LogRecord) -> str:
        # Datos base del log
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "process": record.process,
        }
        
        # Añadir request_id si está disponible
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id
        
        # Añadir user_id si está disponible
        user_id = user_id_var.get()
        if user_id:
            log_data["user_id"] = user_id
        
        # Añadir información de excepción si existe
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Añadir campos extra si existen
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data, ensure_ascii=False, default=str)

class AlertManagerLogger:
    """
    Logger personalizado para el sistema de alertas
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Configura el logger con handlers apropiados"""
        if self.logger.handlers:
            return  # Ya está configurado
        
        self.logger.setLevel(logging.INFO)
        
        # Handler para consola (desarrollo)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(StructuredFormatter())
        console_handler.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)
        
        # Handler para archivo (producción)
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Log general
        file_handler = logging.FileHandler(log_dir / "alert_manager.log", encoding='utf-8')
        file_handler.setFormatter(StructuredFormatter())
        file_handler.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        
        # Log solo para errores
        error_handler = logging.FileHandler(log_dir / "errors.log", encoding='utf-8')
        error_handler.setFormatter(StructuredFormatter())
        error_handler.setLevel(logging.ERROR)
        self.logger.addHandler(error_handler)
        
        # Evitar propagación a root logger
        self.logger.propagate = False
    
    def info(self, message: str, **extra_fields):
        """Log nivel INFO"""
        self._log(logging.INFO, message, extra_fields)
    
    def warning(self, message: str, **extra_fields):
        """Log nivel WARNING"""
        self._log(logging.WARNING, message, extra_fields)
    
    def error(self, message: str, **extra_fields):
        """Log nivel ERROR"""
        self._log(logging.ERROR, message, extra_fields)
    
    def debug(self, message: str, **extra_fields):
        """Log nivel DEBUG"""
        self._log(logging.DEBUG, message, extra_fields)
    
    def critical(self, message: str, **extra_fields):
        """Log nivel CRITICAL"""
        self._log(logging.CRITICAL, message, extra_fields)
    
    def _log(self, level: int, message: str, extra_fields: Dict[str, Any]):
        """Método interno para logging con campos extra"""
        if extra_fields:
            self.logger.log(level, message, extra={'extra_fields': extra_fields})
        else:
            self.logger.log(level, message)

# Instancia global del logger
logger = AlertManagerLogger("alert_manager")

def log_api_request(method: str, path: str, status_code: int, 
                   duration_ms: float, **extra_fields):
    """
    Log específico para requests de API
    """
    logger.info(
        f"API Request: {method} {path} - {status_code}",
        event_type="api_request",
        method=method,
        path=path,
        status_code=status_code,
        duration_ms=duration_ms,
        **extra_fields
    )

def log_business_operation(operation: str, entity_type: str, 
                          entity_id: Optional[str] = None, **extra_fields):
    """
    Log específico para operaciones de negocio
    """
    logger.info(
        f"Business Operation: {operation} on {entity_type}",
        event_type="business_operation",
        operation=operation,
        entity_type=entity_type,
        entity_id=entity_id,
        **extra_fields
    )

def log_data_source_check(source_name: str, success: bool, 
                         alerts_created: int = 0, **extra_fields):
    """
    Log específico para verificación de fuentes de datos
    """
    status = "success" if success else "failed"
    logger.info(
        f"Data Source Check: {source_name} - {status}",
        event_type="data_source_check",
        source_name=source_name,
        success=success,
        alerts_created=alerts_created,
        **extra_fields
    )

def log_airflow_task(dag_id: str, task_id: str, state: str, **extra_fields):
    """
    Log específico para tareas de Airflow
    """
    logger.info(
        f"Airflow Task: {dag_id}.{task_id} - {state}",
        event_type="airflow_task",
        dag_id=dag_id,
        task_id=task_id,
        state=state,
        **extra_fields
    )

def log_error(error: Exception, context: str, **extra_fields):
    """
    Log específico para errores
    """
    logger.error(
        f"Error in {context}: {str(error)}",
        event_type="error",
        error_type=type(error).__name__,
        error_message=str(error),
        context=context,
        **extra_fields,
        exc_info=True
    )

def log_security_event(event_type: str, description: str, **extra_fields):
    """
    Log específico para eventos de seguridad
    """
    logger.warning(
        f"Security Event: {event_type} - {description}",
        event_type="security",
        security_event_type=event_type,
        description=description,
        **extra_fields
    )

def set_request_context(request_id: str, user_id: Optional[str] = None):
    """
    Establece el contexto de la request actual
    """
    request_id_var.set(request_id)
    if user_id:
        user_id_var.set(user_id)

def clear_request_context():
    """
    Limpia el contexto de la request
    """
    request_id_var.set(None)
    user_id_var.set(None)