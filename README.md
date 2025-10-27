# ALERT MANAGER

**Alert Manager** es un sistema diseñado para la **gestión, ingesta y administración de alertas** (meteorológicas, de tráfico, emergencias, etc.) procedentes de múltiples fuentes.
Su objetivo principal es crear una infraestructura escalable, basada en **servicios en la nube y contenedores Docker**, que permita recopilar, procesar y distribuir información de alertas de forma eficiente y segura.

Para más información, consulte el README del **Hito 1**.

---

## Documentación

Toda la información técnica y el desarrollo del proyecto se encuentran documentados en la carpeta [`/doc`](./doc).

- [Hito 1: Creación del repositorio y definición del problema](./doc/hito1.md)

- [Hito 2: Integración continua](./doc/hito2.md)

Consideraciones previas hito2: los archivos que se presentan en el repositorio no tienen por qué tener documentación. Para el Hito 2, como se centraba en la configuración de CI y la ejecución de algunos tests, no se han hecho, por ejemplo, test para los endpoints de la API. En futuras actualizaciones, se añadirán, ya que se irán refactorizando el comportamiento de la aplicación y añadiendo lógica de negocio.

Hasta ahora, se han probado los DAGs, el set up Docker y las operaciones CRUD. En el futuro habrá más pruebas para los ENDPOINTS de la API y el comportamiento de Airflow en sí, ya que puede ser que se añadan más DAG o se modifiquen los que ya hay.

También recalcar que para la issue #19 hay muchos commits por el hecho de que quería testearlo en GitHub. No obstante, a partir de ese punto, se configuró el entorno local para poder ejecutar Poetry (gestor de tareas).

> A medida que avance el desarrollo, se irán añadiendo nuevos hitos y documentación adicional.

---

## Seguimiento del proyecto

Puedes seguir el progreso del desarrollo, reportar errores o proponer mejoras desde los siguientes apartados del repositorio:

- [Issues](https://github.com/davidmunozsanchez/alert_manager/issues): seguimiento de errores y tareas pendientes.
- [Milestones](https://github.com/davidmunozsanchez/alert_manager/milestones): planificación y avances por etapas.

Añadir lo que se ha hecho.

---

## Autor

Proyecto desarrollado por **David Muñoz Sánchez**, estudiante del **Máster en Ingeniería Informática** de la **Universidad de Granada (UGR)**.

---

## Licencia

Este proyecto es **privado**.
