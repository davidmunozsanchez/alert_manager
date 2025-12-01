# 🚀 Hito 4: Composición de Servicios y Contenedores

## 🏗️ Estructura del Clúster
Para este hito se ha diseñado una arquitectura de microservicios orquestada mediante **Docker Compose**. El objetivo es desacoplar la lógica de negocio, la persistencia de datos y la observabilidad.

El clúster (`compose.yaml`) se compone de los siguientes servicios:

1.  **`web` (Alert Manager):**
    * **Función:** Microservicio principal (FastAPI) desarrollado en los hitos anteriores.
    * **Justificación:** Se ejecuta en un contenedor independiente para permitir su escalado horizontal si fuera necesario sin afectar a la base de datos.
    * **Imagen:** Se descarga automáticamente desde `ghcr.io` (GitHub Packages) tras ser construida por el CI.

2.  **`db` (PostgreSQL):**
    * **Función:** Base de datos relacional para persistencia de alertas.
    * **Justificación:** Usamos la imagen oficial `postgres:15` por estabilidad y seguridad. Los datos se persisten mediante un volumen `pgdata`.

3.  **Ecosistema Airflow (`airflow-webserver`, `scheduler`, `init`, `db`):**
    * **Función:** Orquestación de tareas de ingesta de datos (ETL).
    * **Justificación:** Se ha aislado Airflow en sus propios contenedores estándar para manejar los workflows complejos sin "contaminar" el código de la API principal.

4.  **Observabilidad (`seq`, `dozzle`):**
    * **Función:** Centralización de logs.
    * **Justificación:** `Seq` permite estructurar los logs y realizar búsquedas complejas, vital para depurar un sistema distribuido donde mirar logs de texto plano contenedor por contenedor es ineficiente.

---

## 🐳 Justificación de Imágenes y Dockerfile

### Servicio `web` (Custom Dockerfile)
Para el microservicio principal, he creado un `Dockerfile` optimizado:

* **Imagen Base:** `python:3.11-slim`.
    * *Por qué:* Las imágenes "slim" de Debian contienen lo mínimo necesario para ejecutar Python, reduciendo el tamaño final de la imagen (~150MB vs ~900MB de la imagen completa) y la superficie de ataque de seguridad.
* **Gestión de Dependencias:** Uso `poetry` instalado en la fase de construcción, pero configurado para no crear entornos virtuales dentro del contenedor (`virtualenvs.create false`), ya que el contenedor en sí mismo ya es un entorno aislado.
* **Multistage/Cache:** Se copian primero los ficheros de definición (`pyproject.toml`) y luego el código, aprovechando la caché de capas de Docker para acelerar las builds posteriores.

### Servicios de Infraestructura
Para el resto de servicios (`postgres`, `airflow`, `seq`) se han utilizado las **imágenes oficiales** del registro de Docker Hub. 
* *Justificación:* No es necesario (y es una mala práctica) reconstruir desde cero servicios estándar. Las imágenes oficiales reciben parches de seguridad y están optimizadas por los proveedores.

---

## 🔄 Integración Continua (CI/CD)

Se han implementado dos workflows de GitHub Actions para cumplir con los requisitos de "Configuración como Código" y automatización:

1.  **Publicación (`publish-docker.yml`):**
    * Se activa con cada push a `main`.
    * Construye la imagen del servicio `web` usando el `Dockerfile`.
    * Se autentica contra **GitHub Container Registry (GHCR)**.
    * Sube la imagen etiquetada como `latest`.

2.  **Test de Integración (`cluster-test.yml`):**
    * Se ejecuta tras la publicación o manualmente.
    * **Descarga (Pull)** explícitamente la imagen desde GHCR para asegurar que se usa la versión de producción.
    * Levanta el clúster completo (`docker compose up -d`).
    * **Verificación:** Ejecuta un script que espera pacientemente (retry loop) a que servicios pesados como Airflow estén disponibles y verifica que el API responda `200 OK`.

## 🛠️ Cómo ejecutar el proyecto

Para levantar todo el entorno localmente:

```bash
# Levantar servicios
docker compose -f docker/docker-compose.yml up -d

# Ver logs
docker compose -f docker/docker-compose.yml logs -f