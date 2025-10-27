# ALERT MANAGER

## HITO 2: INTEGRACIÓN CONTINUA

Este hito establece la infraestructura de Integración Continua (CI) para Alert Manager, garantizando que cada cambio en el código pase por validaciones automáticas de calidad y tests antes de integrarse al proyecto.

Antes de seguir con información más detallada sobre las decisiones tomadas, se hará un resumen de las mismas.

1. Gestor de tareas: Poetry
Herramienta moderna de Python para gestión de dependencias, empaquetado y ejecución de scripts.


2. Biblioteca de Aserciones: pytest.


3. Test Runner: pytest
Sistema completo de descubrimiento, ejecución y reporte de pruebas con un ecosistema de plugins bastante extenso.


4. Integración con construcción: Poetry.


5. Sistema CI: GitHub Actions
Plataforma de integración continua nativa de GitHub con pipeline en 5 etapas.


A continuación, se irán detallando las etapas siguiendo un orden lógico de construcción, es decir, siguiendo los dos hitos creados para el desarrollo del Hito 2. No obstante, se darán explicaciones de como ha quedado finalmente esa parte, es decir, detallando una especie de finalización del Hito 2, sin cerrar posibles modificaciones en el futuro. Para seguir el orden cornológico que se siguió en la implementación de todos los apartados para configurar y correr CI, se recomienda consultar las issues y los milestones del repositorio.

### GitHub Actions

GitHub Actions es la plataforma de CI/CD nativa de GitHub que permite automatizar workflows directamente desde el repositorio. Se ha elegido por su integración perfecta con el ecosistema GitHub y su facilidad de configuración mediante archivos YAML. Además, solo había usado Jenkins en otros proyectos y me parece más fácil y rápido de configurar.



---

#### Arquitectura del Pipeline

El workflow está diseñado con **3 jobs independientes** organizados en una arquitectura de pipeline con paralelización:

```
┌──────────────────────────┐
│    JOB 1: LINT           │
│  Análisis estático       │
│  • isort                 │
│  • flake8                │
│  • bandit                │
│  • mypy                  │
│  • pylint                │
└────────┬─────────────────┘
         │
    ┌────┴──────────────────────────┐
    │    (ejecución paralela)       │
    │                               │
┌───▼──────────────────┐  ┌────────▼─────────────┐
│ JOB 2: DOCKER TESTS  │  │ JOB 3: DAG TESTS     │
│ • Setup containers   │  │ • Airflow DAGs       │
│ • API integration    │  │ • Import validation  │
│ • Database tests     │  │ • Syntax checks      │
│ • Cleanup            │  │                      │
└──────────────────────┘  └──────────────────────┘
```

**Características de diseño:**


- `lint` se ejecuta primero como gate de calidad. No obstante, su fallo en alguno de los test no implica que no se corran las siguientes tareas. Simplemente es una prueba de calidad y se irán actualizando sus refactorizaciones sugeridas en futuros commits.

- Además, se pasó **black** en local para autoformatear el código automáticamente, garantizando un estilo consistente según las convenciones PEP 8. Black es un formateador de código Python "sin configuración" que elimina debates sobre estilo al aplicar un formato determinista y legible.
- `test_docker_integration` y `test_dags` se ejecutan en paralelo tras lint
   
- Cada job tiene su propio entorno Ubuntu limpio y así no hay interferencias entre tests.


---

#### Triggers del Workflow

El pipeline se activa automáticamente en:

```yaml
on:
  push:
    branches: [ "main", "hito2" ]
  pull_request:
    branches: [ "main", "hito2" ]
```

**Estrategia de ramas:**
- **`main`**: validación de código en producción
- **`hito2`**: rama de desarrollo activo del hito 2.
- **Pull Requests**: comprobación de calidad antes de merge.

#### Protección de ramas

En un entorno de producción donde se contara con GitHub Enterprise, sería posible usar reglas de protección de las ramas para:

**Ejemplos de reglas de protección:**
- **Require status checks**: obligar que pasen todos los checks del CI antes del merge
- **Require pull request reviews**: exigir al menos 1-2 revisiones de código aprobadas
- **Dismiss stale reviews**: invalidar reviews cuando se añaden nuevos commits
- **Require branches to be up to date**: Forzar actualización con la rama base antes del merge
- **Restrict pushes**: solo permitir merges via pull request, prohibiendo pushes directos
- **Require signed commits**: obligar commits firmados digitalmente para mayor seguridad

**Limitaciones en repositorios públicos gratuitos:**
- Las reglas de protección avanzadas requieren **GitHub Enterprise**.
- En repos públicos gratuitos solo están disponibles protecciones básicas

Así quedría el workflow si se consulta en Actions:

![alt text](./imgs/actions1.png)


### Poetry

Poetry es el gestor de dependencias y empaquetado moderno elegido para Alert Manager. Reemplaza el flujo tradicional de `pip + requirements.txt` con un enfoque más robusto y determinista.

#### ¿Por qué Poetry?

**Ventajas principales:**
- **Gestión de entornos virtuales**: crea y maneja venvs automáticamente
- **Gestión de grupos**: separación clara entre dependencias de producción y desarrollo. Esto será una mejora en futuras revisiones del código. Ahora mismo, los test se están ejecutando y la CI funcionando.

**Alternativas evaluadas:**
- **pip + requirements.txt**: estándar tradicional pero sin resolución de dependencias, algo que Poetry sí contempla, recomendando incluso versiones compatibles entre sí.

---

#### Archivo pyproject.toml

El archivo `pyproject.toml` es el corazón de la configuración del proyecto. Define metadatos, dependencias, herramientas de desarrollo y configuración.

**Estructura básica:**

```toml
[tool.poetry]
name = "alert_manager"
version = "0.1.0"
description = "Alert Management System"
authors = ["dmunozs14@correo.ugr.es"]
readme = "README.md"
packages = [{include = "src"}]
```

**Metadatos del proyecto:**
- `name`: identificador único del paquete.
- `packages`: directorio que contiene el .código fuente.
- `readme`: archivo de documentación principal.

---

##### Dependencias de producción

```toml
[tool.poetry.dependencies]
python = ">=3.11,<3.13"
```

**¿Por qué no hay más dependencias aquí?**
En este proyecto, las dependencias de producción están mezcladas con las de desarrollo en `[tool.poetry.group.dev.dependencies]`. En un entorno real, aquí irían solo las dependencias necesarias para ejecutar la aplicación. Se actualizará en futuras versiones.

---

##### Dependencias de desarrollo

```toml
[tool.poetry.group.dev.dependencies]
...
```
Aquí están todas las dependencias necesarias para correr los tests.
**Sintaxis de versiones:**
- `^7.4.2`: Compatible con `>=7.4.2, <8.0.0` (patch/minor updates)
- `>=1.4.36,<2.0`: Rango específico (evita breaking changes)
- `2.9.1`: Versión exacta (para compatibilidad crítica como Airflow)

##### Configuración de Pytest

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
```

- `testpaths`: directorio donde buscar tests
- `python_files`: patrón de archivos de test

#### Integración con GitHub Actions

Poetry se integra en el workflow mediante la action oficial `snok/install-poetry@v1`:

```yaml
- name: Install Poetry
  uses: snok/install-poetry@v1

- name: Install dependencies
  run: poetry install
```

**Ejecución de tests:**
```bash
# Via Poetry
poetry run pytest -v

```

Si añadiéramos -s podríamos ver todos los logs de las ejecuciones de los tests.

#### Poetry.lock
`poetry.lock` es generado automáticamente y contiene las versiones exactas de todas las dependencias. En este caso, no se ha tenido en cuenta ya que cada test inicia un entorno independiente Ubuntu e instala las dependencias desde 0.

### **Biblioteca de aserciones y Test Runner: pytest**
   
Antes de hablar sobre esto, convendría explicar detenidamente todos los test que se llevarán a cabo, y si siguen un enfoque BDD o TDD.


#### Test de los DAGs

##### Tests de DAGs de Airflow

Los tests de DAGs validan la correcta estructura, configuración y relaciones entre tareas de los workflows de Airflow sin necesidad de ejecutarlos. Utilizan `DagBag` de Airflow para cargar y analizar los DAGs estáticamente. Para estos test se sigue un enfoque TDD, ya que fueron escritos sin tener en cuenta como serán futuros DAGS, lanzando arseciones para corroborar que a ojos de Airflow, los DAGS son correctos.

###### ¿Qué son los fixtures en pytest?

Los **fixtures** son funciones que proporcionan recursos reutilizables para los tests. Actúan como "preparación" y "limpieza" antes y después de cada test, garantizando un entorno consistente y controlado.

**Scopes disponibles:**
- `function`: ejecuta antes/después de cada función de test (por defecto).
- `class`: ejecuta una vez por clase de test.
- `module`: ejecuta una vez por archivo de test.
- `session`: ejecuta una vez por sesión completa de tests.

###### Fixture: dagbag

```python
@pytest.fixture(scope="module")
def dagbag():
    """Load all DAGs from the src/dags folder"""
```

Carga todos los DAGs desde `src/dags/` una sola vez por módulo de test.

- Define `AIRFLOW_HOME` temporal para aislar tests
- Configura carpeta de DAGs apuntando a `src/dags/`
- Desactiva ejemplos de Airflow (`AIRFLOW__CORE__LOAD_EXAMPLES=False`)
- Retorna un `DagBag` con todos los DAGs cargados.

---

###### 1. `test_no_import_errors`

```python
def test_no_import_errors(dagbag):
    """Test that all DAGs can be imported without errors"""
    assert len(dagbag.import_errors) == 0
```

**Qué valida:**
- Todos los archivos Python en `src/dags/` se importan sin errores
- No hay errores de sintaxis
- Todas las dependencias están disponibles

**Falla si:**
- Hay un `SyntaxError` en algún DAG
- Falta algún import (`ModuleNotFoundError`)
- Hay errores en la definición del DAG

---

###### 2. `test_dags_loaded`

```python
def test_dags_loaded(dagbag):
    """Test that DAGs are loaded"""
    assert len(dagbag.dags) > 0
```

**Qué valida:**
- Al menos un DAG fue cargado exitosamente
- La carpeta `src/dags/` no está vacía

**Falla si:**
- No hay archivos `.py` con DAGs válidos
- Todos los DAGs tienen errores de importación

---

###### 3. `test_dag_structure`

```python
def test_dag_structure(dagbag):
    """Test each DAG has required attributes"""
    for dag_id, dag in dagbag.dags.items():
        assert dag.owner is not None
        assert dag.start_date is not None
        assert isinstance(dag.start_date, datetime)
```

**Qué valida para cada DAG:**
- Tiene un `owner` definido (responsable del DAG)
- Tiene `start_date` (fecha desde la cual puede ejecutarse)
- El `start_date` es un objeto `datetime` válido
- Emite warning si `schedule_interval` es `None` (DAG manual)

**Falla si:**
- `owner` es `None`.
- `start_date` no está definido o no es `datetime`.

---

###### 4. `test_dag_has_tasks`

```python
def test_dag_has_tasks(dagbag):
    """Test that each DAG has at least one task"""
    assert len(dag.tasks) > 0
```

**Qué valida:**
- Cada DAG tiene al menos una tarea definida
- Imprime la lista de tasks para debugging

**Falla si:**
- Un DAG está vacío (sin operadores/tasks)

---

###### 5. `test_dag_task_dependencies`

```python
def test_dag_task_dependencies(dagbag):
    """Test that tasks have proper dependencies"""
    for upstream_task_id in task.upstream_task_ids:
        assert upstream_task_id in dag.task_dict
```

**Qué valida:**
- Todas las dependencias upstream existen en el DAG
- No hay referencias a tasks inexistentes

**Falla si:**
```python
# task1 >> task2  pero task1 no existe
task2.set_upstream('task1')  # task1 no definido
```

---

###### 6. `test_dag_cycles`

```python
def test_dag_cycles(dagbag):
    """Test that DAGs don't have cycles"""
    assert dag_id not in dagbag.import_errors
```

**Qué valida:**
- No hay dependencias cíclicas entre tasks
- El grafo del DAG es acíclico (DAG = Directed Acyclic Graph)

**Falla si hay ciclo:**
```python
task1 >> task2 >> task3 >> task1  # Ciclo!
```

---

###### 7. `test_dag_default_args`

```python
def test_dag_default_args(dagbag):
    """Test that DAGs have proper default_args"""
    required_default_args = ["owner"]
```

**Qué valida:**
- El DAG tiene `default_args` con al menos `owner`
- Si no hay `default_args`, verifica que `owner` esté en el DAG directamente
---

###### 8. `test_dag_task_retries`

```python
def test_dag_task_retries(dagbag):
    """Test that tasks have retry configuration"""
    retries = task.retries or dag.default_args.get("retries")
    assert retries >= 0
```

**Qué valida:**
- Cada task tiene configuración de reintentos (directa o heredada).
- El número de retries no es negativo.
- Emite warning si no hay configuración de retries.

**Por qué es importante:**
- Tareas sin retries pueden fallar permanentemente por errores temporales.

---

###### 9. `test_dag_tasks_have_operators`

```python
def test_dag_tasks_have_operators(dagbag):
    """Test that tasks use valid operators"""
    valid_operators = [
        "PythonOperator", "BashOperator", "DummyOperator", ...
    ]
```

**Qué valida:**
- Las tasks usan operadores conocidos de Airflow.
- Emite warning si usa operadores custom o poco comunes.

**No falla el test**, solo informa sobre operadores no estándar.

**Ejemplo:**
- `PythonOperator` → Reconocido
- `MyCustomOperator` → Warning (pero no falla).

###### 10. `test_dag_scheduling`

```python
def test_dag_scheduling(dagbag):
    """Test that DAGs have valid scheduling configuration"""
```

**Qué valida:**
- Si hay `schedule_interval`, no es una cadena vacía
- El `start_date` no está más de 1 año en el futuro
- Compatibilidad de timezone entre `start_date` y `datetime.now()`
- Warning si no hay schedule (DAG manual)


---

###### 11. `test_dag_timeout_configuration`

```python
def test_dag_timeout_configuration(dagbag):
    """Test that DAGs have timeout configuration"""
```

**Qué valida:**
- Verifica si las tasks tienen `execution_timeout` configurado.
- No falla, solo informa.

---

###### 12. `test_dag_tags`

```python
def test_dag_tags(dagbag):
    """Test that DAGs have tags for organization"""
```

**Qué valida:**
- Verifica si el DAG tiene tags para organización.
- No falla, solo recomienda añadir tags.


---

###### 13. `test_dag_documentation`

```python
def test_dag_documentation(dagbag):
    """Test that DAGs have documentation"""
```

**Qué valida:**
- Verifica si el DAG tiene `description`.
- Verifica si las tasks tienen `doc` o `doc_md`.
- No falla, solo recomienda documentación.

---
