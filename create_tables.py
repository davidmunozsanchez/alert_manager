"""
Script para probar la funcionalidad de expiración de alertas
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import requests
import json
from datetime import datetime, timedelta, timezone

BASE_URL = "http://127.0.0.1:8000"

def test_endpoint(url, description, method="GET", data=None):
    """Test individual endpoint"""
    print(f"\n🔍 Testing: {description}")
    print(f"URL: {url}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            print(f"❌ Unsupported method: {method}")
            return
            
        print(f"Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            try:
                data = response.json()
                if isinstance(data, dict):
                    if "items" in data:
                        print(f"✅ SUCCESS - Items: {len(data['items'])}, Total: {data.get('total', 'N/A')}")
                        if "expired_processed" in data and data["expired_processed"] is not None:
                            print(f"    🔄 Expired processed: {data['expired_processed']}")
                    elif "expired_alerts_processed" in data:
                        print(f"✅ SUCCESS - Expired processed: {data['expired_alerts_processed']}")
                    elif "statistics" in data:
                        stats = data["statistics"]
                        print(f"✅ SUCCESS - Total: {stats.get('total_alerts')}, Expired: {stats.get('expired_but_active')}")
                    elif "types" in data:
                        types = data["types"]
                        print(f"✅ SUCCESS - Found {len(types)} different alert types:")
                        for type_info in types:
                            print(f"    - {type_info['type']}: {type_info['count']} alerts")
                    else:
                        keys = list(data.keys())[:5]
                        print(f"✅ SUCCESS - Keys: {keys}")
                else:
                    print(f"✅ SUCCESS - Type: {type(data)}")
            except:
                print(f"✅ SUCCESS - Raw response: {response.text[:100]}...")
        else:
            print(f"❌ FAILED - {response.text}")
    
    except requests.exceptions.RequestException as e:
        print(f"❌ CONNECTION ERROR: {e}")
    except Exception as e:
        print(f"❌ ERROR: {e}")

def create_test_expired_alert():
    """Crear una alerta de prueba que ya haya expirado"""
    print("\n🚀 Creating test expired alert...")
    
    # Usar datetime con timezone UTC
    expired_time = datetime.now(timezone.utc) - timedelta(hours=1)
    
    alert_data = {
        "title": "Test Expired Alert",
        "description": "Esta alerta debería estar expirada",
        "level": "warning",
        "type": "other",
        "region": "Test Region",
        "expires_at": expired_time.isoformat(),
        "latitude": 40.4168,
        "longitude": -3.7038,
        "source": "test"
    }
    
    test_endpoint(f"{BASE_URL}/alerts/", "Create expired alert", "POST", alert_data)

def create_test_future_alert():
    """Crear una alerta que expire en el futuro"""
    print("\n🚀 Creating test future alert...")
    
    # Usar datetime con timezone UTC
    future_time = datetime.now(timezone.utc) + timedelta(hours=2)
    
    alert_data = {
        "title": "Test Future Alert",
        "description": "Esta alerta no debería estar expirada",
        "level": "info",
        "type": "other", 
        "region": "Test Region",
        "expires_at": future_time.isoformat(),
        "latitude": 40.4168,
        "longitude": -3.7038,
        "source": "test"
    }
    
    test_endpoint(f"{BASE_URL}/alerts/", "Create future alert", "POST", alert_data)

def main():
    """Test expiration functionality"""
    print("🚀 Testing Alert Expiration Functionality")
    print("=" * 60)
    
    # 1. Verificar tipos de alerta en BD
    test_endpoint(f"{BASE_URL}/alerts/debug/types", "Check alert types in database")
    
    # 2. Ver estado inicial
    test_endpoint(f"{BASE_URL}/alerts/expire/status", "Initial expiration status")
    
    # 3. Ver alertas raw para entender los datos
    test_endpoint(f"{BASE_URL}/alerts/debug/raw", "Raw alerts data")
    
    # 4. Crear alertas de prueba
    create_test_expired_alert()
    create_test_future_alert()
    
    # 5. Ver estado después de crear alertas
    test_endpoint(f"{BASE_URL}/alerts/expire/status", "Expiration status after creating test alerts")
    
    # 6. Probar endpoint de verificación de expiradas
    test_endpoint(f"{BASE_URL}/alerts/expire/check", "Manual expiration check", "POST")
    
    # 7. Ver estado después de procesar
    test_endpoint(f"{BASE_URL}/alerts/expire/status", "Expiration status after processing")
    
    # 8. Probar get alerts con verificación automática
    test_endpoint(f"{BASE_URL}/alerts/?check_expired=true", "Get alerts with auto-expiration check")
    
    # 9. Probar get alerts sin verificación
    test_endpoint(f"{BASE_URL}/alerts/?check_expired=false", "Get alerts without expiration check")
    
    # 10. Ver alertas activas solamente
    test_endpoint(f"{BASE_URL}/alerts/?active_only=true", "Get only active alerts")
    
    # 11. Verificar health check
    test_endpoint(f"{BASE_URL}/alerts/health", "Health check")
    
    print("\n" + "=" * 60)
    print("✅ Expiration testing completed!")
    print("💡 Check the logs for detailed processing information")

if __name__ == "__main__":
    main()