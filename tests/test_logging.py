"""
Tests completos para el sistema de logging
"""
import sys
from pathlib import Path

# Setup path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
import json
import tempfile
import logging
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.infrastructure.logging import (
    get_logger,
    JSONFormatter,
    ContextFilter,
    log_business_operation,
    log_error,
    log_data_source_check,
    set_request_context,
    clear_request_context
)

class TestJSONFormatter:
    """Tests para el formateador JSON"""
    
    def test_json_formatter_basic(self):
        """Test formateo básico JSON"""
        formatter = JSONFormatter()
        
        # Crear record de prueba
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=123,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Formatear
        formatted = formatter.format(record)
        
        # Verificar que es JSON válido
        data = json.loads(formatted)
        
        assert data["level"] == "INFO"
        assert data["message"] == "Test message"
        assert data["logger"] == "test_logger"  # CORREGIDO: "module" -> "logger"
        assert data["line"] == 123
        assert "timestamp" in data

    def test_json_formatter_with_extra_fields(self):
        """Test formateo con campos extra"""
        formatter = JSONFormatter()
        
        record = logging.LogRecord(
            name="test_logger",
            level=logging.WARNING,
            pathname="/test/path.py", 
            lineno=456,
            msg="Warning message",
            args=(),
            exc_info=None
        )
        
        # Agregar campos extra
        record.user_id = "user123"
        record.request_id = "req456"
        record.custom_field = "custom_value"
        
        formatted = formatter.format(record)
        data = json.loads(formatted)
        
        assert data["user_id"] == "user123"
        assert data["request_id"] == "req456"
        assert data["custom_field"] == "custom_value"

    def test_json_formatter_with_exception(self):
        """Test formateo con información de excepción"""
        formatter = JSONFormatter()
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
        
        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="/test/path.py",
            lineno=789,
            msg="Error occurred",
            args=(),
            exc_info=exc_info
        )
        
        formatted = formatter.format(record)
        data = json.loads(formatted)
        
        assert data["level"] == "ERROR"
        assert "exception" in data
        assert "ValueError" in data["exception"]
        assert "Test exception" in data["exception"]

class TestContextFilter:
    """Tests para el filtro de contexto"""
    
    def test_context_filter_adds_fields(self):
        """Test que el filtro agrega campos de contexto"""
        filter_obj = ContextFilter()
        
        # Establecer contexto
        set_request_context("req123", "user456")
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=123,
            msg="Test message", 
            args=(),
            exc_info=None
        )
        
        # Aplicar filtro
        result = filter_obj.filter(record)
        
        assert result is True
        assert hasattr(record, 'request_id')
        assert hasattr(record, 'user_id')
        assert record.request_id == "req123"
        assert record.user_id == "user456"
        
        # Limpiar contexto
        clear_request_context()

class TestLoggerCreation:
    """Tests para creación de loggers"""
    
    def test_get_logger_creates_logger(self):
        """Test que get_logger crea un logger correctamente"""
        logger = get_logger("test_module")
        
        assert logger.name == "test_module"
        
        # Verificar que el logger root tiene handlers
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) > 0

    def test_get_logger_caches_loggers(self):
        """Test que los loggers se cachean correctamente"""
        logger1 = get_logger("cached_module")
        logger2 = get_logger("cached_module")
        
        # Debe ser la misma instancia
        assert logger1 is logger2

    def test_logger_can_log_json(self):
        """Test que el logger puede generar JSON"""
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.log', delete=False) as tmp:
            # Configurar logger con archivo temporal
            logger = get_logger("json_test")
            
            # Crear un handler específico para este test
            file_handler = logging.FileHandler(tmp.name)
            file_handler.setFormatter(JSONFormatter())
            file_handler.addFilter(ContextFilter())
            logger.addHandler(file_handler)
            logger.setLevel(logging.INFO)
            
            # Establecer contexto para el test
            set_request_context("test_req", "test_user")
            
            # Log un mensaje
            logger.info("Test JSON message", extra={
                "action": "test_action"
            })
            
            # Flush and close
            file_handler.flush()
            file_handler.close()
            
            # Limpiar contexto
            clear_request_context()
            
            # Leer y verificar
            with open(tmp.name, 'r') as f:
                line = f.readline().strip()
                data = json.loads(line)
                
                assert data["message"] == "Test JSON message"
                assert data["action"] == "test_action"
                # El contexto debe estar en el log
                assert "request_id" in data or "user_id" in data

class TestBusinessLogging:
    """Tests para funciones de logging de negocio"""
    
    @patch('src.infrastructure.logging.logger')
    def test_log_business_operation(self, mock_logger):
        """Test logging de operaciones de negocio"""
        
        log_business_operation(
            operation="create",
            entity_type="alert",
            entity_id="123",
            title="Test Alert",
            level="warning"
        )
        
        # Verificar que se llamó info
        mock_logger.info.assert_called_once()
        
        # Verificar argumentos del log
        call_args = mock_logger.info.call_args
        assert "create" in call_args[0][0]  # Mensaje contiene 'create'
        assert "alert" in call_args[0][0]   # Mensaje contiene 'alert'
        
        extra_data = call_args[1]["extra"]
        assert extra_data["operation"] == "create"
        assert extra_data["entity_type"] == "alert"
        assert extra_data["entity_id"] == "123"

    @patch('src.infrastructure.logging.logger')
    def test_log_error(self, mock_logger):
        """Test logging de errores"""
        
        test_exception = ValueError("Test error")
        
        log_error(
            test_exception,
            "test_operation",  # CORREGIDO: context como segundo argumento
            user_id="user123"
        )
        
        # Verificar que se llamó error
        mock_logger.error.assert_called_once()
        
        # Verificar argumentos
        call_args = mock_logger.error.call_args
        assert "test_operation" in call_args[0][0]
        
        extra_data = call_args[1]["extra"]
        assert extra_data["context"] == "test_operation"
        assert extra_data["user_id"] == "user123"
        assert extra_data["error_type"] == "ValueError"

    @patch('src.infrastructure.logging.logger')
    def test_log_data_source_check(self, mock_logger):
        """Test logging de verificación de fuentes de datos"""
        
        log_data_source_check(
            source_name="weather_api",
            success=True,
            alerts_created=5,
            execution_time=1.23
        )
        
        # Verificar que se llamó info
        mock_logger.info.assert_called_once()
        
        call_args = mock_logger.info.call_args
        extra_data = call_args[1]["extra"]
        assert extra_data["source_name"] == "weather_api"
        assert extra_data["success"] is True
        assert extra_data["alerts_created"] == 5
        assert extra_data["execution_time"] == 1.23

class TestLoggingIntegration:
    """Tests de integración del sistema de logging"""
    
    def test_full_logging_pipeline(self):
        """Test completo del pipeline de logging"""
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as tmp:
            # Configurar logger completo
            logger = get_logger("integration_test")
            
            # Crear handler específico para el test
            handler = logging.FileHandler(tmp.name)
            handler.setFormatter(JSONFormatter())
            handler.addFilter(ContextFilter())
            
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            
            # Establecer contexto
            set_request_context("req789", "user456")
            
            # Simular operaciones de negocio
            logger.info(
                "Alert created successfully",
                extra={
                    "operation": "create",
                    "entity_type": "alert", 
                    "entity_id": "test123"
                }
            )
            
            logger.warning(
                "Alert about to expire",
                extra={
                    "operation": "expiration_check",
                    "entity_id": "test123",
                    "expires_at": "2025-11-10T10:00:00Z"
                }
            )
            
            logger.error(
                "Database connection failed",
                extra={
                    "operation": "db_connect",
                    "error_type": "ConnectionError",
                    "retry_count": 3
                }
            )
            
            # Cerrar handler
            handler.close()
            
            # Limpiar contexto
            clear_request_context()
            
            # Verificar logs
            with open(tmp.name, 'r') as f:
                lines = f.readlines()
            
            assert len(lines) >= 3  # Al menos 3 logs
            
            # Verificar primer log
            first_log = json.loads(lines[0].strip())
            assert first_log["level"] == "INFO"
            assert "Alert created successfully" in first_log["message"]
            assert first_log["entity_type"] == "alert"
            assert first_log["entity_id"] == "test123"
            
            # Cleanup
            import os
            try:
                os.unlink(tmp.name)
            except FileNotFoundError:
                pass

    def test_context_variables_isolation(self):
        """Test que las context variables están aisladas por thread"""
        
        def test_context_in_thread(request_id, user_id, results):
            set_request_context(request_id, user_id)
            
            # Crear log record y aplicar filtro
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="/test/path.py",
                lineno=123,
                msg="Test message",
                args=(),
                exc_info=None
            )
            
            filter_obj = ContextFilter()
            filter_obj.filter(record)
            
            results.append({
                'request_id': getattr(record, 'request_id', None),
                'user_id': getattr(record, 'user_id', None)
            })
            
            clear_request_context()
        
        import threading
        
        results = []
        
        # Crear threads con contextos diferentes
        thread1 = threading.Thread(
            target=test_context_in_thread,
            args=("req1", "user1", results)
        )
        thread2 = threading.Thread(
            target=test_context_in_thread,
            args=("req2", "user2", results)
        )
        
        thread1.start()
        thread2.start()
        
        thread1.join()
        thread2.join()
        
        # Verificar que cada thread tuvo su contexto
        assert len(results) == 2
        
        # Los resultados pueden estar en cualquier orden
        request_ids = [r['request_id'] for r in results]
        user_ids = [r['user_id'] for r in results]
        
        assert "req1" in request_ids
        assert "req2" in request_ids
        assert "user1" in user_ids
        assert "user2" in user_ids

    def test_logging_performance(self):
        """Test de rendimiento básico del logging"""
        import time
        
        logger = get_logger("performance_test")
        
        # Medir tiempo de 1000 logs
        start_time = time.time()
        
        for i in range(1000):
            logger.info(f"Performance test message {i}", extra={
                "iteration": i,
                "test_type": "performance"
            })
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Debe ser razonablemente rápido (menos de 5 segundos para 1000 logs)
        assert duration < 5.0, f"Logging too slow: {duration:.2f}s for 1000 logs"
        
        # Rate aproximado
        rate = 1000 / duration
        print(f"Logging rate: {rate:.0f} logs/second")
        
        assert rate > 200, f"Logging rate too low: {rate:.0f} logs/second"