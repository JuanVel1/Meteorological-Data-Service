import httpx
import asyncio
from typing import List, Optional
from config import settings
from schemas import GeocodeResponse
import logging

logger = logging.getLogger(__name__)

class GeocodingService:
    def __init__(self):
        self.base_url = settings.NOMINATIM_API_URL
        self.headers = {
            'User-Agent': 'Meteorological-Data-Service/1.0 (your-email@domain.com)'
        }
    
    async def geocode_location(self, location_name: str, country: Optional[str] = None) -> List[GeocodeResponse]:
        """
        Geocodifica una ubicación usando Nominatim OpenStreetMap API
        """
        try:
            params = {
                'q': location_name,
                'format': 'json',
                'limit': 5,
                'addressdetails': 1,
                'extratags': 1
            }
            
            if country:
                params['countrycodes'] = country.lower()
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/search",
                    params=params,
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                
                results = response.json()
                geocoded_locations = []
                
                for result in results:
                    try:
                        geocoded_location = GeocodeResponse(
                            name=result.get('name', location_name),
                            display_name=result.get('display_name', ''),
                            latitude=float(result['lat']),
                            longitude=float(result['lon']),
                            country=result.get('address', {}).get('country', ''),
                            state=result.get('address', {}).get('state', None),
                            city=result.get('address', {}).get('city', 
                                  result.get('address', {}).get('town', 
                                  result.get('address', {}).get('village', None)))
                        )
                        geocoded_locations.append(geocoded_location)
                    except (KeyError, ValueError) as e:
                        logger.warning(f"Error procesando resultado de geocodificación: {e}")
                        continue
                
                return geocoded_locations
                
        except httpx.HTTPError as e:
            logger.error(f"Error HTTP en geocodificación: {e}")
            return []
        except Exception as e:
            logger.error(f"Error inesperado en geocodificación: {e}")
            return []
    
    async def reverse_geocode(self, latitude: float, longitude: float) -> Optional[GeocodeResponse]:
        """
        Geocodificación reversa: obtiene información de ubicación desde coordenadas
        """
        try:
            params = {
                'lat': latitude,
                'lon': longitude,
                'format': 'json',
                'addressdetails': 1
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/reverse",
                    params=params,
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                
                result = response.json()
                
                if result and 'error' not in result:
                    return GeocodeResponse(
                        name=result.get('name', f"Lat: {latitude}, Lon: {longitude}"),
                        display_name=result.get('display_name', ''),
                        latitude=latitude,
                        longitude=longitude,
                        country=result.get('address', {}).get('country', ''),
                        state=result.get('address', {}).get('state', None),
                        city=result.get('address', {}).get('city', 
                              result.get('address', {}).get('town', 
                              result.get('address', {}).get('village', None)))
                    )
                return None
                
        except httpx.HTTPError as e:
            logger.error(f"Error HTTP en geocodificación reversa: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado en geocodificación reversa: {e}")
            return None

# Instancia singleton del servicio
geocoding_service = GeocodingService() 