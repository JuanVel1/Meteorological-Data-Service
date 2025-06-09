# 🌤️ Servicio Meteorológico Integrado

Sistema completo de datos meteorológicos que obtiene información en tiempo real desde múltiples fuentes, la normaliza y la almacena en PostgreSQL, proporcionando una API REST robusta para consultas meteorológicas.

## ✨ Características Principales

- **🔄 Integración con APIs externas**: Open-Meteo, WorldClim, Nominatim/OpenStreetMap
- **☁️ Base de datos Supabase**: Almacenamiento en la nube con PostgreSQL
- **🌍 Geocodificación**: Resolución automática de ubicaciones usando Nominatim
- **🚨 Sistema de alertas**: Alertas automáticas basadas en umbrales meteorológicos
- **📡 API REST**: Documentación automática con OpenAPI/Swagger
- **⚡ Procesamiento asíncrono**: Operaciones no bloqueantes
- **📈 Datos históricos**: Almacenamiento y consulta de datos pasados
- **🔮 Pronósticos**: Hasta 16 días de pronósticos meteorológicos
- **🏥 Monitoreo**: Logs detallados y endpoints de salud
- **🛠️ Panel administrativo**: Gestión completa del sistema

## 🚀 Instalación

### Requisitos Previos

- Python 3.8+
- Cuenta en Supabase (base de datos)
- pip

### 1. Clonar el Repositorio

```bash
git clone <repository_url>
cd Meteorological-data
```

### 2. Instalar Dependencias

```bash
# Dependencias de producción
pip install -r requirements.txt

# Dependencias de desarrollo (opcional)
pip install -r requirements-dev.txt
```

### 3. Configurar Variables de Entorno

Crear archivo `.env` en el directorio raíz:

```env
# Base de datos Supabase
DATABASE_URL=postgresql://postgres:[TU_PASSWORD]@db.[TU_PROJECT_REF].supabase.co:5432/postgres

# Servidor
HOST=0.0.0.0
PORT=8000
DEBUG=False

# Logs
LOG_LEVEL=INFO
```

### 4. Configurar Base de Datos en Supabase

1. **Crear proyecto en Supabase**: https://supabase.com/
2. **Ejecutar el esquema SQL**:
   - Abrir SQL Editor en Supabase
   - Copiar el contenido del archivo `database_schema.sql` (ver sección de esquema)
   - Ejecutar el script completo
3. **Obtener la cadena de conexión** desde Settings > Database

### 5. Ejecutar la Aplicación

```bash
# Desarrollo
python start.py

# Producción con uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 📋 Uso de la API

### Documentación Interactiva

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Endpoints Principales

#### 🌡️ Clima Actual

```bash
# Por nombre de ubicación
GET /api/v1/weather/current?location_name=Bogotá

# Por coordenadas
GET /api/v1/weather/current?latitude=4.6097&longitude=-74.0817
```

#### 🔮 Pronóstico

```bash
# Pronóstico de 7 días
GET /api/v1/weather/forecast?location_name=Medellín&days=7
```

#### 📈 Datos Históricos

```bash
# Datos históricos por rango de fechas
GET /api/v1/weather/historical?location_name=Cali&start_date=2024-01-01&end_date=2024-01-31
```

#### 🌍 Geocodificación

```bash
# Geocodificar ubicación
POST /api/v1/weather/geocode
{
    "location_name": "Cartagena, Colombia"
}
```

#### 🚨 Alertas

```bash
# Alertas activas
GET /api/v1/weather/alerts?location_name=Barranquilla

# Estadísticas de alertas
GET /api/v1/admin/alerts/statistics
```

### Ejemplos de Respuesta

#### Clima Actual
```json
{
    "success": true,
    "location": {
        "id": 1,
        "name": "Bogotá",
        "country": "Colombia",
        "latitude": 4.6097,
        "longitude": -74.0817
    },
    "current_weather": {
        "temperature_2m": 18.5,
        "relativehumidity_2m": 72,
        "weather_description": "Parcialmente nublado",
        "windspeed_10m": 8.2,
        "pressure_msl": 1013.25,
        "data_source": "OpenMeteo"
    },
    "active_alerts": []
}
```

## 🏗️ Arquitectura

### Componentes Principales

```
📦 Servicio Meteorológico
├── 🌐 API Layer (FastAPI)
├── 🔧 Services Layer
│   ├── Weather Service (Coordinador principal)
│   ├── Open-Meteo Service (Datos globales)
│   ├── Geocoding Service (Nominatim)
│   ├── Alert Service (Sistema de alertas)
│   └── WorldClim Service (Datos históricos)
├── ☁️ Database Layer (Supabase PostgreSQL)
├── 📊 Models (SQLAlchemy)
└── 🛡️ Schemas (Pydantic)
```

### Base de Datos (Supabase)

**Tablas principales:**
- `locations`: Ubicaciones geográficas
- `weather_data`: Datos meteorológicos
- `weather_forecasts`: Pronósticos
- `alerts`: Sistema de alertas
- `user_preferences`: Preferencias de usuario
- `data_logs`: Logs del sistema

### Flujo de Datos

1. **Solicitud API** → Validación con Pydantic
2. **Geocodificación** → Nominatim (si es necesario)
3. **Obtención de datos** → Open-Meteo API
4. **Procesamiento** → Normalización y validación
5. **Almacenamiento** → Supabase PostgreSQL
6. **Evaluación de alertas** → Sistema automático
7. **Respuesta** → JSON estructurado

## ☁️ Esquema de Base de Datos para Supabase

Para configurar la base de datos en Supabase, ejecuta el siguiente SQL en el SQL Editor:

```sql
-- =====================================================
-- ESQUEMA DE BASE DE DATOS PARA SERVICIO METEOROLÓGICO
-- Compatible con Supabase (PostgreSQL)
-- =====================================================

-- Activar extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- TABLA: locations
-- =====================================================
CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    country VARCHAR(100) NOT NULL,
    state VARCHAR(100),
    city VARCHAR(100),
    region VARCHAR(100),
    latitude FLOAT8 NOT NULL,
    longitude FLOAT8 NOT NULL,
    altitude FLOAT8,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- Índices para locations
CREATE INDEX idx_locations_lat_lon ON locations (latitude, longitude);
CREATE INDEX idx_locations_region ON locations (region);
CREATE INDEX idx_locations_name ON locations (name);
CREATE INDEX idx_locations_country ON locations (country);

-- =====================================================
-- TABLA: weather_data
-- =====================================================
CREATE TABLE weather_data (
    id SERIAL PRIMARY KEY,
    location_id INTEGER NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    time TIMESTAMPTZ NOT NULL,
    temperature_2m FLOAT8,
    relativehumidity_2m FLOAT8,
    dewpoint_2m FLOAT8,
    rain FLOAT8,
    precipitation FLOAT8,
    weathercode INTEGER,
    weather_description VARCHAR(255),
    windspeed_10m FLOAT8,
    wind_direction FLOAT8,
    windgusts_10m FLOAT8,
    cloudcover FLOAT8,
    pressure_msl FLOAT8,
    surface_pressure FLOAT8,
    visibility FLOAT8,
    uv_index FLOAT8,
    data_source VARCHAR(50) NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Continuar con el resto del esquema...
-- Ver archivo database_schema.sql completo para todas las tablas
```

### Configuración de Conexión

```python
# En tu archivo .env
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres

# Ejemplo real:
DATABASE_URL=postgresql://postgres:mi_password@db.abcdefghij.supabase.co:5432/postgres
```

## 🔗 Fuentes de Datos

### Open-Meteo
- **Cobertura**: Global
- **Datos**: Tiempo real, pronósticos, algunos históricos
- **Frecuencia**: Tiempo real
- **Documentación**: https://open-meteo.com/

### Nominatim/OpenStreetMap
- **Cobertura**: Global
- **Función**: Geocodificación y geocodificación inversa
- **Limitaciones**: Rate limiting (1 req/seg)
- **Documentación**: https://nominatim.org/

### WorldClim
- **Cobertura**: Global
- **Datos**: Datos climáticos históricos promedio
- **Resolución**: Datos mensuales 1970-2000
- **Documentación**: https://worldclim.org/

## 🚨 Sistema de Alertas

### Tipos de Alertas

- **Temperatura alta/baja**: Basado en umbrales configurables
- **Lluvia intensa**: Por acumulación de precipitación
- **Viento fuerte**: Por velocidad del viento
- **Humedad extrema**: Por niveles de humedad

### Niveles de Riesgo

- **Bajo**: Condiciones que requieren atención
- **Medio**: Condiciones que requieren precaución
- **Alto**: Condiciones peligrosas
- **Crítico**: Condiciones extremadamente peligrosas

### Configuración de Umbrales

```python
# Ejemplo de umbrales (configurables)
THRESHOLDS = {
    'temperatura_alta': {
        'bajo': 30.0,     # °C
        'medio': 35.0,
        'alto': 40.0,
        'crítico': 45.0
    },
    'lluvia_intensa': {
        'bajo': 10.0,     # mm
        'medio': 25.0,
        'alto': 50.0,
        'crítico': 100.0
    }
}
```

## 🧪 Testing

### Ejecutar Tests

```bash
# Tests completos
pytest

# Tests con cobertura
pytest --cov=. --cov-report=html

# Tests específicos
pytest tests/test_models.py
pytest tests/test_services.py
pytest tests/test_api.py
```

### Estructura de Tests

```
tests/
├── conftest.py          # Configuración de fixtures
├── test_models.py       # Tests de modelos de base de datos
├── test_services.py     # Tests de servicios
└── test_api.py         # Tests de endpoints API
```

## 📊 Administración

### Panel Administrativo

Endpoints disponibles en `/api/v1/admin/`:

- **📍 Ubicaciones**: `GET /admin/locations`
- **📊 Estadísticas**: `GET /admin/stats`
- **📋 Logs**: `GET /admin/logs`
- **🧹 Limpieza**: `DELETE /admin/cleanup`
- **🚨 Gestión de alertas**: `GET /admin/alerts`

### Monitoreo

```bash
# Verificar salud del servicio
curl http://localhost:8000/health

# Estadísticas del sistema
curl http://localhost:8000/api/v1/admin/stats

# Logs recientes
curl http://localhost:8000/api/v1/admin/logs?hours=24
```

## 🐳 Despliegue

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose con Supabase

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
      - DEBUG=false
    restart: unless-stopped

volumes:
  app_data:
```

## 🔧 Configuración Avanzada

### Variables de Entorno

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `DATABASE_URL` | URL de conexión Supabase | `postgresql://user:password@db.supabase.co:5432/postgres` |
| `HOST` | Host del servidor | `0.0.0.0` |
| `PORT` | Puerto del servidor | `8000` |
| `DEBUG` | Modo debug | `False` |
| `LOG_LEVEL` | Nivel de logging | `INFO` |

### Personalización de Umbrales

Los umbrales de alertas se pueden personalizar editando `services/alert_service.py`:

```python
# Personalizar umbrales
DEFAULT_THRESHOLDS = {
    'temperatura_alta': {
        'bajo': 28.0,    # Personalizado para clima tropical
        'medio': 33.0,
        'alto': 38.0,
        'crítico': 43.0
    }
}
```

## 🤝 Contribución

1. Fork el repositorio
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

### Estándares de Código

- **PEP 8**: Estilo de código Python
- **Type hints**: Usar anotaciones de tipos
- **Docstrings**: Documentar funciones y clases
- **Tests**: Cobertura mínima del 80%

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para más detalles.

## 📞 Soporte

Para soporte técnico o preguntas:

- **Issues**: Usar GitHub Issues para reportar bugs
- **Documentación**: Consultar `/docs` en la API corriendo
- **Email**: contacto@meteorologia.com (ejemplo)

## 🗺️ Roadmap

### Versión 1.1
- [ ] Integración con más fuentes de datos
- [ ] Notificaciones por email/SMS
- [ ] Dashboard web frontend
- [ ] Caching con Redis

### Versión 1.2
- [ ] Machine Learning para predicciones
- [ ] API GraphQL
- [ ] Métricas con Prometheus
- [ ] Soporte para múltiples idiomas

---

**🌟 ¡Gracias por usar nuestro Servicio Meteorológico Integrado!** 