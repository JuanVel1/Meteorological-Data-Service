from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

# Esquemas para Ubicaciones
class LocationBase(BaseModel):
    name: str = Field(..., description="Nombre de la ubicación")
    country: str = Field(..., description="País")
    state: Optional[str] = Field(None, description="Estado/Departamento")
    city: Optional[str] = Field(None, description="Ciudad")
    region: Optional[str] = Field(None, description="Región")
    latitude: float = Field(..., ge=-90, le=90, description="Latitud")
    longitude: float = Field(..., ge=-180, le=180, description="Longitud")
    altitude: Optional[float] = Field(None, description="Altitud en metros")

class LocationCreate(LocationBase):
    pass

class LocationResponse(LocationBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Esquemas para Datos Meteorológicos (actualizados)
class WeatherDataBase(BaseModel):
    temperature_2m: Optional[float] = Field(None, description="Temperatura a 2m en Celsius")
    relativehumidity_2m: Optional[float] = Field(None, ge=0, le=100, description="Humedad relativa en porcentaje")
    dewpoint_2m: Optional[float] = Field(None, description="Punto de rocío en Celsius")
    rain: Optional[float] = Field(None, ge=0, description="Lluvia en mm")
    precipitation: Optional[float] = Field(None, ge=0, description="Precipitación total en mm")
    weathercode: Optional[int] = Field(None, description="Código de clima")
    weather_description: Optional[str] = Field(None, description="Descripción del clima")
    windspeed_10m: Optional[float] = Field(None, ge=0, description="Velocidad del viento a 10m en m/s")
    wind_direction: Optional[float] = Field(None, ge=0, le=360, description="Dirección del viento en grados")
    windgusts_10m: Optional[float] = Field(None, ge=0, description="Ráfagas de viento en m/s")
    cloudcover: Optional[float] = Field(None, ge=0, le=100, description="Cobertura de nubes en porcentaje")
    pressure_msl: Optional[float] = Field(None, description="Presión al nivel del mar en hPa")
    surface_pressure: Optional[float] = Field(None, description="Presión superficial en hPa")
    visibility: Optional[float] = Field(None, ge=0, description="Visibilidad en km")
    uv_index: Optional[float] = Field(None, ge=0, description="Índice UV")

class WeatherDataCreate(WeatherDataBase):
    location_id: int
    time: datetime
    data_source: str = Field(..., description="Fuente de datos (OpenMeteo, WorldClim)")
    recorded_at: datetime

class WeatherDataResponse(WeatherDataBase):
    id: int
    location_id: int
    time: datetime
    data_source: str
    recorded_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

# Esquemas para Pronósticos
class WeatherForecastBase(BaseModel):
    forecast_date: datetime
    temperature_max: Optional[float] = Field(None, description="Temperatura máxima en Celsius")
    temperature_min: Optional[float] = Field(None, description="Temperatura mínima en Celsius")
    humidity: Optional[float] = Field(None, ge=0, le=100, description="Humedad en porcentaje")
    precipitation_probability: Optional[float] = Field(None, ge=0, le=100, description="Probabilidad de precipitación")
    precipitation_amount: Optional[float] = Field(None, ge=0, description="Cantidad de precipitación en mm")
    wind_speed: Optional[float] = Field(None, ge=0, description="Velocidad del viento en m/s")
    wind_direction: Optional[float] = Field(None, ge=0, le=360, description="Dirección del viento en grados")
    weather_description: Optional[str] = Field(None, description="Descripción del clima")
    weather_code: Optional[str] = Field(None, description="Código del clima")

class WeatherForecastCreate(WeatherForecastBase):
    location_id: int
    data_source: str
    forecast_generated_at: datetime

class WeatherForecastResponse(WeatherForecastBase):
    id: int
    location_id: int
    data_source: str
    forecast_generated_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

# Esquemas para Alertas (nuevo)
class AlertBase(BaseModel):
    alert_type: str = Field(..., description="Tipo de alerta (temperatura, lluvia, viento, etc.)")
    risk_level: str = Field(..., description="Nivel de riesgo (bajo, medio, alto, crítico)")
    severity: Optional[str] = Field(None, description="Severidad (info, warning, watch, advisory)")
    threshold_value: Optional[float] = Field(None, description="Valor de umbral")
    current_value: Optional[float] = Field(None, description="Valor actual")
    alert_start: datetime = Field(..., description="Inicio de la alerta")
    alert_end: Optional[datetime] = Field(None, description="Fin de la alerta")
    is_active: bool = Field(True, description="Si la alerta está activa")
    description: Optional[str] = Field(None, description="Descripción de la alerta")
    recommendations: Optional[str] = Field(None, description="Recomendaciones")

class AlertCreate(AlertBase):
    location_id: int
    weather_data_id: Optional[int] = None

class AlertResponse(AlertBase):
    id: int
    location_id: int
    weather_data_id: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Esquemas para Preferencias de Usuario (nuevo)
class UserPreferenceBase(BaseModel):
    notification_types: Optional[str] = Field(None, description="Tipos de notificación (JSON string)")
    alert_levels: Optional[str] = Field(None, description="Niveles de alerta de interés")
    contact_method: Optional[str] = Field(None, description="Método de contacto (email, sms, push)")
    timezone: str = Field("UTC", description="Zona horaria")
    is_active: bool = Field(True, description="Si las preferencias están activas")

class UserPreferenceCreate(UserPreferenceBase):
    location_id: int

class UserPreferenceResponse(UserPreferenceBase):
    id: int
    location_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Esquemas para consultas
class WeatherQuery(BaseModel):
    location_name: Optional[str] = Field(None, description="Nombre de la ubicación")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitud")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitud")
    start_date: Optional[datetime] = Field(None, description="Fecha de inicio")
    end_date: Optional[datetime] = Field(None, description="Fecha de fin")
    data_source: Optional[str] = Field(None, description="Fuente de datos específica")

class WeatherResponse(BaseModel):
    location: LocationResponse
    current_weather: Optional[WeatherDataResponse]
    historical_data: List[WeatherDataResponse] = []
    forecast_data: List[WeatherForecastResponse] = []
    active_alerts: List[AlertResponse] = []

# Esquemas para geocodificación
class GeocodeRequest(BaseModel):
    location_name: str = Field(..., description="Nombre de la ubicación a geocodificar")
    country: Optional[str] = Field(None, description="País para filtrar resultados")

class GeocodeResponse(BaseModel):
    name: str
    display_name: str
    latitude: float
    longitude: float
    country: str
    state: Optional[str]
    city: Optional[str]

# Esquemas para alertas avanzadas
class AlertQuery(BaseModel):
    location_id: Optional[int] = Field(None, description="ID de ubicación")
    alert_type: Optional[str] = Field(None, description="Tipo de alerta")
    risk_level: Optional[str] = Field(None, description="Nivel de riesgo")
    is_active: Optional[bool] = Field(None, description="Solo alertas activas")
    start_date: Optional[datetime] = Field(None, description="Fecha de inicio")
    end_date: Optional[datetime] = Field(None, description="Fecha de fin")

class AlertStatistics(BaseModel):
    total_alerts: int
    active_alerts: int
    alerts_by_type: dict
    alerts_by_risk_level: dict
    most_affected_location: Optional[LocationResponse]

# Esquemas de respuesta general
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[str] = None

# Esquemas para logs de datos
class DataLogResponse(BaseModel):
    id: int
    data_source: str
    status: str
    message: Optional[str]
    records_processed: int
    execution_time: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True 