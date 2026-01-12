# Configuración de AEMET API Key en GitHub Secrets y Airflow

## El endpoint funciona con autenticación

Cuando se usa la API key del JWT, el endpoint retorna una estructura con URLs para descargar los datos:

```json
{
  "descripcion": "exito",
  "estado": 200,
  "datos": "https://opendata.aemet.es/opendata/sh/xxxxx",
  "metadatos": "https://opendata.aemet.es/opendata/sh/yyyyy"
}
```

El archivo `datos` es un **TAR sin compresión** que contiene cientos de archivos XML en formato **CAP** (Common Alerting Protocol).


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
