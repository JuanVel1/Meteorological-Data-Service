import pytest
import asyncio
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from database import Base, get_db
from main import app
import os

# Configurar base de datos de prueba
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
def event_loop():
    """Crear un event loop para toda la sesión de pruebas."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def db_session():
    """Crear base de datos de prueba para cada test."""
    # Crear todas las tablas
    Base.metadata.create_all(bind=engine)
    
    # Crear sesión
    session = TestingSessionLocal()
    
    yield session
    
    # Limpiar después del test
    session.close()
    
    # Eliminar todas las tablas
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client():
    """Cliente de prueba para FastAPI."""
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def sample_location_data():
    """Datos de ejemplo para ubicación."""
    return {
        "name": "Bogotá",
        "country": "Colombia",
        "state": "Cundinamarca", 
        "city": "Bogotá",
        "latitude": 4.6097,
        "longitude": -74.0817
    }

@pytest.fixture
def sample_location(db_session, sample_location_data):
    """Ubicación de ejemplo guardada en la base de datos."""
    from models import Location
    location = Location(**sample_location_data)
    db_session.add(location)
    db_session.commit()
    db_session.refresh(location)
    return location

@pytest.fixture
def sample_weather_data():
    """Datos de ejemplo para clima."""
    return {
        "temperature": 18.5,
        "humidity": 75.0,
        "pressure": 1013.25,
        "wind_speed": 5.2,
        "wind_direction": 270.0,
        "precipitation": 0.0,
        "weather_description": "Parcialmente nublado",
        "weather_code": "03",
        "cloud_cover": 45.0
    }

@pytest.fixture
def mock_open_meteo_response():
    """Respuesta mock de Open-Meteo API."""
    return {
        "current": {
            "time": "2024-01-01T12:00",
            "temperature_2m": 18.5,
            "relative_humidity_2m": 75.0,
            "pressure_msl": 1013.25,
            "wind_speed_10m": 5.2,
            "wind_direction_10m": 270.0,
            "precipitation": 0.0,
            "weather_code": 3,
            "cloud_cover": 45.0
        }
    }

@pytest.fixture
def mock_nominatim_response():
    """Respuesta mock de Nominatim API."""
    return [
        {
            "name": "Bogotá",
            "display_name": "Bogotá, Colombia",
            "lat": "4.6097",
            "lon": "-74.0817",
            "address": {
                "city": "Bogotá",
                "state": "Cundinamarca",
                "country": "Colombia"
            }
        }
    ]

# Configurar variables de entorno para testing
os.environ["DATABASE_URL"] = SQLALCHEMY_DATABASE_URL
os.environ["DEBUG"] = "True" 