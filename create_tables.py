"""
Script para crear las tablas actualizadas
"""
import sys
import os
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from app.database import engine
from app.models import Alert, DataSource

def create_tables():
    """Crea todas las tablas"""
    print("🔄 Creando tablas...")
    
    # Crear todas las tablas
    Alert.metadata.create_all(bind=engine)
    DataSource.metadata.create_all(bind=engine)
    
    print("✅ Tablas creadas exitosamente")
    print("📋 Tablas disponibles:")
    print("  - alerts (con nuevos campos: source, metadata)")  
    print("  - data_sources (nueva tabla)")

if __name__ == "__main__":
    create_tables()