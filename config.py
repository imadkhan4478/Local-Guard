"""
LocalGuard: API Configuration
Store your API keys here
"""

# OpenWeatherMap API (Weather verification)
OPENWEATHER_API_KEY = "596807e097400f3840ed03d52284f372"

# News API (News verification)
NEWS_API_KEY = "YOUR_NEWS_API_KEY_HERE"  # Optional - can add later

# NASA FIRMS API (Satellite fire detection)
NASA_FIRMS_API_KEY = "cea5d2ed41948439baa50c98237fdb2a"

# Twitter/X API (Social media verification)
TWITTER_API_KEY = "ZNbSVt7q1mJQOnO0pPfjUUMDN"
TWITTER_API_SECRET = "g07vTY9ib0gFbh6jo3UA5Tx5CVp5wPPHoE8u7icXUFRBqiqtMt"

# Air Quality API (Pollution/smog disasters)
AQI_API_KEY = "065654a7fa7d36689aae35e9a7608e624bf92e73"

# Google Geocoding API (Location verification)
# Get from: https://console.cloud.google.com/


# API Settings
WEATHER_API_ENABLED = True
NEWS_API_ENABLED = False  # Enable when you get the key
NASA_FIRMS_ENABLED = True
TWITTER_API_ENABLED = True
AQI_API_ENABLED = True
GEOCODING_ENABLED = False  # Enable when you get Google key

# USGS Earthquake API (No key needed - always enabled)
USGS_ENABLED = True

# Cache settings
CACHE_DURATION_MINUTES = 30

# Rate limiting
MAX_NEWS_SEARCHES_PER_SESSION = 50
MAX_WEATHER_CHECKS_PER_SESSION = 500
MAX_TWITTER_SEARCHES_PER_SESSION = 100
MAX_NASA_FIRMS_CHECKS_PER_SESSION = 200

# Verification thresholds
MIN_NEWS_SOURCES_FOR_VERIFICATION = 2
WEATHER_MATCH_THRESHOLD = 0.7
MIN_TWITTER_MENTIONS_FOR_VERIFICATION = 5