# Quick Start - Ejecuta el proyecto YA

## 1️⃣ Obtén tu AEMET_API_KEY desde GitHub

Si ya lo tienes en GitHub Secrets, cópialo. Si no, ve a:
- GitHub Settings > Secrets and variables > Actions
- Busca `AEMET_API_KEY`

## 2️⃣ Ejecuta localmente

### En Windows (PowerShell)
```powershell
$env:AEMET_API_KEY="tu_api_key_aqui"
cd docker/
docker-compose up
```

### En Mac/Linux (Bash/Zsh)
```bash
export AEMET_API_KEY="tu_api_key_aqui"
cd docker/
docker-compose up
```

### Todo en una línea
```bash
cd docker/ && AEMET_API_KEY="tu_api_key_aqui" docker-compose up
```

## 3️⃣ Espera a que todo esté listo

Deberías ver en los logs:
- ✅ `db is ready`
- ✅ `Airflow init completed`
- ✅ `Starting Alert Manager with Seq logging...`

## 4️⃣ Accede a los servicios

| Servicio | URL | Usuario/Pass |
|----------|-----|-------------|
| Airflow | http://localhost:8080 | admin/admin |
| API Alert Manager | http://localhost:8000 | - |
| Seq Logs | http://localhost:5341 | - |
| PostgreSQL | localhost:5432 | postgres/postgres |

## 5️⃣ Ejecuta el DAG manualmente

1. Abre http://localhost:8080
2. En la columna izquierda busca "aemet_alerts_ingestion"
3. Haz clic en el DAG
4. Haz clic en el botón ▶️ para ejecutar

O usa la CLI:
```bash
docker-compose exec airflow-webserver airflow dags trigger aemet_alerts_ingestion
```

## 6️⃣ Verifica los logs

```bash
cd docker/
docker-compose logs airflow-scheduler -f
```

Deberías ver:
```
🔐 Iniciando obtención de datos de AEMET con autenticación...
✅ Respuesta AEMET: exito
📥 Descargando archivo TAR...
✅ TAR descargado: 4239360 bytes
📦 Extrayendo y procesando XMLs...
✅ 300+ alertas extraídas...