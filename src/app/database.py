# src/app/database.py
import os
import time

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Leer DATABASE_URL del entorno (si existe)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/alerts")

# Crear engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def wait_for_postgres(max_retries=10, delay=2):
    """Espera a que PostgreSQL esté disponible"""
    from sqlalchemy import text
    
    for attempt in range(max_retries):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            print("✅ Conexión exitosa a PostgreSQL")
            return
        except Exception as e:
            print(f"Intento {attempt + 1}/{max_retries}: PostgreSQL no disponible - {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
    
    raise Exception("No se pudo conectar a PostgreSQL después de varios intentos.")


# Solo esperar a PostgreSQL si NO estamos en modo testing
if os.getenv("TESTING") != "1":  # ← Añadir esta condición
    wait_for_postgres()