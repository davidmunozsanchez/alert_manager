import os
import time

import psycopg2
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# URL por defecto para desarrollo local
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/alerts")

# Base declarativa (API 1.4 compatible)
Base = declarative_base()

# Crear engine con configuración compatible
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def wait_for_postgres(max_retries=10, delay=2):
    """Espera a que PostgreSQL esté disponible"""
    for attempt in range(max_retries):
        try:
            print(f"Intentando conectar a PostgreSQL (intento {attempt + 1})...")
            conn = psycopg2.connect(DATABASE_URL)
            conn.close()
            print("✅ Conexión exitosa a PostgreSQL.")
            return True
        except psycopg2.OperationalError as e:
            print(f"❌ Conexión fallida: {e}")
            if attempt < max_retries - 1:
                print(f"⏳ Esperando {delay} segundos antes del siguiente intento...")
                time.sleep(delay)
    
    print("💥 No se pudo conectar a PostgreSQL después de varios intentos.")
    return False

def get_db():
    """Dependency para obtener sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection():
    """Función para probar la conexión"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        print(f"Error de conexión: {e}")
        return False