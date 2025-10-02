# ALERT MANAGER

## HITO 1: CREACIÓN DEL REPOSITORIO Y DEFINICIÓN DEL PROBLEMA

### Origen del problema

El problema se basará en el backend de un proyecto de la asignatura del máster GIDM. El backend se puede consultar aquí: [API ALERTAS](https://github.com/davidmunozsanchez/alertas_api).

La idea tras este código es gestionar de forma eficiente alertas meteorológicas, accientes, es decir, toda comunicación por parte de autoridades que necesite llegar al máximo número de personas posibles.

La estructura de este repositorio es la siguiente:

- app/ — carpeta que contiene el código de la API Rest. Se tienen endpoints para la carga y visualización de puntos, así como validación de información con Pydantic. Además, se implementan endpoints para búsquedas con filtros.

- dags/ — carpeta de Airflow donde se definen flujos de trabajo programados (“Directed Acyclic Graphs”, DAGs) para tareas automáticas. En este caso, hay un DAG encargado de monitorizar si un archivo en el repositorio cambia o no y otro para si cambia ingestar los puntos en la base de datos.

- load_data.py — script para cargar datos iniciales o ingestión de datos.

- En este punto, ya se puede observar que el backend originalmente se hizo como apoyo a la aplicación Android que se estaba desarrollando, a modo de prueba. Sin embargo, en este proyecto, donde se pretende resolver un problema mediante uno o varios servicios desplegados en la nube, se podría profundizar mucho más en el aspecto de la carga de puntos, algo de lo que se hablará al terminar esta sección.

- reset_db.py — script para reiniciar la base de datos (limpiar tablas, volver al estado inicial).

- Dockerfile, docker-compose.yml, start.sh — para empaquetar todo el sistema en contenedores Docker y orquestar servicios. El docker compose file contiene los siguientes servicios y volúmenes:

    - **db**: PostgreSQL.  
    - **web**: API de alertas, conecta a `db`, expuesta en puerto `8000`.  
    - **airflow-db**: PostgreSQL exclusivo para Airflow.  
    - **airflow-webserver**: interfaz web de Apache Airflow (puerto `8080`).  
    - **airflow-scheduler**: planifica y ejecuta tareas de Airflow.  
    - **pgdata**: datos de la BD principal.  
    - **airflow_pgdata**: datos de Airflow.  

.env — variables de entorno (credenciales, urls, configuración).


### Definición del problema
