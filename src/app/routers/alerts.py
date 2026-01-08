"""
Router de alertas refactorizado - CORREGIDO
"""
import sys
import logging
from datetime import datetime
from typing import Optional, List
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..dependencies import get_alert_service, get_data_source_service, get_db
from ..schemas import (
    AlertCreateSchema, AlertUpdateSchema, AlertResponseSchema, 
    AlertFilterSchema, HealthCheckSchema, StatisticsSchema,
    DataSourceCreateSchema, DataSourceResponseSchema,
    PaginatedAlertsResponse
)
from ...domain.services import AlertService, DataSourceService
from ...domain.exceptions import (
    AlertNotFoundException, InvalidAlertDataException, 
    DuplicateAlertException, AlertExpiredException
)
from ...domain.entities import AlertFilter, AlertLevel, AlertStatus, AlertType
# CAMBIO: Usar logger estándar en lugar del personalizado
from ...infrastructure.logging import get_logger

# Logger para este módulo
logger = get_logger("alerts_router")

router = APIRouter(prefix="/alerts", tags=["Alerts"])

# ================================
# HEALTH CHECK
# ================================

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint para monitoreo - SIMPLIFICADO
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": {"status": "unknown", "message": ""},
        "version": "1.0.0",
        "environment": "development"
    }

    try:
        # Verificar conexión a base de datos
        from sqlalchemy import text
        result = db.execute(text("SELECT 1")).scalar()

        if result == 1:
            health_status["database"]["status"] = "connected"
            health_status["database"]["message"] = "Database connection successful"
            
            # Contar alertas
            alert_count = db.execute(text("SELECT COUNT(*) FROM alerts")).scalar()
            health_status["database"]["alert_count"] = alert_count
            
            # Log simplificado
            logger.info(
                "Health check successful",
                extra={
                    "event_type": "health_check",
                    "database_status": "connected",
                    "alert_count": alert_count
                }
            )
        else:
            health_status["status"] = "degraded"
            health_status["database"]["status"] = "error"
            health_status["database"]["message"] = "Database query returned unexpected result"

    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["database"]["status"] = "disconnected"
        health_status["database"]["message"] = str(e)
        health_status["database"]["error_type"] = type(e).__name__
        
        # Log de error simplificado
        logger.error(
            f"Health check failed: {str(e)}",
            extra={
                "event_type": "health_check_error",
                "error_type": type(e).__name__
            }
        )

    return health_status

# ================================
# ENDPOINT DE EXPIRACIÓN
# ================================

@router.post("/expire/check")
def check_expired_alerts(
    alert_service: AlertService = Depends(get_alert_service)
):
    """
    Verificar y marcar alertas expiradas como resueltas
    """
    try:
        logger.info("Starting expired alerts check")
        
        expired_count = alert_service.process_expired_alerts()
        
        result = {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "expired_alerts_processed": expired_count,
            "message": f"Processed {expired_count} expired alerts"
        }
        
        logger.info(
            f"Expired alerts check completed: {expired_count} alerts processed",
            extra={
                "event_type": "expired_alerts_check",
                "expired_count": expired_count
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error checking expired alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error procesando alertas expiradas: {str(e)}")

@router.get("/expire/status")
def get_expiration_status(
    db: Session = Depends(get_db)
):
    """
    Obtener estadísticas sobre alertas expiradas
    """
    try:
        from sqlalchemy import text
        
        # Contar alertas por estado de expiración
        now = datetime.utcnow()
        
        total_alerts = db.execute(text("SELECT COUNT(*) FROM alerts")).scalar()
        active_alerts = db.execute(text("SELECT COUNT(*) FROM alerts WHERE status = 'active'")).scalar()
        
        # Alertas que han expirado pero siguen activas
        expired_active = db.execute(text(
            "SELECT COUNT(*) FROM alerts WHERE status = 'active' AND expires_at < :now"
        ), {"now": now}).scalar()
        
        # Alertas que expiran pronto (próximas 24 horas)
        from sqlalchemy import text
        expiring_soon = db.execute(text(
            "SELECT COUNT(*) FROM alerts WHERE status = 'active' AND expires_at > :now AND expires_at < :future"
        ), {
            "now": now,
            "future": now.replace(hour=23, minute=59, second=59)  # Fin del día
        }).scalar()
        
        result = {
            "status": "success",
            "timestamp": now.isoformat(),
            "statistics": {
                "total_alerts": total_alerts,
                "active_alerts": active_alerts,
                "expired_but_active": expired_active,
                "expiring_today": expiring_soon
            },
            "needs_cleanup": expired_active > 0
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting expiration status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo estado de expiración: {str(e)}")

# ================================
# CRUD DE ALERTAS
# ================================

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_alert(
    alert_data: AlertCreateSchema,
    alert_service: AlertService = Depends(get_alert_service)
):
    """Crear una nueva alerta - SIMPLIFICADO"""
    try:
        alert = alert_service.create_alert(
            title=alert_data.title,
            description=alert_data.description,
            level=alert_data.level.value,
            type=alert_data.type.value,
            region=alert_data.region,
            expires_at=alert_data.expires_at,
            latitude=alert_data.latitude,
            longitude=alert_data.longitude,
            source=alert_data.source
        )
        
        logger.info(
            f"Alert created successfully: {alert.title}",
            extra={
                "event_type": "alert_created",
                "alert_id": alert.id,
                "level": alert.level.value,
                "region": alert.region
            }
        )
        
        return AlertResponseSchema.from_domain(alert).dict()
        
    except (InvalidAlertDataException, DuplicateAlertException) as e:
        logger.warning(
            f"Invalid alert data: {e.message}",
            extra={"error_code": e.error_code}
        )
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error creating alert: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/")
def get_alerts(
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(20, ge=1, le=100, description="Elementos por página"),
    level: Optional[AlertLevel] = Query(None, description="Filtrar por nivel"),
    type: Optional[AlertType] = Query(None, description="Filtrar por tipo"), 
    region: Optional[str] = Query(None, description="Filtrar por región"),
    status: Optional[AlertStatus] = Query(None, description="Filtrar por estado"),
    active_only: bool = Query(False, description="Solo alertas activas"),
    high_priority_only: bool = Query(False, description="Solo alertas de alta prioridad"),
    check_expired: bool = Query(True, description="Verificar alertas expiradas antes de devolver resultados"),
    alert_service: AlertService = Depends(get_alert_service),
    db: Session = Depends(get_db)  # Agregar esta línea
):
    """
    Obtener lista de alertas con filtros y paginación - CON VERIFICACIÓN DE EXPIRACIÓN
    """
    try:
        # Log del request
        logger.info(
            f"Getting alerts: page={page}, per_page={per_page}, level={level}",
            extra={
                "page": page,
                "per_page": per_page,
                "level": str(level) if level else None,
                "type": str(type) if type else None,
                "check_expired": check_expired
            }
        )
        
        # Verificar alertas expiradas si está habilitado
        expired_count = 0
        if check_expired:
            try:
                expired_count = alert_service.process_expired_alerts()
                if expired_count > 0:
                    logger.info(f"Processed {expired_count} expired alerts before query")
            except Exception as e:
                logger.warning(f"Error processing expired alerts: {e}")
        
        # Crear filtro SOLO si hay valores no None
        filter_params = {}
        if level is not None:
            filter_params['level'] = level
        if type is not None:
            filter_params['type'] = type
        if region is not None:
            filter_params['region'] = region
        if status is not None:
            filter_params['status'] = status
        if active_only:
            filter_params['active_only'] = active_only
        if high_priority_only:
            filter_params['high_priority_only'] = high_priority_only
        
        # Crear filtro solo si hay parámetros
        alert_filter = AlertFilter(**filter_params) if filter_params else None
        
        logger.info(f"Created filter: {filter_params}")
        
        # Obtener alertas
        if alert_filter:
            all_alerts = alert_service.get_filtered_alerts(alert_filter)
        else:
            all_alerts = alert_service.get_all_alerts()
        
        logger.info(f"Found {len(all_alerts)} alerts")
        
        # Paginación manual
        total = len(all_alerts)
        pages = ceil(total / per_page) if total > 0 else 1
        start = (page - 1) * per_page
        end = start + per_page
        alerts_page = all_alerts[start:end]
        
        # Convertir a dict directamente para evitar problemas de schema
        alert_dicts = []
        for alert in alerts_page:
            try:
                alert_schema = AlertResponseSchema.from_domain(alert)
                alert_dicts.append(alert_schema.dict())
            except Exception as e:
                logger.error(f"Error converting alert {alert.id}: {e}")
                # Crear dict básico manualmente
                alert_dicts.append({
                    "id": alert.id,
                    "title": alert.title,
                    "description": alert.description,
                    "level": alert.level.value if hasattr(alert.level, 'value') else str(alert.level),
                    "type": alert.type.value if hasattr(alert.type, 'value') else str(alert.type),
                    "region": alert.region,
                    "status": alert.status.value if hasattr(alert.status, 'value') else str(alert.status),
                    "timestamp": alert.timestamp.isoformat() if alert.timestamp else None,
                    "expires_at": alert.expires_at.isoformat() if alert.expires_at else None
                })
        
        result = {
            "items": alert_dicts,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1,
            "expired_processed": expired_count if check_expired else None
        }
        
        logger.info(f"Returning {len(alert_dicts)} alerts")
        return result
        
    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.get("/{alert_id}")
def get_alert(
    alert_id: int,
    alert_service: AlertService = Depends(get_alert_service)
):
    """Obtener una alerta específica por ID - SIMPLIFICADO"""
    try:
        alert = alert_service.get_alert_by_id(alert_id)
        alert_schema = AlertResponseSchema.from_domain(alert)
        return alert_schema.dict()
    except AlertNotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Error getting alert {alert_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.put("/{alert_id}", status_code=status.HTTP_200_OK)
def update_alert_full(
    alert_id: int,
    alert_data: AlertUpdateSchema,
    alert_service: AlertService = Depends(get_alert_service)
):
    """Actualizar completamente una alerta existente (PUT) - SIMPLIFICADO"""
    try:
        # Preparar datos para actualización
        update_dict = alert_data.dict(exclude_unset=False, exclude_none=False)
        
        # Convertir enums a valores si existen
        if 'level' in update_dict and update_dict['level']:
            update_dict['level'] = update_dict['level'].value
        if 'type' in update_dict and update_dict['type']:
            update_dict['type'] = update_dict['type'].value
        if 'status' in update_dict and update_dict['status']:
            update_dict['status'] = update_dict['status'].value
        
        alert = alert_service.update_alert(alert_id, update_dict)
        
        logger.info(
            f"Alert updated successfully: {alert_id}",
            extra={
                "event_type": "alert_updated",
                "alert_id": alert.id,
                "method": "PUT"
            }
        )
        
        return AlertResponseSchema.from_domain(alert).dict()
        
    except AlertNotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except (InvalidAlertDataException, DuplicateAlertException) as e:
        logger.warning(f"Invalid alert data for update: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Error updating alert {alert_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.patch("/{alert_id}", status_code=status.HTTP_200_OK)
def update_alert_partial(
    alert_id: int,
    alert_data: AlertUpdateSchema,
    alert_service: AlertService = Depends(get_alert_service)
):
    """Actualizar parcialmente una alerta existente (PATCH) - SIMPLIFICADO"""
    try:
        # Preparar datos para actualización (solo incluir campos con valores)
        update_dict = alert_data.dict(exclude_unset=True, exclude_none=True)
        
        # Convertir enums a valores si existen
        if 'level' in update_dict and update_dict['level']:
            update_dict['level'] = update_dict['level'].value
        if 'type' in update_dict and update_dict['type']:
            update_dict['type'] = update_dict['type'].value
        if 'status' in update_dict and update_dict['status']:
            update_dict['status'] = update_dict['status'].value
        
        alert = alert_service.update_alert(alert_id, update_dict)
        
        logger.info(
            f"Alert partially updated successfully: {alert_id}",
            extra={
                "event_type": "alert_updated",
                "alert_id": alert.id,
                "method": "PATCH",
                "fields_updated": list(update_dict.keys())
            }
        )
        
        return AlertResponseSchema.from_domain(alert).dict()
        
    except AlertNotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except (InvalidAlertDataException, DuplicateAlertException) as e:
        logger.warning(f"Invalid alert data for update: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Error partially updating alert {alert_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(
    alert_id: int,
    alert_service: AlertService = Depends(get_alert_service)
):
    """Eliminar una alerta existente - SIMPLIFICADO"""
    try:
        alert_service.delete_alert(alert_id)
        
        logger.info(
            f"Alert deleted successfully: {alert_id}",
            extra={
                "event_type": "alert_deleted",
                "alert_id": alert_id
            }
        )
        
        return None  # 204 No Content
        
    except AlertNotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Error deleting alert {alert_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# ================================
# ENDPOINTS ESPECIALES
# ================================

@router.get("/statistics/summary")
def get_statistics(
    alert_service: AlertService = Depends(get_alert_service)
):
    """Obtener estadísticas generales del sistema - SIMPLIFICADO"""
    try:
        stats = alert_service.get_alert_statistics()
        return stats  # Devolver dict directamente
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# Endpoints simplificados para debug
@router.get("/debug/simple")
def debug_simple():
    """Endpoint de debug super simple"""
    return {"status": "ok", "message": "Simple endpoint working"}

@router.get("/debug/count")
def debug_count(db: Session = Depends(get_db)):
    """Contar alertas directamente"""
    try:
        from sqlalchemy import text
        count = db.execute(text("SELECT COUNT(*) FROM alerts")).scalar()
        return {"count": count}
    except Exception as e:
        return {"error": str(e)}

@router.get("/debug/raw")
def debug_raw_alerts(db: Session = Depends(get_db)):
    """Ver alertas directas de BD"""
    try:
        from sqlalchemy import text
        result = db.execute(text("SELECT id, title, level, region, type, status, expires_at FROM alerts LIMIT 5"))
        alerts = []
        for row in result:
            alerts.append({
                "id": row[0],
                "title": row[1], 
                "level": row[2],
                "region": row[3],
                "type": row[4],
                "status": row[5],
                "expires_at": str(row[6]) if row[6] else None
            })
        return {"alerts": alerts}
    except Exception as e:
        return {"error": str(e)}

@router.get("/debug/types")
def debug_alert_types(db: Session = Depends(get_db)):
    """Ver tipos de alerta en BD"""
    try:
        from sqlalchemy import text
        result = db.execute(text("SELECT DISTINCT type, COUNT(*) FROM alerts GROUP BY type ORDER BY type"))
        types = []
        for row in result:
            types.append({
                "type": row[0],
                "count": row[1]
            })
        return {"types": types}
    except Exception as e:
        return {"error": str(e)}