"""
Sistema de logging nativo con logger estándar de Python
"""
import json
import logging
import logging.handlers
import sys
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar
from pathlib import Path
import os
import threading
import queue
import time

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

class SeqCLEFFormatter(logging.Formatter):
    """Formatter CLEF para Seq"""
    
    def format(self, record):
        # Convertir timestamp a formato UTC ISO 8601 con Z
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        
        # Mapear niveles de Python a Seq
        level_map = {
            'DEBUG': 'Debug',
            'INFO': 'Information',
            'WARNING': 'Warning',
            'ERROR': 'Error',
            'CRITICAL': 'Fatal'
        }
        
        clef_entry = {
            "@t": timestamp,
            "@l": level_map.get(record.levelname, record.levelname),
            "@mt": record.getMessage(),
            "Logger": record.name,
            "Module": record.module,
            "Function": record.funcName,
            "Line": record.lineno,
            "Thread": record.thread
        }
        
        # Añadir contexto
        if hasattr(record, 'request_id') and record.request_id:
            clef_entry["RequestId"] = record.request_id
        
        if hasattr(record, 'user_id') and record.user_id:
            clef_entry["UserId"] = record.user_id
        
        # Añadir campos extra
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info', 
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated', 
                          'thread', 'threadName', 'processName', 'process', 'message',
                          'request_id', 'user_id']:
                # Capitalizar primera letra para seguir convenciones de Seq
                seq_key = key.replace('_', '').title() if '_' in key else key.capitalize()
                clef_entry[seq_key] = value
        
        # Añadir excepción si existe
        if record.exc_info:
            clef_entry["Exception"] = self.formatException(record.exc_info)
        
        return json.dumps(clef_entry, default=str, separators=(',', ':'))

class SeqHTTPHandler(logging.Handler):
    """Handler que envía logs a Seq via HTTP"""
    
    def __init__(self, seq_url: str, batch_size: int = 50, flush_interval: float = 5.0):
        super().__init__()
        self.seq_url = seq_url.rstrip('/')
        self.api_url = f"{self.seq_url}/api/events/raw"
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.buffer = queue.Queue()
        self.shutdown_event = threading.Event()
        
        # Iniciar hilo de procesamiento
        self.worker_thread = threading.Thread(target=self._process_logs, daemon=True)
        self.worker_thread.start()
    
    def emit(self, record):
        """Envía un log record al buffer"""
        if not self.shutdown_event.is_set():
            try:
                formatted = self.format(record)
                self.buffer.put(formatted, block=False)
            except queue.Full:
                # Si el buffer está lleno, descarta el log más antiguo
                try:
                    self.buffer.get_nowait()
                    self.buffer.put(formatted, block=False)
                except queue.Empty:
                    pass
            except Exception:
                # No imprimir errores para evitar loops infinitos
                pass
    
    def _process_logs(self):
        """Procesa logs en lotes en un hilo separado"""
        batch = []
        last_flush = time.time()
        
        while not self.shutdown_event.is_set():
            try:
                # Intentar obtener un log del buffer (con timeout)
                try:
                    log_entry = self.buffer.get(timeout=1.0)
                    batch.append(log_entry)
                except queue.Empty:
                    pass
                
                current_time = time.time()
                should_flush = (
                    len(batch) >= self.batch_size or 
                    (batch and (current_time - last_flush) >= self.flush_interval)
                )
                
                if should_flush and batch:
                    self._send_batch(batch)
                    batch.clear()
                    last_flush = current_time
                    
            except Exception:
                # En caso de error, limpiar el lote y continuar
                batch.clear()
                time.sleep(1)
        
        # Enviar logs restantes al cerrar
        if batch:
            self._send_batch(batch)
    
    def _send_batch(self, batch):
        """Envía un lote de logs a Seq"""
        try:
            # Unir logs con newlines para formato CLEF
            payload = '\n'.join(batch).encode('utf-8')
            
            req = urllib.request.Request(
                self.api_url,
                data=payload,
                headers={
                    'Content-Type': 'application/vnd.serilog.clef',
                    'Content-Length': str(len(payload))
                }
            )
            
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status not in [200, 201, 202]:
                    # Error pero no imprimir para evitar loops
                    pass
                    
        except Exception:
            # Error de red o Seq no disponible - fallar silenciosamente
            # Los logs se seguirán escribiendo a archivos
            pass
    
    def close(self):
        """Cierra el handler y espera a que se procesen los logs restantes"""
        self.shutdown_event.set()
        if self.worker_thread.is_alive():
            self.worker_thread.join(timeout=2.0)
        super().close()

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
    
    # 🔥 Handler para Seq (si está configurado)
    seq_url = os.getenv("SEQ_URL")
    if seq_url:
        try:
            seq_handler = SeqHTTPHandler(seq_url)
            seq_handler.setLevel(logging.INFO)
            seq_handler.setFormatter(SeqCLEFFormatter())
            seq_handler.addFilter(context_filter)
            root_logger.addHandler(seq_handler)
            
            # Log de confirmación (se enviará a todos los handlers incluyendo Seq)
            logger = logging.getLogger("alert_manager.setup")
            logger.info("✅ Seq logging configurado correctamente", extra={
                "seq_url": seq_url,
                "event_type": "logging_setup"
            })
            
        except Exception as e:
            # Si falla Seq, continuar con logging local
            logger = logging.getLogger("alert_manager.setup")
            logger.warning(f"⚠️ No se pudo configurar Seq logging: {e}", extra={
                "seq_url": seq_url,
                "event_type": "logging_setup_warning"
            })

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