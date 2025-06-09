import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from models import Location, WeatherData, WeatherForecast, DataLog, Alert, UserPreference
from database import get_db

class TestLocationModel:
    """Tests para el modelo Location"""
    
    def test_create_location(self, db_session: Session):
        """Test creación de ubicación"""
        location = Location(
            name="Bogotá",
            country="Colombia", 
            state="Cundinamarca",
            city="Bogotá",
            latitude=4.6097,
            longitude=-74.0817,
            altitude=2625
        )
        
        db_session.add(location)
        db_session.commit()
        db_session.refresh(location)
        
        assert location.id is not None
        assert location.name == "Bogotá"
        assert location.latitude == 4.6097
        assert location.longitude == -74.0817
        assert location.created_at is not None

    def test_location_relationships(self, db_session: Session):
        """Test relaciones de ubicación"""
        location = Location(
            name="Medellín",
            country="Colombia",
            state="Antioquia", 
            city="Medellín",
            latitude=6.2486,
            longitude=-75.5742
        )
        
        db_session.add(location)
        db_session.commit()
        db_session.refresh(location)
        
        # Verificar que las relaciones están definidas
        assert hasattr(location, 'weather_data')
        assert hasattr(location, 'weather_forecasts')
        assert hasattr(location, 'alerts')

class TestWeatherDataModel:
    """Tests para el modelo WeatherData"""
    
    def test_create_weather_data(self, db_session: Session, sample_location):
        """Test creación de datos meteorológicos"""
        weather_data = WeatherData(
            location_id=sample_location.id,
            time=datetime.now(),
            temperature_2m=25.5,
            relativehumidity_2m=65.0,
            dewpoint_2m=18.5,
            rain=0.0,
            precipitation=0.0,
            weathercode=1,
            weather_description="Principalmente despejado",
            windspeed_10m=10.2,
            wind_direction=270.0,
            windgusts_10m=15.5,
            cloudcover=25.0,
            pressure_msl=1013.25,
            surface_pressure=1010.0,
            visibility=10.0,
            uv_index=6.5,
            data_source="OpenMeteo",
            recorded_at=datetime.now()
        )
        
        db_session.add(weather_data)
        db_session.commit()
        db_session.refresh(weather_data)
        
        assert weather_data.id is not None
        assert weather_data.temperature_2m == 25.5
        assert weather_data.data_source == "OpenMeteo"
        assert weather_data.location_id == sample_location.id

    def test_weather_data_relationships(self, db_session: Session, sample_location):
        """Test relaciones de datos meteorológicos"""
        weather_data = WeatherData(
            location_id=sample_location.id,
            time=datetime.now(),
            temperature_2m=20.0,
            data_source="OpenMeteo",
            recorded_at=datetime.now()
        )
        
        db_session.add(weather_data)
        db_session.commit()
        db_session.refresh(weather_data)
        
        # Verificar relación con ubicación
        assert weather_data.location is not None
        assert weather_data.location.id == sample_location.id

class TestWeatherForecastModel:
    """Tests para el modelo WeatherForecast"""
    
    def test_create_weather_forecast(self, db_session: Session, sample_location):
        """Test creación de pronóstico meteorológico"""
        forecast = WeatherForecast(
            location_id=sample_location.id,
            forecast_date=datetime.now() + timedelta(days=1),
            temperature_max=28.0,
            temperature_min=18.0,
            humidity=70.0,
            precipitation_probability=30.0,
            precipitation_amount=2.5,
            wind_speed=12.0,
            wind_direction=180.0,
            weather_description="Parcialmente nublado",
            weather_code="2",
            data_source="OpenMeteo",
            forecast_generated_at=datetime.now()
        )
        
        db_session.add(forecast)
        db_session.commit()
        db_session.refresh(forecast)
        
        assert forecast.id is not None
        assert forecast.temperature_max == 28.0
        assert forecast.temperature_min == 18.0
        assert forecast.data_source == "OpenMeteo"

class TestAlertModel:
    """Tests para el modelo Alert"""
    
    def test_create_alert(self, db_session: Session, sample_location):
        """Test creación de alerta"""
        alert = Alert(
            location_id=sample_location.id,
            alert_type="temperatura_alta",
            risk_level="medio",
            severity="warning",
            threshold_value=35.0,
            current_value=37.2,
            alert_start=datetime.now(),
            is_active=True,
            description="Temperatura alta detectada",
            recommendations="Manténgase hidratado y evite exposición al sol"
        )
        
        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)
        
        assert alert.id is not None
        assert alert.alert_type == "temperatura_alta"
        assert alert.risk_level == "medio"
        assert alert.is_active is True

class TestUserPreferenceModel:
    """Tests para el modelo UserPreference"""
    
    def test_create_user_preference(self, db_session: Session, sample_location):
        """Test creación de preferencias de usuario"""
        preference = UserPreference(
            location_id=sample_location.id,
            notification_types='["temperatura_alta", "lluvia_intensa"]',
            alert_levels='["medio", "alto", "crítico"]',
            contact_method="email",
            timezone="America/Bogota",
            is_active=True
        )
        
        db_session.add(preference)
        db_session.commit()
        db_session.refresh(preference)
        
        assert preference.id is not None
        assert preference.location_id == sample_location.id
        assert preference.timezone == "America/Bogota"
        assert preference.is_active is True

class TestDataLogModel:
    """Tests para el modelo DataLog"""
    
    def test_create_data_log(self, db_session: Session):
        """Test creación de log de datos"""
        log = DataLog(
            data_source="OpenMeteo",
            status="success",
            message="Datos obtenidos correctamente",
            records_processed=5,
            execution_time=1.25
        )
        
        db_session.add(log)
        db_session.commit()
        db_session.refresh(log)
        
        assert log.id is not None
        assert log.data_source == "OpenMeteo"
        assert log.status == "success"
        assert log.records_processed == 5

    def test_create_error_log(self, db_session: Session):
        """Test creación de log de error"""
        error_log = DataLog(data_source="OpenMeteo", status="error", message="Failed")
        
        db_session.add(error_log)
        db_session.commit()
        db_session.refresh(error_log)
        
        assert error_log.id is not None
        assert error_log.status == "error"
        assert error_log.records_processed == 0

class TestModelConstraints:
    """Tests para restricciones del modelo"""
    
    def test_location_coordinates_validation(self, db_session: Session):
        """Test validación de coordenadas"""
        # Coordenadas válidas
        location = Location(
            name="Test Location",
            country="Test Country",
            latitude=45.0,
            longitude=90.0
        )
        
        db_session.add(location)
        db_session.commit()
        
        assert location.id is not None

    def test_weather_data_foreign_key(self, db_session: Session, sample_location):
        """Test clave foránea en datos meteorológicos"""
        weather_data = WeatherData(
            location_id=sample_location.id,
            time=datetime.now(),
            data_source="OpenMeteo",
            recorded_at=datetime.now()
        )
        
        db_session.add(weather_data)
        db_session.commit()
        
        # Verificar que la relación funciona
        assert weather_data.location.id == sample_location.id 