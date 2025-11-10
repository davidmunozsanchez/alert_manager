## Tests de DAGs de Airflow (`tests/test_dags.py`)
Estos tests están diseñados para validar la estructura, configuración y propiedades esenciales de los DAGs de Apache Airflow. Se ejecutan de forma estática, sin necesidad de un entorno Airflow en ejecución, utilizando `DagBag` para cargar y analizar los DAGs.

### `dagbag` (fixture)
- **Propósito**: carga todos los DAGs desde el directorio `src/dags` una única vez por módulo de test.
- **Funcionalidad**:
    - Configura `AIRFLOW_HOME` y `AIRFLOW__CORE__DAGS_FOLDER` para aislar los tests.
    - Desactiva la carga de ejemplos de Airflow.
    - Retorna una instancia de `DagBag` con todos los DAGs encontrados.

### `test_no_import_errors`
- **Propósito**: verifica que todos los archivos Python en el directorio de DAGs puedan importarse sin errores de sintaxis o dependencias.
- **Funcionalidad**:
    - Comprueba que la lista `dagbag.import_errors` esté vacía.
    - **Falla si**: hay `SyntaxError`, `ModuleNotFoundError` o cualquier otro error de importación en un archivo DAG.

### `test_dags_loaded`
- **Propósito**: asegura que al menos un DAG haya sido cargado exitosamente por `DagBag`.
- **Funcionalidad**:
    - Verifica que el número de DAGs en `dagbag.dags` sea mayor que cero.
    - **Falla si**: el directorio de DAGs está vacío o todos los DAGs tienen errores de importación.

### `test_dag_structure`
- **Propósito**: valida que cada DAG tenga atributos esenciales como `owner` y `start_date` definidos correctamente.
- **Funcionalidad**:
    - Itera sobre cada DAG cargado.
    - Comprueba que `dag.owner` no sea `None`.
    - Comprueba que `dag.start_date` no sea `None` y sea una instancia de `datetime`.
    - Emite una advertencia si `dag.schedule_interval` es `None`, indicando un DAG manual o bajo demanda.
    - **Falla si**: `owner` o `start_date` no están definidos.

### `test_dag_has_tasks`
- **Propósito**: verifica que cada DAG tenga al menos una tarea definida.
- **Funcionalidad**:
    - Comprueba que `len(dag.tasks) > 0` para cada DAG.
    - **Falla si**: un DAG está vacío sin tareas.

### `test_dag_task_dependencies`
- **Propósito**: valida que todas las dependencias de tareas referencien tareas que existen en el DAG.
- **Funcionalidad**:
    - Itera sobre cada tarea de cada DAG.
    - Verifica que cada `upstream_task_id` existe en `dag.task_dict`.
    - **Falla si**: una tarea depende de otra que no existe.

### `test_dag_cycles`
- **Propósito**: asegura que los DAGs no contengan ciclos en sus dependencias.
- **Funcionalidad**:
    - Verifica que el DAG no aparezca en `dagbag.import_errors`.
    - **Falla si**: Airflow detecta un ciclo durante la carga del DAG.

### `test_dag_default_args`
- **Propósito**: comprueba que los DAGs tengan argumentos por defecto apropiados, especialmente `owner`.
- **Funcionalidad**:
    - Verifica que `default_args` contenga los argumentos requeridos.
    - Si no hay `default_args`, verifica que al menos `dag.owner` esté definido.
    - Emite advertencias para argumentos faltantes.
    - **Falla si**: no hay `default_args` ni `owner` definido.

### `test_dag_task_retries`
- **Propósito**: verifica que las tareas tengan configuración de reintentos para manejo de fallos.
- **Funcionalidad**:
    - Comprueba la configuración de `retries` a nivel de tarea o en `default_args`.
    - Emite advertencias si no hay configuración de reintentos.
    - **Falla si**: el número de reintentos es negativo.

### `test_dag_tasks_have_operators`
- **Propósito**: valida que las tareas usen operadores conocidos y válidos de Airflow.
- **Funcionalidad**:
    - Compara el nombre de clase del operador contra una lista de operadores válidos.
    - Emite advertencias para operadores no comunes o personalizados.
    - **No falla**: solo advierte sobre operadores inusuales.

### `test_dag_scheduling`
- **Propósito**: verifica que los DAGs tengan configuración de programación válida.
- **Funcionalidad**:
    - Comprueba que `schedule_interval` no sea una cadena vacía.
    - Valida que `start_date` sea razonable (no más de 1 año en el futuro).
    - Maneja fechas con y sin zona horaria correctamente.
    - Emite advertencias para DAGs sin programación.
    - **Falla si**: `schedule_interval` es una cadena vacía.

### `test_dag_timeout_configuration`
- **Propósito**: verifica que las tareas tengan configuración de timeout para evitar ejecuciones indefinidas.
- **Funcionalidad**:
    - Comprueba si las tareas tienen `execution_timeout` configurado.
    - Registra información sobre timeouts configurados.
    - **No falla**: es una verificación informativa.

### `test_dag_tags`
- **Propósito**: asegura que los DAGs tengan etiquetas para organización y categorización.
- **Funcionalidad**:
    - Verifica que `dag.tags` no esté vacío.
    - Emite advertencias si no hay etiquetas definidas.
    - **No falla**: las etiquetas son opcionales pero recomendadas.

### `test_dag_documentation`
- **Propósito**: verifica que los DAGs y sus tareas tengan documentación adecuada.
- **Funcionalidad**:
    - Comprueba que `dag.description` no esté vacío.
    - Verifica documentación en tareas (`doc` o `doc_md`).
    - Emite advertencias para DAGs sin descripción.
    - **No falla**: la documentación es recomendada pero no obligatoria.

### Tests comentados (específicos por DAG)
- `test_data_ingesting_dag` y `test_data_checking_dag` están comentados.
- **Propósito**: validar estructura específica de DAGs particulares.
- **Funcionalidad**: verificar tareas esperadas y configuración específica de cada DAG.