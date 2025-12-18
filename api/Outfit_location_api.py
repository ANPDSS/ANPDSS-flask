"""
Outfit Location API
Handles weather data requests for outfit recommendations
"""
import os
from urllib import response
import requests
from flask import Blueprint, request, jsonify

outfit_location_api = Blueprint('outfit_location_api', __name__, url_prefix='/api/outfit')


@outfit_location_api.route('/weather/current', methods=['GET', 'OPTIONS'])
def weather_current():
    """Get current weather by coordinates or ZIP code"""
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:4500'
        response.headers['Access-Control-Allow-Credentials'] = 'true'

        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Origin'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response, 204
    
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    zip_code = request.args.get('zip')
    
    # Read API key from environment variable
    api_key = os.environ.get('OPENWEATHER_API_KEY')
    
    if not api_key:
        response = jsonify({'message': 'Weather API key not configured'})
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:4500'
        response.headers['Access-Control-Allow-Credentials'] = 'true'

        return response, 500
    
    # Build API URL based on parameters
    if zip_code:
        url = f"https://api.openweathermap.org/data/2.5/weather?zip={zip_code},us&appid={api_key}&units=imperial"
    elif lat and lon:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=imperial"
    else:
        response = jsonify({'message': 'Missing location parameters (lat/lon or zip)'})
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:4500'
        response.headers['Access-Control-Allow-Credentials'] = 'true'

        return response, 400
    
    try:
        weather_response = requests.get(url, timeout=10)
        weather_response.raise_for_status()
        
        response = jsonify(weather_response.json())
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:4500'
        response.headers['Access-Control-Allow-Credentials'] = 'true'

        return response, 200
        
    except requests.exceptions.RequestException as e:
        response = jsonify({'message': f'Weather API error: {str(e)}'})
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:4500'
        response.headers['Access-Control-Allow-Credentials'] = 'true'

        return response, 500


@outfit_location_api.route('/weather/forecast', methods=['GET', 'OPTIONS'])
def weather_forecast():
    """Get weather forecast by coordinates"""
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:4500'
        response.headers['Access-Control-Allow-Credentials'] = 'true'

        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Origin'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response, 204
    
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    
    # Read API key from environment variable
    api_key = os.environ.get('OPENWEATHER_API_KEY')
    
    if not api_key:
        response = jsonify({'message': 'Weather API key not configured'})
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:4500'
        response.headers['Access-Control-Allow-Credentials'] = 'true'

        return response, 500
    
    if not lat or not lon:
        response = jsonify({'message': 'Missing coordinates (lat and lon required)'})
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:4500'
        response.headers['Access-Control-Allow-Credentials'] = 'true'

        return response, 400
    
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=imperial"
    
    try:
        weather_response = requests.get(url, timeout=10)
        weather_response.raise_for_status()
        
        response = jsonify(weather_response.json())
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:4500'
        response.headers['Access-Control-Allow-Credentials'] = 'true'

        return response, 200
        
    except requests.exceptions.RequestException as e:
        response = jsonify({'message': f'Weather API error: {str(e)}'})
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:4500'
        response.headers['Access-Control-Allow-Credentials'] = 'true'

        return response, 500