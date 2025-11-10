# Detalle de Tests del Sistema de Logging

## TestJSONFormatter

### test_json_formatter_basic()
- **propósito**: verifica que el formateador JSON convierte correctamente un LogRecord básico a formato JSON válido
- **funcionalidad**: crea un registro de log simple y verifica que los campos básicos (level, message, logger, line, timestamp) se formateen correctamente

### test_json_formatter_with_extra_fields()
- **propósito**: prueba que el formateador incluye campos adicionales personalizados en la salida JSON
- **funcionalidad**: agrega campos extra al LogRecord y verifica que aparezcan en el JSON formateado

### test_json_formatter_with_exception()
- **propósito**: valida que las excepciones se formatean correctamente en el JSON
- **funcionalidad**: genera una excepción, crea un LogRecord con exc_info y verifica que la información de la excepción esté presente

## TestContextFilter

### test_context_filter_adds_fields()
- **propósito**: confirma que el filtro de contexto agrega correctamente los campos de request_id y user_id a los registros de log
- **funcionalidad**: establece contexto, aplica el filtro y verifica que los campos se agreguen al LogRecord

## TestLoggerCreation

### test_get_logger_creates_logger()
- **propósito**: verifica que get_logger crea correctamente un logger con el nombre especificado
- **funcionalidad**: crea un logger y verifica su nombre y que tenga handlers configurados

### test_get_logger_caches_loggers()
- **propósito**: confirma que los loggers se cachean y reutilizan para el mismo nombre
- **funcionalidad**: crea el mismo logger dos veces y verifica que sea la misma instancia

### test_logger_can_log_json()
- **propósito**: prueba que el logger puede generar salida JSON completa con contexto
- **funcionalidad**: configura un logger con JSONFormatter y ContextFilter, registra un mensaje y verifica el JSON generado

## TestBusinessLogging

### test_log_business_operation()
- **propósito**: verifica que las operaciones de negocio se registren con el formato y campos correctos
- **funcionalidad**: llama a log_business_operation y verifica que se registre con los campos esperados

### test_log_error()
- **propósito**: confirma que los errores se registren correctamente con información de contexto y excepción
- **funcionalidad**: registra un error y verifica que incluya tipo de error, contexto y campos adicionales

### test_log_data_source_check()
- **propósito**: valida que las verificaciones de fuentes de datos se registren con métricas apropiadas
- **funcionalidad**: registra una verificación de fuente de datos y confirma que incluya success, alerts_created y execution_time

## TestLoggingIntegration

### test_full_logging_pipeline()
- **propósito**: prueba el pipeline completo de logging desde la creación hasta la escritura en archivo
- **funcionalidad**: configura un logger completo, registra diferentes tipos de mensajes y verifica la salida JSON en archivo

### test_context_variables_isolation()
- **propósito**: confirma que las variables de contexto están correctamente aisladas entre threads
- **funcionalidad**: ejecuta logging en múltiples threads con diferentes contextos y verifica que no haya interferencia

### test_logging_performance()
- **propósito**: mide el rendimiento del sistema de logging para garantizar velocidad adecuada
- **funcionalidad**: ejecuta 1000 operaciones de logging, mide el tiempo y verifica que cumpla con umbrales de rendimiento (>200 logs/seg, <5 segundos total)

