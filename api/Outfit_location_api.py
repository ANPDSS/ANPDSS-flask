"""
Outfit Location API
Handles weather data requests for outfit recommendations

Programming Constructs Used:
- Sequencing: Code executes step by step
- Selection: if/elif/else for parameter validation and error handling
- Iteration: Loops for processing weather data and outfit recommendations
- Lists: Arrays for storing outfit suggestions and weather conditions
"""
import os
from urllib import response
import requests
from flask import Blueprint, request, jsonify

outfit_location_api = Blueprint('outfit_location_api', __name__, url_prefix='/api/outfit')

# List of weather condition categories for outfit recommendations
WEATHER_CONDITIONS = ['sunny', 'cloudy', 'rainy', 'snowy', 'windy', 'hot', 'cold', 'mild']

# List of outfit recommendations based on temperature ranges
OUTFIT_RECOMMENDATIONS = [
    {'temp_min': 0, 'temp_max': 32, 'outfit': 'Heavy winter coat, boots, gloves'},
    {'temp_min': 33, 'temp_max': 50, 'outfit': 'Light jacket, long pants'},
    {'temp_min': 51, 'temp_max': 65, 'outfit': 'Sweater or hoodie, jeans'},
    {'temp_min': 66, 'temp_max': 80, 'outfit': 'T-shirt, shorts or light pants'},
    {'temp_min': 81, 'temp_max': 120, 'outfit': 'Light breathable clothing, hat'}
]


def get_outfit_for_temperature(temp):
    """
    Iterate through outfit recommendations to find appropriate clothing.
    Demonstrates iteration and selection.
    """
    recommended_outfit = 'Casual clothing'

    # Iteration: Loop through the list of outfit recommendations
    for recommendation in OUTFIT_RECOMMENDATIONS:
        # Selection: Check if temperature falls within range
        if recommendation['temp_min'] <= temp <= recommendation['temp_max']:
            recommended_outfit = recommendation['outfit']
            break

    return recommended_outfit


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
        weather_data = weather_response.json()

        # Add outfit recommendation based on temperature (demonstrates iteration/selection)
        if 'main' in weather_data and 'temp' in weather_data['main']:
            temp = weather_data['main']['temp']
            weather_data['outfit_recommendation'] = get_outfit_for_temperature(temp)

            # List: Collect applicable weather conditions
            applicable_conditions = []
            for condition in WEATHER_CONDITIONS:
                if condition in str(weather_data.get('weather', [])).lower():
                    applicable_conditions.append(condition)
            weather_data['matched_conditions'] = applicable_conditions

        return jsonify(weather_data), 200

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