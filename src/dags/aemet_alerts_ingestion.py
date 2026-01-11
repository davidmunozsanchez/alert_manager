import json
import os
import traceback
import tarfile
import io
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Any, Optional

import psycopg2
import requests
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable


def fetch_aemet_alerts_from_opendata() -> str:
    """
    Obtiene los últimos avisos CAP de AEMET OpenData.
    
    Flujo:
    1. Autentica con API key
    2. Obtiene URL de descarga de TAR
    3. Descarga el archivo TAR
    4. Extrae XMLs
    5. Convierte XMLs a JSON normalizado
    6. Guarda en archivo para siguiente tarea
    """
    try:
        print("🔐 Iniciando obtención de datos de AEMET con autenticación...")
        
        # Obtener API key desde Airflow Variable o env
        api_key = None
        try:
            api_key = Variable.get("AEMET_API_KEY")
        except Exception as e:
            print(f"⚠️  No se pudo leer de Variable: {e}")
            api_key = os.getenv("AEMET_API_KEY")
        
        if not api_key:
            print("⚠️  AEMET_API_KEY no configurada. Usando datos de demostración.")
            demo_data = [
                {
                    "title": "Alerta Meteorológica - Viento",
                    "description": "Vientos fuertes en el litoral",
                    "level": "naranja",
                    "type": "wind",
                    "region": "Cataluña",
                    "status": "active",
                    "expires_at": "2026-01-06T12:00:00Z",
                    "latitude": 41.5,
                    "longitude": 1.5
                }
            ]
            output_path = "/opt/airflow/dags/aemet_alerts.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(demo_data, f, indent=2, ensure_ascii=False)
            return output_path
        
        # Paso 1: Obtener URL con autenticación
        url = "https://opendata.aemet.es/opendata/api/avisos_cap/ultimoelaborado/area/esp"
        print(f"Llamando a: {url}")
        
        auth_response = requests.get(
            url,
            headers={"api_key": api_key},
            timeout=30
        )
        
        if auth_response.status_code != 200:
            raise Exception(f"Error en autenticación: {auth_response.status_code}")
        
        auth_data = auth_response.json()
        print(f"✅ Respuesta AEMET: {auth_data.get('descripcion')}")
        
        # Paso 2: Descargar TAR
        data_url = auth_data.get("datos")
        if not data_url:
            print("⚠️  No hay datos disponibles en AEMET")
            return None
        
        print(f"📥 Descargando archivo TAR desde AEMET ({len(data_url)} bytes de URL)...")
        tar_response = requests.get(data_url, timeout=60)
        
        if tar_response.status_code != 200:
            raise Exception(f"Error descargando TAR: {tar_response.status_code}")
        
        print(f"✅ TAR descargado: {len(tar_response.content)} bytes")
        
        # Paso 3: Extraer y procesar XMLs
        print("📦 Extrayendo y procesando XMLs...")
        tar_bytes = io.BytesIO(tar_response.content)
        tar = tarfile.open(fileobj=tar_bytes, mode='r')
        
        alerts_list = []
        xml_members = [m for m in tar.getmembers() if m.name.endswith('.xml')]
        print(f"Encontrados {len(xml_members)} archivos XML")
        
        for xml_member in xml_members:
            try:
                f = tar.extractfile(xml_member)
                xml_content = f.read().decode('utf-8')
                
                # Parsear CAP XML
                alert_data = parse_cap_xml(xml_content)
                if alert_data:
                    alerts_list.append(alert_data)
            except Exception as e:
                print(f"⚠️  Error procesando {xml_member.name}: {e}")
                continue
        
        tar.close()
        
        print(f"✅ {len(alerts_list)} alertas extraídas y procesadas")
        
        # Paso 4: Guardar JSON
        output_path = "/opt/airflow/dags/aemet_alerts.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(alerts_list, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Datos guardados en {output_path}")
        return output_path
        
    except Exception as e:
        print(f"❌ Error en obtención de datos:")
        traceback.print_exc()
        raise


def parse_cap_xml(xml_content: str) -> Optional[Dict[str, Any]]:
    """
    Parsea un archivo XML en formato CAP (Common Alerting Protocol)
    y lo convierte a formato normalizado.
    """
    try:
        # Namespaces en CAP
        ns = {'cap': 'urn:oasis:names:tc:emergency:cap:1.2'}
        
        root = ET.fromstring(xml_content)
        
        # Extraer información principal
        identifier = root.findtext('cap:identifier', namespaces=ns) or ""
        sent = root.findtext('cap:sent', namespaces=ns) or ""
        
        # Buscar elemento info
        info = root.find('cap:info', namespaces=ns)
        if info is None:
            return None
        
        # Extraer datos del info
        event = info.findtext('cap:event', namespaces=ns) or "Desconocido"
        headline = info.findtext('cap:headline', namespaces=ns) or ""
        description = info.findtext('cap:description', namespaces=ns) or ""
        
        # Nivel y categoría
        severity = info.findtext('cap:severity', namespaces=ns) or "Unknown"
        category = info.findtext('cap:category', namespaces=ns) or "Met"
        
        # Fechas
        onset = info.findtext('cap:onset', namespaces=ns) or ""
        expires = info.findtext('cap:expires', namespaces=ns) or ""
        
        # Área
        area = info.find('cap:area', namespaces=ns)
        area_desc = ""
        latitude = 0.0
        longitude = 0.0
        
        if area is not None:
            area_desc = area.findtext('cap:areaDesc', namespaces=ns) or "España"
            
            # Extraer primer punto de polígono si existe
            polygon_text = area.findtext('cap:polygon', namespaces=ns)
            if polygon_text:
                try:
                    first_point = polygon_text.split()[0]
                    latitude, longitude = map(float, first_point.split(','))
                except:
                    latitude = 40.0
                    longitude = -3.0  # Coordenadas de Madrid como default
        
        # Mapear nivel AEMET a formato normalizado
        level_map = {
            'Extreme': 'emergency',
            'Severe': 'critical',
            'Moderate': 'warning',
            'Minor': 'info',
            'Unknown': 'info'
        }
        
        # Extraer nivel de parámetros AEMET si existe
        level = 'naranja'  # Default
        for param in info.findall('cap:parameter', namespaces=ns):
            param_name = param.findtext('cap:valueName', namespaces=ns) or ""
            param_value = param.findtext('cap:value', namespaces=ns) or ""
            
            if "AEMET-Meteoalerta nivel" in param_name:
                level = param_value
                break
        
        # Aplicar mapeo
        mapped_level = level_map.get(level, 'info')
        
        # Mapear tipo de categoría CAP
        type_map = {
            'met': 'weather',
            'fire': 'fire',
            'security': 'security',
            'rescue': 'infrastructure',
            'health': 'health',
            'env': 'natural_disaster',
            'transport': 'traffic',
            'infra': 'infrastructure',
            'cbaci': 'other',
            'other': 'other'
        }
        mapped_type = type_map.get(category.lower(), 'weather')
        
        alert_data = {
            "title": event,
            "description": headline or description,
            "level": mapped_level,
            "type": mapped_type,
            "region": area_desc,
            "status": "active",
            "expires_at": expires or "",
            "latitude": latitude,
            "longitude": longitude,
            "identifier": identifier,
            "sent": sent
        }
        
        return alert_data
        
    except Exception as e:
        print(f"❌ Error parseando XML: {e}")
        return None


def validate_and_insert_aemet_alerts() -> None:
    """
    Valida las alertas AEMET e inserta en PostgreSQL.
    """
    import time
    
    try:
        print("Iniciando validación e inserción de alertas AEMET...")
        
        json_path = "/opt/airflow/dags/aemet_alerts.json"
        if not os.path.exists(json_path):
            print("⚠️  Archivo de alertas no encontrado. Abortando.")
            return
        
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            data = [data]
        
        print(f"Procesando {len(data)} alertas...")
        
        valid_alerts = []
        invalid_alerts = []
        
        # Validar alertas
        required_fields = [
            "title", "description", "level", "type",
            "region", "status", "expires_at", "latitude", "longitude"
        ]
        
        for idx, alert in enumerate(data):
            errors = []
            
            # Verificar campos requeridos
            for field in required_fields:
                if field not in alert:
                    errors.append(f"Campo faltante: {field}")
            
            # Validar coordenadas
            if "latitude" in alert:
                try:
                    lat = float(alert["latitude"])
                    if not (-90 <= lat <= 90):
                        errors.append(f"Latitud fuera de rango: {lat}")
                except (ValueError, TypeError):
                    errors.append(f"Latitud inválida: {alert.get('latitude')}")
            
            if "longitude" in alert:
                try:
                    lon = float(alert["longitude"])
                    if not (-180 <= lon <= 180):
                        errors.append(f"Longitud fuera de rango: {lon}")
                except (ValueError, TypeError):
                    errors.append(f"Longitud inválida: {alert.get('longitude')}")
            
            if errors:
                invalid_alerts.append({"index": idx, "alert": alert, "errors": errors})
            else:
                valid_alerts.append(alert)
        
        print(f"✅ Validación: {len(valid_alerts)} válidas, {len(invalid_alerts)} inválidas")
        
        if not valid_alerts:
            print("⚠️  No hay alertas válidas para insertar.")
            return
        
        # Conectar a PostgreSQL con reintentos
        conn = None
        max_retries = 10
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                conn = psycopg2.connect(
                    dbname="alert_manager",
                    user="postgres",
                    password="postgres",
                    host="db",
                    port=5432
                )
                print(f"✅ Conexión a PostgreSQL establecida en intento {attempt + 1}")
                break
            except psycopg2.Error as e:
                print(f"⏳ Error conectando a PostgreSQL (intento {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    print(f"   Esperando {retry_delay}s antes de reintentar...")
                    time.sleep(retry_delay)
                else:
                    print(f"❌ No se pudo conectar a PostgreSQL después de {max_retries} intentos")
                    raise
        
        cur = conn.cursor()
        
        # Verificar que la tabla existe
        print("🔍 Verificando que la tabla 'alerts' existe...")
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'alerts'
            )
        """)
        table_exists = cur.fetchone()[0]
        
        if not table_exists:
            print("⚠️  Tabla 'alerts' no existe aún. Esperando a que se cree...")
            conn.close()
            print("   Esperando 30s para que FastAPI inicialice la BD...")
            time.sleep(30)
            
            # Reconectar
            for attempt in range(3):
                try:
                    conn = psycopg2.connect(
                        dbname="alert_manager",
                        user="postgres",
                        password="postgres",
                        host="db",
                        port=5432
                    )
                    cur = conn.cursor()
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.tables 
                            WHERE table_name = 'alerts'
                        )
                    """)
                    table_exists = cur.fetchone()[0]
                    if table_exists:
                        print("✅ Tabla 'alerts' ahora existe")
                        break
                except Exception as e:
                    print(f"⏳ Reintentando... ({attempt + 1}/3): {e}")
                    time.sleep(10)
            
            if not table_exists:
                print("❌ La tabla 'alerts' sigue sin existir. Abortando.")
                if conn:
                    conn.close()
                return
        
        # PASO 1: Borrar solo las alertas de AEMET anteriores
        print("🗑️  Borrando alertas AEMET anteriores...")
        try:
            cur.execute("DELETE FROM alerts WHERE source = %s", ("aemet_opendata",))
            deleted_count = cur.rowcount
            conn.commit()
            print(f"✅ {deleted_count} alertas AEMET eliminadas")
        except Exception as e:
            print(f"⚠️  Error al borrar alertas: {e}")
            conn.rollback()
        
        # PASO 2: Insertar nuevas alertas de AEMET
        print("📝 Insertando nuevas alertas AEMET...")
        inserted_count = 0
        for alert in valid_alerts:
            try:
                cur.execute(
                    """
                    INSERT INTO alerts (
                        title, description, level, type, region, status,
                        expires_at, timestamp, latitude, longitude, source
                    ) VALUES (
                        %(title)s, %(description)s, %(level)s, %(type)s,
                        %(region)s, %(status)s, %(expires_at)s, NOW(),
                        %(latitude)s, %(longitude)s, %(source)s
                    )
                """,
                    {
                        "title": str(alert.get("title", ""))[:200],
                        "description": str(alert.get("description", ""))[:1000],
                        "level": str(alert.get("level", ""))[:50],
                        "type": str(alert.get("type", ""))[:50],
                        "region": str(alert.get("region", ""))[:200],
                        "status": str(alert.get("status", ""))[:50],
                        "expires_at": alert.get("expires_at") or None,
                        "latitude": float(alert.get("latitude", 0)),
                        "longitude": float(alert.get("longitude", 0)),
                        "source": "aemet_opendata"
                    }
                )
                inserted_count += 1
            except Exception as e:
                print(f"⚠️  Error insertando alerta: {e}")
                continue
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ {inserted_count} alertas insertadas en la base de datos.")
        
    except psycopg2.Error as e:
        print(f"❌ Error de conexión a PostgreSQL: {e}")
        raise
    
    except Exception as e:
        print(f"❌ Error durante validación:")
        traceback.print_exc()
        raise


# Definir el DAG
with DAG(
    dag_id="aemet_alerts_ingestion",
    start_date=datetime.today(),
    schedule_interval="*/15 * * * *",  # Cada 15 minutos
    catchup=False,
    description="Obtiene alertas CAP de AEMET OpenData y las inserta en PostgreSQL",
    tags=["aemet", "alerts", "ingestion", "opendata"]
) as dag:
    
    # Tarea 1: Obtener datos de AEMET
    fetch_task = PythonOperator(
        task_id="fetch_aemet_alerts",
        python_callable=fetch_aemet_alerts_from_opendata,
        doc="Descarga y procesa XMLs CAP de AEMET OpenData"
    )
    
    # Tarea 2: Validar e insertar
    validate_task = PythonOperator(
        task_id="validate_and_insert",
        python_callable=validate_and_insert_aemet_alerts,
        doc="Valida alertas e inserta en PostgreSQL"
    )
    
    # Dependencias
    fetch_task >> validate_task
