from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import asyncio
import logging

from models import Location, WeatherData, WeatherForecast, DataLog
from schemas import WeatherDataCreate, WeatherForecastCreate
from services.geocoding_service import geocoding_service
from services.weather_apis import open_meteo_service, worldclim_service
from services.alert_service import alert_service

logger = logging.getLogger(__name__)

class WeatherService:
    """Servicio principal para coordinar la obtención de datos meteorológicos"""
    
    def __init__(self):
        self.data_sources = {
            'OpenMeteo': open_meteo_service,
            'WorldClim': worldclim_service
        }
    
    async def find_or_create_location(self, db: Session, location_name: str, 
                                    latitude: Optional[float] = None, 
                                    longitude: Optional[float] = None) -> Optional[Location]:
        """
        Encuentra una ubicación existente o crea una nueva
        """
        try:
            # Buscar ubicación existente
            if latitude and longitude:
                location = db.query(Location).filter(
                    (Location.latitude.between(latitude - 0.001, latitude + 0.001)) &
                    (Location.longitude.between(longitude - 0.001, longitude + 0.001))
                ).first()
            else:
                location = db.query(Location).filter(
                    Location.name.ilike(f"%{location_name}%")
                ).first()
            
            if location:
                return location
            
            # Si no existe, geocodificar
            if latitude and longitude:
                geocoded = await geocoding_service.reverse_geocode(latitude, longitude)
            else:
                geocoded_results = await geocoding_service.geocode_location(location_name)
                geocoded = geocoded_results[0] if geocoded_results else None
            
            if not geocoded:
                return None
            
            # Crear nueva ubicación
            new_location = Location(
                name=geocoded.get('name', location_name),
                country=geocoded.get('country', ''),
                state=geocoded.get('state', ''),
                city=geocoded.get('city', ''),
                latitude=geocoded.get('latitude', latitude),
                longitude=geocoded.get('longitude', longitude)
            )
            
            db.add(new_location)
            db.commit()
            db.refresh(new_location)
            
            return new_location
            
        except Exception as e:
            logger.error(f"Error encontrando/creando ubicación: {e}")
            return None
    
    async def collect_current_weather(self, db: Session, location: Location) -> Optional[WeatherData]:
        """
        Recolecta datos meteorológicos actuales para una ubicación específica
        """
        try:
            # Obtener datos de Open-Meteo
            weather_data = await open_meteo_service.get_current_weather(
                location.latitude, location.longitude
            )
            
            if not weather_data:
                return None
            
            # Crear registro en la base de datos con campos compatibles
            db_weather_data = WeatherData(
                location_id=location.id,
                time=weather_data.get('recorded_at', datetime.now()),
                # Campos principales para compatibilidad
                temperature=weather_data.get('temperature_2m'),
                humidity=weather_data.get('relativehumidity_2m'),
                pressure=weather_data.get('pressure_msl'),
                wind_speed=weather_data.get('windspeed_10m'),
                wind_direction=weather_data.get('wind_direction'),
                precipitation=weather_data.get('precipitation'),
                weather_description=weather_data.get('weather_description'),
                weather_code=str(weather_data.get('weathercode', '')),
                cloud_cover=weather_data.get('cloudcover'),
                # Campos específicos de Open-Meteo
                temperature_2m=weather_data.get('temperature_2m'),
                relativehumidity_2m=weather_data.get('relativehumidity_2m'),
                dewpoint_2m=weather_data.get('dewpoint_2m'),
                rain=weather_data.get('rain'),
                weathercode=weather_data.get('weathercode'),
                windspeed_10m=weather_data.get('windspeed_10m'),
                windgusts_10m=weather_data.get('windgusts_10m'),
                cloudcover=weather_data.get('cloudcover'),
                pressure_msl=weather_data.get('pressure_msl'),
                surface_pressure=weather_data.get('surface_pressure'),
                visibility=weather_data.get('visibility'),
                uv_index=weather_data.get('uv_index'),
                data_source='OpenMeteo',
                recorded_at=weather_data.get('recorded_at', datetime.now())
            )
            
            db.add(db_weather_data)
            db.commit()
            db.refresh(db_weather_data)
            
            # Evaluar alertas
            try:
                await asyncio.create_task(
                    asyncio.to_thread(alert_service.evaluate_weather_data, db, db_weather_data)
                )
            except Exception as e:
                logger.warning(f"Error evaluando alertas: {e}")
            
            return db_weather_data
            
        except Exception as e:
            logger.error(f"Error recolectando datos meteorológicos: {e}")
            return None
    
    async def get_current_weather_by_location(self, db: Session, location_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el clima actual para una ubicación específica por nombre
        """
        try:
            # Buscar la ubicación en la base de datos
            location = db.query(Location).filter(
                Location.name.ilike(f"%{location_name}%")
            ).first()
            
            if not location:
                # Si no existe, intentar geocodificar
                geocoded = await geocoding_service.geocode_location(location_name)
                if not geocoded:
                    return None
                
                # Crear nueva ubicación
                location = Location(
                    name=geocoded['name'],
                    country=geocoded.get('country', ''),
                    state=geocoded.get('state', ''),
                    city=geocoded.get('city', ''),
                    latitude=geocoded['latitude'],
                    longitude=geocoded['longitude']
                )
                db.add(location)
                db.commit()
                db.refresh(location)
            
            # Obtener datos meteorológicos actuales
            weather_data = None
            
            # Usar Open-Meteo como fuente principal
            try:
                openmeteo_data = await open_meteo_service.get_current_weather(
                    location.latitude, location.longitude
                )
                if openmeteo_data:
                    weather_data = WeatherData(
                        location_id=location.id,
                        time=openmeteo_data.get('recorded_at', datetime.now()),
                        temperature_2m=openmeteo_data.get('temperature_2m'),
                        relativehumidity_2m=openmeteo_data.get('relativehumidity_2m'),
                        dewpoint_2m=openmeteo_data.get('dewpoint_2m'),
                        rain=openmeteo_data.get('rain'),
                        precipitation=openmeteo_data.get('precipitation'),
                        weathercode=openmeteo_data.get('weathercode'),
                        weather_description=openmeteo_data.get('weather_description'),
                        windspeed_10m=openmeteo_data.get('windspeed_10m'),
                        wind_direction=openmeteo_data.get('wind_direction'),
                        windgusts_10m=openmeteo_data.get('windgusts_10m'),
                        cloudcover=openmeteo_data.get('cloudcover'),
                        pressure_msl=openmeteo_data.get('pressure_msl'),
                        surface_pressure=openmeteo_data.get('surface_pressure'),
                        visibility=openmeteo_data.get('visibility'),
                        uv_index=openmeteo_data.get('uv_index'),
                        data_source='OpenMeteo',
                        recorded_at=openmeteo_data.get('recorded_at', datetime.now())
                    )
                    
                    db.add(weather_data)
                    db.commit()
                    db.refresh(weather_data)
                    
                    # Evaluar alertas meteorológicas
                    await asyncio.create_task(
                        asyncio.to_thread(alert_service.evaluate_weather_data, db, weather_data)
                    )
                    
            except Exception as e:
                logger.warning(f"Error obteniendo datos de Open-Meteo: {e}")
            
            # Registrar la ejecución
            self._log_execution(db, 'OpenMeteo', 'success' if weather_data else 'error', 
                              1 if weather_data else 0)
            
            return {
                'location': location,
                'weather_data': weather_data,
                'data_source': 'OpenMeteo'
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo clima actual: {e}")
            self._log_execution(db, 'WeatherService', 'error', 0, str(e))
            return None
    
    async def get_current_weather_by_coordinates(self, db: Session, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """
        Obtiene el clima actual para coordenadas específicas
        """
        try:
            # Buscar ubicación existente cercana (radio de ~1km)
            location = db.query(Location).filter(
                (Location.latitude.between(latitude - 0.01, latitude + 0.01)) &
                (Location.longitude.between(longitude - 0.01, longitude + 0.01))
            ).first()
            
            if not location:
                # Crear nueva ubicación con geocodificación inversa
                geocoded = await geocoding_service.reverse_geocode(latitude, longitude)
                location_name = geocoded.get('name', f"Lat:{latitude:.4f}, Lon:{longitude:.4f}")
                
                location = Location(
                    name=location_name,
                    country=geocoded.get('country', ''),
                    state=geocoded.get('state', ''),
                    city=geocoded.get('city', ''),
                    latitude=latitude,
                    longitude=longitude
                )
                db.add(location)
                db.commit()
                db.refresh(location)
            
            # Obtener datos meteorológicos de Open-Meteo
            openmeteo_data = await open_meteo_service.get_current_weather(latitude, longitude)
            
            if openmeteo_data:
                weather_data = WeatherData(
                    location_id=location.id,
                    time=openmeteo_data.get('recorded_at', datetime.now()),
                    temperature_2m=openmeteo_data.get('temperature_2m'),
                    relativehumidity_2m=openmeteo_data.get('relativehumidity_2m'),
                    dewpoint_2m=openmeteo_data.get('dewpoint_2m'),
                    rain=openmeteo_data.get('rain'),
                    precipitation=openmeteo_data.get('precipitation'),
                    weathercode=openmeteo_data.get('weathercode'),
                    weather_description=openmeteo_data.get('weather_description'),
                    windspeed_10m=openmeteo_data.get('windspeed_10m'),
                    wind_direction=openmeteo_data.get('wind_direction'),
                    windgusts_10m=openmeteo_data.get('windgusts_10m'),
                    cloudcover=openmeteo_data.get('cloudcover'),
                    pressure_msl=openmeteo_data.get('pressure_msl'),
                    surface_pressure=openmeteo_data.get('surface_pressure'),
                    visibility=openmeteo_data.get('visibility'),
                    uv_index=openmeteo_data.get('uv_index'),
                    data_source='OpenMeteo',
                    recorded_at=openmeteo_data.get('recorded_at', datetime.now())
                )
                
                db.add(weather_data)
                db.commit()
                db.refresh(weather_data)
                
                # Evaluar alertas
                await asyncio.create_task(
                    asyncio.to_thread(alert_service.evaluate_weather_data, db, weather_data)
                )
                
                self._log_execution(db, 'OpenMeteo', 'success', 1)
                
                return {
                    'location': location,
                    'weather_data': weather_data,
                    'data_source': 'OpenMeteo'
                }
            
            self._log_execution(db, 'OpenMeteo', 'error', 0)
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo clima por coordenadas: {e}")
            self._log_execution(db, 'WeatherService', 'error', 0, str(e))
            return None
    
    async def get_weather_forecast(self, db: Session, location_id: int, days: int = 7) -> List[WeatherForecast]:
        """
        Obtiene pronóstico meteorológico para una ubicación
        """
        try:
            location = db.query(Location).filter(Location.id == location_id).first()
            if not location:
                return []
            
            # Obtener pronóstico de Open-Meteo
            forecast_data = await open_meteo_service.get_forecast(
                location.latitude, location.longitude, days
            )
            
            if not forecast_data:
                self._log_execution(db, 'OpenMeteo', 'error', 0)
                return []
            
            forecasts = []
            for data in forecast_data:
                forecast = WeatherForecast(
                    location_id=location.id,
                    forecast_date=data['forecast_date'],
                    temperature_max=data.get('temperature_max'),
                    temperature_min=data.get('temperature_min'),
                    humidity=data.get('humidity'),
                    precipitation_probability=data.get('precipitation_probability'),
                    precipitation_amount=data.get('precipitation_amount'),
                    wind_speed=data.get('wind_speed'),
                    wind_direction=data.get('wind_direction'),
                    weather_description=data.get('weather_description'),
                    weather_code=data.get('weather_code'),
                    data_source=data['data_source'],
                    forecast_generated_at=data['forecast_generated_at']
                )
                forecasts.append(forecast)
                db.add(forecast)
            
            db.commit()
            self._log_execution(db, 'OpenMeteo', 'success', len(forecasts))
            
            return forecasts
            
        except Exception as e:
            logger.error(f"Error obteniendo pronóstico: {e}")
            self._log_execution(db, 'WeatherService', 'error', 0, str(e))
            return []
    
    async def get_historical_weather(self, db: Session, location_id: int, 
                                   start_date: datetime, end_date: datetime) -> List[WeatherData]:
        """
        Obtiene datos meteorológicos históricos
        """
        try:
            # Buscar datos existentes en la base de datos
            existing_data = db.query(WeatherData).filter(
                WeatherData.location_id == location_id,
                WeatherData.time >= start_date,
                WeatherData.time <= end_date
            ).order_by(WeatherData.time.desc()).all()
            
            logger.info(f"Encontrados {len(existing_data)} registros históricos en BD")
            return existing_data
            
        except Exception as e:
            logger.error(f"Error obteniendo datos históricos: {e}")
            self._log_execution(db, 'WeatherService', 'error', 0, str(e))
            return []
    
    def _log_execution(self, db: Session, data_source: str, status: str, 
                      records_processed: int, message: str = None):
        """
        Registra la ejecución de un proceso de obtención de datos
        """
        try:
            log_entry = DataLog(
                data_source=data_source,
                status=status,
                message=message,
                records_processed=records_processed,
                execution_time=0.0  # Se podría implementar medición de tiempo
            )
            db.add(log_entry)
            db.commit()
        except Exception as e:
            logger.error(f"Error registrando log: {e}")

# Instancia singleton del servicio
weather_service = WeatherService() 