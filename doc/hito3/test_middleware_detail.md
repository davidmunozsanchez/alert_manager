# Tests Exhaustivos del Sistema de Middleware

Este documento describe los tests implementados para validar el funcionamiento completo del sistema de middleware sin dependencias externas.

## Estructura de Tests

### Configuración y Fixtures

**@pytest.fixture mock_request()**: crea un request mock con configuración estándar incluyendo método GET, URL de prueba, headers básicos y dirección IP del cliente.

**@pytest.fixture mock_response()**: genera un response mock con status code 200 y headers vacíos para simular respuestas exitosas.

**@pytest.fixture sample_app()**: proporciona una aplicación FastAPI básica con endpoints de prueba incluyendo rutas normales, de error y de negocio.

### Tests del Rate Limiter Simple

**TestSimpleRateLimiter.test_rate_limiter_creation()**: verifica la creación correcta del rate limiter con parámetros específicos y estado inicial limpio.

**TestSimpleRateLimiter.test_rate_limiter_allows_under_limit()**: confirma que las requests bajo el límite establecido son permitidas y que el contador de requests restantes se actualiza correctamente.

**TestSimpleRateLimiter.test_rate_limiter_blocks_over_limit()**: valida que las requests que exceden el límite son bloqueadas apropiadamente y que el contador llega a cero.

**TestSimpleRateLimiter.test_rate_limiter_time_window_reset()**: prueba que el rate limiter se resetea correctamente después de que expira la ventana de tiempo configurada.

**TestSimpleRateLimiter.test_rate_limiter_different_clients()**: asegura que diferentes clientes tienen límites independientes y no se afectan entre sí.

### Tests de Detección de IP

**TestClientIP.test_get_client_ip_direct()**: verifica la extracción correcta de la IP cuando viene directamente del objeto client del request.

**TestClientIP.test_get_client_ip_x_forwarded_for()**: valida la detección de IP desde el header X-Forwarded-For, tomando la primera IP de la lista.

**TestClientIP.test_get_client_ip_x_real_ip()**: confirma la extracción de IP desde el header X-Real-IP cuando está presente.

**TestClientIP.test_get_client_ip_no_client()**: verifica el manejo apropiado cuando no hay información del cliente disponible, retornando "unknown".

### Tests del Middleware de Logging

**TestRequestLoggingMiddleware.test_logging_middleware_success()**: prueba el logging exitoso de requests normales, verificando que se añaden headers de respuesta y se registra la información.

**TestRequestLoggingMiddleware.test_logging_middleware_business_error()**: valida el manejo de errores de negocio (AlertManagerException) con logging apropiado y respuesta JSON estructurada.

**TestRequestLoggingMiddleware.test_logging_middleware_unexpected_error()**: confirma el manejo de errores inesperados con logging detallado y respuesta de error 500.

### Tests del Middleware de Rate Limiting

**TestRateLimitMiddleware.test_rate_limit_middleware_under_limit()**: verifica que requests bajo el límite pasan correctamente y reciben headers informativos de rate limit.

**TestRateLimitMiddleware.test_rate_limit_middleware_over_limit()**: valida que requests sobre el límite son rechazadas con status 429 y headers apropiados.

**TestRateLimitMiddleware.test_rate_limit_middleware_excludes_health_endpoints()**: confirma que los endpoints de health bypass el rate limiting incluso con límites muy restrictivos.

### Tests del Middleware de Seguridad

**TestSecurityHeadersMiddleware.test_security_headers_http()**: verifica que todos los headers de seguridad requeridos se añaden en conexiones HTTP, excluyendo HSTS.

**TestSecurityHeadersMiddleware.test_security_headers_https()**: confirma que en conexiones HTTPS se incluye el header HSTS con configuración apropiada de max-age.

### Tests del Middleware de Health Check

**TestHealthCheckMiddleware.test_health_check_middleware_health_endpoint()**: valida que el endpoint /health responde directamente sin pasar por el resto de la aplicación.

**TestHealthCheckMiddleware.test_health_check_middleware_ping_endpoint()**: confirma que el endpoint /ping también bypassa el pipeline normal de procesamiento.

**TestHealthCheckMiddleware.test_health_check_middleware_other_endpoint()**: verifica que otros endpoints pasan normalmente a través del middleware sin interferencias.

### Tests de Integración

**TestMiddlewareIntegration.test_middleware_stack_simulation()**: simula un stack completo de middleware verificando la creación e interacción correcta entre componentes.

**TestMiddlewareIntegration.test_health_check_priority()**: confirma que el middleware de health check tiene la prioridad correcta en el pipeline.

### Tests de Performance

**TestMiddlewarePerformance.test_rate_limiter_performance()**: evalúa la performance del rate limiter procesando múltiples requests rápidamente.

**TestMiddlewarePerformance.test_middleware_memory_usage()**: verifica que los middleware no acumulan memoria excesiva durante operaciones repetitivas.

### Tests de Casos Edge

**TestMiddlewareEdgeCases.test_rate_limiter_edge_cases()**: prueba el manejo de casos extremos como clientes con nombres vacíos, muy largos o con caracteres especiales.

**TestMiddlewareEdgeCases.test_ip_detection_edge_cases()**: valida la detección de IP en situaciones límite como headers faltantes, vacíos o mal formateados.

### Tests de Debugging

**TestMiddlewareDebugging.test_rate_limiter_state_inspection()**: permite inspeccionar el estado interno del rate limiter para debugging y monitoreo.

**TestMiddlewareDebugging.test_middleware_configuration_validation()**: valida diferentes configuraciones de middleware desde normales hasta casos extremos.
