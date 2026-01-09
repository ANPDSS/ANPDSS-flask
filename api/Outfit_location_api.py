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

    # CORS is handled globally by flask-cors in __init__.py
    # No need to handle OPTIONS manually

    lat = request.args.get('lat')
    lon = request.args.get('lon')
    zip_code = request.args.get('zip')

    # Read API key from environment variable
    api_key = os.environ.get('OPENWEATHER_API_KEY')

    if not api_key:
        return jsonify({'message': 'Weather API key not configured'}), 500

    # Build API URL based on parameters
    if zip_code:
        url = f"https://api.openweathermap.org/data/2.5/weather?zip={zip_code},us&appid={api_key}&units=imperial"
    elif lat and lon:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=imperial"
    else:
        return jsonify({'message': 'Missing location parameters (lat/lon or zip)'}), 400

    try:
        weather_response = requests.get(url, timeout=10)
        weather_response.raise_for_status()
        return jsonify(weather_response.json()), 200

    except requests.exceptions.RequestException as e:
        return jsonify({'message': f'Weather API error: {str(e)}'}), 500


@outfit_location_api.route('/weather/forecast', methods=['GET', 'OPTIONS'])
def weather_forecast():
    """Get weather forecast by coordinates"""

    # CORS is handled globally by flask-cors in __init__.py
    # No need to handle OPTIONS manually

    lat = request.args.get('lat')
    lon = request.args.get('lon')

    # Read API key from environment variable
    api_key = os.environ.get('OPENWEATHER_API_KEY')

    if not api_key:
        return jsonify({'message': 'Weather API key not configured'}), 500

    if not lat or not lon:
        return jsonify({'message': 'Missing coordinates (lat and lon required)'}), 400

    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=imperial"

    try:
        weather_response = requests.get(url, timeout=10)
        weather_response.raise_for_status()
        return jsonify(weather_response.json()), 200

    except requests.exceptions.RequestException as e:
        return jsonify({'message': f'Weather API error: {str(e)}'}), 500