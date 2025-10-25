import sys
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import auth, crud, database, schemas
from app.database import Base, SessionLocal, engine

Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/alerts", tags=["Alerts"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


#### que me devuelva bien la database
@router.get("/health")
def health_check(db: Session = Depends(database.get_db)):
    """
    Health check endpoint para monitoreo

    Verifica:
    - Estado de la API
    - Conexión a la base de datos
    - Timestamp del check

    Returns 200 siempre, pero reporta el estado real de los componentes
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "database": {"status": "unknown", "message": ""},
    }

    # Verificar conexión a base de datos
    try:
        # Intentar una query simple
        result = db.execute(text("SELECT 1")).scalar()

        if result == 1:
            health_status["database"]["status"] = "connected"
            health_status["database"]["message"] = "Database connection successful"

            # Opcional: verificar si las tablas existen
            try:
                # Contar alertas (puede ser 0 si está vacía, y está bien)
                alert_count = db.execute(text("SELECT COUNT(*) FROM alerts")).scalar()
                health_status["database"]["alert_count"] = alert_count
                health_status["database"]["message"] = f"Database operational ({alert_count} alerts)"
            except Exception as table_error:
                # Las tablas no existen aún
                health_status["database"]["message"] = "Database connected but tables not initialized"
                health_status["database"]["tables_exist"] = False
        else:
            health_status["status"] = "degraded"
            health_status["database"]["status"] = "error"
            health_status["database"]["message"] = "Database query returned unexpected result"

    except Exception as e:
        # Database error - pero NO lanzamos excepción, solo reportamos
        health_status["status"] = "unhealthy"
        health_status["database"]["status"] = "disconnected"
        health_status["database"]["message"] = str(e)
        health_status["database"]["error_type"] = type(e).__name__

    return health_status


@router.get("/", response_model=list[schemas.Alert])
def get_alerts(
    skip: int = 0,
    limit: int = 5000,
    db: Session = Depends(database.get_db),
    # username: str = Depends(auth.verify_access_token)  # Verifica el token
):
    return crud.get_alerts(db, skip=skip, limit=limit)


@router.post("/", response_model=schemas.Alert)
def create_alert(
    alert: schemas.AlertCreate,
    db: Session = Depends(database.get_db),
    # username: str = Depends(auth.verify_access_token)  # Verifica el token
):
    return crud.create_alert(db, alert)


@router.get("/by_community", response_model=list[schemas.Alert])
def get_alerts_by_community(
    community_id: Optional[str] = Query("", alias="community_id"),
    type: str = "",
    priority: str = "",
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    # username: str = Depends(auth.verify_access_token)
):
    return crud.get_alerts_by_community(db, community_id, type, priority, skip, limit)


@router.get("/inactive", response_model=list[schemas.Alert])
def get_inactive_alerts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    # username: str = Depends(auth.verify_access_token)
):
    return crud.get_inactive_alerts(db, skip=skip, limit=limit)


@router.put("/reactivate/{alert_id}", response_model=schemas.Alert)
def reactivate_alert(
    alert_id: int,
    db: Session = Depends(database.get_db),
    # username: str = Depends(auth.verify_access_token)
):
    return crud.reactivate_alert(db, alert_id)


@router.put("/deactivate/{alert_id}", response_model=schemas.Alert)
def deactivate_alert(
    alert_id: int,
    db: Session = Depends(database.get_db),
    # username: str = Depends(auth.verify_access_token)
):
    return crud.deactivate_alert(db, alert_id)
