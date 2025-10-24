import time
import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/alerts")

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
