# Configuración de Base de Datos en Supabase

## Resumen

Este documento describe cómo configurar la base de datos para el Servicio Meteorológico en Supabase utilizando PostgreSQL.

## Prerrequisitos

1. Cuenta en [Supabase](https://supabase.com)
2. Proyecto creado en Supabase
3. Acceso al SQL Editor de Supabase

## Instrucciones de Configuración

### 1. Crear el Proyecto en Supabase

1. Accede a [Supabase Dashboard](https://app.supabase.com)
2. Crea un nuevo proyecto
3. Anota las credenciales de conexión:
   - `Database URL`
   - `API URL`
   - `anon key`
   - `service_role key`

### 2. Ejecutar el Schema SQL

1. Ve al **SQL Editor** en tu proyecto de Supabase
2. Crea una nueva consulta
3. Copia y pega el contenido completo del archivo `supabase_schema.sql`
4. Ejecuta la consulta para crear todas las tablas, índices y funciones

### 3. Verificar la Estructura

Después de ejecutar el script, deberías tener las siguientes tablas:

- ✅ `locations` - Ubicaciones geográficas
- ✅ `weather_data` - Datos meteorológicos actuales
- ✅ `weather_forecasts` - Pronósticos meteorológicos
- ✅ `alerts` - Sistema de alertas
- ✅ `user_preferences` - Preferencias de usuario
- ✅ `data_logs` - Logs del sistema

### 4. Configurar Variables de Entorno

Actualiza tu archivo `.env` con las credenciales de Supabase:

```env
# Supabase Configuration
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
SUPABASE_URL=https://[PROJECT_REF].supabase.co
SUPABASE_ANON_KEY=eyJ[...]
SUPABASE_SERVICE_ROLE_KEY=eyJ[...]

# Otras configuraciones del servicio meteorológico
OPENMETEO_API_URL=https://api.open-meteo.com/v1
IDEAM_API_URL=https://www.ideam.gov.co/documents/21021/418894/Estaciones.xlsx
NOMINATIM_API_URL=https://nominatim.openstreetmap.org
```

### 5. Configuración de Seguridad (Opcional)

#### Row Level Security (RLS)

Si necesitas implementar seguridad a nivel de fila, puedes habilitar RLS:

```sql
-- Habilitar RLS en tablas sensibles
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;

-- Crear políticas de ejemplo
CREATE POLICY "Users can view their own preferences" ON user_preferences
  FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Users can update their own preferences" ON user_preferences
  FOR UPDATE USING (auth.uid()::text = user_id);
```

#### API Keys y Autenticación

```sql
-- Crear tabla para gestionar API keys (opcional)
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key_name VARCHAR(255) NOT NULL,
    api_key VARCHAR(500) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE
);
```

## Funciones Útiles Incluidas

### 1. Limpieza de Datos Antiguos

```sql
-- Limpiar datos de más de 30 días
SELECT * FROM cleanup_old_data(30);
```

### 2. Consulta de Datos Meteorológicos Recientes

```sql
-- Obtener datos de las últimas 24 horas para Bogotá
SELECT * FROM get_recent_weather_data('Bogotá', 24);
```

## Vistas Disponibles

### 1. `weather_data_with_location`
Datos meteorológicos con información de ubicación incluida.

### 2. `active_alerts_with_location`
Alertas activas con información de ubicación.

### 3. `location_stats`
Estadísticas agregadas por ubicación.

## Mantenimiento

### Limpieza Automática
Se recomienda configurar un cron job para ejecutar la función de limpieza:

```sql
-- Ejecutar semanalmente
SELECT cron.schedule('cleanup-old-data', '0 2 * * 0', 'SELECT cleanup_old_data(30);');
```

### Monitoreo
Usa la tabla `data_logs` para monitorear el uso del sistema:

```sql
-- Ver logs recientes
SELECT * FROM data_logs 
ORDER BY created_at DESC 
LIMIT 100;

-- Estadísticas de uso por acción
SELECT action, COUNT(*), AVG(execution_time)
FROM data_logs 
WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '7 days'
GROUP BY action;
```

## Indexación y Performance

El schema incluye índices optimizados para:

- Búsquedas por ubicación y tiempo
- Consultas de alertas activas
- Logs por usuario y acción
- Coordenadas geográficas

### Consultas de Ejemplo Optimizadas

```sql
-- Datos meteorológicos recientes por ubicación (usa índice location_timestamp)
SELECT * FROM weather_data 
WHERE location_id = 'uuid-here' 
  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
ORDER BY timestamp DESC;

-- Alertas activas por región (usa índice partial)
SELECT * FROM alerts 
WHERE is_active = TRUE 
  AND expires_at > CURRENT_TIMESTAMP;
```

## Troubleshooting

### Errores Comunes

1. **Extension not found**: Asegúrate de que las extensiones `uuid-ossp` y `btree_gin` estén habilitadas.

2. **Permission denied**: Verifica que tengas permisos de admin en el proyecto de Supabase.

3. **Foreign key constraint**: Las tablas deben crearse en el orden correcto (locations primero).

### Validación de Instalación

```sql
-- Verificar que todas las tablas existen
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- Verificar índices
SELECT indexname, tablename 
FROM pg_indexes 
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- Verificar funciones
SELECT routine_name, routine_type
FROM information_schema.routines
WHERE routine_schema = 'public'
ORDER BY routine_name;
```

## Respaldo y Restauración

Supabase proporciona respaldos automáticos, pero también puedes crear respaldos manuales:

```bash
# Exportar schema y datos
pg_dump -h db.PROJECT_REF.supabase.co -U postgres -d postgres --schema-only > schema_backup.sql
pg_dump -h db.PROJECT_REF.supabase.co -U postgres -d postgres --data-only > data_backup.sql
```

## Próximos Pasos

1. Ejecutar el schema SQL
2. Configurar las variables de entorno
3. Probar la conexión desde la aplicación
4. Insertar datos de prueba
5. Verificar que las APIs funcionen correctamente

Para más información, consulta la [documentación oficial de Supabase](https://supabase.com/docs). 