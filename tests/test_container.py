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


def test_02_airflow_webserver_health(wait_for, airflow_url):
    """Test that Airflow webserver is accessible and healthy"""
    print(f"\n[TEST] Testing Airflow webserver: {airflow_url}")
    
    # En CI, dar más tiempo inicial para que Airflow arranque
    if os.getenv("CI"):
        print("[TEST] Running in CI, waiting 30s before checking...")
        time.sleep(30)
    
    def is_airflow_ready():
        try:
            print(f"[TEST] Checking Airflow health at {airflow_url}...")
            r = requests.get(airflow_url, timeout=15)
            print(f"[TEST] Status code: {r.status_code}")
            
            if r.status_code == 200:
                print("[TEST] ✅ Airflow is healthy!")
                return True
            elif r.status_code == 404:
                # Intentar con la raíz si /health no existe
                base_url = airflow_url.replace('/health', '')
                print(f"[TEST] Trying base URL: {base_url}")
                r = requests.get(base_url, timeout=15)
                return r.status_code == 200
            return False
        except requests.exceptions.ConnectionError as e:
            print(f"[TEST] ✗ Connection error: {e}")
            return False
        except requests.exceptions.Timeout:
            print(f"[TEST] ✗ Request timeout")
            return False
        except Exception as e:
            print(f"[TEST] ✗ Unexpected error: {type(e).__name__}: {str(e)[:100]}")
            return False
    
    # Timeouts más largos, especialmente en CI
    timeout = 600.0 if os.getenv("CI") else 360.0
    pause = 10.0 if os.getenv("CI") else 5.0
    
    wait_for(is_airflow_ready, timeout=timeout, pause=pause)
    print("[TEST] ✅ Airflow webserver is ready!")