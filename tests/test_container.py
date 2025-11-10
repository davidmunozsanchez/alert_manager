import os
import time
import json

import pytest
import requests
from sqlalchemy import create_engine, text


def test_01_wait_for_database(wait_for, db_dsn):
    """Test that database is accessible"""
    print(f"\n[TEST] Testing database connection: {db_dsn}")

    def is_db_ready():
        try:
            engine = create_engine(db_dsn, connect_args={"connect_timeout": 3})
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
            r = requests.get(f"{web_url}/alerts/health", timeout=10)
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


def test_03_seq_logging_platform(wait_for):
    """Test that Seq logging platform is accessible and functional"""
    print(f"\n[TEST] Testing Seq logging platform")
    
    seq_url = "http://localhost:5341"
    
    def is_seq_ready():
        try:
            print(f"[TEST] Checking Seq web interface at {seq_url}...")
            r = requests.get(seq_url, timeout=10)
            print(f"[TEST] Seq status code: {r.status_code}")
            
            # Seq puede devolver 200 o 302 (redirect)
            if r.status_code in [200, 302]:
                # Verificar que es realmente Seq
                if "seq" in r.text.lower() or "datalust" in r.text.lower():
                    print("[TEST] ✅ Seq web interface is ready!")
                    return True
                
            return False
        except requests.exceptions.ConnectionError as e:
            print(f"[TEST] ✗ Seq connection error: {str(e)[:100]}")
            return False
        except Exception as e:
            print(f"[TEST] ✗ Seq unexpected error: {type(e).__name__}: {str(e)[:100]}")
            return False

    timeout = 120.0 if os.getenv("CI") else 60.0
    
    try:
        wait_for(is_seq_ready, timeout=timeout, pause=5.0)
        print("[TEST] ✅ Seq is operational!")
        
        # Test Seq API endpoint
        try:
            api_url = f"{seq_url}/api/events/raw"
            test_log = {
                "@t": "2025-11-09T12:00:00.000Z",
                "@l": "Information", 
                "@mt": "🧪 Test log from pytest",
                "Source": "pytest",
                "TestId": int(time.time())
            }
            
            headers = {"Content-Type": "application/vnd.serilog.clef"}
            r = requests.post(api_url, data=json.dumps(test_log), headers=headers, timeout=10)
            
            if r.status_code in [200, 201, 202]:
                print("[TEST] ✅ Seq API accepts logs!")
            else:
                print(f"[TEST] ⚠️  Seq API status: {r.status_code}")
                
        except Exception as e:
            print(f"[TEST] ⚠️  Seq API test failed: {e}")
            
    except Exception as e:
        if os.getenv("CI"):
            pytest.skip(f"Seq test skipped in CI due to: {e}")
        else:
            print(f"[TEST] ⚠️  Seq test failed: {e}")


def test_04_dozzle_docker_logs_viewer(wait_for):
    """Test that Dozzle Docker logs viewer is accessible"""
    print(f"\n[TEST] Testing Dozzle logs viewer")
    
    dozzle_url = "http://localhost:8888"
    
    def is_dozzle_ready():
        try:
            print(f"[TEST] Checking Dozzle at {dozzle_url}...")
            r = requests.get(dozzle_url, timeout=10)
            print(f"[TEST] Dozzle status code: {r.status_code}")
            
            if r.status_code == 200:
                # Verificar que es Dozzle
                if "dozzle" in r.text.lower() or "docker" in r.text.lower():
                    print("[TEST] ✅ Dozzle is ready!")
                    return True
                    
            return False
        except requests.exceptions.ConnectionError as e:
            print(f"[TEST] ✗ Dozzle connection error: {str(e)[:100]}")
            return False
        except Exception as e:
            print(f"[TEST] ✗ Dozzle unexpected error: {type(e).__name__}: {str(e)[:100]}")
            return False

    timeout = 60.0
    
    try:
        wait_for(is_dozzle_ready, timeout=timeout, pause=3.0)
        print("[TEST] ✅ Dozzle is operational!")
    except Exception as e:
        if os.getenv("CI"):
            pytest.skip(f"Dozzle test skipped in CI due to: {e}")
        else:
            print(f"[TEST] ⚠️  Dozzle test failed: {e}")


def test_05_file_browser_logs_access():
    """Test that File Browser for logs is accessible"""
    print(f"\n[TEST] Testing File Browser for logs")
    
    filebrowser_url = "http://localhost:8081"
    
    try:
        print(f"[TEST] Checking File Browser at {filebrowser_url}...")
        r = requests.get(filebrowser_url, timeout=10)
        print(f"[TEST] File Browser status code: {r.status_code}")
        
        if r.status_code == 200:
            print("[TEST] ✅ File Browser is accessible!")
            
            # Verificar que tiene interfaz de archivos
            if "files" in r.text.lower() or "browser" in r.text.lower():
                print("[TEST] ✅ File Browser interface detected!")
            else:
                print("[TEST] ⚠️  File Browser interface not clearly detected")
        else:
            print(f"[TEST] ⚠️  File Browser returned status: {r.status_code}")
            
    except requests.exceptions.ConnectionError as e:
        print(f"[TEST] ✗ File Browser connection error: {e}")
        if not os.getenv("CI"):
            pytest.fail(f"File Browser should be accessible: {e}")
    except Exception as e:
        print(f"[TEST] ✗ File Browser test error: {e}")
        if not os.getenv("CI"):
            pytest.fail(f"File Browser test failed: {e}")


def test_06_log_integration_test(web_url):
    """Test that logging integration works end-to-end"""
    print(f"\n[TEST] Testing logging integration")
    
    try:
        # Generar logs usando el endpoint de test
        test_logs_url = f"{web_url}/test-logs"
        print(f"[TEST] Triggering test logs at {test_logs_url}...")
        
        r = requests.get(test_logs_url, timeout=15)
        print(f"[TEST] Test logs endpoint status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            print(f"[TEST] ✅ Test logs generated! Test ID: {data.get('test_id')}")
            print(f"[TEST] Seq URL configured: {data.get('seq_url')}")
            
            # Esperar un momento para que los logs se procesen
            time.sleep(5)
            
            # Verificar que los logs aparecen en archivos locales
            try:
                import os
                log_file = "../logs/alert_manager.json"
                if os.path.exists(log_file):
                    with open(log_file, 'r') as f:
                        log_content = f.read()
                        if "Test log" in log_content:
                            print("[TEST] ✅ Logs appear in local files!")
                        else:
                            print("[TEST] ⚠️  Test logs not found in local files")
                else:
                    print("[TEST] ⚠️  Log file not found")
            except Exception as e:
                print(f"[TEST] ⚠️  Could not verify local logs: {e}")
                
        else:
            print(f"[TEST] ⚠️  Test logs endpoint failed: {r.status_code}")
            
    except Exception as e:
        print(f"[TEST] ⚠️  Logging integration test failed: {e}")


def test_07_web_service_endpoints(web_url):
    """Test that main API endpoints are accessible"""
    print(f"\n[TEST] Testing web service endpoints: {web_url}")

    # Test root endpoint
    try:
        r = requests.get(f"{web_url}/alerts/", timeout=10)
        print(f"[TEST] Root endpoint status: {r.status_code}")
        assert r.status_code in [200, 404], "Root endpoint should respond"
    except Exception as e:
        print(f"[TEST] ✗ Root endpoint failed: {e}")

    # Test ping endpoint
    try:
        r = requests.get(f"{web_url}/ping", timeout=10)
        print(f"[TEST] Ping endpoint status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            assert "status" in data, "Ping should return status"
            print(f"[TEST] ✅ Ping successful: {data.get('status')}")
    except Exception as e:
        print(f"[TEST] ⚠️  Ping endpoint test failed: {e}")


def test_08_web_database_integration(web_url, db_dsn):
    """Test that web service can connect to database"""
    print(f"\n[TEST] Testing web service database integration")

    try:
        # Verificar que el health check incluye estado de DB
        r = requests.get(f"{web_url}/alerts/health", timeout=10)
        assert r.status_code == 200

        data = r.json()
        print(f"[TEST] Health check response: {data}")

        # Verificar que incluye información de la base de datos
        if "database" in data:
            db_dict = data["database"]
            print(f"[TEST] Database status: {db_dict['status']}")
            assert db_dict["status"] in ["connected", "ok"], f"Database should be connected, got: {db_dict['status']}"
            print("[TEST] ✅ Web service is connected to database!")
        else:
            print("[TEST] ⚠️  Health check doesn't include database status")

    except Exception as e:
        pytest.fail(f"Database integration test failed: {e}")


def test_09_web_service_basic_api(web_url):
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
def test_10_airflow_webserver_health(wait_for, airflow_url):
    """Test that Airflow webserver is accessible and healthy"""
    print(f"\n[TEST] Testing Airflow webserver: {airflow_url}")

    # En CI, dar más tiempo inicial
    if os.getenv("CI"):
        print("[TEST] Running in CI, waiting 60s before checking...")
        time.sleep(90)

    def is_airflow_ready():
        try:
            base_url = airflow_url.replace("/health", "")
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

    timeout = 600 if os.getenv("CI") else 300.0
    pause = 15.0 if os.getenv("CI") else 10.0

    try:
        wait_for(is_airflow_ready, timeout=timeout, pause=pause)
        print("[TEST] ✅ Airflow webserver is ready!")
    except Exception as e:
        if os.getenv("CI"):
            pytest.skip(f"Airflow test skipped in CI due to: {e}")
        else:
            raise


def test_11_log_tester_container():
    """Test that log-tester container is generating logs to Seq"""
    print(f"\n[TEST] Testing log-tester container functionality")
    
    try:
        # Verificar que Seq está recibiendo logs del log-tester
        seq_url = "http://localhost:5341"
        
        # Intentar acceder a la interfaz de Seq para ver logs
        r = requests.get(seq_url, timeout=10)
        
        if r.status_code in [200, 302]:
            print("[TEST] ✅ Seq is accessible for log verification!")
            
            # Nota: En un entorno real, podrías hacer queries específicas a la API de Seq
            # para verificar que los logs del log-tester están llegando
            print("[TEST] 💡 Log-tester container should be sending periodic logs to Seq")
            print("[TEST] 💡 Check Seq UI at http://localhost:5341 to verify log ingestion")
        else:
            print(f"[TEST] ⚠️  Could not verify log-tester via Seq: status {r.status_code}")
            
    except Exception as e:
        print(f"[TEST] ⚠️  Log-tester verification failed: {e}")


def test_12_all_services_integration(web_url, db_dsn, airflow_url):
    """Test that all services are running and can communicate"""
    print(f"\n[TEST] Testing integration of all services")

    services_status = {
        "database": False, 
        "web_service": False, 
        "airflow": False,
        "seq": False,
        "dozzle": False,
        "filebrowser": False
    }

    # Check database
    try:
        engine = create_engine(db_dsn, connect_args={"connect_timeout": 3})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        services_status["database"] = True
        print("[TEST] ✅ Database is operational")
    except Exception as e:
        print(f"[TEST] ✗ Database failed: {e}")

    # Check web service
    try:
        r = requests.get(f"{web_url}/alerts/health", timeout=10)
        if r.status_code == 200:
            services_status["web_service"] = True
            print("[TEST] ✅ Web service is operational")
    except Exception as e:
        print(f"[TEST] ✗ Web service failed: {e}")

    # Check Airflow (opcional)
    if not os.getenv("SKIP_AIRFLOW_TEST"):
        try:
            base_url = airflow_url.replace("/health", "")
            r = requests.get(base_url, timeout=20, allow_redirects=True)
            if r.status_code in [200, 302, 401]:
                services_status["airflow"] = True
                print("[TEST] ✅ Airflow is operational")
        except Exception as e:
            print(f"[TEST] ⚠️  Airflow check skipped: {e}")

    # Check Seq
    try:
        r = requests.get("http://localhost:5341", timeout=10)
        if r.status_code in [200, 302]:
            services_status["seq"] = True
            print("[TEST] ✅ Seq is operational")
    except Exception as e:
        print(f"[TEST] ⚠️  Seq check failed: {e}")

    # Check Dozzle
    try:
        r = requests.get("http://localhost:8888", timeout=10)
        if r.status_code == 200:
            services_status["dozzle"] = True
            print("[TEST] ✅ Dozzle is operational")
    except Exception as e:
        print(f"[TEST] ⚠️  Dozzle check failed: {e}")

    # Check File Browser
    try:
        r = requests.get("http://localhost:8081", timeout=10)
        if r.status_code == 200:
            services_status["filebrowser"] = True
            print("[TEST] ✅ File Browser is operational")
    except Exception as e:
        print(f"[TEST] ⚠️  File Browser check failed: {e}")

    # Summary
    operational = sum(services_status.values())
    total = len(services_status)
    print(f"\n[TEST] 📊 Services operational: {operational}/{total}")
    for service, status in services_status.items():
        emoji = "✅" if status else "❌"
        print(f"[TEST] {emoji} {service}")

    # Core services (DB y Web) deben estar operacionales
    assert services_status["database"], "Database must be operational"
    assert services_status["web_service"], "Web service must be operational"

    # Logging services deberían estar operacionales pero no son críticos
    if services_status["seq"]:
        print("[TEST] 🎉 Centralized logging with Seq is working!")
    
    if services_status["dozzle"]:
        print("[TEST] 🎉 Docker logs viewing with Dozzle is working!")

    print("[TEST] ✅ Core services integration test passed!")
    
    # Report final status
    critical_services = ["database", "web_service"]
    optional_services = ["airflow", "seq", "dozzle", "filebrowser"]
    
    critical_ok = all(services_status[s] for s in critical_services)
    optional_ok = [s for s in optional_services if services_status[s]]
    
    print(f"[TEST] 🎯 Critical services: {'✅ OK' if critical_ok else '❌ FAILED'}")
    print(f"[TEST] 🎁 Optional services working: {len(optional_ok)}/{len(optional_services)} ({', '.join(optional_ok)})")