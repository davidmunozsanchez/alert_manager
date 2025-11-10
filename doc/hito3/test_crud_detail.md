
## Tests de operaciones CRUD (`TestAlertCRUD`)

- **Propósito**: verifica la creación de alertas a través del servicio de dominio
- **Funcionalidad**: 
    - Crea una alerta usando `AlertService.create_alert()`
    - Valida que se genere un ID automáticamente
    - Verifica que los valores se mapeen correctamente a los enums de dominio
    - Confirma que el estado inicial sea `ACTIVE`

### `test_create_alert_via_repository`
- **Propósito**: prueba la creación directa a través del repositorio
- **Funcionalidad**:
    - Crea una entidad `Alert` de dominio manualmente
    - La persiste directamente usando `alert_repository.save()`
    - Verifica que se asigne un ID y se mantengan los datos

### `test_find_alert_by_id`
- **Propósito**: valida la búsqueda de alertas por identificador único
- **Funcionalidad**:
    - Crea una alerta a través del servicio
    - La busca usando `find_by_id()` del repositorio
    - Verifica que se recupere la alerta correcta con todos sus datos

### `test_find_all_alerts`
- **Propósito**: prueba la recuperación de todas las alertas
- **Funcionalidad**:
    - Crea múltiples alertas con títulos diferentes
    - Usa `find_all()` para obtener todas las alertas
    - Verifica que se retornen al menos las alertas creadas

### `test_alert_mapper_bidirectional`
- **Propósito**: valida la conversión entre entidades de dominio y modelos de BD
- **Funcionalidad**:
    - Crea una entidad de dominio `Alert`
    - La convierte a modelo de BD usando `AlertMapper.to_model()`
    - La convierte de vuelta a dominio usando `AlertMapper.to_domain()`
    - Verifica que no se pierdan datos en las conversiones

## Tests de reglas de negocio (`TestAlertBusinessRules`)

### `test_alert_expiration_validation`
- **Propósito**: verifica la lógica de expiración temporal de alertas
- **Funcionalidad**:
    - Crea una alerta con expiración en 1 segundo
    - Verifica que inicialmente no esté expirada (`is_expired()` retorna `False`)
    - Simula el paso del tiempo con `time.sleep(2)`
    - Confirma que después esté expirada

### `test_duplicate_alert_detection`
- **Propósito**: Valida la prevención de alertas duplicadas
- **Funcionalidad**:
    - Crea una alerta inicial exitosamente
    - Intenta crear una segunda alerta con los mismos datos
    - Verifica que se lance `DuplicateAlertException`
    - Confirma que solo exista una alerta con ese título en la base de datos

### `test_alert_statistics`
- **Propósito**: Prepara la base para futuras estadísticas del sistema
- **Funcionalidad**:
    - Crea alertas de diferentes niveles (warning, critical)
    - Documenta la futura implementación de `get_statistics()`
    - Actualmente es un test de preparación para funcionalidad futura

### `test_filter_by_level`
- **Propósito**: Verifica el filtrado de alertas por nivel de severidad
- **Funcionalidad**:
    - Crea alertas de niveles `WARNING` y `CRITICAL`
    - Recupera todas las alertas del repositorio
    - Filtra manualmente las alertas críticas
    - Verifica que se encuentren las alertas del nivel correcto

### `test_filter_active_only`
- **Propósito**: Valida el filtrado por estado de la alerta
- **Funcionalidad**:
    - Crea una alerta activa
    - Cambia su estado a resuelto usando `alert.resolve()`
    - Persiste el cambio en la base de datos
    - Filtra alertas por estado activo y resuelto
    - Verifica que existan alertas en estado resuelto

## Fixtures de testing

### `test_db`
Base de datos SQLite en memoria para aislamiento de tests

### `alert_repository`
Instancia del repositorio SQLAlchemy para operaciones de persistencia

### `alert_service`
Servicio de dominio que encapsula la lógica de negocio

### `sample_alert_data`
Datos de prueba estandarizados para crear alertas consistentes