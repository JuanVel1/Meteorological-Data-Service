-- =============================================================================
-- CONSULTAS SQL ÚTILES PARA EL SERVICIO METEOROLÓGICO
-- Supabase (PostgreSQL)
-- =============================================================================

-- =============================================================================
-- CONSULTAS DE VERIFICACIÓN
-- =============================================================================

-- Verificar estructura de tablas
SELECT 
    t.table_name,
    c.column_name,
    c.data_type,
    c.is_nullable,
    c.column_default
FROM information_schema.tables t
JOIN information_schema.columns c ON t.table_name = c.table_name
WHERE t.table_schema = 'public' 
  AND t.table_type = 'BASE TABLE'
ORDER BY t.table_name, c.ordinal_position;

-- Verificar relaciones (foreign keys)
SELECT
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu 
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu 
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
ORDER BY tc.table_name;

-- Verificar índices
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- =============================================================================
-- DATOS DE PRUEBA
-- =============================================================================

-- Insertar datos de prueba (ejecutar solo una vez)
DO $$
DECLARE
    bogota_id UUID;
    medellin_id UUID;
    test_weather_id UUID;
BEGIN
    -- Obtener IDs de ubicaciones existentes
    SELECT id INTO bogota_id FROM locations WHERE name = 'Bogotá' LIMIT 1;
    SELECT id INTO medellin_id FROM locations WHERE name = 'Medellín' LIMIT 1;
    
    IF bogota_id IS NOT NULL THEN
        -- Insertar datos meteorológicos de prueba para Bogotá
        INSERT INTO weather_data (
            location_id, source, timestamp, temperature_2m, relativehumidity_2m,
            precipitation, windspeed_10m, weathercode, pressure_msl
        ) VALUES 
        (bogota_id, 'open-meteo', CURRENT_TIMESTAMP, 18.5, 75.0, 0.0, 5.2, 1, 1013.25),
        (bogota_id, 'open-meteo', CURRENT_TIMESTAMP - INTERVAL '1 hour', 19.2, 72.0, 2.5, 6.1, 61, 1012.8),
        (bogota_id, 'open-meteo', CURRENT_TIMESTAMP - INTERVAL '2 hours', 20.1, 68.0, 0.1, 4.8, 2, 1014.1);
        
        -- Insertar pronóstico de prueba
        INSERT INTO weather_forecasts (
            location_id, source, forecast_date, temperature_2m_max, temperature_2m_min,
            precipitation_sum, weathercode
        ) VALUES 
        (bogota_id, 'open-meteo', CURRENT_DATE + INTERVAL '1 day', 22.0, 12.0, 5.2, 61),
        (bogota_id, 'open-meteo', CURRENT_DATE + INTERVAL '2 days', 24.5, 14.0, 0.0, 1);
        
        -- Insertar preferencias de usuario de prueba
        INSERT INTO user_preferences (
            user_id, location_id, alert_types, temperature_max_threshold,
            precipitation_threshold, notification_enabled
        ) VALUES 
        ('test-user-1', bogota_id, ARRAY['temperatura_alta', 'lluvia_intensa'], 30.0, 25.0, true);
        
        -- Insertar alerta de prueba
        INSERT INTO alerts (
            location_id, alert_type, severity, title, description,
            threshold_value, current_value, expires_at
        ) VALUES 
        (bogota_id, 'temperatura_alta', 'medio', 'Temperatura elevada en Bogotá',
         'La temperatura ha superado el umbral establecido', 25.0, 27.5,
         CURRENT_TIMESTAMP + INTERVAL '6 hours');
         
        RAISE NOTICE 'Datos de prueba insertados correctamente para Bogotá';
    END IF;
END $$;

-- =============================================================================
-- CONSULTAS DE ANÁLISIS Y MONITOREO
-- =============================================================================

-- Resumen de datos por ubicación
SELECT 
    l.name,
    l.country,
    COUNT(DISTINCT wd.id) as total_weather_records,
    COUNT(DISTINCT wf.id) as total_forecasts,
    COUNT(DISTINCT a.id) as total_alerts,
    COUNT(DISTINCT CASE WHEN a.is_active THEN a.id END) as active_alerts,
    MAX(wd.timestamp) as last_weather_update,
    MIN(wd.timestamp) as first_weather_record
FROM locations l
LEFT JOIN weather_data wd ON l.id = wd.location_id
LEFT JOIN weather_forecasts wf ON l.id = wf.location_id
LEFT JOIN alerts a ON l.id = a.location_id
GROUP BY l.id, l.name, l.country
ORDER BY total_weather_records DESC;

-- Datos meteorológicos más recientes por ubicación
WITH recent_weather AS (
    SELECT 
        wd.*,
        l.name as location_name,
        ROW_NUMBER() OVER (PARTITION BY wd.location_id ORDER BY wd.timestamp DESC) as rn
    FROM weather_data wd
    JOIN locations l ON wd.location_id = l.id
)
SELECT 
    location_name,
    timestamp,
    temperature_2m,
    relativehumidity_2m,
    precipitation,
    windspeed_10m,
    weathercode
FROM recent_weather
WHERE rn = 1
ORDER BY location_name;

-- Alertas activas con información detallada
SELECT 
    l.name as ubicacion,
    a.alert_type as tipo_alerta,
    a.severity as severidad,
    a.title as titulo,
    a.current_value as valor_actual,
    a.threshold_value as umbral,
    a.created_at as fecha_creacion,
    a.expires_at as fecha_expiracion,
    CASE 
        WHEN a.expires_at IS NULL THEN 'Sin expiración'
        WHEN a.expires_at > CURRENT_TIMESTAMP THEN 'Activa'
        ELSE 'Expirada'
    END as estado
FROM alerts a
JOIN locations l ON a.location_id = l.id
WHERE a.is_active = TRUE
ORDER BY a.severity DESC, a.created_at DESC;

-- Probar función de limpieza
SELECT * FROM cleanup_old_data(7);

-- Probar función de datos recientes
SELECT * FROM get_recent_weather_data('Bogotá', 48);

-- =============================================================================
-- FIN DE CONSULTAS
-- ============================================================================= 