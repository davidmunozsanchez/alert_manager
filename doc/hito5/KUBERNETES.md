# Despliegue en Kubernetes (Hito 5)

Este documento detalla la arquitectura, justificación y proceso de despliegue del sistema Alert Manager en un clúster de Kubernetes gestionado (OKE) en Oracle Cloud, usando el nivel gratuito Always Free.

## Justificación de la elección de Kubernetes y Oracle OKE

El despliegue en Kubernetes responde a la necesidad de gestionar aplicaciones complejas, distribuidas y resilientes, superando las limitaciones de Docker Compose en entornos de producción. Mientras Docker permite ejecutar contenedores de forma aislada en una sola máquina, Kubernetes orquesta múltiples contenedores (pods) en varios nodos, proporcionando:
- Alta disponibilidad y auto-recuperación ante fallos.
- Escalado automático y balanceo de carga.
- Gestión declarativa de la infraestructura (infraestructura como código).
- Integración nativa con herramientas de observabilidad y monitorización.

Oracle Cloud Infrastructure (OCI) y su servicio Oracle Kubernetes Engine (OKE) han sido seleccionados porque:
- Ofrecen un clúster Kubernetes real, con 4 OCPU y 24GB RAM ARM, almacenamiento y balanceador de carga, todo ello sin coste en el Always Free Tier.
- Permiten desplegar en la región europea (eu-frankfurt-1), cumpliendo requisitos legales de protección de datos.
- El entorno es reproducible y automatizable mediante scripts y manifiestos YAML versionados en el repositorio.
- El clúster soporta múltiples pods (API, Airflow, PostgreSQL, observabilidad) y pruebas de carga razonables para el alcance académico.

**Diferencia clave Docker vs Kubernetes:**
- Docker Compose es adecuado para desarrollo local y pruebas, pero no gestiona alta disponibilidad, auto-recuperación ni escalado real.
- Kubernetes es el estándar de facto para producción, permitiendo despliegues robustos, escalables y observables en la nube.

## Arquitectura del sistema desplegado

El sistema Alert Manager se compone de los siguientes servicios, cada uno desplegado como uno o varios pods en el clúster:

- API FastAPI: Servicio principal de gestión de alertas (2 réplicas para alta disponibilidad).
- PostgreSQL: Base de datos principal.
- Airflow Webserver y Scheduler: Orquestación de flujos de trabajo y tareas programadas.
- Airflow DB: Metadatos de Airflow.
- Seq: Agregador centralizado de logs estructurados.
- Observabilidad: Prometheus y Node Exporter para métricas, monitorización y alertas.

El tráfico externo llega a través de un Load Balancer gestionado por Oracle, pasa por un Ingress (nginx) y se enruta a los servicios internos según reglas declarativas.

## Proceso de despliegue y automatización

1. **Repositorio GitHub**: contiene el código fuente, Dockerfiles, manifiestos YAML de Kubernetes y scripts de automatización.
2. **GitHub Actions**: automatiza el build, push y despliegue en OKE tras cada push a main/hito5, garantizando integración y entrega continua.
3. **OCI CLI y kubectl**: scripts reproducibles para crear el namespace, aplicar recursos y gestionar secretos.
4. **Manifiestos YAML y Kustomize**: definen deployments, servicios, ingress, configmaps y secrets, permitiendo reproducir el entorno desde cero.
5. **Secrets y credenciales**: gestionados de forma segura mediante GitHub Secrets y Kubernetes Secrets.

## Pasos principales para el despliegue

- Crear cuenta en Oracle Cloud y configurar la CLI y kubectl.
- Crear el clúster OKE en la región europea.
- Configurar los secrets necesarios en GitHub y en el clúster.
- Ejecutar los scripts y aplicar los manifiestos YAML con Kustomize.
- Verificar el estado de los pods y servicios con kubectl.
- Acceder a los servicios expuestos (API, Airflow, Seq, Prometheus) mediante las IPs públicas asignadas por el Load Balancer.

## Observabilidad y monitorización

- **Prometheus**: desplegado vía YAML, monitoriza métricas de nodos y pods, permitiendo detectar cuellos de botella y analizar el desempeño.
- **Node Exporter**: expone métricas de CPU, RAM, disco y red de los nodos del clúster.
- **Seq**: centraliza y estructura los logs de la aplicación para facilitar el análisis de errores y eventos.
- **Airflow UI**: permite monitorizar la ejecución de DAGs y tareas programadas.

## Ventajas del enfoque Kubernetes en OKE

- Despliegue reproducible y portable en cualquier proveedor compatible con Kubernetes.
- Escalabilidad horizontal y vertical según la carga y necesidades.
- Alta disponibilidad y tolerancia a fallos gracias a la orquestación automática de pods y nodos.
- Integración sencilla con herramientas de observabilidad, monitorización y logging.
- Coste cero para el alcance académico gracias al Always Free Tier de Oracle.

---

## Arquitectura

```
                                    ┌─────────────────────────────────────────────────────────────┐
                                    │                 ORACLE CLOUD KUBERNETES (OKE)                │
                                    │                    (eu-frankfurt-1 - EU)                     │
┌─────────────┐                     │   ┌─────────────────────────────────────────────────────┐   │
│   Usuario   │                     │   │                 Namespace: alert-manager             │   │
│   (Client)  │                     │   │                                                      │   │
└──────┬──────┘                     │   │  ┌─────────────┐    ┌─────────────────────────────┐ │   │
       │                            │   │  │   Ingress   │    │        API FastAPI          │ │   │
       │ HTTPS                      │   │  │   (nginx)   │───▶│   ┌───────┐   ┌───────┐    │ │   │
       │                            │   │  └─────────────┘    │   │ Pod 1 │   │ Pod 2 │    │ │   │
       ▼                            │   │                      │   └───┬───┘   └───┬───┘    │ │   │
┌──────────────┐                    │   │                      └───────┼─────────┼─────────┘ │   │
│ LoadBalancer │────────────────────┼───┼──────────────────────────────┘         │           │   │
│ (OCI Flex)   │                    │   │                                        │           │   │
└──────────────┘                    │   │  ┌─────────────────────────────────────┼─────────┐ │   │
                                    │   │  │           PostgreSQL                 │         │ │   │
                                    │   │  │   ┌───────────┐                     │         │ │   │
                                    │   │  │   │   Pod     │◀────────────────────┘         │ │   │
                                    │   │  │   └─────┬─────┘                               │ │   │
                                    │   │  │         │                                     │ │   │
                                    │   │  │   ┌─────▼─────┐                               │ │   │
                                    │   │  │   │    PVC    │ (oci-bv - Block Volume)       │ │   │
                                    │   │  │   └───────────┘                               │ │   │
                                    │   │  └───────────────────────────────────────────────┘ │   │
                                    │   │                                                      │   │
                                    │   │  ┌─────────────────────────────────────────────────┐ │   │
                                    │   │  │                    Airflow                       │ │   │
                                    │   │  │   ┌───────────────┐   ┌──────────────┐          │ │   │
                                    │   │  │   │   Webserver   │   │  Scheduler   │          │ │   │
                                    │   │  │   │     Pod       │   │     Pod      │          │ │   │
                                    │   │  │   └───────┬───────┘   └──────┬───────┘          │ │   │
                                    │   │  │           │                  │                  │ │   │
                                    │   │  │           └────────┬─────────┘                  │ │   │
                                    │   │  │                    ▼                            │ │   │
                                    │   │  │            ┌───────────────┐                    │ │   │
                                    │   │  │            │  Airflow DB   │                    │ │   │
                                    │   │  │            │  (PostgreSQL) │                    │ │   │
                                    │   │  │            └───────────────┘                    │ │   │
                                    │   │  └─────────────────────────────────────────────────┘ │   │
                                    │   │                                                      │   │
                                    │   │  ┌─────────────────────────────────────────────────┐ │   │
                                    │   │  │              Observabilidad                      │ │   │
                                    │   │  │   ┌───────────────┐                             │ │   │
                                    │   │  │   │     Seq       │  (Logs estructurados)       │ │   │
                                    │   │  │   │     Pod       │                             │ │   │
                                    │   │  │   └───────────────┘                             │ │   │
                                    │   │  └─────────────────────────────────────────────────┘ │   │
                                    │   │                                                      │   │
                                    │   └──────────────────────────────────────────────────────┘   │
                                    └─────────────────────────────────────────────────────────────┘
```

### Componentes

| Componente | Descripción | Réplicas |
|------------|-------------|----------|
| **API FastAPI** | Servicio principal de alertas | 2 |
| **PostgreSQL** | Base de datos principal | 1 |
| **Airflow Webserver** | Interfaz web de Airflow | 1 |
| **Airflow Scheduler** | Programador de DAGs | 1 |
| **Airflow DB** | Metadatos de Airflow | 1 |
| **Seq** | Agregador de logs | 1 |

