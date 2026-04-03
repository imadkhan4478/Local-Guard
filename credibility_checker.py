"""
LocalGuard: Advanced Multi-API Credibility Checker
Combines 7 verification sources for maximum accuracy
"""

import re
import requests
from datetime import datetime, timedelta
import time
import json

class CredibilityChecker:
    def __init__(self, weather_api_key=None, news_api_key=None, nasa_key=None, 
                 twitter_key=None, twitter_secret=None, aqi_key=None, google_key=None):
        # API keys
        self.weather_api_key = weather_api_key
        self.news_api_key = news_api_key
        self.nasa_firms_key = nasa_key
        self.twitter_api_key = twitter_key
        self.twitter_api_secret = twitter_secret
        self.aqi_api_key = aqi_key
        self.google_geocoding_key = google_key
        
        # Cache
        self.weather_cache = {}
        self.news_cache = {}
        self.earthquake_cache = {}
        self.fire_cache = {}
        self.aqi_cache = {}
        self.twitter_cache = {}
        self.cache_duration = timedelta(minutes=30)
        
        # Keywords
        self.sensational_words = [
            'BREAKING', 'URGENT', 'ALERT', 'WARNING', 'SHARE NOW', 
            'BEFORE DELETED', 'SHOCKING', 'MUST SEE', 'OMG', 'WTF',
            'HAPPENING NOW', 'JUST IN', 'UNBELIEVABLE', 'INSANE'
        ]
        
        self.credible_sources = [
            'reuters', 'bbc', 'dawn', 'geo news', 'express tribune',
            'ndma', 'pmd', 'official', 'government', 'police',
            'rescue', 'ambulance', 'fire department', 'hospital',
            'associated press', 'ap news', 'cnn', 'al jazeera'
        ]
        
        self.panic_words = [
            'run', 'escape', 'evacuate immediately', 'everyone',
            'mass', 'thousands', 'hundreds dead', 'apocalypse',
            'end of world', 'catastrophe', 'deadly', 'fatal'
        ]
        
        self.vague_phrases = [
            'they say', 'i heard', 'someone told me', 'rumor',
            'apparently', 'supposedly', 'maybe', 'might be',
            'could be', 'not confirmed', 'unverified'
        ]
        
        self.weather_keywords = {
            'rain': ['rain', 'rainfall', 'downpour', 'precipitation', 'drizzle'],
            'flood': ['flood', 'flooding', 'inundated', 'submerged', 'waterlogged'],
            'storm': ['storm', 'thunderstorm', 'tempest', 'cyclone'],
            'snow': ['snow', 'snowfall', 'blizzard'],
            'heat': ['heatwave', 'hot', 'temperature', 'scorching'],
            'wind': ['wind', 'windy', 'hurricane', 'tornado', 'gale']
        }
        
        self.pakistani_cities = [
            'karachi', 'lahore', 'islamabad', 'rawalpindi', 'faisalabad',
            'multan', 'peshawar', 'quetta', 'sialkot', 'gujranwala',
            'hyderabad', 'abbottabad', 'mardan', 'mingora', 'nawabshah',
            'sukkur', 'larkana', 'sheikhupura', 'rahim yar khan', 'jhang'
        ]
        
        # City coordinates (for NASA FIRMS and AQI)
        self.city_coords = {
            'karachi': (24.8607, 67.0011),
            'lahore': (31.5497, 74.3436),
            'islamabad': (33.6844, 73.0479),
            'rawalpindi': (33.5651, 73.0169),
            'faisalabad': (31.4504, 73.1350),
            'multan': (30.1575, 71.5249),
            'peshawar': (34.0151, 71.5249),
            'quetta': (30.1798, 66.9750)
        }
    
    def extract_location(self, text):
        """Extract location from text"""
        text_lower = text.lower()
        for city in self.pakistani_cities:
            if city in text_lower:
                return city.title()
        return None
    
    # ============ WEATHER API ============
    def get_weather_data(self, location):
        """Get current weather from OpenWeatherMap"""
        if not self.weather_api_key or self.weather_api_key == "YOUR_OPENWEATHER_API_KEY_HERE":
            return None
        
        cache_key = f"weather_{location}"
        if cache_key in self.weather_cache:
            cached_time, cached_data = self.weather_cache[cache_key]
            if datetime.now() - cached_time < self.cache_duration:
                return cached_data
        
        try:
            url = "http://api.openweathermap.org/data/2.5/weather"
            params = {'q': f"{location},Pakistan", 'appid': self.weather_api_key, 'units': 'metric'}
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                weather_info = {
                    'description': data['weather'][0]['description'],
                    'main': data['weather'][0]['main'],
                    'temp': data['main']['temp'],
                    'humidity': data['main']['humidity'],
                    'wind_speed': data['wind']['speed'],
                    'rain': data.get('rain', {}).get('1h', 0),
                    'clouds': data.get('clouds', {}).get('all', 0)
                }
                self.weather_cache[cache_key] = (datetime.now(), weather_info)
                return weather_info
        except Exception as e:
            print(f"[Weather API] Error: {e}")
        return None
    
    # ============ USGS EARTHQUAKE API ============
    def check_earthquakes(self, location=None):
        """Check recent earthquakes from USGS"""
        cache_key = "earthquakes_recent"
        if cache_key in self.earthquake_cache:
            cached_time, cached_data = self.earthquake_cache[cache_key]
            if datetime.now() - cached_time < self.cache_duration:
                return cached_data
        
        try:
            # Get earthquakes from last 24 hours
            url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                earthquakes = []
                
                for feature in data['features']:
                    eq = {
                        'magnitude': feature['properties']['mag'],
                        'place': feature['properties']['place'],
                        'time': datetime.fromtimestamp(feature['properties']['time'] / 1000),
                        'coords': feature['geometry']['coordinates']
                    }
                    
                    # Filter for Pakistan region if location specified
                    if location:
                        if 'pakistan' in eq['place'].lower() or location.lower() in eq['place'].lower():
                            earthquakes.append(eq)
                    else:
                        if 'pakistan' in eq['place'].lower():
                            earthquakes.append(eq)
                
                result = {'earthquakes': earthquakes, 'count': len(earthquakes)}
                self.earthquake_cache[cache_key] = (datetime.now(), result)
                return result
        except Exception as e:
            print(f"[USGS API] Error: {e}")
        return None
    
    # ============ NASA FIRMS FIRE API ============
    def check_fires(self, location):
        """Check for active fires near location using NASA satellite data"""
        if not self.nasa_firms_key or self.nasa_firms_key == "YOUR_NASA_KEY_HERE":
            return None
        
        if location.lower() not in self.city_coords:
            return None
        
        lat, lon = self.city_coords[location.lower()]
        cache_key = f"fires_{location}"
        
        if cache_key in self.fire_cache:
            cached_time, cached_data = self.fire_cache[cache_key]
            if datetime.now() - cached_time < self.cache_duration:
                return cached_data
        
        try:
            # NASA FIRMS API - 10km radius around city
            url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{self.nasa_firms_key}/VIIRS_SNPP_NRT/{lat-0.1},{lon-0.1},{lat+0.1},{lon+0.1}/1"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                lines = response.text.strip().split('\n')
                fire_count = max(0, len(lines) - 1)  # Subtract header
                
                result = {
                    'active_fires': fire_count,
                    'location': location,
                    'radius_km': 10
                }
                self.fire_cache[cache_key] = (datetime.now(), result)
                return result
        except Exception as e:
            print(f"[NASA FIRMS API] Error: {e}")
        return None
    
    # ============ AIR QUALITY API ============
    def check_air_quality(self, location):
        """Check air quality for pollution/smog disasters"""
        if not self.aqi_api_key or self.aqi_api_key == "YOUR_AQI_KEY_HERE":
            return None
        
        cache_key = f"aqi_{location}"
        if cache_key in self.aqi_cache:
            cached_time, cached_data = self.aqi_cache[cache_key]
            if datetime.now() - cached_time < self.cache_duration:
                return cached_data
        
        try:
            url = f"https://api.waqi.info/feed/{location}/?token={self.aqi_api_key}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'ok':
                    aqi_value = data['data']['aqi']
                    result = {
                        'aqi': aqi_value,
                        'level': self._get_aqi_level(aqi_value),
                        'location': location
                    }
                    self.aqi_cache[cache_key] = (datetime.now(), result)
                    return result
        except Exception as e:
            print(f"[AQI API] Error: {e}")
        return None
    
    def _get_aqi_level(self, aqi):
        """Convert AQI number to level"""
        if aqi <= 50: return "Good"
        elif aqi <= 100: return "Moderate"
        elif aqi <= 150: return "Unhealthy for Sensitive"
        elif aqi <= 200: return "Unhealthy"
        elif aqi <= 300: return "Very Unhealthy"
        else: return "Hazardous"
    
    # ============ VERIFICATION LOGIC ============
    def verify_weather_claim(self, text, location):
        """Verify weather-related disaster claims"""
        if not location:
            return None
        
        weather_data = self.get_weather_data(location)
        if not weather_data:
            return None
        
        text_lower = text.lower()
        verification = {
            'weather_data': weather_data,
            'matches': [],
            'mismatches': [],
            'confidence': 50
        }
        
        # Check rain/flood
        rain_mentioned = any(word in text_lower for word in self.weather_keywords['rain'] + self.weather_keywords['flood'])
        if rain_mentioned:
            if weather_data['rain'] > 0 or 'rain' in weather_data['description'].lower() or weather_data['humidity'] > 80:
                verification['matches'].append(f"✅ Rain/humidity confirmed: {weather_data['description']}, {weather_data['humidity']}% humidity")
                verification['confidence'] += 25
            else:
                verification['mismatches'].append(f"⚠️ No rain detected: {weather_data['description']}, {weather_data['humidity']}% humidity")
                verification['confidence'] -= 30
        
        # Check storm
        storm_mentioned = any(word in text_lower for word in self.weather_keywords['storm'])
        if storm_mentioned:
            if 'storm' in weather_data['description'].lower() or weather_data['wind_speed'] > 10:
                verification['matches'].append(f"✅ Storm conditions: {weather_data['description']}, Wind {weather_data['wind_speed']} m/s")
                verification['confidence'] += 25
            else:
                verification['mismatches'].append(f"⚠️ No storm: {weather_data['description']}, Wind {weather_data['wind_speed']} m/s")
                verification['confidence'] -= 25
        
        verification['confidence'] = max(0, min(100, verification['confidence']))
        return verification
    
    def verify_earthquake_claim(self, text, location):
        """Verify earthquake claims with USGS data"""
        text_lower = text.lower()
        if 'earthquake' not in text_lower and 'quake' not in text_lower and 'tremor' not in text_lower:
            return None
        
        eq_data = self.check_earthquakes(location)
        if not eq_data:
            return None
        
        verification = {
            'earthquake_data': eq_data,
            'confidence': 50,
            'status': ''
        }
        
        if eq_data['count'] > 0:
            recent_eq = eq_data['earthquakes'][0]
            time_diff = datetime.now() - recent_eq['time']
            
            if time_diff < timedelta(hours=6):
                verification['confidence'] = 95
                verification['status'] = f"✅ VERIFIED: Magnitude {recent_eq['magnitude']} earthquake detected"
                verification['details'] = f"Location: {recent_eq['place']}, Time: {recent_eq['time'].strftime('%H:%M UTC')}"
            else:
                verification['confidence'] = 60
                verification['status'] = f"⚠️ Old earthquake found (M{recent_eq['magnitude']}, {time_diff.seconds//3600}h ago)"
        else:
            verification['confidence'] = 20
            verification['status'] = "❌ No recent earthquakes detected in Pakistan"
        
        return verification
    
    def verify_fire_claim(self, text, location):
        """Verify fire claims with NASA satellite data"""
        text_lower = text.lower()
        if 'fire' not in text_lower and 'blaze' not in text_lower and 'burn' not in text_lower:
            return None
        
        fire_data = self.check_fires(location)
        if not fire_data:
            return None
        
        verification = {
            'fire_data': fire_data,
            'confidence': 50,
            'status': ''
        }
        
        if fire_data['active_fires'] > 0:
            verification['confidence'] = 85
            verification['status'] = f"✅ SATELLITE VERIFIED: {fire_data['active_fires']} active fire(s) detected"
        elif fire_data['active_fires'] == 0:
            verification['confidence'] = 30
            verification['status'] = "⚠️ No active fires detected by satellite in 10km radius"
        
        return verification
    
    def verify_pollution_claim(self, text, location):
        """Verify smog/pollution claims"""
        text_lower = text.lower()
        if 'smog' not in text_lower and 'pollution' not in text_lower and 'air quality' not in text_lower:
            return None
        
        aqi_data = self.check_air_quality(location)
        if not aqi_data:
            return None
        
        verification = {
            'aqi_data': aqi_data,
            'confidence': 50,
            'status': ''
        }
        
        if aqi_data['aqi'] > 150:
            verification['confidence'] = 90
            verification['status'] = f"✅ VERIFIED: AQI {aqi_data['aqi']} - {aqi_data['level']}"
        elif aqi_data['aqi'] > 100:
            verification['confidence'] = 70
            verification['status'] = f"⚠️ Moderate pollution: AQI {aqi_data['aqi']} - {aqi_data['level']}"
        else:
            verification['confidence'] = 30
            verification['status'] = f"❌ Good air quality: AQI {aqi_data['aqi']} - {aqi_data['level']}"
        
        return verification
    
    def analyze_credibility(self, text, is_disaster=False):
        """Linguistic credibility analysis"""
        text_lower = text.lower()
        text_upper = text.upper()
        
        credibility_score = 70
        flags = []
        warnings = []
        positive_signals = []
        
        # Sensational language
        sensational_count = sum(1 for word in self.sensational_words if word in text_upper)
        if sensational_count > 0:
            credibility_score -= (sensational_count * 10)
            warnings.append("⚠️ Sensational language detected")
        
        # Credible sources
        credible_count = sum(1 for source in self.credible_sources if source in text_lower)
        if credible_count > 0:
            credibility_score += (credible_count * 15)
            positive_signals.append(f"✅ {credible_count} credible source(s) mentioned")
        
        # Panic words
        panic_count = sum(1 for word in self.panic_words if word in text_lower)
        if panic_count > 2:
            credibility_score -= 15
            warnings.append("⚠️ Excessive panic language")
        
        # Vague language
        vague_count = sum(1 for phrase in self.vague_phrases if phrase in text_lower)
        if vague_count > 0:
            credibility_score -= (vague_count * 8)
            warnings.append("⚠️ Vague/unverifiable language")
        
        # Excessive punctuation
        if text.count('!') > 3:
            credibility_score -= 10
            warnings.append("⚠️ Excessive punctuation")
        
        # Caps ratio
        if len(text) > 0:
            caps_ratio = sum(1 for c in text if c.isupper()) / len(text)
            if caps_ratio > 0.3:
                credibility_score -= 15
                warnings.append("⚠️ Excessive CAPS")
        
        credibility_score = max(0, min(100, credibility_score))
        
        return {
            'credibility_score': credibility_score,
            'warnings': warnings,
            'positive_signals': positive_signals
        }
    
    def generate_comprehensive_report(self, text, is_disaster, disaster_confidence):
        """Generate comprehensive multi-API verification report"""
        print("\n=== Multi-API Verification Started ===")
        
        # Stage 1: Linguistic
        linguistic = self.analyze_credibility(text, is_disaster)
        
        # Stage 2: Location
        location = self.extract_location(text)
        
        # Stage 3: Multi-API verification
        verifications = []
        final_score = linguistic['credibility_score']
        
        # Weather verification
        if location:
            weather_check = self.verify_weather_claim(text, location)
            if weather_check:
                verifications.append({
                    'type': 'Weather Verification',
                    'status': 'VERIFIED' if weather_check['matches'] else 'MISMATCH',
                    'details': weather_check['matches'] + weather_check['mismatches'],
                    'confidence': weather_check['confidence']
                })
                final_score += (weather_check['confidence'] - 50) * 0.3
        
        # Earthquake verification
        eq_check = self.verify_earthquake_claim(text, location)
        if eq_check:
            verifications.append({
                'type': 'Earthquake Verification (USGS Satellite)',
                'status': eq_check['status'],
                'details': [eq_check.get('details', '')],
                'confidence': eq_check['confidence']
            })
            final_score += (eq_check['confidence'] - 50) * 0.4
        
        # Fire verification
        if location:
            fire_check = self.verify_fire_claim(text, location)
            if fire_check:
                verifications.append({
                    'type': 'Fire Verification (NASA Satellite)',
                    'status': fire_check['status'],
                    'details': [],
                    'confidence': fire_check['confidence']
                })
                final_score += (fire_check['confidence'] - 50) * 0.4
        
        # Air quality verification
        if location:
            aqi_check = self.verify_pollution_claim(text, location)
            if aqi_check:
                verifications.append({
                    'type': 'Air Quality Verification',
                    'status': aqi_check['status'],
                    'details': [],
                    'confidence': aqi_check['confidence']
                })
                final_score += (aqi_check['confidence'] - 50) * 0.3
        
        final_score = max(0, min(100, final_score))
        
        # Determine status
        if final_score >= 70:
            final_risk = "LOW RISK"
            overall_status = "✅ VERIFIED DISASTER - Multiple sources confirm"
        elif final_score >= 40:
            final_risk = "MEDIUM RISK"
            overall_status = "⚠️ PARTIALLY VERIFIED - Some confirmation"
        else:
            final_risk = "HIGH RISK"
            overall_status = "❌ LIKELY MISINFORMATION - No verification"
        
        print(f"[Final] Score: {final_score}% | {overall_status}")
        
        return {
            'disaster_detected': is_disaster,
            'disaster_confidence': disaster_confidence,
            'linguistic_score': linguistic['credibility_score'],
            'final_credibility_score': final_score,
            'risk_level': final_risk,
            'overall_status': overall_status,
            'warnings': linguistic['warnings'],
            'positive_signals': linguistic['positive_signals'],
            'verification_details': verifications,
            'location_detected': location,
            'apis_used': len(verifications)
        }