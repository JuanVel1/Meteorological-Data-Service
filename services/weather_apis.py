import aiohttp
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from config import settings

logger = logging.getLogger(__name__)

class OpenMeteoService:
    """Servicio para integración con Open-Meteo API"""
    
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1"
    
    async def get_current_weather(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """
        Obtiene datos meteorológicos actuales de Open-Meteo
        """
        try:
            params = {
                'latitude': latitude,
                'longitude': longitude,
                'current': 'temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,weather_code,cloud_cover,pressure_msl,surface_pressure,wind_speed_10m,wind_direction_10m,wind_gusts_10m',
                'timezone': 'auto'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/forecast", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        current = data.get('current', {})
                        
                        if current:
                            return {
                                'temperature_2m': current.get('temperature_2m'),
                                'relativehumidity_2m': current.get('relative_humidity_2m'),
                                'dewpoint_2m': current.get('apparent_temperature'),
                                'rain': current.get('rain', current.get('precipitation')),
                                'precipitation': current.get('precipitation'),
                                'weathercode': current.get('weather_code'),
                                'weather_description': self._get_weather_description(current.get('weather_code')),
                                'windspeed_10m': current.get('wind_speed_10m'),
                                'wind_direction': current.get('wind_direction_10m'),
                                'windgusts_10m': current.get('wind_gusts_10m'),
                                'cloudcover': current.get('cloud_cover'),
                                'pressure_msl': current.get('pressure_msl'),
                                'surface_pressure': current.get('surface_pressure'),
                                'visibility': None,  # No disponible en Open-Meteo
                                'uv_index': None,   # Requiere parámetro adicional
                                'data_source': 'OpenMeteo',
                                'recorded_at': datetime.fromisoformat(current.get('time').replace('Z', '+00:00'))
                            }
                    else:
                        logger.warning(f"Open-Meteo API respondió con código: {response.status}")
                        
        except aiohttp.ClientError as e:
            logger.error(f"Error HTTP en Open-Meteo: {e}")
        except Exception as e:
            logger.error(f"Error inesperado en Open-Meteo: {e}")
            
        return None
    
    async def get_forecast(self, latitude: float, longitude: float, days: int = 7) -> Optional[List[Dict[str, Any]]]:
        """
        Obtiene pronóstico meteorológico de Open-Meteo
        """
        try:
            params = {
                'latitude': latitude,
                'longitude': longitude,
                'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,wind_speed_10m_max,wind_direction_10m_dominant,weather_code',
                'timezone': 'auto',
                'forecast_days': min(days, 16)  # Open-Meteo soporta hasta 16 días
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/forecast", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        daily = data.get('daily', {})
                        
                        if daily and 'time' in daily:
                            forecasts = []
                            for i, date_str in enumerate(daily['time']):
                                forecast = {
                                    'forecast_date': datetime.fromisoformat(date_str),
                                    'temperature_max': daily.get('temperature_2m_max', [None])[i],
                                    'temperature_min': daily.get('temperature_2m_min', [None])[i],
                                    'humidity': None,  # No disponible en daily
                                    'precipitation_probability': daily.get('precipitation_probability_max', [None])[i],
                                    'precipitation_amount': daily.get('precipitation_sum', [None])[i],
                                    'wind_speed': daily.get('wind_speed_10m_max', [None])[i],
                                    'wind_direction': daily.get('wind_direction_10m_dominant', [None])[i],
                                    'weather_description': self._get_weather_description(
                                        daily.get('weather_code', [None])[i]
                                    ),
                                    'weather_code': str(daily.get('weather_code', [None])[i]),
                                    'data_source': 'OpenMeteo',
                                    'forecast_generated_at': datetime.now()
                                }
                                forecasts.append(forecast)
                            
                            return forecasts
                    else:
                        logger.warning(f"Open-Meteo forecast API respondió con código: {response.status}")
                        
        except aiohttp.ClientError as e:
            logger.error(f"Error HTTP en Open-Meteo forecast: {e}")
        except Exception as e:
            logger.error(f"Error inesperado en Open-Meteo forecast: {e}")
            
        return None
    
    async def get_weather_forecast(self, latitude: float, longitude: float, days: int = 7) -> Optional[List[Dict[str, Any]]]:
        """
        Alias para get_forecast - mantener compatibilidad con tests
        """
        return await self.get_forecast(latitude, longitude, days)
    
    def _get_weather_description(self, weather_code: Optional[int]) -> str:
        """
        Convierte códigos de clima de Open-Meteo a descripciones en español
        """
        if weather_code is None:
            return "Desconocido"
            
        weather_codes = {
            0: "Despejado",
            1: "Principalmente despejado",
            2: "Parcialmente nublado",
            3: "Nublado",
            45: "Niebla",
            48: "Niebla con escarcha",
            51: "Llovizna ligera",
            53: "Llovizna moderada",
            55: "Llovizna intensa",
            56: "Llovizna helada ligera",
            57: "Llovizna helada intensa",
            61: "Lluvia ligera",
            63: "Lluvia moderada",
            65: "Lluvia intensa",
            66: "Lluvia helada ligera",
            67: "Lluvia helada intensa",
            71: "Nieve ligera",
            73: "Nieve moderada",
            75: "Nieve intensa",
            77: "Granizo",
            80: "Chubascos ligeros",
            81: "Chubascos moderados",
            82: "Chubascos intensos",
            85: "Chubascos de nieve ligeros",
            86: "Chubascos de nieve intensos",
            95: "Tormenta",
            96: "Tormenta con granizo ligero",
            99: "Tormenta con granizo intenso"
        }
        
        return weather_codes.get(weather_code, f"Código {weather_code}")

class WorldClimService:
    """Servicio para datos climáticos históricos de WorldClim"""
    
    def __init__(self):
        self.base_url = "https://worldclim.org/data"
    
    async def get_historical_climate_data(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """
        Obtiene datos climáticos históricos de WorldClim
        Nota: WorldClim proporciona datos promedio mensuales, no datos en tiempo real
        """
        try:
            # WorldClim requiere descarga de archivos raster
            # Para este ejemplo, retornamos datos simulados
            # En implementación real, se necesitaría procesar archivos GeoTIFF
            
            logger.info(f"Solicitando datos históricos para lat:{latitude}, lon:{longitude}")
            
            # Simulación de datos climáticos promedio
            return {
                'temperature_avg': 20.0,  # Temperatura promedio anual
                'precipitation_avg': 100.0,  # Precipitación promedio mensual
                'humidity_avg': 70.0,
                'data_source': 'WorldClim',
                'data_type': 'historical_average',
                'period': '1970-2000'
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo datos históricos: {e}")
            return None

# Instancias de servicios
open_meteo_service = OpenMeteoService()
worldclim_service = WorldClimService() 