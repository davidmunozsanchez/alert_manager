# ALERT MANAGER

**Alert Manager** es un sistema diseñado para la **gestión, ingesta y administración de alertas** (meteorológicas, de tráfico, emergencias, etc.) procedentes de múltiples fuentes.
Su objetivo principal es crear una infraestructura escalable, basada en **servicios en la nube y contenedores Docker**, que permita recopilar, procesar y distribuir información de alertas de forma eficiente y segura.

Para más información, consulte el README del **Hito 1**.

---

## Documentación

Toda la información técnica y el desarrollo del proyecto se encuentran documentados en la carpeta [`/doc`](./doc).

- [Hito 1: Creación del repositorio y definición del problema](./doc/hito1.md)

- [Hito 2: Integración continua](./doc/hito2.md)

- [Hito 3: Diseño de microservicios](./doc/hito3.md)

- [Hito 4: Composición de servicios](./doc/hito4.md)
  
- [Hito 5: Despliegue de la app en un PaaS](./doc/hito5.md)

**Consideraciones hito5:** se han eliminado algunos contenedores que no se veían necesarios de los hitos previos, como filebrowser, y se han añadido otros como Prometheus. Están comentadas algunas mejoras futuras también. Además, uno de los test de los Dags falla en GitHub porque se ha añadido el DAG no terminado para ingestar datos de la DGT, el que funciona es el de la AEMET.

---

## Seguimiento del proyecto

Puedes seguir el progreso del desarrollo, reportar errores o proponer mejoras desde los siguientes apartados del repositorio:

- [Issues](https://github.com/davidmunozsanchez/alert_manager/issues): seguimiento de errores y tareas pendientes.
- [Milestones](https://github.com/davidmunozsanchez/alert_manager/milestones): planificación y avances por etapas.


---

## Autor

Proyecto desarrollado por **David Muñoz Sánchez**, estudiante del **Máster en Ingeniería Informática** de la **Universidad de Granada (UGR)**.

---

## Licencia

Este proyecto es **privado**.
