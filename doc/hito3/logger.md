# Sistema de logging nativo

Este módulo proporciona un sistema de logging robusto y centralizado basado en el logger estándar de Python, diseñado para entornos de producción con soporte para múltiples destinos de logs.

## Características principales

- **Logging estructurado**: formateo JSON para logs de producción
- **Integración con Seq**: envío automático de logs a Seq usando formato CLEF
- **Context tracking**: seguimiento de request_id y user_id a través de contextos
- **Múltiples handlers**: consola, archivos rotativos y Seq
- **Batching inteligente**: envío eficiente de logs en lotes a Seq
- **Funciones de conveniencia**: logs especializados para diferentes tipos de eventos

## Componentes del sistema

### Context variables
```python
request_id_var: ContextVar[Optional[str]]
user_id_var: ContextVar[Optional[str]]
```

Permiten rastrear información de contexto a través de todas las operaciones asíncronas.

### Formatters especializados

#### JSONFormatter
Convierte logs a formato JSON estructurado con:
- Timestamp en formato ISO
- Información de contexto (request_id, user_id)
- Metadatos del código (módulo, función, línea)
- Campos personalizados
- Información de excepciones

#### SeqCLEFFormatter
Formatea logs según el estándar CLEF (Compact Log Event Format) para Seq:
- Timestamps UTC con zona horaria
- Mapeo de niveles de Python a Seq
- Convenciones de naming para campos
- Optimización de tamaño

### Handlers

#### SeqHTTPHandler
Handler especializado para envío a Seq con:
- **Batching**: agrupa logs para envío eficiente
- **Buffering**: cola interna para manejo asíncrono
- **Thread seguro**: procesamiento en hilo separado
- **Resilencia**: continúa funcionando si Seq no está disponible
- **Auto-flush**: envío automático por tiempo o tamaño de lote

## Configuración por entornos

### Development
- Logs a consola con formato legible
- Nivel DEBUG activado
- Formato simple con colores

### Production
- Solo logs a archivos y Seq
- Nivel INFO por defecto
- Formato JSON estructurado
- Rotación automática de archivos

## Archivos de log

| Archivo | Propósito | Rotación |
|---------|-----------|----------|
| `logs/alert_manager.json` | Logs generales | 10MB, 5 backups |
| `logs/errors.json` | Solo errores | 5MB, 10 backups |

## Funciones de logging especializadas

### log_api_request()
Registra requests HTTP con métricas de rendimiento:
```python
log_api_request("GET", "/api/alerts", 200, 45.2)
```

### log_business_operation()
Registra operaciones de negocio:
```python
log_business_operation("create", "alert", entity_id="alert_123")
```

### log_data_source_check()
Registra verificaciones de fuentes de datos:
```python
log_data_source_check("database_monitor", True, alerts_created=3)
```

### log_airflow_task()
Registra estados de tareas Airflow:
```python
log_airflow_task("data_pipeline", "extract_data", "success")
```

### log_error()
Registra errores con contexto completo:
```python
log_error(exception, "processing_alert", alert_id="123")
```

### log_security_event()
Registra eventos de seguridad:
```python
log_security_event("failed_login", "Multiple failed attempts", ip="192.168.1.1")
```

## Gestión de contexto

### set_request_context()
Establece contexto para el request actual:
```python
set_request_context("req_123", user_id="user_456")
```

### clear_request_context()
Limpia el contexto al finalizar el request:
```python
clear_request_context()
```

## Variables de entorno

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `ENVIRONMENT` | Entorno de ejecución | `development`, `production` |
| `SEQ_URL` | URL de Seq para logging centralizado | `http://seq.company.com:5341` |

## Uso básico

```python
from logger import get_logger, set_request_context

# Obtener logger
logger = get_logger("mi_modulo")

# Establecer contexto
set_request_context("req_123", "user_456")

# Logging básico
logger.info("Operación completada")

# Logging con campos extra
logger.info("Alert creada", extra={
    "alert_id": "alert_123",
    "priority": "high"
})
```

## Integración con Seq

Cuando `SEQ_URL` está configurado, los logs se envían automáticamente a Seq con:
- **Formato CLEF**: estándar de la industria
- **Envío en lotes**: optimización de red
- **Fallback local**: archivos como respaldo
- **Métricas automáticas**: tracking de rendimiento

El sistema está diseñado para ser resiliente y mantener el funcionamiento normal incluso si Seq no está disponible.