"""
Router de alertas refactorizado - Usa servicios de dominio
"""
import sys
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
from ...infrastructure.logging import logger, log_business_operation

router = APIRouter(prefix="/alerts", tags=["Alerts"])

# ================================
# HEALTH CHECK
# ================================

@router.get("/health", response_model=HealthCheckSchema)
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint para monitoreo

    Verifica:
    - Estado de la API
    - Conexión a la base de datos
    - Timestamp del check
    - Versión del sistema
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
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
            
            logger.info(
                "Health check successful",
                event_type="health_check",
                database_status="connected",
                alert_count=alert_count
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
        
        logger.error(
            f"Health check failed: {str(e)}",
            event_type="health_check_error",
            error_type=type(e).__name__
        )

    return health_status

# ================================
# CRUD DE ALERTAS
# ================================

@router.post("/", response_model=AlertResponseSchema, status_code=status.HTTP_201_CREATED)
def create_alert(
    alert_data: AlertCreateSchema,
    alert_service: AlertService = Depends(get_alert_service)
):
    """
    Crear una nueva alerta

    - **title**: Título descriptivo de la alerta
    - **description**: Descripción detallada
    - **level**: Nivel de severidad (info, warning, critical, emergency)
    - **type**: Tipo de alerta (weather, security, etc.)
    - **region**: Región afectada
    - **expires_at**: Fecha de expiración (opcional)
    - **latitude/longitude**: Coordenadas (opcional)
    - **source**: Fuente que genera la alerta (opcional)
    """
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
            event_type="alert_created",
            alert_id=alert.id,
            level=alert.level.value,
            region=alert.region
        )
        
        return AlertResponseSchema.from_domain(alert)
        
    except (InvalidAlertDataException, DuplicateAlertException) as e:
        logger.warning(f"Invalid alert data: {e.message}", error_code=e.error_code)
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error creating alert: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/", response_model=PaginatedAlertsResponse)
def get_alerts(
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(20, ge=1, le=100, description="Elementos por página"),
    level: Optional[AlertLevel] = Query(None, description="Filtrar por nivel"),
    type: Optional[AlertType] = Query(None, description="Filtrar por tipo"), 
    region: Optional[str] = Query(None, description="Filtrar por región"),
    status: Optional[AlertStatus] = Query(None, description="Filtrar por estado"),
    active_only: bool = Query(False, description="Solo alertas activas"),
    high_priority_only: bool = Query(False, description="Solo alertas de alta prioridad"),
    alert_service: AlertService = Depends(get_alert_service)
):
    """
    Obtener lista de alertas con filtros y paginación

    Parámetros de filtrado:
    - **level**: Nivel de severidad
    - **type**: Tipo de alerta  
    - **region**: Región (búsqueda parcial)
    - **status**: Estado de la alerta
    - **active_only**: Solo alertas activas y no expiradas
    - **high_priority_only**: Solo alertas críticas y de emergencia

    Paginación:
    - **page**: Número de página (empezando en 1)
    - **per_page**: Elementos por página (máximo 100)
    """
    try:
        # Crear filtro
        filter = AlertFilter(
            level=level,
            type=type,
            region=region,
            status=status,
            active_only=active_only,
            high_priority_only=high_priority_only
        )
        
        # Obtener todas las alertas filtradas
        all_alerts = alert_service.get_all_alerts(filter)
        
        # Paginación manual
        total = len(all_alerts)
        pages = ceil(total / per_page) if total > 0 else 1
        start = (page - 1) * per_page
        end = start + per_page
        alerts_page = all_alerts[start:end]
        
        # Convertir a schemas
        alert_schemas = [AlertResponseSchema.from_domain(alert) for alert in alerts_page]
        
        return PaginatedAlertsResponse(
            items=alert_schemas,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1
        )
        
    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/{alert_id}", response_model=AlertResponseSchema)
def get_alert(
    alert_id: int,
    alert_service: AlertService = Depends(get_alert_service)
):
    """
    Obtener una alerta específica por ID
    """
    try:
        alert = alert_service.get_alert_by_id(alert_id)
        return AlertResponseSchema.from_domain(alert)
    except AlertNotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Error getting alert {alert_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.put("/{alert_id}", response_model=AlertResponseSchema)
def update_alert(
    alert_id: int,
    alert_data: AlertUpdateSchema,
    alert_service: AlertService = Depends(get_alert_service)
):
    """
    Actualizar una alerta existente
    """
    try:
        # Obtener alerta actual
        alert = alert_service.get_alert_by_id(alert_id)
        
        # Actualizar solo campos proporcionados
        if alert_data.title is not None:
            alert.title = alert_data.title
        if alert_data.description is not None:
            alert.description = alert_data.description
        if alert_data.level is not None:
            from ...domain.entities import AlertLevel as DomainAlertLevel
            alert.level = DomainAlertLevel(alert_data.level.value)
        if alert_data.region is not None:
            alert.region = alert_data.region
        # ... más campos
        
        # Guardar cambios
        updated_alert = alert_service._repository.save(alert)
        
        logger.info(
            f"Alert updated: {alert_id}",
            event_type="alert_updated",
            alert_id=alert_id
        )
        
        return AlertResponseSchema.from_domain(updated_alert)
        
    except AlertNotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except (InvalidAlertDataException, AlertExpiredException) as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Error updating alert {alert_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.patch("/{alert_id}/resolve", response_model=AlertResponseSchema)
def resolve_alert(
    alert_id: int,
    alert_service: AlertService = Depends(get_alert_service)
):
    """
    Resolver una alerta (cambiar estado a 'resolved')
    """
    try:
        alert = alert_service.resolve_alert(alert_id)
        
        logger.info(
            f"Alert resolved: {alert_id}",
            event_type="alert_resolved",
            alert_id=alert_id
        )
        
        return AlertResponseSchema.from_domain(alert)
        
    except AlertNotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except (AlertExpiredException, InvalidAlertDataException) as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Error resolving alert {alert_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(
    alert_id: int,
    alert_service: AlertService = Depends(get_alert_service)
):
    """
    Eliminar una alerta
    """
    try:
        success = alert_service.delete_alert(alert_id)
        if success:
            logger.info(f"Alert deleted: {alert_id}", event_type="alert_deleted", alert_id=alert_id)
        return None
    except AlertNotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Error deleting alert {alert_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# ================================
# ENDPOINTS ESPECIALES
# ================================

@router.get("/statistics/summary", response_model=StatisticsSchema)
def get_statistics(
    alert_service: AlertService = Depends(get_alert_service)
):
    """
    Obtener estadísticas generales del sistema
    """
    try:
        stats = alert_service.get_alert_statistics()
        return StatisticsSchema(**stats)
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.post("/cleanup/expired", status_code=status.HTTP_200_OK)
def cleanup_expired_alerts(
    alert_service: AlertService = Depends(get_alert_service)
):
    """
    Limpiar alertas expiradas (marcarlas como resueltas)
    """
    try:
        processed = alert_service.cleanup_expired_alerts()
        
        logger.info(
            f"Expired alerts cleanup completed: {processed} processed",
            event_type="cleanup_expired",
            processed_count=processed
        )
        
        return {"message": f"{processed} alertas expiradas procesadas"}
    except Exception as e:
        logger.error(f"Error in cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")