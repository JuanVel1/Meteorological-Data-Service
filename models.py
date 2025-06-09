from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Location(Base):
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    country = Column(String(100), nullable=False)
    state = Column(String(100))
    city = Column(String(100))
    region = Column(String(100))  # Agregado para compatibilidad
    latitude = Column(Float, nullable=False)  # Cambiado a Float para usar float8
    longitude = Column(Float, nullable=False)  # Cambiado a Float para usar float8
    altitude = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    weather_data = relationship("WeatherData", back_populates="location")
    weather_forecasts = relationship("WeatherForecast", back_populates="location")
    alerts = relationship("Alert", back_populates="location")
    user_preferences = relationship("UserPreference", back_populates="location")
    
    # Índices
    __table_args__ = (
        Index('idx_lat_lon', 'latitude', 'longitude'),
        Index('idx_region', 'region'),
    )

class WeatherData(Base):
    __tablename__ = "weather_data"
    
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    
    # Campos principales (compatibilidad con tests)
    time = Column(DateTime(timezone=True), nullable=False)
    temperature = Column(Float)  # Campo principal para compatibilidad con tests
    humidity = Column(Float)     # Campo principal para compatibilidad con tests
    pressure = Column(Float)     # Campo principal para compatibilidad con tests
    wind_speed = Column(Float)   # Campo principal para compatibilidad con tests
    wind_direction = Column(Float)
    precipitation = Column(Float)
    weather_description = Column(String(255))
    weather_code = Column(String(10))  # Volver a String para compatibilidad
    cloud_cover = Column(Float)  # Campo principal para compatibilidad con tests
    
    # Campos específicos de Open-Meteo (adicionales)
    temperature_2m = Column(Float)  # Específico de Open-Meteo
    relativehumidity_2m = Column(Float)  # Específico de Open-Meteo  
    dewpoint_2m = Column(Float)  # Específico de Open-Meteo
    rain = Column(Float)  # Específico de Open-Meteo
    weathercode = Column(Integer)  # Específico de Open-Meteo
    windspeed_10m = Column(Float)  # Específico de Open-Meteo
    windgusts_10m = Column(Float)  # Específico de Open-Meteo
    cloudcover = Column(Float)  # Específico de Open-Meteo
    pressure_msl = Column(Float)  # Específico de Open-Meteo
    surface_pressure = Column(Float)  # Específico de Open-Meteo
    visibility = Column(Float)
    uv_index = Column(Float)
    
    # Metadatos
    data_source = Column(String(50), nullable=False)
    recorded_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    location = relationship("Location", back_populates="weather_data")
    alerts = relationship("Alert", back_populates="weather_data")
    
    # Índices
    __table_args__ = (
        Index('idx_location_time', 'location_id', 'time'),
        Index('idx_data_source', 'data_source'),
        Index('idx_weathercode', 'weathercode'),
    )

class WeatherForecast(Base):
    __tablename__ = "weather_forecasts"
    
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    
    # Datos de pronóstico
    forecast_date = Column(DateTime(timezone=True), nullable=False)
    temperature_max = Column(Float)
    temperature_min = Column(Float)
    humidity = Column(Float)
    precipitation_probability = Column(Float)
    precipitation_amount = Column(Float)
    wind_speed = Column(Float)
    wind_direction = Column(Float)
    weather_description = Column(String(255))
    weather_code = Column(String(10))
    
    # Metadatos
    data_source = Column(String(50), nullable=False)
    forecast_generated_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    location = relationship("Location", back_populates="weather_forecasts")
    
    # Índices
    __table_args__ = (
        Index('idx_location_forecast_date', 'location_id', 'forecast_date'),
    )

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    weather_data_id = Column(Integer, ForeignKey("weather_data.id"), nullable=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    
    # Tipo y nivel de alerta
    alert_type = Column(String(100), nullable=False)  # temperatura, lluvia, viento, etc.
    risk_level = Column(String(50), nullable=False)   # bajo, medio, alto, crítico
    severity = Column(String(50))  # info, warning, watch, advisory
    
    # Valores de umbral
    threshold_value = Column(Float)  # Valor que activó la alerta
    current_value = Column(Float)    # Valor actual que disparó la alerta
    
    # Tiempo de alerta
    alert_start = Column(DateTime(timezone=True), nullable=False)
    alert_end = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Información adicional
    description = Column(Text)
    recommendations = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    weather_data = relationship("WeatherData", back_populates="alerts")
    location = relationship("Location", back_populates="alerts")
    
    # Índices
    __table_args__ = (
        Index('idx_location_alert_type', 'location_id', 'alert_type'),
        Index('idx_is_active', 'is_active'),
        Index('idx_risk_level', 'risk_level'),
        Index('idx_alert_start', 'alert_start'),
    )

class UserPreference(Base):
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    
    # Preferencias de notificación
    notification_types = Column(String(255))  # JSON string con tipos de alertas
    alert_levels = Column(String(100))        # Niveles de alerta que interesan
    contact_method = Column(String(50))       # email, sms, push, etc.
    timezone = Column(String(50), default='UTC')
    
    # Estado
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    location = relationship("Location", back_populates="user_preferences")
    
    # Índices
    __table_args__ = (
        Index('idx_location_active', 'location_id', 'is_active'),
    )

class DataLog(Base):
    __tablename__ = "data_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    data_source = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)  # success, error, warning
    message = Column(Text)
    records_processed = Column(Integer, default=0)
    execution_time = Column(Float)  # segundos
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Índices
    __table_args__ = (
        Index('idx_source_status', 'data_source', 'status'),
        Index('idx_created_at', 'created_at'),
    ) 