# Configuración de AEMET API Key en GitHub Secrets y Airflow

## El endpoint funciona con autenticación

Cuando usas la API key del JWT, el endpoint retorna una estructura con URLs para descargar los datos:

```json
{
  "descripcion": "exito",
  "estado": 200,
  "datos": "https://opendata.aemet.es/opendata/sh/xxxxx",
  "metadatos": "https://opendata.aemet.es/opendata/sh/yyyyy"
}
```

El archivo `datos` es un **TAR sin compresión** que contiene cientos de archivos XML en formato **CAP** (Common Alerting Protocol).

---

## Paso 1: Agregar la API Key a GitHub Secrets

⚠️ **Para instrucciones detalladas sobre GitHub Secrets**, ver [GITHUB_SECRETS_SETUP.md](GITHUB_SECRETS_SETUP.md)

### Resumen rápido:

1. Ve a tu repositorio en GitHub: `https://github.com/tu-usuario/alert_manager`
2. **Settings** → **Secrets and variables** → **Actions**
3. **New repository secret**
   - **Name**: `AEMET_API_KEY`
   - **Value**: Tu API key JWT
4. **Add secret**

## Paso 2: Usar el Secret en Airflow (Docker)

### Para desarrollo local:

```bash
export AEMET_API_KEY="tu_api_key_aqui"
cd docker/
docker-compose up
```

O sin exportar:

```bash
cd docker/
AEMET_API_KEY="tu_api_key_aqui" docker-compose up
```

### En CI/CD (GitHub Actions):

Ver [GITHUB_SECRETS_SETUP.md](GITHUB_SECRETS_SETUP.md) para instrucciones completas.

### En Airflow UI (Recomendado para producción):

1. Abre la UI de Airflow: `http://localhost:8080`
2. Ve a **Admin** → **Variables**
3. Haz clic en **+**
4. **Key**: `AEMET_API_KEY`
5. **Value**: Tu API key
6. **Save**

---

## Cómo acceden los DAGs a la variable

Los DAGs automáticamente buscan la variable en este orden:

1. **Airflow Variables** (`Variable.get("AEMET_API_KEY")`) - ✅ Más seguro
2. **Variables de entorno** (`os.getenv("AEMET_API_KEY")`) - Fallback

### En código:

```python
from airflow.models import Variable

api_key = Variable.get("AEMET_API_KEY", default=None)
if not api_key:
    raise RuntimeError("AEMET_API_KEY no configurada")
```

---

## Estado actual

El archivo `docker-compose.yml` ha sido actualizado para pasar `AEMET_API_KEY` a:
- ✅ `airflow-init`
- ✅ `airflow-webserver`
- ✅ `airflow-scheduler`

Esto permite que los DAGs accedan a la variable automáticamente.

---

## Información sobre el DAG creado

### Archivo: [src/dags/aemet_alerts_ingestion.py](src/dags/aemet_alerts_ingestion.py)

El DAG realiza tres operaciones principales:

#### 1. **`fetch_aemet_alerts_from_opendata`**: Obtención y procesamiento de datos
   
   - 🔐 **Autenticación**: Usa el API key JWT para autenticarse
   - 📥 **Descarga**: Obtiene URL del archivo TAR desde AEMET
   - 📦 **Extracción**: Descomprime el TAR y extrae todos los XMLs
   - 🔄 **Parsing**: Convierte XMLs CAP a formato JSON normalizado
   - 💾 **Guardado**: Genera archivo `/opt/airflow/dags/aemet_alerts.json`

#### 2. **`parse_cap_xml`**: Procesamiento de XMLs en formato CAP
   
   - Parsea el namespace CAP estándar
   - Extrae información: evento, nivel, región, área, coordenadas
   - Interpreta los parámetros específicos de AEMET
   - Normaliza a estructura JSON uniforme

#### 3. **`validate_and_insert_aemet_alerts`**: Validación e inserción

   - ✅ **Validación**: Verifica campos requeridos y rangos de coordenadas
   - 🗄️ **Inserción**: Inserta alertas en tabla `alerts` de PostgreSQL
   - 🔄 **Deduplicación**: Usa `ON CONFLICT DO NOTHING` para evitar duplicados

### Campos procesados del XML CAP

```json
{
  "title": "Aviso de nevadas de nivel naranja",
  "description": "Acumulación de nieve en 24 horas: 10 cm",
  "level": "naranja|rojo|amarillo|verde",
  "type": "Met",
  "region": "Centro y valle de Villaverde",
  "status": "active|expired",
  "expires_at": "2026-01-06T11:59:59+01:00",
  "latitude": 43.27,
  "longitude": -4.55,
  "identifier": "2.49.0.0.724.0.ES...",
  "sent": "2026-01-05T17:46:46-00:00"
}
```

### Configuración actual

- **Frecuencia**: Cada hora (`0 * * * *`)
- **Base de datos**: PostgreSQL en `db:5432`
- **Usuario**: `postgres` / password: `postgres`
- **Base de datos**: `alerts`
- **Área**: `esp` (España)
- **Autenticación**: API key JWT requerida

---

## Estructura actual

El endpoint `/opendata/api/avisos_cap/ultimoelaborado/area/esp` devuelve:

- **Con autenticación**: URLs para descargar datos
  - URL de datos: Archivo TAR ~4MB con 300+ XMLs CAP
  - URL de metadatos: Información adicional
  
- **Sin autenticación**: Respuesta vacía (200 OK pero sin contenido)

### Archivos XML en el TAR

Los XMLs tiene nombres como:
- `Z_CAP_C_LEMM_20260105174646_AFAZ663903NENV0611.xml`
- `Z_CAP_C_LEMM_20260105174646_AFAZ750101NENV0611.xml`
- etc.

Cada XML contiene una alerta individual en formato CAP 1.2 con:
- Identificador único
- Descripción del evento
- Nivel (rojo/naranja/amarillo/verde)
- Área geográfica (polígono)
- Fechas de efectividad y expiración
- Parámetros específicos de AEMET

---

## Nota importante

⚠️ **El DAG está completamente funcional**. El flujo es:

1. ✅ Se autentica con la API key
2. ✅ Obtiene el TAR comprimido (~4MB)
3. ✅ Extrae y procesa 300+ archivos XML
4. ✅ Normaliza los datos a JSON
5. ✅ Valida e inserta en PostgreSQL

**No hay datos de demostración necesarios** - el DAG funciona con datos reales de AEMET cuando se ejecuta.

---

## Troubleshooting

### "AEMET_API_KEY no encontrada"
- Verifica que esté en GitHub Secrets
- Asegúrate de que esté también en la variable de entorno de Docker
- En la UI de Airflow, ve a Admin → Variables y verifica que exista

### "Conexión rechazada a PostgreSQL"
- Verifica que el contenedor `db` está corriendo: `docker ps`
- Revisa los logs: `docker-compose logs db`

### "El DAG no aparece en Airflow"
- Reinicia Airflow: `docker-compose restart webserver scheduler`
- Verifica que el archivo está en `docker/dags/` (se monta en Docker)
