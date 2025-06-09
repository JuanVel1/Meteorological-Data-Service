from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import func, and_

from database import get_db
from models import Location, WeatherData, WeatherForecast, DataLog, Alert
from schemas import (
    APIResponse, LocationResponse, DataLogResponse, WeatherDataResponse,
    AlertResponse, AlertQuery, AlertStatistics
)
from services.weather_service import weather_service
from services.alert_service import alert_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

@router.get("/locations", response_model=List[LocationResponse],
           summary="Listar todas las ubicaciones")
async def list_locations(
    skip: int = Query(0, ge=0, description="Registros a omitir"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros"),
    search: Optional[str] = Query(None, description="Buscar por nombre de ubicación"),
    db: Session = Depends(get_db)
):
    """
    Lista todas las ubicaciones registradas en el sistema.
    """
    try:
        query = db.query(Location)
        
        if search:
            query = query.filter(Location.name.ilike(f"%{search}%"))
        
        locations = query.offset(skip).limit(limit).all()
        
        return [LocationResponse.from_orm(location) for location in locations]
        
    except Exception as e:
        logger.error(f"Error listando ubicaciones: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.post("/locations/{location_id}/refresh", response_model=APIResponse,
            summary="Actualizar datos de una ubicación")
async def refresh_location_data(
    location_id: int,
    include_forecast: bool = Query(True, description="Incluir actualización de pronósticos"),
    db: Session = Depends(get_db)
):
    """
    Fuerza la actualización de datos meteorológicos para una ubicación específica.
    """
    try:
        # Buscar la ubicación
        location = db.query(Location).filter(Location.id == location_id).first()
        
        if not location:
            raise HTTPException(status_code=404, detail="Ubicación no encontrada")
        
        records_updated = 0
        
        # Actualizar datos actuales
        current_weather = await weather_service.collect_current_weather(db, location)
        if current_weather:
            records_updated += 1
        
        # Actualizar pronósticos si se solicita
        if include_forecast:
            forecasts = await weather_service.collect_weather_forecast(db, location)
            records_updated += len(forecasts)
        
        return APIResponse(
            success=True,
            message=f"Datos actualizados para {location.name}",
            data={"records_updated": records_updated}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando datos de ubicación: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/logs", response_model=List[DataLogResponse],
            summary="Obtener logs del sistema")
async def get_system_logs(
    skip: int = Query(0, ge=0, description="Registros a omitir"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros"),
    data_source: Optional[str] = Query(None, description="Filtrar por fuente de datos"),
    status: Optional[str] = Query(None, description="Filtrar por estado (success, error, warning)"),
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin"),
    db: Session = Depends(get_db)
):
    """
    Obtiene logs de operaciones del sistema.
    """
    try:
        query = db.query(DataLog)
        
        if data_source:
            query = query.filter(DataLog.data_source == data_source)
        
        if status:
            query = query.filter(DataLog.status == status)
        
        if start_date:
            query = query.filter(DataLog.created_at >= start_date)
        
        if end_date:
            query = query.filter(DataLog.created_at <= end_date)
        
        logs = query.order_by(DataLog.created_at.desc()).offset(skip).limit(limit).all()
        
        return [
            {
                "id": log.id,
                "data_source": log.data_source,
                "status": log.status,
                "message": log.message,
                "records_processed": log.records_processed,
                "execution_time": log.execution_time,
                "created_at": log.created_at
            }
            for log in logs
        ]
        
    except Exception as e:
        logger.error(f"Error obteniendo logs: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/stats", summary="Estadísticas del sistema")
async def get_system_stats(
    days: int = Query(7, ge=1, le=365, description="Número de días para estadísticas"),
    db: Session = Depends(get_db)
):
    """
    Obtiene estadísticas generales del sistema.
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Estadísticas básicas
        total_locations = db.query(Location).count()
        total_weather_records = db.query(WeatherData).filter(
            WeatherData.created_at >= cutoff_date
        ).count()
        total_forecasts = db.query(WeatherForecast).filter(
            WeatherForecast.created_at >= cutoff_date
        ).count()
        
        # Registros por fuente de datos
        data_sources = db.query(
            WeatherData.data_source,
            func.count(WeatherData.id).label('count')
        ).filter(
            WeatherData.created_at >= cutoff_date
        ).group_by(WeatherData.data_source).all()
        
        # Ubicación con más datos
        most_active_location = db.query(
            Location.name,
            func.count(WeatherData.id).label('count')
        ).join(WeatherData).filter(
            WeatherData.created_at >= cutoff_date
        ).group_by(Location.id, Location.name).order_by(
            func.count(WeatherData.id).desc()
        ).first()
        
        # Estadísticas de alertas
        alert_stats = alert_service.get_alert_statistics(db, days)
        
        return {
            "success": True,
            "data": {
                "period_days": days,
                "locations": {
                    "total": total_locations
                },
                "weather_data": {
                    "total_records": total_weather_records,
                    "by_source": dict(data_sources),
                    "most_active_location": {
                        "name": most_active_location[0] if most_active_location else None,
                        "record_count": most_active_location[1] if most_active_location else 0
                    }
                },
                "forecasts": {
                    "total_records": total_forecasts
                },
                "alerts": {
                    "total": alert_stats.total_alerts,
                    "active": alert_stats.active_alerts,
                    "by_type": alert_stats.alerts_by_type,
                    "by_risk_level": alert_stats.alerts_by_risk_level
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.delete("/cleanup", response_model=APIResponse,
              summary="Limpiar datos antiguos")
async def cleanup_old_data(
    days: int = Query(90, ge=30, le=365, description="Días de datos a conservar"),
    dry_run: bool = Query(True, description="Solo mostrar qué se eliminaría sin ejecutar"),
    db: Session = Depends(get_db)
):
    """
    Elimina datos meteorológicos antiguos para liberar espacio.
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Contar registros que se eliminarían
        weather_count = db.query(WeatherData).filter(
            WeatherData.created_at < cutoff_date
        ).count()
        
        forecast_count = db.query(WeatherForecast).filter(
            WeatherForecast.created_at < cutoff_date
        ).count()
        
        alert_count = db.query(Alert).filter(
            and_(
                Alert.created_at < cutoff_date,
                Alert.is_active == False
            )
        ).count()
        
        log_count = db.query(DataLog).filter(
            DataLog.created_at < cutoff_date
        ).count()
        
        if dry_run:
            return {
                "success": True,
                "message": "Vista previa de limpieza (no se eliminó nada)",
                "data": {
                    "cutoff_date": cutoff_date.isoformat(),
                    "would_delete": {
                        "weather_records": weather_count,
                        "forecasts": forecast_count,
                        "inactive_alerts": alert_count,
                        "logs": log_count
                    }
                }
            }
        
        # Ejecutar limpieza real
        deleted_weather = db.query(WeatherData).filter(
            WeatherData.created_at < cutoff_date
        ).delete()
        
        deleted_forecasts = db.query(WeatherForecast).filter(
            WeatherForecast.created_at < cutoff_date
        ).delete()
        
        deleted_alerts = db.query(Alert).filter(
            and_(
                Alert.created_at < cutoff_date,
                Alert.is_active == False
            )
        ).delete()
        
        deleted_logs = db.query(DataLog).filter(
            DataLog.created_at < cutoff_date
        ).delete()
        
        db.commit()
        
        return {
            "success": True,
            "message": "Limpieza ejecutada exitosamente",
            "data": {
                "cutoff_date": cutoff_date.isoformat(),
                "deleted": {
                    "weather_records": deleted_weather,
                    "forecasts": deleted_forecasts,
                    "inactive_alerts": deleted_alerts,
                    "logs": deleted_logs
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error en limpieza de datos: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error durante la limpieza")

# Nuevos endpoints para alertas

@router.get("/alerts", response_model=List[AlertResponse],
            summary="Obtener todas las alertas")
async def get_all_alerts(
    location_id: Optional[int] = Query(None, description="Filtrar por ubicación"),
    alert_type: Optional[str] = Query(None, description="Tipo de alerta"),
    risk_level: Optional[str] = Query(None, description="Nivel de riesgo"),
    is_active: Optional[bool] = Query(None, description="Solo alertas activas"),
    hours: int = Query(24, ge=1, le=168, description="Horas hacia atrás"),
    limit: int = Query(100, ge=1, le=500, description="Límite de alertas"),
    db: Session = Depends(get_db)
):
    """
    Obtiene todas las alertas del sistema.
    """
    try:
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        query = db.query(Alert).filter(Alert.created_at >= cutoff_time)
        
        if location_id:
            query = query.filter(Alert.location_id == location_id)
        if alert_type:
            query = query.filter(Alert.alert_type == alert_type)
        if risk_level:
            query = query.filter(Alert.risk_level == risk_level)
        if is_active is not None:
            query = query.filter(Alert.is_active == is_active)
        
        alerts = query.order_by(Alert.created_at.desc()).limit(limit).all()
        return alerts
        
    except Exception as e:
        logger.error(f"Error obteniendo alertas: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/alerts/statistics", response_model=AlertStatistics,
            summary="Obtener estadísticas de alertas")
async def get_alert_statistics(
    days: int = Query(30, ge=1, le=365, description="Días para estadísticas"),
    db: Session = Depends(get_db)
):
    """
    Obtiene estadísticas de alertas.
    """
    try:
        stats = alert_service.get_alert_statistics(db, days)
        return stats
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de alertas: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.patch("/alerts/{alert_id}/deactivate", response_model=APIResponse,
              summary="Desactivar una alerta específica")
async def deactivate_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """
    Desactiva una alerta específica.
    """
    try:
        success = alert_service.deactivate_alert(db, alert_id)
        
        if success:
            return APIResponse(
                success=True,
                message=f"Alerta {alert_id} desactivada exitosamente"
            )
        else:
            raise HTTPException(status_code=404, detail="Alerta no encontrada")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error desactivando alerta {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/alerts/types", summary="Obtener tipos de alertas disponibles")
async def get_alert_types():
    """
    Obtiene los tipos de alertas disponibles.
    """
    return {
        "success": True,
        "data": {
            "alert_types": [
                "temperatura_alta",
                "temperatura_baja", 
                "lluvia_intensa",
                "viento_fuerte",
                "humedad_alta"
            ],
            "risk_levels": [
                "bajo",
                "medio",
                "alto",
                "crítico"
            ],
            "severity_levels": [
                "info",
                "warning", 
                "watch",
                "advisory"
            ]
        }
    } 