from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import logging

from models import Location, WeatherData, Alert, UserPreference
from schemas import AlertCreate, AlertResponse, AlertQuery, AlertStatistics

logger = logging.getLogger(__name__)

class AlertService:
    """Servicio para gestión de alertas meteorológicas"""
    
    # Umbrales por defecto para diferentes tipos de alertas
    DEFAULT_THRESHOLDS = {
        'temperatura_alta': {
            'bajo': 30.0,
            'medio': 35.0, 
            'alto': 40.0,
            'crítico': 45.0
        },
        'temperatura_baja': {
            'bajo': 5.0,
            'medio': 0.0,
            'alto': -5.0,
            'crítico': -10.0
        },
        'lluvia_intensa': {
            'bajo': 10.0,
            'medio': 25.0,
            'alto': 50.0,
            'crítico': 100.0
        },
        'viento_fuerte': {
            'bajo': 20.0,
            'medio': 35.0,
            'alto': 50.0,
            'crítico': 75.0
        },
        'humedad_alta': {
            'bajo': 80.0,
            'medio': 90.0,
            'alto': 95.0,
            'crítico': 98.0
        }
    }
    
    def __init__(self):
        self.thresholds = self.DEFAULT_THRESHOLDS.copy()
    
    def evaluate_weather_data(self, db: Session, weather_data: WeatherData) -> List[Alert]:
        """Evalúa datos meteorológicos y genera alertas si es necesario"""
        alerts = []
        
        try:
            # Evaluar temperatura alta
            if weather_data.temperature_2m is not None:
                alert = self._check_temperature_high(weather_data)
                if alert:
                    alerts.append(alert)
                
                # Evaluar temperatura baja
                alert = self._check_temperature_low(weather_data)
                if alert:
                    alerts.append(alert)
            
            # Evaluar lluvia intensa
            if weather_data.rain is not None:
                alert = self._check_heavy_rain(weather_data)
                if alert:
                    alerts.append(alert)
            
            # Evaluar viento fuerte
            if weather_data.windspeed_10m is not None:
                alert = self._check_strong_wind(weather_data)
                if alert:
                    alerts.append(alert)
            
            # Evaluar humedad alta
            if weather_data.relativehumidity_2m is not None:
                alert = self._check_high_humidity(weather_data)
                if alert:
                    alerts.append(alert)
            
            # Guardar alertas en la base de datos
            for alert in alerts:
                # Verificar si ya existe una alerta similar activa
                existing_alert = db.query(Alert).filter(
                    and_(
                        Alert.location_id == alert.location_id,
                        Alert.alert_type == alert.alert_type,
                        Alert.is_active == True,
                        Alert.alert_start >= datetime.now() - timedelta(hours=24)
                    )
                ).first()
                
                if not existing_alert:
                    db.add(alert)
            
            if alerts:
                db.commit()
                logger.info(f"Generated {len(alerts)} alerts for location {weather_data.location_id}")
            
        except Exception as e:
            logger.error(f"Error evaluating weather data for alerts: {e}")
            db.rollback()
        
        return alerts
    
    def _check_temperature_high(self, weather_data: WeatherData) -> Optional[Alert]:
        """Verifica alertas por temperatura alta"""
        temp = weather_data.temperature_2m
        thresholds = self.thresholds['temperatura_alta']
        
        risk_level = None
        if temp >= thresholds['crítico']:
            risk_level = 'crítico'
        elif temp >= thresholds['alto']:
            risk_level = 'alto'
        elif temp >= thresholds['medio']:
            risk_level = 'medio'
        elif temp >= thresholds['bajo']:
            risk_level = 'bajo'
        
        if risk_level:
            return Alert(
                location_id=weather_data.location_id,
                weather_data_id=weather_data.id,
                alert_type='temperatura_alta',
                risk_level=risk_level,
                severity='warning' if risk_level in ['bajo', 'medio'] else 'advisory',
                threshold_value=thresholds[risk_level],
                current_value=temp,
                alert_start=datetime.now(),
                description=f"Temperatura alta detectada: {temp}°C",
                recommendations=self._get_temperature_recommendations(temp, 'alta')
            )
        return None
    
    def _check_temperature_low(self, weather_data: WeatherData) -> Optional[Alert]:
        """Verifica alertas por temperatura baja"""
        temp = weather_data.temperature_2m
        thresholds = self.thresholds['temperatura_baja']
        
        risk_level = None
        if temp <= thresholds['crítico']:
            risk_level = 'crítico'
        elif temp <= thresholds['alto']:
            risk_level = 'alto'
        elif temp <= thresholds['medio']:
            risk_level = 'medio'
        elif temp <= thresholds['bajo']:
            risk_level = 'bajo'
        
        if risk_level:
            return Alert(
                location_id=weather_data.location_id,
                weather_data_id=weather_data.id,
                alert_type='temperatura_baja',
                risk_level=risk_level,
                severity='warning' if risk_level in ['bajo', 'medio'] else 'advisory',
                threshold_value=thresholds[risk_level],
                current_value=temp,
                alert_start=datetime.now(),
                description=f"Temperatura baja detectada: {temp}°C",
                recommendations=self._get_temperature_recommendations(temp, 'baja')
            )
        return None
    
    def _check_heavy_rain(self, weather_data: WeatherData) -> Optional[Alert]:
        """Verifica alertas por lluvia intensa"""
        rain = weather_data.rain
        thresholds = self.thresholds['lluvia_intensa']
        
        risk_level = None
        if rain >= thresholds['crítico']:
            risk_level = 'crítico'
        elif rain >= thresholds['alto']:
            risk_level = 'alto'
        elif rain >= thresholds['medio']:
            risk_level = 'medio'
        elif rain >= thresholds['bajo']:
            risk_level = 'bajo'
        
        if risk_level:
            return Alert(
                location_id=weather_data.location_id,
                weather_data_id=weather_data.id,
                alert_type='lluvia_intensa',
                risk_level=risk_level,
                severity='watch' if risk_level in ['alto', 'crítico'] else 'warning',
                threshold_value=thresholds[risk_level],
                current_value=rain,
                alert_start=datetime.now(),
                description=f"Lluvia intensa detectada: {rain}mm",
                recommendations="Evitar viajes innecesarios. Manténgase en lugares seguros."
            )
        return None
    
    def _check_strong_wind(self, weather_data: WeatherData) -> Optional[Alert]:
        """Verifica alertas por viento fuerte"""
        wind_speed = weather_data.windspeed_10m
        thresholds = self.thresholds['viento_fuerte']
        
        risk_level = None
        if wind_speed >= thresholds['crítico']:
            risk_level = 'crítico'
        elif wind_speed >= thresholds['alto']:
            risk_level = 'alto'
        elif wind_speed >= thresholds['medio']:
            risk_level = 'medio'
        elif wind_speed >= thresholds['bajo']:
            risk_level = 'bajo'
        
        if risk_level:
            return Alert(
                location_id=weather_data.location_id,
                weather_data_id=weather_data.id,
                alert_type='viento_fuerte',
                risk_level=risk_level,
                severity='advisory' if risk_level in ['alto', 'crítico'] else 'warning',
                threshold_value=thresholds[risk_level],
                current_value=wind_speed,
                alert_start=datetime.now(),
                description=f"Viento fuerte detectado: {wind_speed}m/s",
                recommendations="Evitar actividades al aire libre. Asegurar objetos sueltos."
            )
        return None
    
    def _check_high_humidity(self, weather_data: WeatherData) -> Optional[Alert]:
        """Verifica alertas por humedad alta"""
        humidity = weather_data.relativehumidity_2m
        thresholds = self.thresholds['humedad_alta']
        
        risk_level = None
        if humidity >= thresholds['crítico']:
            risk_level = 'crítico'
        elif humidity >= thresholds['alto']:
            risk_level = 'alto'
        elif humidity >= thresholds['medio']:
            risk_level = 'medio'
        elif humidity >= thresholds['bajo']:
            risk_level = 'bajo'
        
        if risk_level:
            return Alert(
                location_id=weather_data.location_id,
                weather_data_id=weather_data.id,
                alert_type='humedad_alta',
                risk_level=risk_level,
                severity='info',
                threshold_value=thresholds[risk_level],
                current_value=humidity,
                alert_start=datetime.now(),
                description=f"Humedad alta detectada: {humidity}%",
                recommendations="Manténgase hidratado. Busque lugares con ventilación."
            )
        return None
    
    def _get_temperature_recommendations(self, temp: float, type_temp: str) -> str:
        """Obtiene recomendaciones según la temperatura"""
        if type_temp == 'alta':
            if temp >= 40:
                return "Evite la exposición directa al sol. Manténgase hidratado."
            elif temp >= 35:
                return "Limite actividades al aire libre. Use ropa ligera."
            else:
                return "Use protector solar. Manténgase hidratado."
        else:
            return "Use ropa apropiada para el frío."
    
    def get_active_alerts(self, db: Session, location_id: Optional[int] = None) -> List[Alert]:
        """Obtiene alertas activas"""
        try:
            query = db.query(Alert).filter(Alert.is_active == True)
            
            if location_id:
                query = query.filter(Alert.location_id == location_id)
            
            return query.order_by(Alert.alert_start.desc()).all()
            
        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return []
    
    def deactivate_alert(self, db: Session, alert_id: int) -> bool:
        """Desactiva una alerta"""
        try:
            alert = db.query(Alert).filter(Alert.id == alert_id).first()
            if alert:
                alert.is_active = False
                alert.alert_end = datetime.now()
                db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deactivating alert {alert_id}: {e}")
            db.rollback()
            return False
    
    def get_alert_statistics(self, db: Session, days: int = 30) -> AlertStatistics:
        """Obtiene estadísticas de alertas"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Total de alertas
            total_alerts = db.query(Alert).filter(
                Alert.created_at >= cutoff_date
            ).count()
            
            # Alertas activas
            active_alerts = db.query(Alert).filter(
                and_(
                    Alert.is_active == True,
                    Alert.created_at >= cutoff_date
                )
            ).count()
            
            # Alertas por tipo
            alerts_by_type = dict(
                db.query(Alert.alert_type, func.count(Alert.id))
                .filter(Alert.created_at >= cutoff_date)
                .group_by(Alert.alert_type)
                .all()
            )
            
            # Alertas por nivel de riesgo
            alerts_by_risk = dict(
                db.query(Alert.risk_level, func.count(Alert.id))
                .filter(Alert.created_at >= cutoff_date)
                .group_by(Alert.risk_level)
                .all()
            )
            
            # Ubicación más afectada
            most_affected_query = (
                db.query(Location, func.count(Alert.id).label('alert_count'))
                .join(Alert)
                .filter(Alert.created_at >= cutoff_date)
                .group_by(Location.id)
                .order_by(func.count(Alert.id).desc())
                .first()
            )
            
            most_affected_location = most_affected_query[0] if most_affected_query else None
            
            return AlertStatistics(
                total_alerts=total_alerts,
                active_alerts=active_alerts,
                alerts_by_type=alerts_by_type,
                alerts_by_risk_level=alerts_by_risk,
                most_affected_location=most_affected_location
            )
            
        except Exception as e:
            logger.error(f"Error getting alert statistics: {e}")
            return AlertStatistics(
                total_alerts=0,
                active_alerts=0,
                alerts_by_type={},
                alerts_by_risk_level={},
                most_affected_location=None
            )

# Instancia singleton del servicio
alert_service = AlertService() 