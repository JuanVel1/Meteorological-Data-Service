-- =============================================================================
-- SCHEMA DE BASE DE DATOS PARA SERVICIO METEOROLÓGICO
-- Supabase (PostgreSQL)
-- =============================================================================

-- Extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- =============================================================================
-- TABLA: locations
-- Ubicaciones geográficas
-- =============================================================================
CREATE TABLE IF NOT EXISTS locations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    country VARCHAR(100),
    region VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices para locations
CREATE INDEX IF NOT EXISTS idx_locations_coordinates ON locations USING BTREE (latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_locations_name ON locations USING BTREE (name);
CREATE INDEX IF NOT EXISTS idx_locations_country ON locations USING BTREE (country);
CREATE INDEX IF NOT EXISTS idx_locations_region ON locations USING BTREE (region);

-- Restricciones para locations
ALTER TABLE locations 
ADD CONSTRAINT chk_latitude CHECK (latitude >= -90 AND latitude <= 90),
ADD CONSTRAINT chk_longitude CHECK (longitude >= -180 AND longitude <= 180);

-- =============================================================================
-- TABLA: weather_data
-- Datos meteorológicos actuales
-- =============================================================================
CREATE TABLE IF NOT EXISTS weather_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    location_id UUID NOT NULL,
    source VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    temperature_2m DECIMAL(5, 2),
    relativehumidity_2m DECIMAL(5, 2),
    dewpoint_2m DECIMAL(5, 2),
    apparent_temperature DECIMAL(5, 2),
    precipitation DECIMAL(8, 3),
    rain DECIMAL(8, 3),
    showers DECIMAL(8, 3),
    snowfall DECIMAL(8, 3),
    weathercode INTEGER,
    pressure_msl DECIMAL(7, 2),
    surface_pressure DECIMAL(7, 2),
    cloudcover DECIMAL(5, 2),
    visibility DECIMAL(8, 2),
    evapotranspiration DECIMAL(8, 3),
    windspeed_10m DECIMAL(6, 2),
    winddirection_10m DECIMAL(5, 2),
    windgusts_10m DECIMAL(6, 2),
    uv_index DECIMAL(4, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Clave foránea
    CONSTRAINT fk_weather_data_location FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE CASCADE
);

-- Índices para weather_data
CREATE INDEX IF NOT EXISTS idx_weather_data_location_timestamp ON weather_data USING BTREE (location_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_weather_data_source ON weather_data USING BTREE (source);
CREATE INDEX IF NOT EXISTS idx_weather_data_timestamp ON weather_data USING BTREE (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_weather_data_weathercode ON weather_data USING BTREE (weathercode);

-- Restricciones para weather_data
ALTER TABLE weather_data 
ADD CONSTRAINT chk_humidity CHECK (relativehumidity_2m >= 0 AND relativehumidity_2m <= 100),
ADD CONSTRAINT chk_cloudcover CHECK (cloudcover >= 0 AND cloudcover <= 100),
ADD CONSTRAINT chk_precipitation CHECK (precipitation >= 0),
ADD CONSTRAINT chk_windspeed CHECK (windspeed_10m >= 0),
ADD CONSTRAINT chk_uv_index CHECK (uv_index >= 0);

-- =============================================================================
-- TABLA: weather_forecasts
-- Pronósticos meteorológicos
-- =============================================================================
CREATE TABLE IF NOT EXISTS weather_forecasts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    location_id UUID NOT NULL,
    source VARCHAR(50) NOT NULL,
    forecast_date TIMESTAMP WITH TIME ZONE NOT NULL,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    temperature_2m_max DECIMAL(5, 2),
    temperature_2m_min DECIMAL(5, 2),
    precipitation_sum DECIMAL(8, 3),
    precipitation_hours DECIMAL(4, 1),
    weathercode INTEGER,
    uv_index_max DECIMAL(4, 2),
    windspeed_10m_max DECIMAL(6, 2),
    winddirection_10m_dominant DECIMAL(5, 2),
    windgusts_10m_max DECIMAL(6, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Clave foránea
    CONSTRAINT fk_weather_forecasts_location FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE CASCADE
);

-- Índices para weather_forecasts
CREATE INDEX IF NOT EXISTS idx_weather_forecasts_location_date ON weather_forecasts USING BTREE (location_id, forecast_date);
CREATE INDEX IF NOT EXISTS idx_weather_forecasts_source ON weather_forecasts USING BTREE (source);
CREATE INDEX IF NOT EXISTS idx_weather_forecasts_generated ON weather_forecasts USING BTREE (generated_at DESC);

-- Restricciones para weather_forecasts
ALTER TABLE weather_forecasts 
ADD CONSTRAINT chk_forecast_precipitation CHECK (precipitation_sum >= 0),
ADD CONSTRAINT chk_forecast_windspeed CHECK (windspeed_10m_max >= 0),
ADD CONSTRAINT chk_forecast_uv CHECK (uv_index_max >= 0);

-- =============================================================================
-- TABLA: alerts
-- Sistema de alertas meteorológicas
-- =============================================================================
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    location_id UUID NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    recommendations TEXT,
    threshold_value DECIMAL(10, 3),
    current_value DECIMAL(10, 3),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    
    -- Clave foránea
    CONSTRAINT fk_alerts_location FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE CASCADE
);

-- Índices para alerts
CREATE INDEX IF NOT EXISTS idx_alerts_location_active ON alerts USING BTREE (location_id, is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_alerts_type_severity ON alerts USING BTREE (alert_type, severity);
CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts USING BTREE (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_expires ON alerts USING BTREE (expires_at) WHERE expires_at IS NOT NULL;

-- Restricciones para alerts
ALTER TABLE alerts 
ADD CONSTRAINT chk_alert_severity CHECK (severity IN ('bajo', 'medio', 'alto', 'crítico')),
ADD CONSTRAINT chk_alert_type CHECK (alert_type IN ('temperatura_alta', 'temperatura_baja', 'lluvia_intensa', 'viento_fuerte', 'humedad_alta')),
ADD CONSTRAINT chk_alert_expires CHECK (expires_at IS NULL OR expires_at > created_at);

-- =============================================================================
-- TABLA: user_preferences
-- Preferencias de usuario para alertas
-- =============================================================================
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    location_id UUID NOT NULL,
    alert_types TEXT[] DEFAULT '{}',
    temperature_max_threshold DECIMAL(5, 2) DEFAULT 35.0,
    temperature_min_threshold DECIMAL(5, 2) DEFAULT 0.0,
    precipitation_threshold DECIMAL(8, 3) DEFAULT 50.0,
    wind_speed_threshold DECIMAL(6, 2) DEFAULT 60.0,
    humidity_threshold DECIMAL(5, 2) DEFAULT 90.0,
    notification_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Clave foránea
    CONSTRAINT fk_user_preferences_location FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE CASCADE
);

-- Índices para user_preferences
CREATE INDEX IF NOT EXISTS idx_user_preferences_user_location ON user_preferences USING BTREE (user_id, location_id);
CREATE INDEX IF NOT EXISTS idx_user_preferences_location ON user_preferences USING BTREE (location_id);
CREATE INDEX IF NOT EXISTS idx_user_preferences_notifications ON user_preferences USING BTREE (notification_enabled) WHERE notification_enabled = TRUE;

-- Restricción única para user_preferences
ALTER TABLE user_preferences 
ADD CONSTRAINT uk_user_location UNIQUE (user_id, location_id);

-- =============================================================================
-- TABLA: data_logs
-- Logs del sistema para auditoría
-- =============================================================================
CREATE TABLE IF NOT EXISTS data_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    action VARCHAR(100) NOT NULL,
    details JSONB,
    user_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    status VARCHAR(20) DEFAULT 'success',
    error_message TEXT,
    execution_time DECIMAL(8, 3),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices para data_logs
CREATE INDEX IF NOT EXISTS idx_data_logs_action ON data_logs USING BTREE (action);
CREATE INDEX IF NOT EXISTS idx_data_logs_created ON data_logs USING BTREE (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_data_logs_status ON data_logs USING BTREE (status);
CREATE INDEX IF NOT EXISTS idx_data_logs_user ON data_logs USING BTREE (user_id) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_data_logs_details ON data_logs USING GIN (details);

-- =============================================================================
-- TRIGGERS PARA UPDATED_AT
-- =============================================================================

-- Función para actualizar timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers para actualizar updated_at
CREATE TRIGGER update_locations_updated_at 
    BEFORE UPDATE ON locations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at 
    BEFORE UPDATE ON user_preferences 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- VISTAS ÚTILES
-- =============================================================================

-- Vista para datos meteorológicos con información de ubicación
CREATE OR REPLACE VIEW weather_data_with_location AS
SELECT 
    wd.*,
    l.name as location_name,
    l.country,
    l.region
FROM weather_data wd
JOIN locations l ON wd.location_id = l.id;

-- Vista para alertas activas con información de ubicación
CREATE OR REPLACE VIEW active_alerts_with_location AS
SELECT 
    a.*,
    l.name as location_name,
    l.country,
    l.region
FROM alerts a
JOIN locations l ON a.location_id = l.id
WHERE a.is_active = TRUE 
  AND (a.expires_at IS NULL OR a.expires_at > CURRENT_TIMESTAMP);

-- Vista para estadísticas de ubicaciones
CREATE OR REPLACE VIEW location_stats AS
SELECT 
    l.id,
    l.name,
    l.country,
    l.region,
    COUNT(DISTINCT wd.id) as weather_data_count,
    COUNT(DISTINCT wf.id) as forecast_count,
    COUNT(DISTINCT a.id) as total_alerts,
    COUNT(DISTINCT CASE WHEN a.is_active THEN a.id END) as active_alerts,
    MAX(wd.created_at) as last_weather_update,
    MAX(wf.created_at) as last_forecast_update
FROM locations l
LEFT JOIN weather_data wd ON l.id = wd.location_id
LEFT JOIN weather_forecasts wf ON l.id = wf.location_id
LEFT JOIN alerts a ON l.id = a.location_id
GROUP BY l.id, l.name, l.country, l.region;

-- =============================================================================
-- FUNCIONES DE UTILIDAD
-- =============================================================================

-- Función para limpiar datos antiguos
CREATE OR REPLACE FUNCTION cleanup_old_data(days_to_keep INTEGER DEFAULT 30)
RETURNS TABLE(
    deleted_weather_data INTEGER,
    deleted_forecasts INTEGER,
    deleted_logs INTEGER
) AS $$
DECLARE
    deleted_weather INTEGER := 0;
    deleted_fc INTEGER := 0;
    deleted_log INTEGER := 0;
BEGIN
    -- Limpiar weather_data antiguos
    DELETE FROM weather_data 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * days_to_keep;
    GET DIAGNOSTICS deleted_weather = ROW_COUNT;
    
    -- Limpiar pronósticos vencidos
    DELETE FROM weather_forecasts 
    WHERE forecast_date < CURRENT_TIMESTAMP - INTERVAL '1 day' * 7;
    GET DIAGNOSTICS deleted_fc = ROW_COUNT;
    
    -- Limpiar logs antiguos
    DELETE FROM data_logs 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * (days_to_keep * 2);
    GET DIAGNOSTICS deleted_log = ROW_COUNT;
    
    RETURN QUERY SELECT deleted_weather, deleted_fc, deleted_log;
END;
$$ LANGUAGE plpgsql;

-- Función para obtener datos meteorológicos recientes por ubicación
CREATE OR REPLACE FUNCTION get_recent_weather_data(
    location_name_param VARCHAR(255),
    hours_back INTEGER DEFAULT 24
)
RETURNS TABLE(
    timestamp TIMESTAMP WITH TIME ZONE,
    temperature_2m DECIMAL(5, 2),
    humidity DECIMAL(5, 2),
    precipitation DECIMAL(8, 3),
    wind_speed DECIMAL(6, 2),
    weather_code INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        wd.timestamp,
        wd.temperature_2m,
        wd.relativehumidity_2m,
        wd.precipitation,
        wd.windspeed_10m,
        wd.weathercode
    FROM weather_data wd
    JOIN locations l ON wd.location_id = l.id
    WHERE l.name ILIKE '%' || location_name_param || '%'
      AND wd.timestamp >= CURRENT_TIMESTAMP - INTERVAL '1 hour' * hours_back
    ORDER BY wd.timestamp DESC;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- DATOS INICIALES DE EJEMPLO
-- =============================================================================

-- Insertar algunas ubicaciones de ejemplo
INSERT INTO locations (name, latitude, longitude, country, region) VALUES
('Bogotá', 4.7110, -74.0721, 'Colombia', 'Cundinamarca'),
('Medellín', 6.2442, -75.5812, 'Colombia', 'Antioquia'),
('Cali', 3.4516, -76.5320, 'Colombia', 'Valle del Cauca'),
('Barranquilla', 10.9639, -74.7964, 'Colombia', 'Atlántico'),
('Cartagena', 10.4236, -75.5378, 'Colombia', 'Bolívar')
ON CONFLICT DO NOTHING;

-- =============================================================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- =============================================================================

COMMENT ON TABLE locations IS 'Ubicaciones geográficas para las cuales se recopilan datos meteorológicos';
COMMENT ON TABLE weather_data IS 'Datos meteorológicos actuales e históricos por ubicación';
COMMENT ON TABLE weather_forecasts IS 'Pronósticos meteorológicos por ubicación';
COMMENT ON TABLE alerts IS 'Sistema de alertas meteorológicas automáticas';
COMMENT ON TABLE user_preferences IS 'Preferencias de usuario para alertas y notificaciones';
COMMENT ON TABLE data_logs IS 'Logs de auditoría del sistema';

COMMENT ON COLUMN weather_data.temperature_2m IS 'Temperatura a 2 metros en grados Celsius';
COMMENT ON COLUMN weather_data.relativehumidity_2m IS 'Humedad relativa a 2 metros en porcentaje';
COMMENT ON COLUMN weather_data.weathercode IS 'Código WMO de condiciones meteorológicas';
COMMENT ON COLUMN alerts.severity IS 'Nivel de severidad: bajo, medio, alto, crítico';
COMMENT ON COLUMN alerts.alert_type IS 'Tipo de alerta: temperatura_alta, temperatura_baja, lluvia_intensa, viento_fuerte, humedad_alta';

-- =============================================================================
-- FIN DEL SCRIPT
-- ============================================================================= 