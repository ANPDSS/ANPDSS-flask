"""
Outfit Location API
Handles weather data requests for outfit recommendations

SRP Refactoring: Each function has exactly ONE responsibility
- Validation functions: validate request parameters
- Key retrieval: get and check the API key
- URL building: construct OpenWeatherMap URLs
- HTTP fetch: make the request and return JSON
- Data enrichment: add outfit + condition data
- Route orchestrators: coordinate the above steps
"""
import os
import requests
from flask import Blueprint, request, jsonify

outfit_location_api = Blueprint('outfit_location_api', __name__, url_prefix='/api/outfit')

# --- CONFIGURATION ---

WEATHER_CONDITIONS = ['sunny', 'cloudy', 'rainy', 'snowy', 'windy', 'hot', 'cold', 'mild']

OUTFIT_RECOMMENDATIONS = [
    {'temp_min': 0,   'temp_max': 32,  'outfit': 'Heavy winter coat, boots, gloves'},
    {'temp_min': 33,  'temp_max': 50,  'outfit': 'Light jacket, long pants'},
    {'temp_min': 51,  'temp_max': 65,  'outfit': 'Sweater or hoodie, jeans'},
    {'temp_min': 66,  'temp_max': 80,  'outfit': 'T-shirt, shorts or light pants'},
    {'temp_min': 81,  'temp_max': 120, 'outfit': 'Light breathable clothing, hat'},
]

# --- VALIDATION ---

def validate_current_weather_params(zip_code, lat, lon):
    """Single responsibility: validate request parameters for current weather."""
    if not zip_code and not (lat and lon):
        return False, 'Missing location parameters (lat/lon or zip)'
    return True, None


def validate_forecast_params(lat, lon):
    """Single responsibility: validate request parameters for forecast."""
    if not lat or not lon:
        return False, 'Missing coordinates (lat and lon required)'
    return True, None


# --- API KEY ---

def get_api_key():
    """Single responsibility: retrieve and validate the OpenWeatherMap API key."""
    api_key = os.environ.get('OPENWEATHER_API_KEY')
    if not api_key:
        return None, 'Weather API key not configured'
    return api_key, None


# --- URL BUILDING ---

def build_current_weather_url(api_key, zip_code=None, lat=None, lon=None):
    """Single responsibility: construct the OpenWeatherMap current weather URL."""
    if zip_code:
        return f"https://api.openweathermap.org/data/2.5/weather?zip={zip_code},us&appid={api_key}&units=imperial"
    return f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=imperial"


def build_forecast_url(api_key, lat, lon):
    """Single responsibility: construct the OpenWeatherMap forecast URL."""
    return f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=imperial"


# --- HTTP REQUEST ---

def fetch_openweather_data(url):
    """Single responsibility: make HTTP request to OpenWeatherMap and return parsed JSON."""
    weather_response = requests.get(url, timeout=10)
    weather_response.raise_for_status()
    return weather_response.json()


# --- DATA ENRICHMENT ---

def get_outfit_for_temperature(temp):
    """Single responsibility: map a temperature value to an outfit recommendation string."""
    for recommendation in OUTFIT_RECOMMENDATIONS:
        if recommendation['temp_min'] <= temp <= recommendation['temp_max']:
            return recommendation['outfit']
    return 'Casual clothing'


def match_weather_conditions(weather_data):
    """Single responsibility: identify which condition labels apply to the weather data."""
    weather_str = str(weather_data.get('weather', [])).lower()
    return [c for c in WEATHER_CONDITIONS if c in weather_str]


def enrich_weather_response(weather_data):
    """Single responsibility: attach outfit recommendation and matched conditions to weather data."""
    if 'main' in weather_data and 'temp' in weather_data['main']:
        temp = weather_data['main']['temp']
        weather_data['outfit_recommendation'] = get_outfit_for_temperature(temp)
        weather_data['matched_conditions'] = match_weather_conditions(weather_data)
    return weather_data


# --- ROUTE ORCHESTRATORS ---

@outfit_location_api.route('/weather/current', methods=['GET', 'OPTIONS'])
def weather_current():
    """Orchestrator: validate → get key → build URL → fetch → enrich → respond."""
    zip_code = request.args.get('zip')
    lat = request.args.get('lat')
    lon = request.args.get('lon')

    valid, error = validate_current_weather_params(zip_code, lat, lon)
    if not valid:
        return jsonify({'message': error}), 400

    api_key, error = get_api_key()
    if not api_key:
        return jsonify({'message': error}), 500

    url = build_current_weather_url(api_key, zip_code=zip_code, lat=lat, lon=lon)

    try:
        weather_data = fetch_openweather_data(url)
        return jsonify(enrich_weather_response(weather_data)), 200
    except requests.exceptions.RequestException as e:
        return jsonify({'message': f'Weather API error: {str(e)}'}), 500


@outfit_location_api.route('/weather/forecast', methods=['GET', 'OPTIONS'])
def weather_forecast():
    """Orchestrator: validate → get key → build URL → fetch → respond."""
    lat = request.args.get('lat')
    lon = request.args.get('lon')

    valid, error = validate_forecast_params(lat, lon)
    if not valid:
        return jsonify({'message': error}), 400

    api_key, error = get_api_key()
    if not api_key:
        return jsonify({'message': error}), 500

    url = build_forecast_url(api_key, lat, lon)

    try:
        return jsonify(fetch_openweather_data(url)), 200
    except requests.exceptions.RequestException as e:
        return jsonify({'message': f'Weather API error: {str(e)}'}), 500
