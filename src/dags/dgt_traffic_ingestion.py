"""
DAG for ingesting DGT Traffic data from eTraffic Web.
Extracts traffic information from each marker/sensor in the DGT eTraffic system.
Web Scraping: https://etraffic.dgt.es/etrafficWEB/

Workflow:
1. Extract markers from DGT eTraffic website
2. Process and structure the data
3. Delete existing DGT traffic data from database
4. Insert new traffic data into alerts table
5. Log ingestion results
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import logging
import asyncio
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.models import Variable
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configure logging
logger = logging.getLogger(__name__)

# Default DAG arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# DAG definition
dag = DAG(
    'dgt_traffic_ingestion',
    default_args=default_args,
    description='Ingest DGT Traffic data from eTraffic Web',
    schedule_interval='*/15 * * * *',  # Every 15 minutes
    catchup=False,
    tags=['dgt', 'traffic', 'ingestion'],
)


# Database configuration
DB_HOST = Variable.get('db_host', 'localhost')
DB_PORT = Variable.get('db_port', '5432')
DB_NAME = Variable.get('db_name', 'alerts_db')
DB_USER = Variable.get('db_user', 'admin')
DB_PASSWORD = Variable.get('db_password', '')

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
EXTRACTOR_SCRIPT = PROJECT_ROOT / "extract_dgt_markers_production.py"
OUTPUT_FILE = "/tmp/dgt_markers_extracted.json"

# Buscar el script en múltiples ubicaciones
POSSIBLE_PATHS = [
    PROJECT_ROOT / "extract_dgt_markers_production.py",
    Path("/opt") / "extract_dgt_markers_production.py",
    Path("/opt/airflow") / "extract_dgt_markers_production.py",
    Path("/") / "extract_dgt_markers_production.py",
]

def find_extractor_script() -> Path:
    """Find the extractor script in possible locations."""
    for path in POSSIBLE_PATHS:
        if path.exists():
            logger.info(f"Found extractor script at: {path}")
            return path
    
    # If not found, try to find it recursively
    logger.warning("Script not found in standard locations, searching...")
    for path in [Path("/opt"), Path("/home"), PROJECT_ROOT]:
        try:
            for found_path in path.rglob("extract_dgt_markers_production.py"):
                logger.info(f"Found extractor script at: {found_path}")
                return found_path
        except:
            continue
    
    raise FileNotFoundError(f"Cannot find extract_dgt_markers_production.py in {POSSIBLE_PATHS}")


def get_db_engine():
    """Create database engine."""
    return create_engine(DATABASE_URL, echo=False)


def extract_dgt_markers(**context) -> Dict[str, Any]:
    """
    Lee datos extraídos por el servicio Playwright extractor.
    
    Args:
        **context: Airflow context
        
    Returns:
        Dictionary with extraction results
    """
    logger.info("=" * 80)
    logger.info("TASK 1: LEYENDO DATOS EXTRAÍDOS (DGT MARKERS)")
    logger.info("=" * 80)
    
    try:
        from pathlib import Path
        
        # Buscar archivo de extracción en volumen compartido
        possible_paths = [
            Path("/extraction-output/dgt_markers_extracted.json"),
            Path("/tmp/extraction-output/dgt_markers_extracted.json"),
        ]
        
        output_file = None
        for path in possible_paths:
            if path.exists():
                output_file = path
                logger.info(f"✓ Archivo de extracción encontrado: {output_file}")
                break
        
        if not output_file:
            logger.warning(f"⚠ No se encontró archivo de extracción en {possible_paths}")
            # Crear archivo vacío para que el DAG no falle
            output_file = Path("/tmp/dgt_markers_extracted.json")
            data = {
                'extraction_timestamp': datetime.now().isoformat(),
                'total_markers': 0,
                'markers': [],
                'errors': ['Extractor aún no ha generado datos'],
            }
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Archivo vacío creado en: {output_file}")
        
        # Cargar datos
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        result = {
            'status': 'success',
            'total_markers': data.get('total_markers', 0),
            'extraction_timestamp': data.get('extraction_timestamp'),
            'errors': data.get('errors', []),
        }
        
        logger.info(f"✓ Datos leídos: {result['total_markers']} marcadores encontrados")
        
        # Guardar en XCom
        context['task_instance'].xcom_push(key='extraction_result', value=result)
        context['task_instance'].xcom_push(key='markers_file', value=str(output_file))
        
        return result
        
    except Exception as e:
        logger.error(f"✗ Error durante lectura: {str(e)}", exc_info=True)
        raise


def process_traffic_data(**context) -> List[Dict[str, Any]]:
    """
    Process extracted DGT markers into database records.
    
    Args:
        **context: Airflow context
        
    Returns:
        List of processed records ready for database insertion
    """
    logger.info("=" * 80)
    logger.info("TASK 2: PROCESSING EXTRACTED DATA")
    logger.info("=" * 80)
    
    try:
        # Get extraction result
        extraction_result = context['task_instance'].xcom_pull(
            task_ids='extract_markers',
            key='extraction_result'
        )
        markers_file = context['task_instance'].xcom_pull(
            task_ids='extract_markers',
            key='markers_file'
        )
        
        logger.info(f"Processing data from: {markers_file}")
        
        # Load markers
        with open(markers_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        markers = data.get('markers', [])
        logger.info(f"Processing {len(markers)} markers")
        
        processed_records = []
        
        # Convert markers to alert records
        for marker in markers:
            try:
                # Map severity to alert level
                severity_map = {
                    'high': 'critical',
                    'medium': 'warning',
                    'low': 'info',
                    'unknown': 'info',
                }
                
                alert_level = severity_map.get(marker.get('severity', 'low'), 'info')
                
                # Extract region from title or description if possible
                title = marker.get('title', 'Unknown DGT Incident')
                description = marker.get('description', marker.get('full_text', ''))
                region = marker.get('region', 'España')  # Default region
                
                # Try to extract region from title (common format: "A-1 Madrid")
                import re
                region_match = re.search(r'([A-Z]{1,2})\s+(.+?)(?:\s+\d|$)', title)
                if region_match:
                    region = region_match.group(2).strip()[:100]
                
                # Calculate expiration (traffic incidents usually last 1 hour)
                now = datetime.utcnow()
                expires_at = now + timedelta(hours=1)
                
                record = {
                    'title': title[:200],
                    'description': description[:1000],
                    'level': alert_level,
                    'type': 'traffic',
                    'region': region,
                    'status': 'active',
                    'timestamp': now,
                    'expires_at': expires_at,
                    'latitude': float(marker.get('latitude', 0.0)),
                    'longitude': float(marker.get('longitude', 0.0)),
                    'source': 'DGT',
                }
                
                processed_records.append(record)
                logger.debug(f"Processed: {record['title']}")
                
            except Exception as e:
                logger.warning(f"Error processing marker: {e}")
                continue
        
        logger.info(f"✓ Processed {len(processed_records)} valid records for database")
        
        # Save to XCom
        context['task_instance'].xcom_push(
            key='processed_records',
            value=processed_records
        )
        
        return processed_records
        
    except Exception as e:
        logger.error(f"✗ Error during processing: {str(e)}", exc_info=True)
        raise


def delete_existing_dgt_data(**context) -> Dict[str, Any]:
    """
    Delete existing DGT traffic data from database before inserting new data.
    
    Args:
        **context: Airflow context
        
    Returns:
        Dictionary with deletion statistics
    """
    logger.info("=" * 80)
    logger.info("TASK 3: CLEANING EXISTING DGT DATA")
    logger.info("=" * 80)
    
    try:
        engine = get_db_engine()
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Count existing DGT records
        count_query = "SELECT COUNT(*) FROM alerts WHERE source = 'DGT'"
        existing_count = session.execute(text(count_query)).scalar()
        logger.info(f"Found {existing_count} existing DGT records in database")
        
        if existing_count > 0:
            # Delete existing DGT records
            delete_query = "DELETE FROM alerts WHERE source = 'DGT'"
            session.execute(text(delete_query))
            session.commit()
            
            logger.info(f"✓ Deleted {existing_count} DGT records from database")
        else:
            logger.info("No existing DGT records to delete")
        
        result = {
            'status': 'success',
            'deleted_count': existing_count,
        }
        
        # Save to XCom
        context['task_instance'].xcom_push(
            key='deletion_result',
            value=result
        )
        
        session.close()
        return result
        
    except Exception as e:
        logger.error(f"✗ Error during deletion: {str(e)}", exc_info=True)
        raise


def insert_traffic_data(**context) -> Dict[str, Any]:
    """
    Insert processed traffic data into database.
    
    Args:
        **context: Airflow context
        
    Returns:
        Dictionary with insertion statistics
    """
    logger.info("=" * 80)
    logger.info("TASK 4: INSERTING NEW DGT DATA")
    logger.info("=" * 80)
    
    try:
        # Get processed records
        processed_records = context['task_instance'].xcom_pull(
            task_ids='process_data',
            key='processed_records'
        )
        
        if not processed_records:
            logger.warning("No records to insert")
            return {'status': 'success', 'inserted_count': 0}
        
        logger.info(f"Inserting {len(processed_records)} records")
        
        engine = get_db_engine()
        Session = sessionmaker(bind=engine)
        session = Session()
        
        inserted_count = 0
        
        for record in processed_records:
            try:
                insert_query = """
                    INSERT INTO alerts 
                    (title, description, level, type, region, status, timestamp, expires_at, latitude, longitude, source)
                    VALUES (:title, :description, :level, :type, :region, :status, :timestamp, :expires_at, :latitude, :longitude, :source)
                """
                
                session.execute(text(insert_query), record)
                inserted_count += 1
                
                if inserted_count % 50 == 0:
                    session.commit()
                    logger.info(f"Committed {inserted_count} records")
                
            except Exception as e:
                logger.warning(f"Error inserting record '{record.get('title')}': {e}")
                session.rollback()
                continue
        
        # Final commit
        session.commit()
        
        logger.info(f"✓ Successfully inserted {inserted_count} traffic records")
        
        result = {
            'status': 'success',
            'inserted_count': inserted_count,
            'timestamp': datetime.utcnow().isoformat(),
        }
        
        # Save to XCom
        context['task_instance'].xcom_push(
            key='insertion_result',
            value=result
        )
        
        session.close()
        return result
        
    except Exception as e:
        logger.error(f"✗ Error during insertion: {str(e)}", exc_info=True)
        raise


def log_ingestion_summary(**context) -> Dict[str, Any]:
    """
    Log summary of ingestion process.
    
    Args:
        **context: Airflow context
        
    Returns:
        Summary dictionary
    """
    logger.info("=" * 80)
    logger.info("TASK 5: INGESTION SUMMARY")
    logger.info("=" * 80)
    
    try:
        extraction_result = context['task_instance'].xcom_pull(
            task_ids='extract_markers',
            key='extraction_result'
        )
        deletion_result = context['task_instance'].xcom_pull(
            task_ids='delete_existing',
            key='deletion_result'
        )
        insertion_result = context['task_instance'].xcom_pull(
            task_ids='insert_data',
            key='insertion_result'
        )
        
        logger.info(f"\n📊 INGESTION REPORT")
        logger.info(f"{'='*80}")
        logger.info(f"Extraction:")
        logger.info(f"  - Markers found: {extraction_result.get('total_markers', 0)}")
        logger.info(f"  - Errors: {len(extraction_result.get('errors', []))}")
        
        logger.info(f"\nCleaning:")
        logger.info(f"  - Deleted records: {deletion_result.get('deleted_count', 0)}")
        
        logger.info(f"\nInsertion:")
        logger.info(f"  - Inserted records: {insertion_result.get('inserted_count', 0)}")
        logger.info(f"  - Timestamp: {insertion_result.get('timestamp')}")
        
        logger.info(f"\n{'='*80}")
        
        # Verify final count
        try:
            engine = get_db_engine()
            Session = sessionmaker(bind=engine)
            session = Session()
            
            final_count = session.execute(text("SELECT COUNT(*) FROM alerts WHERE source = 'DGT'")).scalar()
            logger.info(f"Final DGT records in database: {final_count}")
            
            session.close()
        except Exception as e:
            logger.warning(f"Could not verify final count: {e}")
        
        return {
            'status': 'completed',
            'extraction': extraction_result,
            'deletion': deletion_result,
            'insertion': insertion_result,
        }
        
    except Exception as e:
        logger.error(f"✗ Error in summary: {str(e)}", exc_info=True)
        raise


# ================================
# AIRFLOW TASKS
# ================================

extract_task = PythonOperator(
    task_id='extract_markers',
    python_callable=extract_dgt_markers,
    provide_context=True,
    dag=dag,
)

process_task = PythonOperator(
    task_id='process_data',
    python_callable=process_traffic_data,
    provide_context=True,
    dag=dag,
)

delete_task = PythonOperator(
    task_id='delete_existing',
    python_callable=delete_existing_dgt_data,
    provide_context=True,
    dag=dag,
)

insert_task = PythonOperator(
    task_id='insert_data',
    python_callable=insert_traffic_data,
    provide_context=True,
    dag=dag,
)

summary_task = PythonOperator(
    task_id='log_summary',
    python_callable=log_ingestion_summary,
    provide_context=True,
    dag=dag,
)

# ================================
# TASK DEPENDENCIES
# ================================

extract_task >> process_task >> delete_task >> insert_task >> summary_task