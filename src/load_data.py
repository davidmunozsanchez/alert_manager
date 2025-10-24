import json
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models, schemas, crud

def load_alerts():
    db: Session = SessionLocal()
    try:
        existing = db.query(models.Alert).first()
        if existing:
            print("Ya existen alertas, no se carga nada.")
            return

        with open("alerts_data.json", "r", encoding="utf-8") as file:
            data = json.load(file)

        for item in data:
            alert = schemas.AlertCreate(**item)
            crud.create_alert(db, alert)

        print(f"{len(data)} alertas cargadas con éxito.")
    except Exception as e:
        print(f"Error al cargar alertas: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    load_alerts()
    print("Proceso de carga de alertas completado.")