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

Como ya se ha comentado anteriormente, el problema a tratar se inspirará en este, pero desde el principio, se buscará una mejora en el backend para poder dotar de mucha más funcionalidad a una posible APP en el futuro, así como aprovechar las numerosas ventajas del Cloud Computing.

Por una parte, hay que gestionar la obtención e ingesta de alertas en nuestra base de datos. Para esto, se crearán DAGs Airflow encargados de hacer web scrapping en ciertas fuentes, consultar periódicamente APIs públicas de alertas. Con esto, se irá actualizando una base de datos.

Airflow también se encargará de adaptar todos los datos a alertas que se puedan introducir en la base de datos relacional. Al tratarse de datos con los cuales se consultarán relaciones complejas (por ejemplo alertas inactivas o activas, alertas de cierta comunidad), tiene sentido usar una base de datos relacional. Además, se pretende una refactorización del código existente para aprovechar PostGIS, Postgres con consultas optimizadas para datos geoespaciales.

Por último, se creará una API Rest para la administración y gestión de alertas por parte de varios usuarios, los cuales serán:
- Admin
- Técnico
- Usuario

Técnico corresponderá con más categorías de profesionales, con diferentes funciones cada uno, según el tipo de alertas que tengan permitido gestionar.

Para ello, se hará uso de FastAPI. Tener una API permitirá poder hacer uso de esta en la APP Android que se estaba desarrollando o incluso una aplicación web.

En cuanto a la seguridad, actualmente se usa Firebase para gestionar los inicios de sesión y los login. Esto permanecerá sin cambios.

Todo esto está pensado para ser usado a través de contenedores Docker. Lo descrito en este último apartado, está sujeto a cambios, aunque se pretendía explicar el problema desde una perspectiva más práctica y aprovechando la infraestructura ya hecha. Si algún cambio fuera introducido en el futuro, se corregiría debidamente los README relacionados.


De momento no hay ningun MVP y lo que si podemos hacer es historias minimas de usuario para futuro y agruparlos en MVPS para la correcta definición del problema.

Implementar varios roles.

Implementar webscrapping

Implementar endpoints principales.

Y alo mejor los dos ultimos son para el MVP de API funcional o algo así.