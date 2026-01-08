import os
import json
import pytest
import requests
from pathlib import Path
from datetime import datetime


class TestAEMETIntegration:
    """
    Tests de integración crítica con la API de AEMET.
    Requiere que:
    - La API de AEMET sea accesible
    - AEMET_API_KEY esté configurada en GitHub Secrets o env
    """

    @pytest.fixture(scope="class")
    def aemet_api_key(self):
        """Obtener API key de AEMET"""
        api_key = os.getenv("AEMET_API_KEY")
        if not api_key:
            pytest.skip("AEMET_API_KEY no está configurada")
        return api_key

    def test_aemet_api_connectivity(self, aemet_api_key):
        """Test 1: Verificar que podemos conectar con la API de AEMET"""
        url = "https://opendata.aemet.es/opendata/api/avisos_cap/ultimoelaborado/area/esp"
        
        response = requests.get(
            url,
            headers={"api_key": aemet_api_key},
            timeout=30
        )
        
        print(f"\n✅ Respuesta AEMET: {response.status_code}")
        assert response.status_code == 200, (
            f"❌ Error conectando con AEMET: {response.status_code}\n"
            f"Respuesta: {response.text}"
        )
        
        data = response.json()
        assert "descripcion" in data, "❌ Respuesta AEMET no contiene descripción"
        print(f"✅ Descripción: {data.get('descripcion')}")

    def test_aemet_api_returns_data_url(self, aemet_api_key):
        """Test 2: Verificar que AEMET retorna una URL de descarga"""
        url = "https://opendata.aemet.es/opendata/api/avisos_cap/ultimoelaborado/area/esp"
        
        response = requests.get(
            url,
            headers={"api_key": aemet_api_key},
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        data_url = data.get("datos")
        assert data_url, "❌ AEMET no retornó URL de datos"
        print(f"✅ URL de datos obtenida: {data_url[:80]}...")
        
        # Verificar que es una URL válida
        assert data_url.startswith("http"), "❌ URL de datos no válida"

    def test_aemet_api_data_downloadable(self, aemet_api_key):
        """Test 3: Verificar que podemos descargar el archivo TAR de AEMET"""
        url = "https://opendata.aemet.es/opendata/api/avisos_cap/ultimoelaborado/area/esp"
        
        # Obtener URL de datos
        response = requests.get(
            url,
            headers={"api_key": aemet_api_key},
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        data_url = data.get("datos")
        
        assert data_url, "❌ No hay URL de datos"
        
        # Descargar archivo TAR
        tar_response = requests.get(data_url, timeout=60)
        
        assert tar_response.status_code == 200, (
            f"❌ Error descargando TAR: {tar_response.status_code}"
        )
        
        # Verificar que es un archivo TAR
        assert len(tar_response.content) > 0, "❌ Archivo TAR vacío"
        assert tar_response.content[:2] in [b'\x1f\x8b', b'BZ'], (
            "❌ El contenido no es un archivo comprimido válido (gzip/bzip2)"
        )
        
        print(f"✅ TAR descargado: {len(tar_response.content)} bytes")

    def test_aemet_api_tar_contains_xml(self, aemet_api_key):
        """Test 4: Verificar que el TAR contiene archivos XML"""
        import tarfile
        import io
        
        url = "https://opendata.aemet.es/opendata/api/avisos_cap/ultimoelaborado/area/esp"
        
        # Obtener URL de datos
        response = requests.get(
            url,
            headers={"api_key": aemet_api_key},
            timeout=30
        )
        
        data_url = response.json().get("datos")
        
        # Descargar TAR
        tar_response = requests.get(data_url, timeout=60)
        
        # Extraer TAR
        tar_bytes = io.BytesIO(tar_response.content)
        tar = tarfile.open(fileobj=tar_bytes, mode='r:*')
        
        # Verificar que contiene XMLs
        xml_members = [m for m in tar.getmembers() if m.name.endswith('.xml')]
        
        assert len(xml_members) > 0, (
            "❌ El TAR no contiene archivos XML"
        )
        
        print(f"✅ TAR contiene {len(xml_members)} archivos XML")
        tar.close()

    def test_aemet_api_xml_parseable(self, aemet_api_key):
        """Test 5: Verificar que los XMLs de AEMET son parseables (formato CAP)"""
        import tarfile
        import io
        import xml.etree.ElementTree as ET
        
        url = "https://opendata.aemet.es/opendata/api/avisos_cap/ultimoelaborado/area/esp"
        
        # Obtener URL de datos
        response = requests.get(
            url,
            headers={"api_key": aemet_api_key},
            timeout=30
        )
        
        data_url = response.json().get("datos")
        
        # Descargar TAR
        tar_response = requests.get(data_url, timeout=60)
        
        # Extraer TAR
        tar_bytes = io.BytesIO(tar_response.content)
        tar = tarfile.open(fileobj=tar_bytes, mode='r:*')
        
        # Procesar primer XML
        xml_members = [m for m in tar.getmembers() if m.name.endswith('.xml')]
        
        assert len(xml_members) > 0, "❌ No hay XMLs"
        
        first_xml = xml_members[0]
        f = tar.extractfile(first_xml)
        xml_content = f.read().decode('utf-8')
        
        # Intentar parsear como XML CAP
        try:
            root = ET.fromstring(xml_content)
            
            # Verificar estructura CAP básica
            ns = {'cap': 'urn:oasis:names:tc:emergency:cap:1.2'}
            identifier = root.findtext('cap:identifier', namespaces=ns)
            
            assert identifier, "❌ XML no es formato CAP válido (sin identifier)"
            
            print(f"✅ XML parseado correctamente")
            print(f"   - Tipo: CAP (Common Alerting Protocol)")
            print(f"   - Identifier: {identifier}")
            
        except ET.ParseError as e:
            raise AssertionError(f"❌ No se pudo parsear XML CAP: {e}")
        
        tar.close()

    def test_aemet_api_extracts_alert_data(self, aemet_api_key):
        """Test 6: Verificar que se pueden extraer datos de alertas del XML"""
        import tarfile
        import io
        import xml.etree.ElementTree as ET
        
        url = "https://opendata.aemet.es/opendata/api/avisos_cap/ultimoelaborado/area/esp"
        
        # Obtener URL de datos
        response = requests.get(
            url,
            headers={"api_key": aemet_api_key},
            timeout=30
        )
        
        data_url = response.json().get("datos")
        
        # Descargar TAR
        tar_response = requests.get(data_url, timeout=60)
        
        # Extraer TAR
        tar_bytes = io.BytesIO(tar_response.content)
        tar = tarfile.open(fileobj=tar_bytes, mode='r:*')
        
        # Procesar XMLs
        xml_members = [m for m in tar.getmembers() if m.name.endswith('.xml')]
        
        alerts_extracted = 0
        
        for xml_member in xml_members[:3]:  # Procesar primeros 3
            try:
                f = tar.extractfile(xml_member)
                xml_content = f.read().decode('utf-8')
                
                root = ET.fromstring(xml_content)
                ns = {'cap': 'urn:oasis:names:tc:emergency:cap:1.2'}
                
                info = root.find('cap:info', namespaces=ns)
                if info is not None:
                    event = info.findtext('cap:event', namespaces=ns)
                    area_desc = info.find('cap:area', namespaces=ns)
                    
                    if area_desc is not None:
                        area_text = area_desc.findtext('cap:areaDesc', namespaces=ns)
                        if event and area_text:
                            alerts_extracted += 1
                            print(f"✅ Alerta extraída: {event} - {area_text}")
            except Exception as e:
                print(f"⚠️  Error procesando {xml_member.name}: {e}")
        
        assert alerts_extracted > 0, (
            "❌ No se pudieron extraer alertas de los XMLs"
        )
        
        print(f"✅ Se extrajeron {alerts_extracted} alertas correctamente")
        tar.close()

    def test_aemet_api_end_to_end(self, aemet_api_key):
        """Test 7: Test END-TO-END completo - simular exactamente lo que hace el DAG"""
        import tarfile
        import io
        import xml.etree.ElementTree as ET
        
        print("\n🔐 Iniciando test END-TO-END de AEMET (simulando DAG)...")
        
        # PASO 1: Autenticación
        print("1️⃣  Paso 1: Autenticación con AEMET...")
        url = "https://opendata.aemet.es/opendata/api/avisos_cap/ultimoelaborado/area/esp"
        
        auth_response = requests.get(
            url,
            headers={"api_key": aemet_api_key},
            timeout=30
        )
        
        assert auth_response.status_code == 200, "❌ Autenticación fallida"
        auth_data = auth_response.json()
        print(f"   ✅ Autenticación OK: {auth_data.get('descripcion')}")
        
        # PASO 2: Obtener URL de descarga
        print("2️⃣  Paso 2: Obtener URL de descarga...")
        data_url = auth_data.get("datos")
        assert data_url, "❌ No hay URL de datos"
        print(f"   ✅ URL obtenida: {data_url[:60]}...")
        
        # PASO 3: Descargar TAR
        print("3️⃣  Paso 3: Descargar archivo TAR...")
        tar_response = requests.get(data_url, timeout=60)
        assert tar_response.status_code == 200, "❌ Error descargando TAR"
        print(f"   ✅ TAR descargado: {len(tar_response.content)} bytes")
        
        # PASO 4: Extraer y procesar XMLs
        print("4️⃣  Paso 4: Extraer y procesar XMLs...")
        tar_bytes = io.BytesIO(tar_response.content)
        tar = tarfile.open(fileobj=tar_bytes, mode='r:*')
        
        xml_members = [m for m in tar.getmembers() if m.name.endswith('.xml')]
        print(f"   ✅ Encontrados {len(xml_members)} archivos XML")
        
        # PASO 5: Convertir XMLs a JSON normalizado
        print("5️⃣  Paso 5: Convertir a datos normalizados...")
        alerts_list = []
        ns = {'cap': 'urn:oasis:names:tc:emergency:cap:1.2'}
        
        for xml_member in xml_members:
            try:
                f = tar.extractfile(xml_member)
                xml_content = f.read().decode('utf-8')
                root = ET.fromstring(xml_content)
                
                identifier = root.findtext('cap:identifier', namespaces=ns)
                info = root.find('cap:info', namespaces=ns)
                
                if info is not None:
                    event = info.findtext('cap:event', namespaces=ns)
                    area = info.find('cap:area', namespaces=ns)
                    
                    if area is not None and event:
                        area_desc = area.findtext('cap:areaDesc', namespaces=ns)
                        
                        alert = {
                            "identifier": identifier,
                            "event": event,
                            "area": area_desc,
                            "timestamp": datetime.now().isoformat()
                        }
                        alerts_list.append(alert)
            except Exception as e:
                print(f"   ⚠️  Error: {e}")
        
        tar.close()
        
        assert len(alerts_list) > 0, "❌ No se extrajeron alertas"
        print(f"   ✅ {len(alerts_list)} alertas normalizadas")
        
        # PASO 6: Validar datos
        print("6️⃣  Paso 6: Validar datos extraídos...")
        for alert in alerts_list[:3]:
            required_fields = ["identifier", "event", "area"]
            for field in required_fields:
                assert field in alert and alert[field], (
                    f"❌ Campo '{field}' faltante o vacío en alerta"
                )
            print(f"   ✅ Alerta válida: {alert['event']} - {alert['area']}")
        
        print("\n🎉 TEST END-TO-END COMPLETADO EXITOSAMENTE")
        print(f"   - Alertas obtenidas: {len(alerts_list)}")
        print(f"   - Fecha: {datetime.now().isoformat()}")
