from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app import crud, schemas, database, auth
from typing import Optional
from fastapi import Query

Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/alerts", tags=["Alerts"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=list[schemas.Alert])
def get_alerts(
    skip: int = 0,
    limit: int = 5000,
    db: Session = Depends(database.get_db),
    username: str = Depends(auth.verify_access_token)  # Verifica el token
):  
    return crud.get_alerts(db, skip=skip, limit=limit)

@router.post("/", response_model=schemas.Alert)
def create_alert(
    alert: schemas.AlertCreate,
    db: Session = Depends(database.get_db),
    username: str = Depends(auth.verify_access_token)  # Verifica el token
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
    username: str = Depends(auth.verify_access_token)
):
    return crud.get_alerts_by_community(db, community_id, type, priority, skip, limit)

@router.get("/inactive", response_model=list[schemas.Alert])
def get_inactive_alerts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    username: str = Depends(auth.verify_access_token)
):
    return crud.get_inactive_alerts(db, skip=skip, limit=limit)

@router.put("/reactivate/{alert_id}", response_model=schemas.Alert)
def reactivate_alert(
    alert_id: int,
    db: Session = Depends(database.get_db),
    username: str = Depends(auth.verify_access_token)
):
    return crud.reactivate_alert(db, alert_id)

@router.put("/deactivate/{alert_id}", response_model=schemas.Alert)
def deactivate_alert(
    alert_id: int,
    db: Session = Depends(database.get_db),
    username: str = Depends(auth.verify_access_token)
):
    return crud.deactivate_alert(db, alert_id)


