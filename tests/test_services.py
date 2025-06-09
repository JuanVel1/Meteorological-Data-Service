import pytest
import httpx
from unittest.mock import AsyncMock, patch
from datetime import datetime

from services.geocoding_service import GeocodingService
from services.weather_apis import OpenMeteoService
from services.weather_service import WeatherService
from models import Location
from schemas import GeocodeResponse

class TestGeocodingService:
    """Pruebas para el servicio de geocodificación."""
    
    @pytest.mark.asyncio
    async def test_geocode_location_success(self, mock_nominatim_response):
        """Test: Debería geocodificar una ubicación exitosamente."""
        # Arrange
        service = GeocodingService()
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_nominatim_response
            mock_response.raise_for_status = AsyncMock()
            mock_get.return_value = mock_response
            
            # Act
            results = await service.geocode_location("Bogotá")
            
            # Assert
            assert len(results) == 1
            assert results[0].name == "Bogotá"
            assert results[0].latitude == 4.6097
            assert results[0].longitude == -74.0817
            assert results[0].country == "Colombia"
    
    @pytest.mark.asyncio
    async def test_geocode_location_no_results(self):
        """Test: Debería manejar cuando no hay resultados."""
        # Arrange
        service = GeocodingService()
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            mock_response.raise_for_status = AsyncMock()
            mock_get.return_value = mock_response
            
            # Act
            results = await service.geocode_location("ubicación_inexistente")
            
            # Assert
            assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_geocode_location_api_error(self):
        """Test: Debería manejar errores de la API."""
        # Arrange
        service = GeocodingService()
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = httpx.HTTPError("Connection failed")
            
            # Act
            results = await service.geocode_location("Bogotá")
            
            # Assert
            assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_reverse_geocode_success(self, mock_nominatim_response):
        """Test: Debería hacer geocodificación reversa exitosamente."""
        # Arrange
        service = GeocodingService()
        reverse_response = mock_nominatim_response[0]
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = reverse_response
            mock_response.raise_for_status = AsyncMock()
            mock_get.return_value = mock_response
            
            # Act
            result = await service.reverse_geocode(4.6097, -74.0817)
            
            # Assert
            assert result is not None
            assert result.name == "Bogotá"
            assert result.latitude == 4.6097
            assert result.longitude == -74.0817

class TestOpenMeteoService:
    """Pruebas para el servicio de Open-Meteo."""
    
    @pytest.mark.asyncio
    async def test_get_current_weather_success(self, mock_open_meteo_response):
        """Test: Debería obtener datos meteorológicos actuales exitosamente."""
        # Arrange
        service = OpenMeteoService()
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_open_meteo_response
            mock_response.raise_for_status = AsyncMock()
            mock_get.return_value = mock_response
            
            # Act
            result = await service.get_current_weather(4.6097, -74.0817)
            
            # Assert
            assert result is not None
            assert result["temperature"] == 18.5
            assert result["humidity"] == 75.0
            assert result["pressure"] == 1013.25
            assert result["data_source"] == "OpenMeteo"
    
    @pytest.mark.asyncio
    async def test_get_current_weather_api_error(self):
        """Test: Debería manejar errores de la API de Open-Meteo."""
        # Arrange
        service = OpenMeteoService()
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = httpx.HTTPError("API Error")
            
            # Act
            result = await service.get_current_weather(4.6097, -74.0817)
            
            # Assert
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_weather_forecast_success(self):
        """Test: Debería obtener pronóstico meteorológico exitosamente."""
        # Arrange
        service = OpenMeteoService()
        forecast_response = {
            "daily": {
                "time": ["2024-01-01", "2024-01-02"],
                "temperature_2m_max": [25.0, 24.0],
                "temperature_2m_min": [15.0, 14.0],
                "precipitation_probability_max": [30.0, 40.0],
                "weather_code": [3, 1]
            }
        }
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = forecast_response
            mock_response.raise_for_status = AsyncMock()
            mock_get.return_value = mock_response
            
            # Act
            results = await service.get_weather_forecast(4.6097, -74.0817, 2)
            
            # Assert
            assert len(results) == 2
            assert results[0]["temperature_max"] == 25.0
            assert results[0]["temperature_min"] == 15.0
            assert results[1]["temperature_max"] == 24.0

class TestWeatherService:
    """Pruebas para el servicio principal de datos meteorológicos."""
    
    @pytest.mark.asyncio
    async def test_find_or_create_location_existing(self, db_session, sample_location_data):
        """Test: Debería encontrar una ubicación existente."""
        # Arrange
        service = WeatherService()
        
        # Crear ubicación existente
        existing_location = Location(**sample_location_data)
        db_session.add(existing_location)
        db_session.commit()
        db_session.refresh(existing_location)
        
        # Act
        result = await service.find_or_create_location(
            db_session, 
            "Bogotá", 
            sample_location_data["latitude"], 
            sample_location_data["longitude"]
        )
        
        # Assert
        assert result is not None
        assert result.id == existing_location.id
        assert result.name == "Bogotá"
    
    @pytest.mark.asyncio
    async def test_find_or_create_location_new(self, db_session, mock_nominatim_response):
        """Test: Debería crear una nueva ubicación."""
        # Arrange
        service = WeatherService()
        
        with patch('services.geocoding_service.geocoding_service.geocode_location') as mock_geocode:
            mock_geocode.return_value = [
                GeocodeResponse(
                    name="Medellín",
                    display_name="Medellín, Colombia",
                    latitude=6.2442,
                    longitude=-75.5812,
                    country="Colombia",
                    state="Antioquia",
                    city="Medellín"
                )
            ]
            
            # Act
            result = await service.find_or_create_location(db_session, "Medellín")
            
            # Assert
            assert result is not None
            assert result.name == "Medellín"
            assert result.latitude == 6.2442
            assert result.longitude == -75.5812
            
            # Verificar que se guardó en la base de datos
            saved_location = db_session.query(Location).filter(Location.name == "Medellín").first()
            assert saved_location is not None
    
    @pytest.mark.asyncio
    async def test_collect_current_weather_success(self, db_session, sample_location_data, mock_open_meteo_response):
        """Test: Debería recolectar datos meteorológicos actuales exitosamente."""
        # Arrange
        service = WeatherService()
        
        # Crear ubicación
        location = Location(**sample_location_data)
        db_session.add(location)
        db_session.commit()
        db_session.refresh(location)
        
        with patch('services.weather_apis.open_meteo_service.get_current_weather') as mock_weather:
            mock_weather.return_value = {
                "temperature": 18.5,
                "humidity": 75.0,
                "pressure": 1013.25,
                "recorded_at": datetime.now(),
                "data_source": "OpenMeteo"
            }
            
            # Act
            result = await service.collect_current_weather(db_session, location)
            
            # Assert
            assert result is not None
            assert result.temperature == 18.5
            assert result.humidity == 75.0
            assert result.location_id == location.id
            
            # Verificar que se guardó en la base de datos
            assert result.id is not None
    
    def test_get_historical_weather(self, db_session, sample_location_data, sample_weather_data):
        """Test: Debería obtener datos históricos correctamente."""
        # Arrange
        service = WeatherService()
        
        # Crear ubicación
        location = Location(**sample_location_data)
        db_session.add(location)
        db_session.commit()
        db_session.refresh(location)
        
        # Crear datos históricos
        from models import WeatherData
        weather1 = WeatherData(
            location_id=location.id,
            data_source="OpenMeteo",
            recorded_at=datetime(2024, 1, 1, 12, 0),
            **sample_weather_data
        )
        weather2 = WeatherData(
            location_id=location.id,
            data_source="OpenMeteo", 
            recorded_at=datetime(2024, 1, 2, 12, 0),
            temperature=20.0,
            humidity=80.0
        )
        
        db_session.add_all([weather1, weather2])
        db_session.commit()
        
        # Act
        results = service.get_historical_weather(
            db_session,
            location.id,
            datetime(2024, 1, 1),
            datetime(2024, 1, 3)
        )
        
        # Assert
        assert len(results) == 2
        assert results[0].recorded_at > results[1].recorded_at  # Ordenado desc
        assert all(r.location_id == location.id for r in results) 