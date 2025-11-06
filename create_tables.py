"""
Script de debug para identificar el problema exacto
"""
import sys
import os
from pathlib import Path

print("🔍 DEBUG: Iniciando diagnóstico...")
print(f"📍 Directorio actual: {os.getcwd()}")
print(f"🐍 Python path: {sys.path}")

# PASO 1: Configurar variables de entorno
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/alerts")
print(f"🔗 DATABASE_URL: {os.getenv('DATABASE_URL')}")

# PASO 2: Añadir src al path
src_path = str(Path(__file__).parent / "src")
print(f"📁 Añadiendo al path: {src_path}")
sys.path.insert(0, src_path)

# PASO 3: Test de conexión directa (sabemos que funciona)
print("\n🧪 PASO 3: Test de conexión directa...")
try:
    import psycopg2
    conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/alerts")
    print("✅ Conexión directa con psycopg2 OK")
    conn.close()
except Exception as e:
    print(f"❌ Error en conexión directa: {e}")
    exit(1)

# PASO 4: Test de import de SQLAlchemy básico
print("\n🧪 PASO 4: Test de SQLAlchemy básico...")
try:
    from sqlalchemy import create_engine
    engine_test = create_engine("postgresql://postgres:postgres@localhost:5432/alerts")
    with engine_test.connect() as conn:
        result = conn.execute("SELECT 1")
        print(f"✅ SQLAlchemy directo OK: {result.scalar()}")
except Exception as e:
    print(f"❌ Error en SQLAlchemy directo: {e}")
    exit(1)

# PASO 5: Test de import de database.py
print("\n🧪 PASO 5: Test de import de database.py...")
try:
    from app.database import DATABASE_URL
    print(f"✅ Import de DATABASE_URL OK: {DATABASE_URL}")
except Exception as e:
    print(f"❌ Error importando DATABASE_URL: {e}")
    exit(1)

# PASO 6: Test de import de engine desde database.py
print("\n🧪 PASO 6: Test de import de engine...")
try:
    from app.database import engine
    print(f"✅ Import de engine OK: {engine}")
except Exception as e:
    print(f"❌ Error importando engine: {e}")
    print("💡 Revisemos el contenido de database.py...")
    
    # Leer y mostrar database.py
    try:
        with open("src/app/database.py", "r") as f:
            content = f.read()
            print("📄 Contenido de database.py:")
            print(content[:500] + "..." if len(content) > 500 else content)
    except Exception as read_error:
        print(f"❌ No se pudo leer database.py: {read_error}")
    exit(1)

# PASO 7: Test de conexión con el engine importado
print("\n🧪 PASO 7: Test de conexión con engine importado...")
try:
    with engine.connect() as conn:
        result = conn.execute("SELECT 1")
        print(f"✅ Engine importado funciona OK: {result.scalar()}")
except Exception as e:
    print(f"❌ Error con engine importado: {e}")
    exit(1)

# PASO 8: Test de import de Base
print("\n🧪 PASO 8: Test de import de Base...")
try:
    from app.database import Base
    print(f"✅ Import de Base OK: {Base}")
except Exception as e:
    print(f"❌ Error importando Base: {e}")
    exit(1)

# PASO 9: Test de import de modelos
print("\n🧪 PASO 9: Test de import de modelos...")
try:
    from app.models import Alert, DataSource
    print(f"✅ Import de modelos OK: Alert={Alert}, DataSource={DataSource}")
except Exception as e:
    print(f"❌ Error importando modelos: {e}")
    print("💡 Revisemos si models.py existe...")
    
    # Verificar si models.py existe
    models_path = Path("src/app/models.py")
    if models_path.exists():
        print(f"✅ models.py existe en {models_path}")
    else:
        print(f"❌ models.py NO existe en {models_path}")
        print("📁 Contenido de src/app/:")
        app_dir = Path("src/app")
        if app_dir.exists():
            for item in app_dir.iterdir():
                print(f"  - {item.name}")
    exit(1)

# PASO 10: Test de creación de tablas
print("\n🧪 PASO 10: Test de creación de tablas...")
try:
    Base.metadata.create_all(bind=engine)
    print("✅ Creación de tablas OK")
except Exception as e:
    print(f"❌ Error creando tablas: {e}")
    exit(1)

print("\n🎉 ¡Todos los pasos funcionaron correctamente!")