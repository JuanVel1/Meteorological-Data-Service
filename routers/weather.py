from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional

from database import get_db
from schemas import (
    WeatherResponse, WeatherQuery, GeocodeRequest, GeocodeResponse,
    LocationResponse, APIResponse, ErrorResponse
)
from services.weather_service import weather_service
from services.geocoding_service import geocoding_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/weather", tags=["Datos Meteorológicos"])

@router.get("/current", response_model=WeatherResponse, 
           summary="Obtener datos meteorológicos actuales")
async def get_current_weather(
    location_name: Optional[str] = Query(None, description="Nombre de la ubicación"),
    latitude: Optional[float] = Query(None, ge=-90, le=90, description="Latitud"),
    longitude: Optional[float] = Query(None, ge=-180, le=180, description="Longitud"),
    refresh: bool = Query(False, description="Forzar actualización desde APIs externas"),
    db: Session = Depends(get_db)
):
    """
    Obtiene datos meteorológicos actuales para una ubicación.
    
    Puedes especificar la ubicación por:
    - Nombre de la ubicación (ej: "Bogotá, Colombia")
    - Coordenadas (latitud y longitud)
    """
    try:
        if not location_name and (latitude is None or longitude is None):
            raise HTTPException(
                status_code=400, 
                detail="Debe proporcionar el nombre de la ubicación o las coordenadas (latitud y longitud)"
            )
        
        # Buscar o crear ubicación
        location = await weather_service.find_or_create_location(
            db, location_name or "", latitude, longitude
        )
        
        if not location:
            raise HTTPException(
                status_code=404,
                detail="No se pudo encontrar o geocodificar la ubicación especificada"
            )
        
        current_weather = None
        
        if refresh:
            # Obtener datos frescos de APIs externas
            current_weather = await weather_service.collect_current_weather(db, location)
        
        if not current_weather:
            # Obtener datos más recientes de la base de datos
            current_weather = weather_service.get_current_weather_from_db(db, location.id)
        
        # Si no hay datos en la DB y no se forzó actualización, intentar obtener datos frescos
        if not current_weather and not refresh:
            current_weather = await weather_service.collect_current_weather(db, location)
        
        return WeatherResponse(
            location=LocationResponse.from_orm(location),
            current_weather=current_weather,
            historical_data=[],
            forecast_data=[]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo datos meteorológicos actuales: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/forecast", response_model=WeatherResponse,
           summary="Obtener pronóstico meteorológico")
async def get_weather_forecast(
    location_name: Optional[str] = Query(None, description="Nombre de la ubicación"),
    latitude: Optional[float] = Query(None, ge=-90, le=90, description="Latitud"),
    longitude: Optional[float] = Query(None, ge=-180, le=180, description="Longitud"),
    days: int = Query(7, ge=1, le=14, description="Número de días de pronóstico"),
    refresh: bool = Query(False, description="Forzar actualización desde APIs externas"),
    db: Session = Depends(get_db)
):
    """
    Obtiene pronóstico meteorológico para una ubicación.
    """
    try:
        if not location_name and (latitude is None or longitude is None):
            raise HTTPException(
                status_code=400,
                detail="Debe proporcionar el nombre de la ubicación o las coordenadas"
            )
        
        # Buscar o crear ubicación
        location = await weather_service.find_or_create_location(
            db, location_name or "", latitude, longitude
        )
        
        if not location:
            raise HTTPException(
                status_code=404,
                detail="No se pudo encontrar o geocodificar la ubicación especificada"
            )
        
        forecast_data = []
        
        if refresh:
            # Obtener pronósticos frescos
            forecast_data = await weather_service.collect_weather_forecast(db, location, days)
        else:
            # Obtener pronósticos de la base de datos
            forecast_data = weather_service.get_weather_forecasts_from_db(db, location.id)
            
            # Si no hay datos o son pocos, obtener datos frescos
            if len(forecast_data) < days:
                fresh_forecasts = await weather_service.collect_weather_forecast(db, location, days)
                if fresh_forecasts:
                    forecast_data = fresh_forecasts
        
        return WeatherResponse(
            location=LocationResponse.from_orm(location),
            current_weather=None,
            historical_data=[],
            forecast_data=forecast_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo pronóstico meteorológico: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/historical", response_model=WeatherResponse,
           summary="Obtener datos meteorológicos históricos")
async def get_historical_weather(
    location_name: Optional[str] = Query(None, description="Nombre de la ubicación"),
    latitude: Optional[float] = Query(None, ge=-90, le=90, description="Latitud"),
    longitude: Optional[float] = Query(None, ge=-180, le=180, description="Longitud"),
    start_date: datetime = Query(..., description="Fecha de inicio (YYYY-MM-DD)"),
    end_date: datetime = Query(..., description="Fecha de fin (YYYY-MM-DD)"),
    data_source: Optional[str] = Query(None, description="Fuente de datos específica"),
    db: Session = Depends(get_db)
):
    """
    Obtiene datos meteorológicos históricos para una ubicación y rango de fechas.
    """
    try:
        if not location_name and (latitude is None or longitude is None):
            raise HTTPException(
                status_code=400,
                detail="Debe proporcionar el nombre de la ubicación o las coordenadas"
            )
        
        if end_date < start_date:
            raise HTTPException(
                status_code=400,
                detail="La fecha de fin debe ser mayor que la fecha de inicio"
            )
        
        # Buscar ubicación
        location = await weather_service.find_or_create_location(
            db, location_name or "", latitude, longitude
        )
        
        if not location:
            raise HTTPException(
                status_code=404,
                detail="No se pudo encontrar la ubicación especificada"
            )
        
        # Obtener datos históricos
        historical_data = weather_service.get_historical_weather(
            db, location.id, start_date, end_date, data_source
        )
        
        return WeatherResponse(
            location=LocationResponse.from_orm(location),
            current_weather=None,
            historical_data=historical_data,
            forecast_data=[]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo datos históricos: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.post("/geocode", response_model=List[GeocodeResponse],
            summary="Geocodificar ubicación")
async def geocode_location(request: GeocodeRequest):
    """
    Geocodifica una ubicación para obtener sus coordenadas.
    """
    try:
        geocoded_locations = await geocoding_service.geocode_location(
            request.location_name, request.country
        )
        
        if not geocoded_locations:
            raise HTTPException(
                status_code=404,
                detail="No se encontraron resultados para la ubicación especificada"
            )
        
        return geocoded_locations
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en geocodificación: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor") 