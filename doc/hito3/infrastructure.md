# Capa de infraestructura - Alert Manager

## Visión general

La **capa de infraestructura** es la capa más externa de la arquitectura y se encarga de implementar los detalles técnicos específicos, proporcionando implementaciones concretas de las interfaces definidas en la capa de dominio. Esta capa contiene toda la lógica de persistencia, logging, middleware, y otros servicios técnicos.

## Estructura de la capa

La infraestructura se organiza en varios módulos especializados. El archivo principal de inicialización establece las configuraciones básicas del paquete. El sistema de logging se centraliza en un módulo dedicado que maneja toda la estructuración y envío de logs. Los middlewares se agrupan en su propio módulo para gestionar aspectos transversales. Las implementaciones concretas de repositorios residen en un archivo específico, mientras que los mappers tienen su propio espacio para las transformaciones de datos. Finalmente, las utilidades de testing se mantienen separadas para facilitar las pruebas.

## Componentes principales

### Sistema de logging

El sistema de logging implementa un enfoque estructurado con integración a Seq y soporte para contexto distribuido. Utiliza logging estructurado en formato JSON para análisis automatizado, incorpora filtros de contexto que enriquecen automáticamente los logs con información de request, y maneja múltiples destinos incluyendo Seq para centralización y archivos locales como fallback. El procesamiento asíncrono garantiza alto rendimiento sin bloqueos.

El módulo incluye un filtro de contexto que añade información del request a los logs, un formateador JSON que convierte logs a formato estructurado, y un handler customizado para envío a Seq con capacidad de fallback. Las funciones de negocio permiten registrar operaciones de dominio, errores con contexto enriquecido, y obtener loggers configurados apropiadamente.

### Stack de middleware

El sistema de middleware implementa múltiples capas para aspectos transversales de la aplicación. El middleware de logging de requests captura automáticamente todas las peticiones y respuestas, incluyendo método, URL, headers y timing, generando un identificador único para trazabilidad y registrando métricas de performance de forma estructurada.

El middleware de headers de seguridad aplica automáticamente cabeceras de protección como prevención de sniffing de contenido, protección contra frames maliciosos y protección XSS. El middleware de health checks proporciona respuesta rápida para verificaciones de salud, evitando el procesamiento del stack completo para endpoints de ping. El middleware de rate limiting controla la cantidad de requests por IP, configurado por defecto para permitir cien peticiones por minuto.

### Repositorios

Las implementaciones concretas de repositorio utilizan SQLAlchemy para persistencia en PostgreSQL. El repositorio de alertas maneja transacciones automáticas con rollback, registra operaciones de negocio, aplica filtros complejos y realiza mapeo automático entre entidades de dominio y modelos de base de datos. Proporciona funcionalidad completa para guardar alertas, buscar por identificador, filtrar según criterios específicos y eliminar registros.

El repositorio de fuentes de datos gestiona entidades automáticas con funcionalidad CRUD completa y validaciones específicas del dominio. Ambos repositorios mantienen separación clara entre la lógica de negocio y los detalles de persistencia.

### Mappers

Los transformadores entre entidades de dominio y modelos de base de datos facilitan la conversión bidireccional de datos. El mapper de alertas convierte modelos SQLAlchemy a entidades de dominio y viceversa, además de actualizar modelos existentes con información de dominio. El mapper de fuentes de datos maneja transformaciones similares incluyendo serialización de configuraciones JSON.

## Patrones de diseño implementados

La implementación utiliza el patrón Repository para abstraer la capa de datos y desacoplar el dominio de la infraestructura. El patrón Mapper transforma entre representaciones de datos aislando cambios en esquemas de base de datos. El patrón Middleware maneja aspectos transversales como logging y seguridad, separando concerns ortogonales. La inyección de dependencias invierte las dependencias utilizando el sistema FastAPI Depends.

## Tecnologías utilizadas

La capa utiliza SQLAlchemy como ORM para Python con PostgreSQL como base de datos relacional, preparando el terreno para futuras migraciones con Alembic. Para logging y monitoreo emplea Seq como plataforma centralizada, el sistema nativo de Python logging y formato CLEF para logs estructurados. El framework web se basa en FastAPI con Uvicorn como servidor ASGI y Starlette como base subyacente.

## Configuración y variables de entorno

El sistema requiere configuración de URL de base de datos PostgreSQL, URL del servidor Seq para logging, nivel de log apropiado, definición de entorno de ejecución, y parámetros de rate limiting incluyendo cantidad de requests permitidos y ventana temporal.

## Aspectos de testing

La infraestructura incluye utilidades específicas para testing con fixtures para bases de datos de prueba, mocks de servicios externos y helpers para setup y teardown. Las estrategias incluyen tests de integración con base de datos real, repositorios mock para pruebas unitarias, y tests de contenedor para verificar conectividad.

## Beneficios de esta arquitectura

La separación de concerns mantiene la lógica técnica apartada de la lógica de negocio con responsabilidades claras para cada componente. La testabilidad se facilita mediante implementaciones fácilmente mockeables y tests unitarios sin dependencias externas. La mantenibilidad se logra aislando cambios de base de datos de la lógica de negocio y centralizando logging y middleware.

La extensibilidad permite agregar fácilmente nuevos tipos de repositorio y configurar el stack de middleware según necesidades. La observabilidad se garantiza con logging estructurado para análisis, métricas automáticas de performance y trazabilidad completa de requests.

## Conclusión

La capa de infraestructura del Alert Manager implementa todos los aspectos técnicos necesarios para una aplicación robusta y observable. Su diseño modular y el uso de patrones establecidos facilita el mantenimiento y la evolución del sistema, mientras que la separación clara de responsabilidades permite testing efectivo y desarrollo independiente de cada componente.
