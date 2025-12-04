# Hito 4: Composición de servicios

## 1. Documentación y justificación de la estructura del clúster

Para este hito, se ha diseñado una arquitectura de microservicios orquestada con **Docker Compose**, definiendo un clúster de contenedores que trabajan de forma cohesionada. Las modificaciones han sido mínimas, ya que se contaba con esta estructura en hitos anteriores.

El objetivo es crear un entorno de desarrollo y pruebas robusto, reproducible y observable, que simule un despliegue en producción. El fichero `docker/docker-compose.yml` define la relación entre los siguientes servicios:

| Servicio | Imagen base | Rol en el clúster | Persistencia de datos |
| :--- | :--- | :--- | :--- |
| `web` | `ghcr.io/davidmunozsanchez/alert_manager:latest` | **Microservicio principal de la API (FastAPI)**. Expone los endpoints para la gestión de alertas. | No directamente, delega en `db`. |
| `db` | `postgres:15` | **Contenedor de datos para la API**. Almacena todas las alertas y datos de la aplicación. | Volumen `pgdata`. |
| `seq` | `datalust/seq:2024.3` | **Plataforma centralizada de logs**. Recibe, almacena y visualiza logs estructurados de todos los servicios. | Volumen `seq-data`. |
| `airflow-webserver` | `apache/airflow:2.9.1` | Interfaz de usuario para la orquestación de tareas de ingesta de datos. | No, estado en `airflow-db`. |
| `airflow-scheduler` | `apache/airflow:2.9.1` | Planificador que ejecuta los DAGs (tareas programadas) en segundo plano. | No. |
| `airflow-db` | `postgres:15` | **Contenedor de datos para Airflow**. Almacena los metadatos, estado de los DAGs y conexiones de Airflow. | Volumen `airflow_pgdata`. |
| `dozzle` | `amir20/dozzle:latest` | Visualizador de logs en tiempo real para todos los contenedores del clúster. | No. |
| `filebrowser` | `filebrowser/filebrowser:latest` | Explorador de archivos para acceder a los logs de respaldo guardados en volúmenes. | No. |
| `log-tester` | `curlimages/curl:latest` | Servicio auxiliar para generar logs de prueba y verificar la conectividad con `seq`. | No. |

### Justificación de la estructura

La estructura está diseñada para ser **resiliente, observable y desacoplada**:
- **Dependencias explícitas**: el servicio `web` no se inicia hasta que la base de datos (`db`) está saludable (`service_healthy`) y `seq` ha comenzado (`service_started`), garantizando un arranque ordenado y evitando errores de conexión en cascada.
- **Persistencia de datos (volúmenes)**: se utilizan **volúmenes con nombre** (`pgdata`, `seq-data`, `airflow_pgdata`) para asegurar que los datos críticos (alertas, logs, metadatos de Airflow) no se pierdan al reiniciar o recrear los contenedores. Esto desacopla el ciclo de vida de los datos del ciclo de vida de los contenedores, permitiendo actualizaciones y mantenimiento sin pérdida de información.
- **Red interna**: todos los servicios se comunican a través de una red interna creada por Docker Compose, usando los nombres de servicio como si fueran DNS (ej. `web` se conecta a `db:5432` o a `seq:80`). Esto abstrae las IPs internas, simplifica la configuración y mejora la seguridad al no exponer puertos innecesarios al exterior.
- **Separación de responsabilidades**: cada servicio tiene un propósito claro. Por ejemplo, Airflow tiene su propia base de datos (`airflow-db`) para no interferir con la base de datos principal de la aplicación (`db`), evitando así que una carga de trabajo intensiva en los DAGs afecte el rendimiento de la API.

## 2. Documentación y justificación de la configuración de cada contenedor

Cada servicio del clúster está configurado para cumplir su función de manera eficiente y segura, siguiendo el principio de **Configuración-como-código**.

### `web` (API Alert Manager)
- **Justificación del contenedor base**: se construye a partir de la imagen `python:3.11-slim` (ver `docker/Dockerfile`), una base ligera y oficial que incluye el intérprete de Python y el gestor de paquetes `pip` sobre un sistema operativo Debian mínimo. Se eligió "slim" para reducir el tamaño de la imagen final.
- **Configuración**: utiliza **variables de entorno** para definir la conexión a la base de datos (`DATABASE_URL`) y al servidor de logs (`SEQ_URL`). Esto desacopla la configuración del código, permitiendo que el mismo contenedor funcione en diferentes entornos (desarrollo, testing, producción) sin necesidad de reconstruir la imagen. Los valores por defecto (`-postgres`) aseguran que el servicio pueda arrancar sin un fichero `.env`, facilitando los tests.
- **Health check**: expone un endpoint `/health` que Docker Compose utiliza para verificar que la API está operativa. Si el endpoint falla, el contenedor se marcará como "unhealthy" y podrá ser reiniciado automáticamente, aumentando la resiliencia del sistema.

### `db` (PostgreSQL para la API)
- **Justificación del contenedor base**: `postgres:15`. Se eligió la imagen oficial de PostgreSQL por ser el estándar de la industria, garantizando estabilidad, seguridad y un mantenimiento óptimo por parte de la comunidad. Proporciona un servidor PostgreSQL listo para usar y se configura fácilmente mediante variables de entorno estándar (`POSTGRES_USER`, etc.).
- **Configuración**: las credenciales (`POSTGRES_USER`, `POSTGRES_PASSWORD`) y el nombre de la base de datos se gestionan mediante variables de entorno, siguiendo las mejores prácticas para no "hardcodear" secretos.
- **Volumen de datos**: el volumen `pgdata` se mapea a `/var/lib/postgresql/data`, el directorio donde PostgreSQL almacena sus datos. Esto es **crucial** para la persistencia y durabilidad de las alertas.

### `seq` (Plataforma de Logging)
- **Justificación del contenedor base**: `datalust/seq:2024.3`. Es la imagen oficial para el servidor de logs Seq, una herramienta potente y fácil de usar para la ingesta y consulta de logs estructurados, ideal para la observabilidad del clúster.
- **Configuración**: requiere aceptar la EULA (`ACCEPT_EULA: "Y"`) y permite configurar una contraseña de administrador mediante variables de entorno para securizar el acceso.
- **Volumen de datos**: el volumen `seq-data` asegura que los logs ingeridos persistan entre reinicios, lo cual es fundamental para la auditoría y el análisis post-mortem de incidentes.

### Ecosistema Airflow
- **Justificación de contenedores base**: se utiliza la imagen oficial `apache/airflow:2.9.1` para el `webserver` y el `scheduler`, y `postgres:15` para su base de datos (`airflow-db`). Usar las imágenes oficiales garantiza la compatibilidad, estabilidad y acceso a las últimas funcionalidades y parches de seguridad del orquestador de tareas.
- **Justificación**: separar Airflow en su propio ecosistema (con su propia base de datos) evita que la carga de trabajo de los DAGs de ingesta de datos pueda impactar el rendimiento de la API principal o su base de datos.

## 3. Documentación del dockerfile

El proyecto utiliza un **único `Dockerfile`** (`docker/Dockerfile`) para construir la imagen del microservicio principal (`web`). Los demás servicios (`db`, `seq`, `airflow`, etc.) utilizan imágenes pre-construidas y oficiales de Docker Hub, ya que no requieren personalización de código. Esta es una práctica estándar y recomendada: **no reinventar la rueda** y aprovechar imágenes mantenidas por la comunidad o los proveedores oficiales.

El `Dockerfile` del servicio `web` sigue un enfoque optimizado para la eficiencia y el cacheo de capas en Docker:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 1. Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 2. Instalar dependencias de Python usando Poetry (capa cacheable)
COPY pyproject.toml ./
RUN pip install --no-cache-dir poetry==1.7.1
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi --no-root

# 3. Copiar el código fuente (capa que cambia con más frecuencia)
COPY src/ ./src/

# 4. Configuración del entorno y ejecución
ENV PYTHONPATH=/app/src
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/alerts/health || exit 1
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Justificación de las fases:**
1.  **Base (`FROM`)**: `python:3.11-slim` es una imagen mínima, lo que reduce el tamaño final del contenedor y la superficie de ataque.
2.  **Dependencias del sistema (`RUN apt-get`)**: Se instalan `postgresql-client` (para que el script `wait_db.py` pueda usar `pg_isready`) y `curl` (para el `HEALTHCHECK`).
3.  **Instalación de paquetes Python (`RUN poetry install`)**: Se copia solo `pyproject.toml` y se instala con `poetry install`. Esta capa solo se reconstruye si las dependencias cambian, no cada vez que se modifica el código fuente. Esto acelera drásticamente las builds durante el desarrollo.
4.  **Copia del código (`COPY src/`)**: El código fuente de la aplicación se copia al final, ya que es la parte que cambia con más frecuencia. De esta manera, Docker reutiliza las capas anteriores cacheadas.
5.  **Ejecución (`CMD`)**: Se expone el puerto `8000`, se define un `HEALTHCHECK` para que Docker sepa si la aplicación está sana, y se inicia el servidor `uvicorn`.

## 4. Publicación de contenedores y actualización automática

La imagen del microservicio `web` se publica de forma automática en **GitHub Packages (ghcr.io)**. Esto se logra mediante el workflow de GitHub Actions definido en `.github/workflows/publish-docker.yml`.

Este workflow se activa en cada `push` a las ramas `main` o `hito4` si se modifican los archivos relevantes (`src/**`, `docker/**`, `pyproject.toml`). Realiza los siguientes pasos:
1.  Hace checkout del código.
2.  Inicia sesión en el registro de contenedores de GitHub (`ghcr.io`) utilizando un `GITHUB_TOKEN` para la autenticación segura.
3.  Construye la imagen Docker usando el `docker/Dockerfile`.
4.  Etiqueta la imagen con `latest` y un tag único basado en el hash del commit (`sha-xxxxxxx`).
5.  Publica (`push`) la imagen en GitHub Packages.

Esto asegura que siempre haya una versión actualizada y lista para desplegar de la aplicación. El `docker-compose.yml` está configurado para usar esta imagen (`image: ghcr.io/davidmunozsanchez/alert_manager:latest`), permitiendo que cualquier entorno que levante el clúster utilice la última versión estable sin necesidad de construirla localmente.

## 5. Documentación del fichero de composición `compose.yaml`

El fichero `docker/docker-compose.yml` es el corazón de la composición de servicios. Define la infraestructura completa como código, garantizando la reproducibilidad.

**Aspectos clave implementados:**
- **Mapeo de puertos**:
  - `web` (`8000:8000`): expone la API al exterior para ser consumida por clientes.
  - `db` (`5432:5432`): permite la conexión a la BD desde el host local para depuración o uso de herramientas de gestión de bases de datos.
  - `seq` (`5341:80`): Expone la interfaz web de Seq.
  - `airflow-webserver` (`8080:8080`): Expone la UI de Airflow.
- **Configuración como código**: todas las configuraciones sensibles o específicas del entorno (URLs, contraseñas) se gestionan con **variables de entorno**, que pueden ser cargadas desde un fichero `.env` (no versionado en git) para mayor seguridad y flexibilidad.
- **Volúmenes de datos**: Se utilizan volúmenes con nombre (`pgdata`, `seq-data`, `airflow_pgdata`) para persistir los datos de los servicios stateful. Esto los desvincula del ciclo de vida del contenedor, permitiendo actualizaciones y reinicios sin pérdida de datos.
- **Comandos de inicio y Health Checks**: se definen comandos de inicio complejos (como en el servicio `web` para esperar a la BD y a Seq) y `healthchecks` para gestionar el estado y las dependencias entre servicios, asegurando un arranque robusto y ordenado del clúster.

Para ver capturas de los diferentes micro servicios funcionando, acceder a la documentación del Hito 3.
[Abrir Hito 3 — línea 236](./hito3.md#L234)

## 6. Test de validación del clúster

Se ha creado un nuevo workflow de GitHub Actions en `.github/workflows/cluster-test.yml` que actúa como un **test de integración para todo el clúster**.

Existen dos tipos de tests de integración en el proyecto, cada uno con un propósito distinto:

1.  **Test de integración con `pytest-docker` (`python-test.yml`)**:
    *   **¿Qué hace?** Este test **construye la imagen Docker desde cero** utilizando el código fuente de la rama actual. Luego, levanta los contenedores necesarios (como la base de datos) y ejecuta tests de `pytest` (`tests/test_container.py`) contra la API. Para ver todo lo implementado, consultar dodu de (`tests/conftest.py`).
    *   **¿Por qué lo hace?** Su objetivo es **validar los cambios en el código fuente *antes*** de que se genere una imagen oficial. Es un test de integración centrado en el desarrollador para asegurar que las nuevas funcionalidades o correcciones funcionan como se espera dentro de un entorno containerizado, pero sin depender de una imagen ya publicada.

2.  **Test de validación del clúster (`cluster-test.yml`)**:
    *   **¿Qué hace?** Este test **NO construye la imagen**. En su lugar, **descarga la imagen `:latest` desde GitHub Packages (ghcr.io)** y levanta todo el clúster definido en `docker-compose.yml` usando la opción `--no-build`. Después, verifica la salud de los servicios con `curl`.
    *   **¿Por qué lo hace?** Su propósito es **validar el artefacto de despliegue final**. Simula lo que haría un entorno de producción: tomar la imagen ya publicada y ejecutarla. Este test confirma que la imagen subida a `ghcr.io` no está corrupta, es accesible y se integra correctamente con el resto de servicios del clúster. Es un test de "humo" o de sanidad sobre el artefacto que se va a desplegar.

---
### Análisis de puntuación

-   **1. Estructura del clúster**: la estructura está claramente definida en `docker-compose.yml`, con justificación para cada servicio, uso de volúmenes para datos y dependencias explícitas. Se cumple el requisito de tener un clúster de más de 3 contenedores, incluyendo contenedores de datos.
-   **2. Configuración de contenedores**: se justifica la elección de imágenes base (oficiales y ligeras) y se utiliza configuración-como-código mediante variables de entorno. Los `healthchecks` mejoran la robustez.
-   **3. Documentación de Dockerfile**: el `Dockerfile` está optimizado y bien documentado. Se justifica por qué solo hay un Dockerfile personalizado, siguiendo las mejores prácticas de reutilización de imágenes oficiales.
-   **4. Publicación en GitHub Packages**: se describe el proceso de construcción y publicación automática de la imagen del microservicio a través del workflow `publish-docker.yml`, desacoplando la construcción del despliegue.
-   **5. Documentación de `compose.yaml`**: el fichero está bien estructurado, documentando mapeo de puertos, volúmenes, redes y configuración, cumpliendo todos los requisitos.
-   **6. Test de validación**: se ha implementado un test de integración (`cluster-test.yml`) que valida el funcionamiento del clúster completo, usando la imagen publicada y verificando la disponibilidad de los servicios. Se explica su diferencia y propósito respecto a tests anteriores.



## Apéndice

Los logs de las Actions son bastante largos. Como se ha documentado todo aquí debidamente, se recomienda consultar los últimos test exitosos en:

[ACTIONS GitHub](https://github.com/davidmunozsanchez/alert_manager/actions)