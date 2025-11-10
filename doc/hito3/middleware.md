# Middleware de FastAPI con librerías estándar

Este módulo implementa varios middleware para FastAPI usando únicamente librerías estándar de Python, sin dependencias externas como Loguru.

## Componentes principales

### Simple rate limiter
Implementa limitación de velocidad en memoria para controlar el número de requests por cliente:

- **Ventana deslizante**: usa `deque` para mantener timestamps de requests
- **Limpieza automática**: elimina requests antiguas fuera de la ventana de tiempo
- **Por IP**: identifica clientes por dirección IP (con soporte para proxies)

### Request logging middleware
Middleware de logging que captura información detallada de cada request:

- **ID único**: genera UUID para cada request usando `uuid4()`
- **Contexto de logging**: mantiene el request ID en el contexto del logger
- **Métricas de tiempo**: mide duración usando `time.perf_counter()`
- **Información del cliente**: extrae IP real considerando headers de proxy
- **Manejo de errores**: diferencia entre errores de negocio y errores internos

### Rate limit middleware
Aplica limitación de velocidad a las requests:

- **Endpoints excluidos**: health checks y documentación bypass el rate limiting
- **Headers informativos**: incluye límites y tiempo de reset en las respuestas
- **Respuesta 429**: retorna Too Many Requests cuando se excede el límite

### Security headers middleware
Añade headers de seguridad modernos a todas las respuestas:

- **XSS protection**: previene ataques de cross-site scripting
- **Content sniffing**: evita que el navegador adivine tipos MIME
- **Frame options**: protege contra clickjacking
- **CSP**: política de seguridad de contenido básica
- **HSTS**: solo en HTTPS, fuerza conexiones seguras

### Health check middleware
Proporciona endpoints de health check optimizados:

- **Bypass completo**: no pasa por otros middleware para máximo rendimiento
- **Respuesta inmediata**: retorna estado sin procesar la aplicación
- **Cache control**: evita cacheo de respuestas de health

## Características técnicas

### Gestión de IP del cliente
```python
def get_client_ip(request: Request) -> str:
```
Extrae la IP real considerando proxies y load balancers mediante headers `X-Forwarded-For` y `X-Real-IP`.

### Rate limiter en memoria
La clase `SimpleRateLimiter` usa un `defaultdict` con `deque` para mantener eficientemente las requests por cliente, limpiando automáticamente las antiguas.

### Contexto de logging
Utiliza el sistema de logging estándar con contexto personalizado para mantener el request ID a través de todo el procesamiento de la request.

### Manejo de excepciones
Diferencia entre:
- **AlertManagerException**: errores de lógica de negocio (400)
- **Exception genérica**: errores internos del servidor (500)

## Configuración
- **Rate limit**: 100 requests por 60 segundos por defecto
- **Endpoints excluidos**: `/health`, `/ping`, `/docs`, `/redoc`, `/openapi.json`
- **Headers de seguridad**: configuración moderna pero compatible.