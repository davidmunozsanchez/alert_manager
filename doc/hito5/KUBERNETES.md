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

1. **Repositorio GitHub**: Contiene el código fuente, Dockerfiles, manifiestos YAML de Kubernetes y scripts de automatización.
2. **GitHub Actions**: Automatiza el build, push y despliegue en OKE tras cada push a main/hito5, garantizando integración y entrega continua.
3. **OCI CLI y kubectl**: Scripts reproducibles para crear el namespace, aplicar recursos y gestionar secretos.
4. **Manifiestos YAML y Kustomize**: Definen deployments, servicios, ingress, configmaps y secrets, permitiendo reproducir el entorno desde cero.
5. **Secrets y credenciales**: Gestionados de forma segura mediante GitHub Secrets y Kubernetes Secrets.

## Pasos principales para el despliegue

- Crear cuenta en Oracle Cloud y configurar la CLI y kubectl.
- Crear el clúster OKE en la región europea.
- Configurar los secrets necesarios en GitHub y en el clúster.
- Ejecutar los scripts y aplicar los manifiestos YAML con Kustomize.
- Verificar el estado de los pods y servicios con kubectl.
- Acceder a los servicios expuestos (API, Airflow, Seq, Prometheus) mediante las IPs públicas asignadas por el Load Balancer.

## Observabilidad y monitorización

- **Prometheus**: Desplegado vía YAML, monitoriza métricas de nodos y pods, permitiendo detectar cuellos de botella y analizar el desempeño.
- **Node Exporter**: Expone métricas de CPU, RAM, disco y red de los nodos del clúster.
- **Seq**: Centraliza y estructura los logs de la aplicación para facilitar el análisis de errores y eventos.
- **Airflow UI**: Permite monitorizar la ejecución de DAGs y tareas programadas.

## Ventajas del enfoque Kubernetes en OKE

- Despliegue reproducible y portable en cualquier proveedor compatible con Kubernetes.
- Escalabilidad horizontal y vertical según la carga y necesidades.
- Alta disponibilidad y tolerancia a fallos gracias a la orquestación automática de pods y nodos.
- Integración sencilla con herramientas de observabilidad, monitorización y logging.
- Coste cero para el alcance académico gracias al Always Free Tier de Oracle.

## Consideraciones finales

Este despliegue demuestra la transición de un entorno de desarrollo local basado en Docker Compose a un entorno de producción real gestionado por Kubernetes, cumpliendo los requisitos de automatización, reproducibilidad, observabilidad y resiliencia exigidos en el hito.

Para detalles técnicos, comandos y troubleshooting, consulta las secciones siguientes del documento y los archivos YAML y scripts del repositorio.

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

---

## Requisitos Previos

### 1. Crear cuenta en Oracle Cloud

1. Ir a [cloud.oracle.com](https://cloud.oracle.com)
2. Registrarse con **Free Tier** (no requiere tarjeta para recursos Always Free)
3. Seleccionar **Frankfurt (eu-frankfurt-1)** como Home Region

### 2. Instalar OCI CLI

```bash
# Linux/macOS
bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"

# Windows (PowerShell)
Invoke-WebRequest https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.ps1 -OutFile install.ps1
./install.ps1

# Configurar credenciales
oci setup config
```

### 3. Instalar kubectl

```bash
# Linux
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install kubectl /usr/local/bin/kubectl

# macOS
brew install kubectl

# Windows
winget install Kubernetes.kubectl
```

### Secrets de GitHub necesarios

Configura estos secrets en tu repositorio (`Settings > Secrets and variables > Actions`):

| Secret | Descripción | Cómo obtenerlo |
|--------|-------------|----------------|
| `OKE_CLUSTER_OCID` | OCID del cluster | Output del script de creación |
| `OCI_TENANCY_OCID` | OCID del tenancy | `oci iam tenancy get` |
| `OCI_USER_OCID` | OCID del usuario | `oci iam user list` |
| `OCI_FINGERPRINT` | Fingerprint de la API key | En `~/.oci/config` |
| `OCI_PRIVATE_KEY` | Contenido de la API key privada | En `~/.oci/oci_api_key.pem` |
| `POSTGRES_PASSWORD` | Contraseña de PostgreSQL | Tu elección |
| `AIRFLOW_ADMIN_PASSWORD` | Contraseña del admin de Airflow | Tu elección |
| `AEMET_API_KEY` | API key de AEMET | [opendata.aemet.es](https://opendata.aemet.es) |
| `FIREBASE_CREDENTIALS` | JSON de credenciales Firebase (base64) | Firebase Console |

---

## Configuración del Cluster

### Crear cluster automáticamente

```bash
# Configurar compartment ID
export OCI_COMPARTMENT_ID=ocid1.compartment.oc1..xxxxx

# Dar permisos de ejecución
chmod +x deploy/create-k8s-cluster.sh

# Ejecutar script
./deploy/create-k8s-cluster.sh alert-manager-cluster
```

### Crear cluster manualmente (Console)

1. Ir a **Oracle Cloud Console** → **Developer Services** → **Kubernetes Clusters (OKE)**
2. Click **Create Cluster** → **Quick Create**
3. Configurar:
   - **Name**: `alert-manager-cluster`
   - **Kubernetes Version**: `v1.29.1`
   - **Node Shape**: `VM.Standard.A1.Flex` (ARM - Always Free)
   - **OCPUs**: 2 por nodo
   - **Memory**: 12 GB por nodo
   - **Number of nodes**: 2
4. Click **Create**

### Configurar kubectl

```bash
# Obtener kubeconfig
oci ce cluster create-kubeconfig \
    --cluster-id <CLUSTER_OCID> \
    --file $HOME/.kube/config \
    --region eu-frankfurt-1 \
    --token-version 2.0.0 \
    --kube-endpoint PUBLIC_ENDPOINT

# Verificar conexión
kubectl get nodes
```

---

## Despliegue

### Despliegue automático (GitHub Actions)

El despliegue se ejecuta automáticamente en cada push a `main`:

```yaml
# .github/workflows/deploy-kubernetes.yml
on:
  push:
    branches: [main]
```

También puedes ejecutarlo manualmente desde la pestaña "Actions" de GitHub.

### Despliegue manual

```bash
# 1. Crear secrets
kubectl create secret generic alert-manager-secrets \
    --namespace alert-manager \
    --from-literal=POSTGRES_PASSWORD='tu-password' \
    --from-literal=AIRFLOW_ADMIN_PASSWORD='tu-password' \
    --from-literal=AEMET_API_KEY='tu-api-key' \
    --from-literal=FIREBASE_CREDENTIALS='tu-json-base64'

# 2. Crear secret del registry
kubectl create secret docker-registry ghcr-credentials \
    --namespace alert-manager \
    --docker-server=ghcr.io \
    --docker-username=tu-usuario \
    --docker-password=tu-github-token

# 3. Aplicar manifiestos con Kustomize
kubectl apply -k k8s/

# 4. Verificar despliegue
kubectl get pods -n alert-manager -w
```

---

## Monitorización

### Acceder a Seq (Logs)

```bash
# Obtener IP externa de Seq
kubectl get svc seq-external -n alert-manager

# Abrir en navegador: http://<IP>:5341
```

### Acceder a Airflow

```bash
# Obtener IP externa de Airflow
kubectl get svc airflow-webserver -n alert-manager

# Abrir en navegador: http://<IP>:8080
# Usuario: admin
# Password: (el configurado en secrets)
```

### Ver logs de la API

```bash
# Logs en tiempo real
kubectl logs -f deployment/alert-manager-api -n alert-manager

# Logs de todos los pods de la API
kubectl logs -l app=alert-manager-api -n alert-manager --all-containers
```

### Métricas del cluster

```bash
# Uso de recursos por pod
kubectl top pods -n alert-manager

# Uso de recursos por nodo
kubectl top nodes
```

---

## Comandos Útiles

### Gestión de Pods

```bash
# Listar pods
kubectl get pods -n alert-manager

# Describir un pod (debugging)
kubectl describe pod <pod-name> -n alert-manager

# Entrar en un pod
kubectl exec -it <pod-name> -n alert-manager -- /bin/bash

# Reiniciar deployment
kubectl rollout restart deployment/alert-manager-api -n alert-manager
```

### Gestión de Secrets

```bash
# Ver secrets
kubectl get secrets -n alert-manager

# Editar un secret
kubectl edit secret alert-manager-secrets -n alert-manager

# Decodificar un valor del secret
kubectl get secret alert-manager-secrets -n alert-manager \
    -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d
```

### Scaling

```bash
# Escalar la API
kubectl scale deployment alert-manager-api --replicas=3 -n alert-manager

# Ver estado del HPA (si está configurado)
kubectl get hpa -n alert-manager
```

### Networking

```bash
# Ver servicios
kubectl get svc -n alert-manager

# Ver ingress
kubectl get ingress -n alert-manager

# Port-forward para acceso local
kubectl port-forward svc/alert-manager-api 8000:8000 -n alert-manager
```

---

## Troubleshooting

### Pod en estado CrashLoopBackOff

```bash
# Ver logs del pod
kubectl logs <pod-name> -n alert-manager --previous

# Describir el pod para ver eventos
kubectl describe pod <pod-name> -n alert-manager
```

### Pod en estado Pending

```bash
# Verificar recursos disponibles
kubectl describe nodes

# Ver eventos del namespace
kubectl get events -n alert-manager --sort-by='.lastTimestamp'
```

### Problemas de conexión a la base de datos

```bash
# Verificar que PostgreSQL está corriendo
kubectl get pods -l app=postgres -n alert-manager

# Verificar logs de PostgreSQL
kubectl logs -l app=postgres -n alert-manager

# Testear conectividad desde otro pod
kubectl run -it --rm debug --image=postgres:15 -n alert-manager -- \
    psql -h postgres -U postgres -d alertmanager
```

### LoadBalancer sin IP externa

```bash
# Puede tardar unos minutos, verificar estado
kubectl get svc -n alert-manager -w

# Verificar eventos del servicio
kubectl describe svc alert-manager-api -n alert-manager
```

### Nodos ARM no disponibles

Si los nodos ARM (A1.Flex) no están disponibles en tu región:

```bash
# Verificar disponibilidad
oci compute shape list --compartment-id $OCI_COMPARTMENT_ID \
    --query "data[?contains(shape, 'A1')]"

# Alternativa: usar nodos AMD (no gratuitos)
# Cambiar NODE_SHAPE en el script a VM.Standard.E4.Flex
```

---

## Comparación de Costes

| Proveedor | Control Plane | Nodos (2x2CPU/4GB) | Storage | Total/mes |
|-----------|---------------|-------------------|---------|-----------|
| **Oracle OKE** | $0 | $0 (ARM Free) | $0 | **$0** ✨ |
| DigitalOcean | $0 | $48 | $1 | ~$49 |
| GKE | $0 | $50+ | $2 | ~$52 |
| EKS | $72 | $60+ | $2 | ~$134 |

---

## Referencias

- [Oracle OKE Documentation](https://docs.oracle.com/en-us/iaas/Content/ContEng/home.htm)
- [OCI CLI Reference](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/)
- [Oracle Always Free Tier](https://www.oracle.com/cloud/free/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [NGINX Ingress Controller](https://kubernetes.github.io/ingress-nginx/)
