import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime

from models import Location, WeatherData
from schemas import GeocodeResponse

class TestWeatherEndpoints:
    """Pruebas para los endpoints de datos meteorológicos."""
    
    def test_root_endpoint(self, client: TestClient):
        """Test: El endpoint raíz debería retornar información del servicio."""
        # Act
        response = client.get("/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Servicio de Datos Meteorológicos"
        assert data["version"] == "1.0.0"
        assert "endpoints" in data
    
    def test_health_endpoint_healthy(self, client: TestClient):
        """Test: El endpoint de salud debería retornar estado saludable."""
        # Act
        response = client.get("/health")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
    
    def test_get_current_weather_missing_params(self, client: TestClient):
        """Test: Debería retornar error 400 si faltan parámetros."""
        # Act
        response = client.get("/api/v1/weather/current")
        
        # Assert
        assert response.status_code == 400
        assert "coordenadas" in response.json()["detail"]
    
    @patch('services.weather_service.weather_service.find_or_create_location')
    @patch('services.weather_service.weather_service.collect_current_weather')
    def test_get_current_weather_success(self, mock_collect, mock_find, client: TestClient, 
                                       sample_location_data, sample_weather_data):
        """Test: Debería obtener datos meteorológicos actuales exitosamente."""
        # Arrange
        mock_location = Location(id=1, **sample_location_data)
        mock_find.return_value = mock_location
        
        mock_weather = WeatherData(
            id=1,
            location_id=1,
            data_source="OpenMeteo",
            recorded_at=datetime.now(),
            **sample_weather_data
        )
        mock_collect.return_value = mock_weather
        
        # Act
        response = client.get(
            "/api/v1/weather/current",
            params={"location_name": "Bogotá", "refresh": True}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["location"]["name"] == "Bogotá"
        assert data["current_weather"]["temperature"] == 18.5
        assert data["current_weather"]["data_source"] == "OpenMeteo"
    
    @patch('services.weather_service.weather_service.find_or_create_location')
    def test_get_current_weather_location_not_found(self, mock_find, client: TestClient):
        """Test: Debería retornar error 404 si no se encuentra la ubicación."""
        # Arrange
        mock_find.return_value = None
        
        # Act
        response = client.get(
            "/api/v1/weather/current",
            params={"location_name": "ubicación_inexistente"}
        )
        
        # Assert
        assert response.status_code == 404
        assert "No se pudo encontrar" in response.json()["detail"]
    
    def test_get_weather_forecast_missing_params(self, client: TestClient):
        """Test: Debería retornar error 400 si faltan parámetros para pronóstico."""
        # Act
        response = client.get("/api/v1/weather/forecast")
        
        # Assert
        assert response.status_code == 400
    
    @patch('services.weather_service.weather_service.find_or_create_location')
    @patch('services.weather_service.weather_service.collect_weather_forecast')
    def test_get_weather_forecast_success(self, mock_collect, mock_find, client: TestClient,
                                        sample_location_data):
        """Test: Debería obtener pronóstico meteorológico exitosamente."""
        # Arrange
        mock_location = Location(id=1, **sample_location_data)
        mock_find.return_value = mock_location
        
        from models import WeatherForecast
        mock_forecasts = [
            WeatherForecast(
                id=1,
                location_id=1,
                forecast_date=datetime(2024, 1, 2),
                temperature_max=25.0,
                temperature_min=15.0,
                data_source="OpenMeteo",
                forecast_generated_at=datetime.now()
            )
        ]
        mock_collect.return_value = mock_forecasts
        
        # Act
        response = client.get(
            "/api/v1/weather/forecast",
            params={"latitude": 4.6097, "longitude": -74.0817, "days": 1, "refresh": True}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["location"]["name"] == "Bogotá"
        assert len(data["forecast_data"]) == 1
        assert data["forecast_data"][0]["temperature_max"] == 25.0
    
    def test_get_historical_weather_invalid_dates(self, client: TestClient):
        """Test: Debería retornar error si las fechas son inválidas."""
        # Act
        response = client.get(
            "/api/v1/weather/historical",
            params={
                "location_name": "Bogotá",
                "start_date": "2024-01-02",
                "end_date": "2024-01-01"  # Fecha fin menor que inicio
            }
        )
        
        # Assert
        assert response.status_code == 400
        assert "fecha de fin debe ser mayor" in response.json()["detail"]
    
    @patch('services.geocoding_service.geocoding_service.geocode_location')
    def test_geocode_location_success(self, mock_geocode, client: TestClient):
        """Test: Debería geocodificar una ubicación exitosamente."""
        # Arrange
        mock_geocode.return_value = [
            GeocodeResponse(
                name="Bogotá",
                display_name="Bogotá, Colombia",
                latitude=4.6097,
                longitude=-74.0817,
                country="Colombia",
                state="Cundinamarca",
                city="Bogotá"
            )
        ]
        
        # Act
        response = client.post(
            "/api/v1/weather/geocode",
            json={"location_name": "Bogotá"}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Bogotá"
        assert data[0]["latitude"] == 4.6097
        assert data[0]["longitude"] == -74.0817
    
    @patch('services.geocoding_service.geocoding_service.geocode_location')
    def test_geocode_location_not_found(self, mock_geocode, client: TestClient):
        """Test: Debería retornar error 404 si no se encuentra la ubicación."""
        # Arrange
        mock_geocode.return_value = []
        
        # Act
        response = client.post(
            "/api/v1/weather/geocode",
            json={"location_name": "ubicación_inexistente"}
        )
        
        # Assert
        assert response.status_code == 404
        assert "No se encontraron resultados" in response.json()["detail"]

class TestAdminEndpoints:
    """Pruebas para los endpoints administrativos."""
    
    def test_list_locations_empty(self, client: TestClient):
        """Test: Debería retornar lista vacía si no hay ubicaciones."""
        # Act
        response = client.get("/api/v1/admin/locations")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data == []
    
    def test_list_locations_with_data(self, client: TestClient, db_session, sample_location_data):
        """Test: Debería listar ubicaciones existentes."""
        # Arrange
        location = Location(**sample_location_data)
        db_session.add(location)
        db_session.commit()
        
        # Act
        response = client.get("/api/v1/admin/locations")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Bogotá"
        assert data[0]["country"] == "Colombia"
    
    def test_list_locations_with_search(self, client: TestClient, db_session, sample_location_data):
        """Test: Debería filtrar ubicaciones por búsqueda."""
        # Arrange
        location1 = Location(**sample_location_data)
        
        location2_data = sample_location_data.copy()
        location2_data["name"] = "Medellín"
        location2_data["latitude"] = 6.2442
        location2_data["longitude"] = -75.5812
        location2 = Location(**location2_data)
        
        db_session.add_all([location1, location2])
        db_session.commit()
        
        # Act
        response = client.get("/api/v1/admin/locations", params={"search": "Bog"})
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Bogotá"
    
    def test_refresh_location_not_found(self, client: TestClient):
        """Test: Debería retornar error 404 para ubicación inexistente."""
        # Act
        response = client.post("/api/v1/admin/locations/999/refresh")
        
        # Assert
        assert response.status_code == 404
        assert "Ubicación no encontrada" in response.json()["detail"]
    
    @patch('services.weather_service.weather_service.collect_current_weather')
    def test_refresh_location_success(self, mock_collect, client: TestClient, 
                                    db_session, sample_location_data, sample_weather_data):
        """Test: Debería actualizar datos de ubicación exitosamente."""
        # Arrange
        location = Location(**sample_location_data)
        db_session.add(location)
        db_session.commit()
        db_session.refresh(location)
        
        mock_weather = WeatherData(
            id=1,
            location_id=location.id,
            data_source="OpenMeteo",
            recorded_at=datetime.now(),
            **sample_weather_data
        )
        mock_collect.return_value = mock_weather
        
        # Act
        response = client.post(f"/api/v1/admin/locations/{location.id}/refresh")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Datos actualizados" in data["message"]
        assert data["data"]["records_updated"] >= 1
    
    def test_get_system_stats(self, client: TestClient, db_session, sample_location_data):
        """Test: Debería obtener estadísticas del sistema."""
        # Arrange
        location = Location(**sample_location_data)
        db_session.add(location)
        db_session.commit()
        
        # Act
        response = client.get("/api/v1/admin/stats")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "total_locations" in data
        assert "total_weather_records" in data
        assert "total_forecasts" in data
        assert data["total_locations"] == 1
    
    def test_cleanup_old_data_dry_run(self, client: TestClient):
        """Test: Debería mostrar datos a eliminar en modo dry-run."""
        # Act
        response = client.delete("/api/v1/admin/data/cleanup", params={"dry_run": True})
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["dry_run"] is True
        assert "Se eliminarían" in data["message"] 