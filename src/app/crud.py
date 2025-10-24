from sqlalchemy.orm import Session
from app import models, schemas, auth
from datetime import datetime
from sqlalchemy import and_


def create_alert(db: Session, alert: schemas.AlertCreate):
    db_alert = models.Alert(
        title=alert.title,
        description=alert.description,
        level=alert.level,
        type=alert.type,
        region=alert.region,
        status=alert.status,
        expires_at=alert.expires_at,
        timestamp=datetime.utcnow(),
        latitude=alert.latitude,  # Asignar latitud
        longitude=alert.longitude  # Asignar longitud
    )
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert

def get_alerts(db: Session, skip: int = 0, limit: int = 10):
    alerts = db.query(models.Alert).offset(skip).limit(limit).all()
    now = datetime.now()
    updated = False
    for alert in alerts:
        if alert.status == "activo" and alert.expires_at < now:
            alert.status = "inactivo"
            db.add(alert)
            updated = True
    if updated:
        db.commit()
    return alerts



def get_alerts_by_community(
    db: Session,
    community_name: str = "",
    type: str = "",
    priority: str = "",
    skip: int = 0,
    limit: int = 10
):
    filters = []
    if community_name:
        filters.append(models.Alert.region.ilike(f"%{community_name}%"))
    if type:
        filters.append(models.Alert.type == type)
    if priority:
        filters.append(models.Alert.level == priority)
    query = db.query(models.Alert)
    if filters:
        query = query.filter(and_(*filters))
    return query.offset(skip).limit(limit).all()

def get_inactive_alerts(db: Session, skip: int = 0, limit: int = 10):
    alerts = db.query(models.Alert).filter(models.Alert.status == "inactivo").offset(skip).limit(limit).all()
    now = datetime.now()
    updated = False
    for alert in alerts:
        if alert.status == "activo" and alert.expires_at < now:
            alert.status = "inactivo"
            db.add(alert)
            updated = True
    if updated:
        db.commit()
    return alerts

def reactivate_alert(db: Session, alert_id: int):
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if alert:
        alert.status = "activo"
        db.commit()
        db.refresh(alert)
    return alert

def deactivate_alert(db: Session, alert_id: int):
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if alert:
        alert.status = "inactivo"
        db.commit()
        db.refresh(alert)
    return alert