# Tests detallados de endpoints sin dependencias externas

## Descripción general

Este archivo contiene tests modernizados para verificar todos los endpoints de la API del Alert Manager sin necesidad de dependencias externas. Utiliza un sistema de mocking completo que simula las respuestas de FastAPI.

## Estructura de tests

### TestHealthEndpoints: tests para endpoints de salud y debug

- **test_ping_endpoint**: verifica que el endpoint `/ping` responda correctamente con estado healthy
- **test_root_endpoint**: comprueba que el endpoint raíz `/` devuelva información básica del servicio
- **test_health_check**: valida el health check específico en `/alerts/health`
- **test_debug_simple_global**: prueba el endpoint de debug simple global `/debug/simple`
- **test_debug_simple_alerts**: verifica el endpoint de debug simple de alertas `/alerts/debug/simple`

### TestAlertEndpoints: tests para endpoints de alertas

- **test_get_alerts_endpoint_exists**: confirma que el endpoint de listado de alertas existe y responde
- **test_create_alert_endpoint_validation**: valida la creación de alertas con datos correctos
- **test_create_alert_missing_fields**: prueba el manejo de errores cuando faltan campos requeridos
- **test_create_alert_invalid_enum**: verifica la validación de valores enum inválidos
- **test_get_alert_by_id_endpoint**: comprueba la obtención de alertas por ID específico
- **test_get_alert_not_found**: valida el comportamiento cuando una alerta no existe
- **test_alerts_filtering_parameters**: prueba los parámetros de filtrado en el listado

### TestExpirationEndpoints: tests para endpoints de expiración

- **test_expiration_status_endpoint**: verifica el endpoint de estado de expiración
- **test_manual_expiration_check_endpoint**: prueba la verificación manual de expiración

### TestStatisticsEndpoints: tests para endpoints de estadísticas

- **test_statistics_summary_endpoint**: valida el endpoint de resumen de estadísticas

### TestDebugEndpoints: tests para endpoints de debug

- **test_debug_simple_endpoint**: prueba el endpoint debug simple
- **test_debug_count_endpoint**: verifica el contador de debug
- **test_debug_raw_endpoint**: comprueba los datos raw de debug
- **test_debug_types_endpoint**: valida el endpoint de tipos de debug

### TestErrorHandling: tests para manejo de errores

- **test_invalid_endpoint_404**: verifica que endpoints inexistentes devuelvan 404
- **test_method_not_allowed**: prueba métodos HTTP no permitidos
- **test_invalid_json_payload**: valida el manejo de JSON inválido

### TestDocumentationEndpoints: tests para endpoints de documentación

- **test_openapi_docs_available**: confirma que la documentación OpenAPI está disponible
- **test_openapi_json_schema**: verifica el esquema JSON de OpenAPI
- **test_redoc_documentation**: comprueba la disponibilidad de ReDoc

### TestSecurityHeaders: tests para headers de seguridad

- **test_security_headers_present**: valida la presencia de headers de seguridad

### TestBasicConnectivity: tests básicos de conectividad

- **test_server_responds**: test básico de respuesta del servidor
- **test_client_type**: verifica el tipo de cliente utilizado
- **test_verify_mock_endpoints**: confirma que todos los endpoints mock funcionan

### TestValidationScenarios: tests específicos de validación

- **test_create_alert_all_valid_levels**: prueba todos los niveles válidos de alertas
- **test_create_alert_all_valid_types**: valida todos los tipos válidos de alertas

## Características del sistema mock

El sistema utiliza un **MockClient** completamente independiente que simula:

- Respuestas HTTP realistas para cada endpoint
- Validación de datos de entrada
- Manejo de errores apropiado
- Estados de respuesta correctos
- Estructuras de datos consistentes con la API real

## Ejecución

Los tests se pueden ejecutar directamente con pytest o mediante el script principal incluido.