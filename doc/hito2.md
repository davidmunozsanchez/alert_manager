# ALERT MANAGER

## HITO 2: INTEGRACIÓN CONTINUA

Este hito establece la infraestructura de Integración Continua (CI) para Alert Manager, garantizando que cada cambio en el código pase por validaciones automáticas de calidad y tests antes de integrarse al proyecto.

Antes de seguir con información más detallada sobre las decisiones tomadas, se hará un resumen de las mismas.

1. Gestor de tareas: Poetry
Herramienta moderna de Python para gestión de dependencias, empaquetado y ejecución de scripts.

Alternativas evaluadas: pip + requirements.txt

2. Biblioteca de Aserciones: pytest (estilo BDD)
Framework de testing con enfoque en Behavior-Driven Development para tests más legibles y mantenibles.


3. Test Runner: pytest
Sistema completo de descubrimiento, ejecución y reporte de pruebas con un ecosistema de plugins bastante extenso.


4. Integración con construcción: Poetry + Makefile
Comandos estandarizados (make test, poetry run test) para ejecutar pruebas de forma consistente en local y CI.


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
