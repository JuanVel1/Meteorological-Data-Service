-- =====================================================
-- ESQUEMA DE BASE DE DATOS PARA SERVICIO METEOROLÓGICO
-- Compatible con Supabase (PostgreSQL)
-- 
-- INSTRUCCIONES:
-- 1. Copiar todo este contenido
-- 2. Abrir SQL Editor en Supabase (dashboard.supabase.com)
-- 3. Pegar y ejecutar el script completo
-- =====================================================

-- Activar extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- TABLA: locations
-- Almacena información de ubicaciones geográficas
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
-- Almacena datos meteorológicos históricos y actuales
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

-- Índices para weather_data
CREATE INDEX idx_weather_data_location_time ON weather_data (location_id, time);
CREATE INDEX idx_weather_data_data_source ON weather_data (data_source);
CREATE INDEX idx_weather_data_weathercode ON weather_data (weathercode);
CREATE INDEX idx_weather_data_recorded_at ON weather_data (recorded_at);
CREATE INDEX idx_weather_data_created_at ON weather_data (created_at);

-- =====================================================
-- TABLA: weather_forecasts
-- Almacena pronósticos meteorológicos
-- =====================================================
CREATE TABLE weather_forecasts (
    id SERIAL PRIMARY KEY,
    location_id INTEGER NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    forecast_date TIMESTAMPTZ NOT NULL,
    temperature_max FLOAT8,
    temperature_min FLOAT8,
    humidity FLOAT8,
    precipitation_probability FLOAT8,
    precipitation_amount FLOAT8,
    wind_speed FLOAT8,
    wind_direction FLOAT8,
    weather_description VARCHAR(255),
    weather_code VARCHAR(10),
    data_source VARCHAR(50) NOT NULL,
    forecast_generated_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para weather_forecasts
CREATE INDEX idx_weather_forecasts_location_date ON weather_forecasts (location_id, forecast_date);
CREATE INDEX idx_weather_forecasts_data_source ON weather_forecasts (data_source);
CREATE INDEX idx_weather_forecasts_generated_at ON weather_forecasts (forecast_generated_at);

-- =====================================================
-- TABLA: alerts
-- Almacena alertas meteorológicas automáticas
-- =====================================================
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    weather_data_id INTEGER REFERENCES weather_data(id) ON DELETE SET NULL,
    location_id INTEGER NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    alert_type VARCHAR(100) NOT NULL,
    risk_level VARCHAR(50) NOT NULL,
    severity VARCHAR(50),
    threshold_value FLOAT8,
    current_value FLOAT8,
    alert_start TIMESTAMPTZ NOT NULL,
    alert_end TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    description TEXT,
    recommendations TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para alerts
CREATE INDEX idx_alerts_location_alert_type ON alerts (location_id, alert_type);
CREATE INDEX idx_alerts_is_active ON alerts (is_active);
CREATE INDEX idx_alerts_risk_level ON alerts (risk_level);
CREATE INDEX idx_alerts_alert_start ON alerts (alert_start);
CREATE INDEX idx_alerts_created_at ON alerts (created_at);

-- =====================================================
-- TABLA: user_preferences
-- Almacena preferencias de usuarios para notificaciones
-- =====================================================
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    location_id INTEGER NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    notification_types VARCHAR(255),
    alert_levels VARCHAR(100),
    contact_method VARCHAR(50),
    timezone VARCHAR(50) DEFAULT 'UTC',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- Índices para user_preferences
CREATE INDEX idx_user_preferences_location_active ON user_preferences (location_id, is_active);
CREATE INDEX idx_user_preferences_contact_method ON user_preferences (contact_method);

-- =====================================================
-- TABLA: data_logs
-- Almacena logs del sistema y ejecución de procesos
-- =====================================================
CREATE TABLE data_logs (
    id SERIAL PRIMARY KEY,
    data_source VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    message TEXT,
    records_processed INTEGER DEFAULT 0,
    execution_time FLOAT8,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para data_logs
CREATE INDEX idx_data_logs_source_status ON data_logs (data_source, status);
CREATE INDEX idx_data_logs_created_at ON data_logs (created_at);
CREATE INDEX idx_data_logs_status ON data_logs (status);

-- =====================================================
-- TRIGGERS PARA UPDATED_AT
-- =====================================================

-- Función para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers para locations
CREATE TRIGGER update_locations_updated_at 
    BEFORE UPDATE ON locations 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Triggers para user_preferences
CREATE TRIGGER update_user_preferences_updated_at 
    BEFORE UPDATE ON user_preferences 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- RESTRICCIONES Y VALIDACIONES
-- =====================================================

-- Validaciones para locations
ALTER TABLE locations ADD CONSTRAINT chk_latitude CHECK (latitude >= -90 AND latitude <= 90);
ALTER TABLE locations ADD CONSTRAINT chk_longitude CHECK (longitude >= -180 AND longitude <= 180);

-- Validaciones para weather_data
ALTER TABLE weather_data ADD CONSTRAINT chk_humidity CHECK (relativehumidity_2m >= 0 AND relativehumidity_2m <= 100);
ALTER TABLE weather_data ADD CONSTRAINT chk_wind_direction CHECK (wind_direction >= 0 AND wind_direction <= 360);
ALTER TABLE weather_data ADD CONSTRAINT chk_cloudcover CHECK (cloudcover >= 0 AND cloudcover <= 100);
ALTER TABLE weather_data ADD CONSTRAINT chk_rain CHECK (rain >= 0);
ALTER TABLE weather_data ADD CONSTRAINT chk_precipitation CHECK (precipitation >= 0);
ALTER TABLE weather_data ADD CONSTRAINT chk_windspeed CHECK (windspeed_10m >= 0);
ALTER TABLE weather_data ADD CONSTRAINT chk_windgusts CHECK (windgusts_10m >= 0);
ALTER TABLE weather_data ADD CONSTRAINT chk_uv_index CHECK (uv_index >= 0);

-- Validaciones para weather_forecasts
ALTER TABLE weather_forecasts ADD CONSTRAINT chk_forecast_humidity CHECK (humidity >= 0 AND humidity <= 100);
ALTER TABLE weather_forecasts ADD CONSTRAINT chk_forecast_precipitation_prob CHECK (precipitation_probability >= 0 AND precipitation_probability <= 100);
ALTER TABLE weather_forecasts ADD CONSTRAINT chk_forecast_precipitation_amount CHECK (precipitation_amount >= 0);
ALTER TABLE weather_forecasts ADD CONSTRAINT chk_forecast_wind_speed CHECK (wind_speed >= 0);
ALTER TABLE weather_forecasts ADD CONSTRAINT chk_forecast_wind_direction CHECK (wind_direction >= 0 AND wind_direction <= 360);

-- Validaciones para alerts
ALTER TABLE alerts ADD CONSTRAINT chk_alert_type CHECK (alert_type IN (
    'temperatura_alta', 'temperatura_baja', 'lluvia_intensa', 
    'viento_fuerte', 'humedad_alta'
));
ALTER TABLE alerts ADD CONSTRAINT chk_risk_level CHECK (risk_level IN (
    'bajo', 'medio', 'alto', 'crítico'
));
ALTER TABLE alerts ADD CONSTRAINT chk_severity CHECK (severity IN (
    'info', 'warning', 'watch', 'advisory'
));
ALTER TABLE alerts ADD CONSTRAINT chk_alert_dates CHECK (alert_end IS NULL OR alert_end >= alert_start);

-- Validaciones para data_logs
ALTER TABLE data_logs ADD CONSTRAINT chk_log_status CHECK (status IN (
    'success', 'error', 'warning', 'info'
));
ALTER TABLE data_logs ADD CONSTRAINT chk_records_processed CHECK (records_processed >= 0);
ALTER TABLE data_logs ADD CONSTRAINT chk_execution_time CHECK (execution_time >= 0);

-- =====================================================
-- VISTAS ÚTILES
-- =====================================================

-- Vista para el resumen meteorológico actual
CREATE VIEW current_weather_summary AS
SELECT 
    l.id as location_id,
    l.name as location_name,
    l.country,
    l.state,
    l.latitude,
    l.longitude,
    wd.temperature_2m,
    wd.relativehumidity_2m,
    wd.weather_description,
    wd.windspeed_10m,
    wd.pressure_msl,
    wd.time as last_update,
    wd.data_source
FROM locations l
JOIN LATERAL (
    SELECT *
    FROM weather_data wd2
    WHERE wd2.location_id = l.id
    ORDER BY wd2.time DESC
    LIMIT 1
) wd ON true;

-- Vista para alertas activas con información de ubicación
CREATE VIEW active_alerts_view AS
SELECT 
    a.id,
    a.alert_type,
    a.risk_level,
    a.severity,
    a.current_value,
    a.threshold_value,
    a.description,
    a.alert_start,
    a.created_at,
    l.name as location_name,
    l.country,
    l.state,
    l.latitude,
    l.longitude
FROM alerts a
JOIN locations l ON a.location_id = l.id
WHERE a.is_active = TRUE
ORDER BY a.risk_level DESC, a.alert_start DESC;

-- =====================================================
-- FUNCIONES AUXILIARES
-- =====================================================

-- Función para obtener el clima actual de una ubicación
CREATE OR REPLACE FUNCTION get_current_weather(location_name_param VARCHAR)
RETURNS TABLE (
    location_name VARCHAR,
    temperature FLOAT8,
    humidity FLOAT8,
    description VARCHAR,
    recorded_time TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        l.name,
        wd.temperature_2m,
        wd.relativehumidity_2m,
        wd.weather_description,
        wd.time
    FROM locations l
    JOIN weather_data wd ON l.id = wd.location_id
    WHERE l.name ILIKE '%' || location_name_param || '%'
    ORDER BY wd.time DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Función para contar alertas activas por ubicación
CREATE OR REPLACE FUNCTION count_active_alerts_by_location()
RETURNS TABLE (
    location_name VARCHAR,
    active_alerts_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        l.name,
        COUNT(a.id)
    FROM locations l
    LEFT JOIN alerts a ON l.id = a.location_id AND a.is_active = TRUE
    GROUP BY l.id, l.name
    ORDER BY COUNT(a.id) DESC;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- DATOS DE EJEMPLO PARA COLOMBIA
-- =====================================================

-- Insertar ubicaciones principales de Colombia
INSERT INTO locations (name, country, state, city, region, latitude, longitude, altitude) VALUES
('Bogotá', 'Colombia', 'Cundinamarca', 'Bogotá', 'Región Andina', 4.6097, -74.0817, 2625),
('Medellín', 'Colombia', 'Antioquia', 'Medellín', 'Región Andina', 6.2486, -75.5742, 1495),
('Cali', 'Colombia', 'Valle del Cauca', 'Cali', 'Región Pacífica', 3.4516, -76.5320, 1018),
('Barranquilla', 'Colombia', 'Atlántico', 'Barranquilla', 'Región Caribe', 10.9639, -74.7964, 18),
('Cartagena', 'Colombia', 'Bolívar', 'Cartagena', 'Región Caribe', 10.3910, -75.4794, 2),
('Bucaramanga', 'Colombia', 'Santander', 'Bucaramanga', 'Región Andina', 7.1253, -73.1198, 959),
('Pereira', 'Colombia', 'Risaralda', 'Pereira', 'Región Andina', 4.8087, -75.6906, 1411),
('Santa Marta', 'Colombia', 'Magdalena', 'Santa Marta', 'Región Caribe', 11.2408, -74.1990, 2),
('Manizales', 'Colombia', 'Caldas', 'Manizales', 'Región Andina', 5.0703, -75.5138, 2153),
('Ibagué', 'Colombia', 'Tolima', 'Ibagué', 'Región Andina', 4.4389, -75.2322, 1285);

-- Insertar log inicial
INSERT INTO data_logs (data_source, status, message, records_processed, execution_time) VALUES
('SYSTEM', 'success', 'Base de datos inicializada con esquema completo en Supabase', 10, 0.250);

-- =====================================================
-- VERIFICACIÓN DEL ESQUEMA
-- =====================================================

-- Verificar que todas las tablas se crearon correctamente
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name IN ('locations', 'weather_data', 'weather_forecasts', 'alerts', 'user_preferences', 'data_logs');
    
    IF table_count = 6 THEN
        RAISE NOTICE '✅ Todas las tablas creadas correctamente (% tablas)', table_count;
    ELSE
        RAISE NOTICE '❌ Error: Solo se crearon % de 6 tablas', table_count;
    END IF;
END $$;

-- =====================================================
-- COMENTARIOS FINALES
-- =====================================================

/*
🎉 ESQUEMA COMPLETO INSTALADO EXITOSAMENTE

Tablas creadas:
✅ locations (ubicaciones geográficas)
✅ weather_data (datos meteorológicos)
✅ weather_forecasts (pronósticos)
✅ alerts (sistema de alertas)
✅ user_preferences (preferencias de usuario)
✅ data_logs (logs del sistema)

Características incluidas:
✅ Índices optimizados para consultas rápidas
✅ Restricciones de validación de datos
✅ Triggers para timestamps automáticos
✅ Vistas para consultas comunes
✅ Funciones auxiliares PostgreSQL
✅ Datos de ejemplo para ciudades colombianas

Próximos pasos:
1. Configurar la cadena de conexión en tu aplicación
2. Probar la conexión desde la API
3. Ejecutar los tests para verificar funcionamiento

Para obtener tu cadena de conexión:
Supabase Dashboard > Settings > Database > Connection string
*/ 