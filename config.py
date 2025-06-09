import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Base de datos externa (Supabase)
    DATABASE_URL: str = "postgresql://user:password@db.supabase.co:5432/postgres"
    
    # APIs meteorológicas
    OPEN_METEO_API_URL: str = "https://api.open-meteo.com/v1/forecast"
    NOMINATIM_API_URL: str = "https://nominatim.openstreetmap.org"
    
    # Configuración del servidor
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # Configuración de logs
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        extra = "allow"  # Permitir campos extra para compatibilidad

settings = Settings() 