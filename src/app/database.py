import os
import time
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/alerts")

Base = declarative_base()

def wait_for_postgres(max_retries=10, delay=2):
    for attempt in range(max_retries):
        try:
            print(f"Intentando conectar a PostgreSQL (intento {attempt + 1})...")
            conn = psycopg2.connect(DATABASE_URL)
            conn.close()
            print("✅ Conexión exitosa a PostgreSQL.")
            return
        except psycopg2.OperationalError as e:
            print(f"❌ Conexión fallida: {e}")
            time.sleep(delay)
    raise Exception("No se pudo conectar a PostgreSQL después de varios intentos.")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Espera activa hasta que PostgreSQL esté listo
wait_for_postgres()

# Inicializa SQLAlchemy después de confirmar que PostgreSQL está disponible
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
