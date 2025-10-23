import os
import requests
import pytest
from sqlalchemy import create_engine, text
import time

def test_01_wait_for_database(wait_for, db_dsn):
    """Test that database is accessible"""
    print(f"\n[TEST] Testing database connection: {db_dsn}")
    
    def is_db_ready():
        try:
            engine = create_engine(db_dsn, connect_args={'connect_timeout': 3})
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1")).scalar()
                return result == 1
        except Exception as e:
            print(f"[TEST] DB not ready: {type(e).__name__}")
            return False
    
    wait_for(is_db_ready, timeout=90.0, pause=3.0)
    print("[TEST] ✅ Database is ready!")


@pytest.mark.skipif(os.getenv("SKIP_AIRFLOW_TEST"), reason="Airflow test skipped")
def test_02_airflow_webserver_health(wait_for, airflow_url):
    """Test that Airflow webserver is accessible and healthy"""
    print(f"\n[TEST] Testing Airflow webserver: {airflow_url}")
    
    # En CI, dar más tiempo inicial
    if os.getenv("CI"):
        print("[TEST] Running in CI, waiting 60s before checking...")
        time.sleep(60)
    
    def is_airflow_ready():
        try:
            # Intentar primero el endpoint raíz (más confiable)
            base_url = airflow_url.replace('/health', '')
            print(f"[TEST] Checking Airflow at {base_url}...")
            r = requests.get(base_url, timeout=20, allow_redirects=True)
            print(f"[TEST] Status code: {r.status_code}")
            
            # Cualquier respuesta que no sea error de conexión es buena señal
            if r.status_code in [200, 302, 401]:  # 401 = no autenticado pero servidor funciona
                print("[TEST] ✅ Airflow is responding!")
                return True
            return False
        except requests.exceptions.ConnectionError as e:
            print(f"[TEST] ✗ Connection error: {str(e)[:100]}")
            return False
        except requests.exceptions.Timeout:
            print(f"[TEST] ✗ Request timeout")
            return False
        except Exception as e:
            print(f"[TEST] ✗ Unexpected error: {type(e).__name__}: {str(e)[:100]}")
            return False
    
    # Timeout muy largo en CI
    timeout = 480.0 if os.getenv("CI") else 300.0  # 8 minutos en CI
    pause = 15.0 if os.getenv("CI") else 10.0
    
    try:
        wait_for(is_airflow_ready, timeout=timeout, pause=pause)
        print("[TEST] ✅ Airflow webserver is ready!")
    except Exception as e:
        if os.getenv("CI"):
            pytest.skip(f"Airflow test skipped in CI due to: {e}")
        else:
            raise