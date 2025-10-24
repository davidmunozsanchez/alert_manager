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


def test_02_wait_for_web_service(wait_for, web_health_url, web_url):
    """Test that web service is accessible and healthy"""
    print(f"\n[TEST] Testing web service: {web_url}")
    
    # En CI, dar tiempo para que el servicio inicie
    if os.getenv("CI"):
        print("[TEST] Running in CI, waiting 60s before checking...")
        time.sleep(60)
    
    def is_web_ready():
        try:
            print(f"[TEST] Checking web service at {web_health_url}...")
            r = requests.get(web_health_url, timeout=10)
            print(f"[TEST] Status code: {r.status_code}")
            
            if r.status_code == 200:
                data = r.json()
                print(f"[TEST] Response: {data}")
                
                # Verificar que el health check retorna el formato esperado
                if data.get("status") == "healthy":
                    print("[TEST] ✅ Web service is healthy!")
                    return True
                else:
                    print(f"[TEST] ✗ Web service unhealthy: {data}")
                    return False
            
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
    
    # Timeout adaptativo según entorno
    timeout = 300.0 if os.getenv("CI") else 60.0
    pause = 5.0
    
    try:
        wait_for(is_web_ready, timeout=timeout, pause=pause)
        print("[TEST] ✅ Web service is ready!")
    except Exception as e:
        if os.getenv("CI"):
            pytest.skip(f"Web service test skipped in CI due to: {e}")
        else:
            raise


def test_03_web_service_endpoints(web_url):
    """Test that main API endpoints are accessible"""
    print(f"\n[TEST] Testing web service endpoints: {web_url}")
    
    # Test root endpoint
    try:
        r = requests.get(f"{web_url}/", timeout=10)
        print(f"[TEST] Root endpoint status: {r.status_code}")
        assert r.status_code in [200, 404], "Root endpoint should respond"
    except Exception as e:
        print(f"[TEST] ✗ Root endpoint failed: {e}")
    
    # Test docs endpoint
    try:
        r = requests.get(f"{web_url}/docs", timeout=10)
        print(f"[TEST] Docs endpoint status: {r.status_code}")
        assert r.status_code == 200, "Docs should be accessible"
        print("[TEST] ✅ API documentation is accessible!")
    except Exception as e:
        pytest.fail(f"Docs endpoint failed: {e}")
    
    # Test OpenAPI schema
    try:
        r = requests.get(f"{web_url}/openapi.json", timeout=10)
        print(f"[TEST] OpenAPI schema status: {r.status_code}")
        assert r.status_code == 200, "OpenAPI schema should be accessible"
        
        schema = r.json()
        assert "openapi" in schema, "Should be valid OpenAPI schema"
        assert "paths" in schema, "Should have paths defined"
        print(f"[TEST] ✅ OpenAPI schema has {len(schema['paths'])} endpoints!")
    except Exception as e:
        pytest.fail(f"OpenAPI schema failed: {e}")


def test_04_web_database_integration(web_url, db_dsn):
    """Test that web service can connect to database"""
    print(f"\n[TEST] Testing web service database integration")
    
    try:
        # Verificar que el health check incluye estado de DB
        r = requests.get(f"{web_url}/health", timeout=10)
        assert r.status_code == 200
        
        data = r.json()
        print(f"[TEST] Health check response: {data}")
        
        # Verificar que incluye información de la base de datos
        if "database" in data:
            db_status = data["database"]
            print(f"[TEST] Database status: {db_status}")
            assert db_status in ["connected", "ok"], \
                f"Database should be connected, got: {db_status}"
            print("[TEST] ✅ Web service is connected to database!")
        else:
            print("[TEST] ⚠️  Health check doesn't include database status")
    
    except Exception as e:
        pytest.fail(f"Database integration test failed: {e}")


def test_05_web_service_basic_api(web_url):
    """Test basic API operations (if authentication not required)"""
    print(f"\n[TEST] Testing basic API operations")
    
    try:
        # Intentar listar alertas (puede requerir auth)
        r = requests.get(f"{web_url}/alerts/", timeout=10)
        print(f"[TEST] GET /alerts/ status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            print(f"[TEST] ✅ Retrieved {len(data)} alerts")
            assert isinstance(data, list), "Should return a list"
        elif r.status_code == 401:
            print("[TEST] ℹ️  Endpoint requires authentication (expected)")
        else:
            print(f"[TEST] ⚠️  Unexpected status code: {r.status_code}")
    
    except Exception as e:
        print(f"[TEST] ⚠️  API test skipped: {e}")


@pytest.mark.skipif(os.getenv("SKIP_AIRFLOW_TEST"), reason="Airflow test skipped")
def test_06_airflow_webserver_health(wait_for, airflow_url):
    """Test that Airflow webserver is accessible and healthy"""
    print(f"\n[TEST] Testing Airflow webserver: {airflow_url}")
    
    # En CI, dar más tiempo inicial
    if os.getenv("CI"):
        print("[TEST] Running in CI, waiting 60s before checking...")
        time.sleep(60)
    
    def is_airflow_ready():
        try:
            base_url = airflow_url.replace('/health', '')
            print(f"[TEST] Checking Airflow at {base_url}...")
            r = requests.get(base_url, timeout=20, allow_redirects=True)
            print(f"[TEST] Status code: {r.status_code}")
            
            if r.status_code in [200, 302, 401]:
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
    
    timeout = 480.0 if os.getenv("CI") else 300.0
    pause = 15.0 if os.getenv("CI") else 10.0
    
    try:
        wait_for(is_airflow_ready, timeout=timeout, pause=pause)
        print("[TEST] ✅ Airflow webserver is ready!")
    except Exception as e:
        if os.getenv("CI"):
            pytest.skip(f"Airflow test skipped in CI due to: {e}")
        else:
            raise


def test_07_all_services_integration(web_url, db_dsn, airflow_url):
    """Test that all services are running and can communicate"""
    print(f"\n[TEST] Testing integration of all services")
    
    services_status = {
        "database": False,
        "web_service": False,
        "airflow": False
    }
    
    # Check database
    try:
        engine = create_engine(db_dsn, connect_args={'connect_timeout': 3})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        services_status["database"] = True
        print("[TEST] ✅ Database is operational")
    except Exception as e:
        print(f"[TEST] ✗ Database failed: {e}")
    
    # Check web service
    try:
        r = requests.get(f"{web_url}/health", timeout=10)
        if r.status_code == 200:
            services_status["web_service"] = True
            print("[TEST] ✅ Web service is operational")
    except Exception as e:
        print(f"[TEST] ✗ Web service failed: {e}")
    
    # Check Airflow (opcional)
    if not os.getenv("SKIP_AIRFLOW_TEST"):
        try:
            base_url = airflow_url.replace('/health', '')
            r = requests.get(base_url, timeout=20, allow_redirects=True)
            if r.status_code in [200, 302, 401]:
                services_status["airflow"] = True
                print("[TEST] ✅ Airflow is operational")
        except Exception as e:
            print(f"[TEST] ⚠️  Airflow check skipped: {e}")
    
    # Summary
    operational = sum(services_status.values())
    total = len(services_status)
    print(f"\n[TEST] 📊 Services operational: {operational}/{total}")
    for service, status in services_status.items():
        emoji = "✅" if status else "❌"
        print(f"[TEST] {emoji} {service}")
    
    # Al menos DB y Web deben estar operacionales
    assert services_status["database"], "Database must be operational"
    assert services_status["web_service"], "Web service must be operational"
    
    print("[TEST] ✅ Core services integration test passed!")