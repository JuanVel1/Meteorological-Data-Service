#  🗄️ Esquema SQL Completo para Supabase
# 📋 Tablas Creadas
- locations - Ubicaciones geográficas
- weather_data - Datos meteorológicos con campos actualizados
- weather_forecasts - Pronósticos meteorológicos
- alerts - Sistema de alertas automáticas ⚠️
- user_preferences - Preferencias de usuario 👥
- data_logs - Logs del sistema 📊
- 🔗 Relaciones Incluidas
- ✅ Foreign Keys correctamente definidas
- ✅ CASCADE para eliminación de ubicaciones
- ✅ SET NULL para alertas cuando se eliminan datos meteorológicos
- ⚡ Características Avanzadas

#  Índices Optimizados:
- locations: lat/lon, región, nombre, país
- weather_data: ubicación+tiempo, fuente, código meteorológico
- alerts: ubicación+tipo, estado activo, nivel de riesgo
- Triggers Automáticos:
- Actualización automática de updated_at
- Para locations y user_preferences
- Validaciones de Datos:
- Latitud/longitud dentro de rangos válidos
- Humedad 0-100%, dirección viento 0-360°
- Valores positivos para lluvia, viento, UV
- Tipos de alertas y niveles de riesgo validados

# Vistas Útiles:
- current_weather_summary - Resumen meteorológico actual
- active_alerts_view - Alertas activas con ubicación
- Funciones PostgreSQL:
- get_current_weather(ciudad) - Obtener clima actual
- count_active_alerts_by_location() - Contar alertas por ubicación
- 🇨🇴 Datos de Ejemplo
- Incluye 10 ciudades principales de Colombia:
- Bogotá, Medellín, Cali, Barranquilla, Cartagena
- Bucaramanga, Pereira, Santa Marta, Manizales, Ibagué