"""
Outfit Location API
Handles weather data requests for outfit recommendations
"""
import os
import requests
from flask import Blueprint, request, jsonify
from flask_restful import Api, Resource

outfit_location_api = Blueprint('outfit_location_api', __name__, url_prefix='/api/outfit')
api = Api(outfit_location_api)


class WeatherCurrentAPI(Resource):
    """API for current weather data - proxies OpenWeatherMap API"""

    def get(self):
        """Get current weather by coordinates or ZIP code"""
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        zip_code = request.args.get('zip')
        
        # Read API key from environment variable
        api_key = os.environ.get('OPENWEATHER_API_KEY')
        
        if not api_key:
            return {'message': 'Weather API key not configured'}, 500
        
        # Build API URL based on parameters
        if zip_code:
            url = f"https://api.openweathermap.org/data/2.5/weather?zip={zip_code},us&appid={api_key}&units=imperial"
        elif lat and lon:
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=imperial"
        else:
            return {'message': 'Missing location parameters (lat/lon or zip)'}, 400
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return jsonify(response.json())
        except requests.exceptions.RequestException as e:
            return {'message': f'Weather API error: {str(e)}'}, 500


class WeatherForecastAPI(Resource):
    """API for weather forecast data - proxies OpenWeatherMap API"""

    def get(self):
        """Get weather forecast by coordinates"""
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        
        # Read API key from environment variable
        api_key = os.environ.get('OPENWEATHER_API_KEY')
        
        if not api_key:
            return {'message': 'Weather API key not configured'}, 500
        
        if not lat or not lon:
            return {'message': 'Missing coordinates (lat and lon required)'}, 400
        
        url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=imperial"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return jsonify(response.json())
        except requests.exceptions.RequestException as e:
            return {'message': f'Weather API error: {str(e)}'}, 500


# Register API resources
api.add_resource(WeatherCurrentAPI, '/weather/current')
api.add_resource(WeatherForecastAPI, '/weather/forecast')