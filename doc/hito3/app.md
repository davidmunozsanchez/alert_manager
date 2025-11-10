# Capa de aplicación - Alert Manager

## Visión general

La capa de aplicación constituye el punto de entrada principal del sistema Alert Manager, funcionando como intermediario entre los clientes externos y la lógica de negocio. Su responsabilidad principal es exponer la funcionalidad del sistema a través de una API REST bien estructurada, manejando aspectos como la serialización de datos, validación de entrada y transformación de respuestas HTTP.

## Principios arquitectónicos

El diseño de esta capa se basa en controladores ligeros que delegan la lógica compleja a los servicios de dominio, manteniendo una separación clara de responsabilidades. La transformación de datos entre formatos HTTP y entidades de dominio se maneja de forma transparente, mientras que un sistema robusto de manejo de errores garantiza respuestas consistentes y descriptivas para todos los escenarios posibles.

## Estructura del código

### Configuración principal (main.py)

Este archivo establece la aplicación FastAPI con su configuración completa, incluyendo metadatos de la API, middleware stack en orden específico para optimizar el rendimiento, y eventos de ciclo de vida para inicialización y limpieza de recursos. La configuración varía según el entorno, habilitando herramientas de debugging solo en desarrollo.

### Esquemas de validación (schemas.py)

Define los contratos de entrada y salida de la API usando Pydantic, proporcionando validación automática de datos, transformación de tipos y generación de documentación. Los esquemas incluyen validaciones específicas para campos como coordenadas geográficas, rangos de fechas y patrones de texto, asegurando la integridad de los datos desde el punto de entrada.

### Router de alertas (routers/alerts.py)

Contiene todos los endpoints relacionados con alertas, implementando operaciones CRUD completas junto con funcionalidades especializadas como verificación de salud del sistema, procesamiento de alertas expiradas y generación de estadísticas. Cada endpoint está diseñado para ser stateless y utiliza inyección de dependencias para acceder a los servicios necesarios.

### Sistema de dependencias (dependencies.py)

Gestiona la creación y ciclo de vida de dependencias como sesiones de base de datos y servicios de dominio, facilitando el testing mediante la inyección de mocks y garantizando la limpieza adecuada de recursos al finalizar cada request.

### Modelos de datos (models.py)

Define las estructuras de datos que representan las entidades del sistema en la base de datos usando SQLAlchemy, incluyendo índices estratégicos para optimizar consultas frecuentes y campos flexibles para almacenar metadata adicional.

### Configuración de base de datos (database.py)

Establece la conexión con PostgreSQL y proporciona utilidades para gestionar la disponibilidad de la base de datos, incluyendo mecanismos de reintento con backoff exponencial para garantizar la robustez del sistema durante el arranque y operación normal.

La capa mantiene un enfoque centrado en la experiencia del desarrollador, proporcionando documentación automática, validación exhaustiva y mensajes de error informativos, mientras optimiza el rendimiento a través de middleware especializado y gestión eficiente de conexiones.

