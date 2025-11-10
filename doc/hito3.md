Alert Manager - Hito 3: Diseño de microservicios

## Descripción del proyecto
**Alert Manager** es un sistema moderno de gestión de alertas meteorológicas y de emergencia. En este hito se consolida como **microservicio** con una arquitectura por capas bien definida, infraestructura reproducible en contenedores y un sistema de **logging centralizado estructurado** que permite auditoría, trazabilidad y observabilidad.

Además, considero que el README del hito anterior quedó demasiado largo. En este se va a responder directamente a lo que se pide y se enlazará con otros .md para más información en caso de que se quiera profundizar.

## Arquitectura por capas
Este ha sido uno de los principales añadidos a lo que había del Hito anterior.
La lógica de negocio queda desacoplada completamente de la API y del acceso a datos. El flujo lógico es:

```
API Layer (FastAPI Routers)
    ↓
Service Layer (Business Logic / Domain Services)
    ↓
Repository Layer (Data Access Abstraction)
    ↓
Database Layer (SQLAlchemy Models / Persistence)
```

### Capas y responsabilidades
| Capa | Directorio / Archivo | Responsabilidad | Ejemplo |
|------|----------------------|-----------------|---------|
| API | `src/app/routers/alerts.py` | Exponer endpoints REST, validación de entrada/salida (Pydantic) | `GET /alerts/` |
| Servicios | `src/domain/services.py` | Reglas de negocio, orquestación de casos de uso | Expiración de alertas |
| Repositories (interface) | `src/domain/repositories.py` | Contratos de acceso a datos (pueden tener múltiples implementaciones) | `AlertRepository` |
| Repositories (infra) | `src/infrastructure/repositories.py` | Implementación concreta con SQLAlchemy | `SQLAlchemyAlertRepository` |
| Modelos | `src/app/models.py` | Modelos ORM persistentes | `AlertModel` |
| Esquemas | `src/app/schemas.py` | Esquemas Pydantic para E/S de la API | `AlertCreate`, `AlertRead` |
| Excepciones | `src/domain/exceptions.py` | Errores de dominio tipados | `AlertNotFoundError` |
| Logging / Middleware | `src/infrastructure/logging.py` / `src/infrastructure/middleware.py` | Observabilidad, seguridad, rate limiting | `RequestLoggingMiddleware` |

Las caracterísitcas de esta arquitectura son:
- Separación de responsabilidades.
- Single Source of Truth para acceso a datos a través de repositorios inyectados.
- DTOs (Pydantic) independientes de modelos ORM para evitar fugas de persistencia.
- Excepciones de dominio manejadas de forma consistente para respuestas HTTP predecibles.

A continuación, se irá detallando lo hecho para las distintas categorías que se califican:

## 1. Justificación técnica del framework (2 puntos)
### FastAPI
FastAPI se eligió como framework principal por su **rendimiento excepcional** basado en Starlette y su capacidad para generar **documentación automática** de la API. Su sistema de validación con Pydantic garantiza tipos seguros en toda la aplicación, mientras que el soporte nativo para programación asíncrona lo hace ideal para un sistema de alertas que debe manejar múltiples operaciones de I/O concurrentes. Además, su arquitectura facilita la implementación de middlewares personalizados para logging y seguridad.

**Beneficios específicos en Alert Manager:** FastAPI facilita un diseño claro de endpoints de alertas y salud con documentación automática, permite el manejo estructurado de errores de dominio transformándolos en respuestas HTTP consistentes para los clientes, y ofrece extensibilidad futura hacia tecnologías como websockets o streaming en caso de requerirse capacidades de tiempo real para el sistema de alertas.

### SQLAlchemy + PostgreSQL
Se eligió **SQLAlchemy** como ORM por su madurez en el manejo de transacciones, sesiones y relaciones complejas, permitiendo implementar patrones como Repository y Unit of Work que desacoplan completamente la persistencia del dominio. PostgreSQL proporciona robustez empresarial con soporte avanzado para consultas complejas y escalabilidad, mientras que la combinación está preparada para migraciones automatizadas con Alembic en el futuro. Esta elección garantiza flexibilidad para cambiar de motor de base de datos sin impactar la lógica de negocio, manteniendo la arquitectura por capas limpia y extensible.

## 2. Diseño de la API y arquitectura por capas (4 puntos)
### Rutas principales
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/alerts/` | Listar alertas (paginable / filtrable) |
| POST | `/alerts/` | Crear alerta |
| GET | `/alerts/{id}` | Obtener alerta por ID |
| PUT | `/alerts/{id}` | Actualizar alerta |
| DELETE | `/alerts/{id}` | Eliminar alerta |
| GET | `/alerts/health` | Health específico de alertas |
| GET | `/health` | Health global del servicio |
| GET | `/ping` | Comprobación simple |
| GET | `/test-logs` | Genera logs de prueba en distintos niveles |


Entre otras llamadas para depuración.

### Dependencias
Los routers inyectan servicios mediante funciones proveedoras (`Depends(get_alert_service)`), que a su vez obtienen repositorios concretos. Esto permite intercambiar implementaciones (p.ej. repositorio en memoria para tests) sin modificar la API ni la lógica de negocio.

### Manejo de excepciones
Las excepciones de dominio (`AlertNotFoundError`, `DuplicateAlertError`, etc.) se capturan y transforman en respuestas JSON con códigos adecuados, favoreciendo un contrato estable para clientes.

### Validación y esquemas
Los modelos Pydantic separan claramente:
- `AlertCreate` / `AlertUpdate`: entrada de la API
- `AlertRead`: salida hacia el cliente
Evitando exponer internamente detalles del ORM.

Para más información sobre la infraestructura por capas, consulte:
- [Arquitectura de la aplicación](./hito3/app.md) - Modelos, esquemas y routers
- [Dominio del negocio](./hito3/domain.md) - Servicios, repositorios y excepciones
- [Infraestructura](./hito3/infrastructure.md) - Implementaciones concretas y persistencia

## 3. Sistema de logs centralizado (2 puntos)
### Stack de Observabilidad
- **Python logging**: logger raíz configurado con handlers múltiples (consola, archivos rotativos).
- **Seq (datalust/seq)**: plataforma centralizada para ingestión y consulta estructurada de logs (formato CLEF).
- **Dozzle**: visualizador en tiempo real de logs de contenedores Docker.
- **File Browser**: Acceso directo a archivos históricos (`logs/alert_manager.json`, `logs/errors.json`).

### Características Implementadas

El sistema cuenta con logging estructurado que utiliza identificadores únicos de request y usuario mediante context variables, permitiendo un seguimiento detallado de cada operación. Para garantizar la resiliencia, se implementaron handlers rotativos que proporcionan respaldo local en caso de que Seq no esté disponible, asegurando que no se pierdan logs críticos durante interrupciones del servicio.

El envío de logs hacia Seq se realiza de forma asíncrona y por lotes para minimizar el impacto en la latencia de las peticiones, manteniendo la responsividad de la API. Además, se desarrollaron múltiples middlewares especializados: `RequestLoggingMiddleware` que traza cada petición incluyendo su duración, `RateLimitMiddleware` para control de tráfico, `SecurityHeadersMiddleware` para reforzar la seguridad, y `HealthCheckMiddleware` para monitoreo del estado del sistema.

Para más información sobre la implementación detallada, consulte:
- [Sistema de Logging](./hito3/logger.md) - Configuración y manejo de logs estructurados
- [Middleware](./hito3/middleware.md) - Componentes de infraestructura y seguridad



### Beneficios

Esta implementación proporciona una auditoría completa de todas las actividades realizadas a través de la API, facilitando el seguimiento y análisis de operaciones. La correlación de eventos mediante request_id permite vincular errores y eventos relacionados, simplificando significativamente el proceso de diagnóstico y depuración.

Finalmente, esta infraestructura de logging establece una base sólida para implementar métricas futuras, incluyendo análisis de duración de operaciones, volumen de alertas procesadas y tasas de error, proporcionando insights valiosos para la optimización y monitoreo del sistema.

## Creación automática de fuentes de datos

### Airflow y procesos automatizados

Se ha incorporado infraestructura lista para orquestar la ingestión y validación de fuentes de datos de manera automatizada. Los DAGs ubicados en los directorios `docker/dags/` y `src/dags/` permiten la lectura periódica de archivos externos como `points.json` y la detección automática de cambios en estas fuentes.

Esta arquitectura permite extender las tareas para incluir procesos de normalización y enriquecimiento de datos antes de persistir las alertas en el sistema. La implementación mantiene una separación clara entre la lógica de extracción de datos y la lógica de negocio del dominio, garantizando que cada responsabilidad esté claramente definida.

### Funcionalidades planeadas

El sistema está preparado para soportar auto-ingesta de archivos en formatos CSV y JSON, con capacidades de validación de integridad y detección de duplicados. Se ha establecido la base para el registro de metadatos de fuentes, incluyendo información como nombre de la fuente, última ejecución y estado actual del proceso.

Adicionalmente, se ha implementado un manejo robusto de errores que permite gestionar situaciones donde las fuentes de datos no están disponibles, asegurando que el sistema mantenga su estabilidad y pueda recuperarse automáticamente cuando las fuentes vuelvan a estar accesibles.

## Infraestructura de microservicios

### Arquitectura distribuida

Alert Manager está diseñado como un ecosistema de microservicios especializados que trabajan en conjunto para proporcionar una solución completa de gestión de alertas. Aunque el servicio principal (`web`) expone la API REST con FastAPI, requiere de servicios complementarios para ofrecer funcionalidades completas de producción.

### Servicios en `docker-compose.yml`
| Servicio | Rol | Puerto Host |
|----------|-----|-------------|
| `web` | API FastAPI principal | 8000 |
| `db` | PostgreSQL persistencia | 5432 |
| `seq` | Plataforma de logs centralizados | 5341 (UI) |
| `airflow-webserver` | UI de orquestación | 8080 |
| `airflow-scheduler` | Planificación de DAGs | Interno |
| `dozzle` | Visualizador de logs Docker | 8888 |
| `filebrowser` | Exploración de archivos de logs | 8081 |
| `log-tester` | Generador de logs sintéticos de verificación | (interno) |

### Características de la infraestructura

La infraestructura implementada incorpora health checks en servicios críticos para garantizar la disponibilidad y correcto funcionamiento del sistema, establece dependencias explícitas donde el servicio web espera que tanto la base de datos como Seq estén operativos antes de iniciarse, utiliza volúmenes persistentes (pgdata, seq-data) para asegurar la durabilidad de los datos entre reinicios de contenedores, y está diseñada con una arquitectura extensible que facilita la adición futura de microservicios adicionales como sistemas de notificaciones o módulos de autenticación sin requerir cambios significativos en la estructura existente.

## 4. Testing Exhaustivo (2 puntos)

El proyecto incluye una suite de testing exhaustiva que cubre todas las capas de la arquitectura, desde endpoints hasta infraestructura. A continuación se describe cada archivo de test y su propósito:

| Archivo | Objetivo |
|---------|----------|
| `tests/test_endpoints.py` | Endpoints principales de alertas |
| `tests/test_crud.py` | Operaciones CRUD y repositorios |
| `tests/test_logging.py` | Funciones de logging de negocio |
| `tests/test_middleware.py` | Comportamiento de middlewares |
| `tests/test_container.py` | Verificación de servicios externos |
| `tests/test_dags.py` | Validación de DAGs de ingestión |

Para información detallada sobre cada archivo de test, consulte la documentación específica:
- [Test de endpoints](./hito3/test_endpoints_detail.md) - Pruebas completas de la API REST
- [Test de CRUD](./hito3/test_crud_detail.md) - Operaciones de base de datos y repositorios
- [Test de logging](./hito3/test_logging_detail.md) - Sistema de logs centralizado
- [Test de middleware](./hito3/test_middleware_detail.md) - Componentes de infraestructura
- [Test de contenedores](./hito3/test_container_detail.md) - Servicios dockerizados
- [Test de DAGs](./hito3/test_dags_detail.md) - Workflows de Airflow



## Ejecución y puesta en marcha
Todos los tests implementados en la suite han sido diseñados para ejecutarse **sin necesidad de desplegar el ecosistema Docker completo**, utilizando bases de datos en memoria y mocks de servicios externos cuando es necesario. Esta estrategia permite una ejecución rápida y confiable de las pruebas en entornos de desarrollo local y pipelines de CI/CD, reduciendo la complejidad y dependencias externas.

Para verificación manual y testing de integración completo, se proporciona toda la información necesaria para **probar el sistema en local** mediante `poetry install` para dependencias Python y `docker-compose up` para levantar el ecosistema completo de servicios. Esta aproximación ofrece flexibilidad durante el desarrollo, permitiendo que el próximo hito determine si el despliegue final se realizará en **Docker** o se migrará hacia **Kubernetes**, sin impactar la arquitectura actual del sistema.

La ausencia de un Makefile específico para GitHub Actions es deliberada, ya que las tareas de construcción y despliegue se simplifican a dos comandos esenciales: `poetry install` para preparar el entorno Python y `docker-compose up` para levantar toda la infraestructura de microservicios, manteniendo la simplicidad operacional y facilitando la adopción por parte de nuevos desarrolladores en el proyecto.
### Levantar infraestructura (desarrollo)
```bash
docker-compose -f docker/docker-compose.yml up -d --build
```

### Verificación inicial
```bash
curl http://localhost:8000/health
curl http://localhost:8000/alerts/health
curl http://localhost:8000/test-logs
```

### Acceso a servicios
- Health Alerts: http://localhost:8000/alerts/health
- Seq Logs: http://localhost:5341
- Dozzle: http://localhost:8888
- File Browser: http://localhost:8081
- Airflow: http://localhost:8080 (admin / admin)

### Ejecutar Tests
```bash
# Instalar dependencias del proyecto
poetry install

# Ejecutar todos los tests
poetry run pytest -v

# Ejecutar test específico con salida detallada
poetry run pytest tests/test_container.py::test_03_seq_logging_platform -v -s

# Ejecutar tests con cobertura
poetry run pytest --cov=src --cov-report=html -v
```

## Lógica de negocio implementada
### Funcionalidades core
- Gestión completa de alertas (CRUD + validaciones)
- Paginación y filtrado flexible (parámetros query)
- Mecanismo de expiración y endpoints de verificación
- Base para ingestión automática vía Airflow
- Logging estructurado para auditoría (request → respuesta)

### Auditoría y observabilidad
- Duración de peticiones (middleware)
- Nivel de severidad en logs (INFO / WARNING / ERROR)
- Contexto enriquecido: módulo, función, línea

## Tecnologías y herramientas
| Capa | Tecnología | Justificación |
|------|-----------|---------------|
| API | FastAPI | Performance, tipado, docs auto |
| Dominio | Python puro + Pydantic | Claridad y validación de datos |
| Persistencia | PostgreSQL + SQLAlchemy | Robustez y extensibilidad |
| Logging | Seq + Python logging | Logs estructurados centralizados |
| Orquestación | Airflow | Workflows y ingestión periódica |
| Contenedores | Docker Compose | Aislamiento, reproducibilidad |
| Testing | Pytest | Simplicidad, fixtures, async |
| Documentación | OpenAPI / Swagger | Generación automática |

## Próximos pasos / mejoras futuras
- **Autenticación con Firebase**: integrar Firebase Authentication para gestión de usuarios y tokens JWT, proporcionando autenticación segura y escalable con soporte para múltiples proveedores (Google, email/password, etc.).
- **Métricas y observabilidad**: implementar métricas con Prometheus y dashboards en Grafana para monitoreo de rendimiento, disponibilidad y uso del sistema.
- **Migraciones automatizadas**: configurar Alembic para migraciones de base de datos automatizadas en pipelines de CI/CD, garantizando consistencia entre entornos.
- **Sistema de notificaciones**: desarrollar módulo de notificaciones con soporte para correo electrónico y webhooks, permitiendo alertas automáticas para eventos críticos del sistema.
- **Rate limiting avanzado**: expandir el middleware de rate limiting con políticas diferenciadas por usuario autenticado y endpoints específicos.
- **Cache distribuido**: integrar Redis para cachear consultas frecuentes y mejorar la performance en operaciones de lectura.

## Ejemplos y demostraciones:
Los resultados completos de testing pueden consultarse en:
🔗 **[GitHub Actions - Latest Test Run](https://github.com/davidmunozsanchez/alert_manager/actions)**


Además, para los servicios nuevos añadidos a docker-compose file, se usan credenciales por defecto o directamente se han desactivado, vayamos uno por uno:




