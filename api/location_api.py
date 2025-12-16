"""
Location API
Handles location data for personalized mood recommendations
"""
from flask import Blueprint, request, jsonify, g
from flask_restful import Api, Resource
from api.jwt_authorize import token_required
from model.location import UserLocation
import requests
import os

location_api = Blueprint('location_api', __name__, url_prefix='/api/location')
api = Api(location_api)

class LocationAPI(Resource):
    """API for managing user location"""

    @token_required()
    def get(self):
        """Get user's most recent location"""
        current_user = g.current_user

        # Get most recent location for user
        location = UserLocation.query.filter_by(_user_id=current_user.id)\
            .order_by(UserLocation._timestamp.desc()).first()

        if not location:
            return {'message': 'No location data found'}, 404

        return jsonify(location.read())

    @token_required()
    def post(self):
        """Save new location data"""
        current_user = g.current_user
        body = request.get_json()

        # Create new location entry
        new_location = UserLocation(
            user_id=current_user.id,
            latitude=body.get('latitude'),
            longitude=body.get('longitude'),
            city=body.get('city'),
            region=body.get('region'),
            country=body.get('country'),
            method=body.get('method', 'IP')
        )

        result = new_location.create()
        if result:
            return jsonify(result.read()), 201
        else:
            return {'message': 'Failed to save location'}, 500


class LocationHistoryAPI(Resource):
    """API for location history"""

    @token_required()
    def get(self):
        """Get user's location history"""
        current_user = g.current_user

        # Get query parameters
        limit = request.args.get('limit', 10, type=int)

        # Query locations for user
        locations = UserLocation.query.filter_by(_user_id=current_user.id)\
            .order_by(UserLocation._timestamp.desc())\
            .limit(limit).all()

        return jsonify([loc.read() for loc in locations])


class WeatherAPI(Resource):
    """API for weather data based on location"""

    @token_required()
    def get(self):
        """Get weather for user's location"""
        current_user = g.current_user

        # Get most recent location
        location = UserLocation.query.filter_by(_user_id=current_user.id)\
            .order_by(UserLocation._timestamp.desc()).first()

        if not location or not location.latitude or not location.longitude:
            return {'message': 'No location data available'}, 404

        # Get weather from external API (using OpenWeatherMap)
        api_key = os.getenv('OPENWEATHER_API_KEY')
        if not api_key:
            return {'message': 'Weather API not configured'}, 503

        try:
            url = f"https://api.openweathermap.org/data/2.5/weather"
            params = {
                'lat': location.latitude,
                'lon': location.longitude,
                'appid': api_key,
                'units': 'metric'  # Celsius
            }

            response = requests.get(url, params=params, timeout=5)

            if response.status_code == 200:
                data = response.json()

                # Extract relevant weather info
                weather_data = {
                    'temperature': data['main']['temp'],
                    'feels_like': data['main']['feels_like'],
                    'humidity': data['main']['humidity'],
                    'description': data['weather'][0]['description'],
                    'icon': data['weather'][0]['icon'],
                    'wind_speed': data['wind']['speed'],
                    'city': location.city
                }

                return jsonify(weather_data)
            else:
                return {'message': 'Failed to fetch weather data'}, response.status_code

        except requests.RequestException as e:
            return {'message': f'Weather API error: {str(e)}'}, 500


class RecommendationsAPI(Resource):
    """API for location-aware mood recommendations"""

    @token_required()
    def post(self):
        """
        Get recommendations based on mood and location

        Requires:
            - mood_score: int (0-100)
            - mood_category: str
            - mood_tags: list
        """
        current_user = g.current_user
        body = request.get_json()

        mood_score = body.get('mood_score')
        mood_category = body.get('mood_category')
        mood_tags = body.get('mood_tags', [])

        if mood_score is None:
            return {'message': 'mood_score is required'}, 400

        # Get user's location
        location = UserLocation.query.filter_by(_user_id=current_user.id)\
            .order_by(UserLocation._timestamp.desc()).first()

        # Get weather if location available
        weather_data = None
        if location and location.latitude and location.longitude:
            api_key = os.getenv('OPENWEATHER_API_KEY')
            if api_key:
                try:
                    url = f"https://api.openweathermap.org/data/2.5/weather"
                    params = {
                        'lat': location.latitude,
                        'lon': location.longitude,
                        'appid': api_key,
                        'units': 'metric'
                    }
                    response = requests.get(url, params=params, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        weather_data = {
                            'temp': data['main']['temp'],
                            'description': data['weather'][0]['description']
                        }
                except:
                    pass  # Continue without weather

        # Generate recommendations using selection and iteration (AP CSP requirement)
        recommendations = _generate_recommendations(
            mood_score, mood_category, mood_tags, location, weather_data
        )

        return jsonify(recommendations)


def _generate_recommendations(mood_score, mood_category, mood_tags, location, weather):
    """
    Generate location-aware recommendations

    Uses lists/arrays and iteration (AP CSP requirement)
    """
    from datetime import datetime

    # Get current time for time-based recommendations
    current_hour = datetime.now().hour

    # Initialize recommendation lists (AP CSP: Using lists/arrays)
    food_recommendations = []
    activity_recommendations = []
    music_recommendations = []

    # Selection based on mood score (AP CSP: Selection)
    if mood_score <= 40:
        # Low mood - comfort recommendations
        food_recommendations = [
            {'name': 'Comfort Food Bowl', 'type': 'comfort', 'reason': 'Warm and comforting'},
            {'name': 'Hot Chocolate', 'type': 'beverage', 'reason': 'Mood-boosting treat'},
            {'name': 'Soup & Bread', 'type': 'meal', 'reason': 'Soothing and easy'}
        ]
        activity_recommendations = [
            {'name': 'Light Walk', 'duration': 15, 'reason': 'Fresh air helps'},
            {'name': 'Journal Writing', 'duration': 20, 'reason': 'Process feelings'},
            {'name': 'Call a Friend', 'duration': 30, 'reason': 'Social support'}
        ]
        music_recommendations = [
            {'title': 'Calm Acoustic', 'genre': 'acoustic', 'mood': 'soothing'},
            {'title': 'Gentle Piano', 'genre': 'classical', 'mood': 'peaceful'}
        ]
    elif mood_score <= 60:
        # Medium mood - balanced recommendations
        food_recommendations = [
            {'name': 'Balanced Bowl', 'type': 'healthy', 'reason': 'Nutritious energy'},
            {'name': 'Smoothie', 'type': 'beverage', 'reason': 'Quick nutrition'},
            {'name': 'Salad & Protein', 'type': 'meal', 'reason': 'Light and satisfying'}
        ]
        activity_recommendations = [
            {'name': 'Yoga Session', 'duration': 30, 'reason': 'Mind-body balance'},
            {'name': 'Creative Activity', 'duration': 45, 'reason': 'Express yourself'},
            {'name': 'Nature Walk', 'duration': 30, 'reason': 'Peaceful exercise'}
        ]
        music_recommendations = [
            {'title': 'Lo-Fi Beats', 'genre': 'lofi', 'mood': 'focused'},
            {'title': 'Indie Chill', 'genre': 'indie', 'mood': 'relaxed'}
        ]
    else:
        # High mood - energetic recommendations
        food_recommendations = [
            {'name': 'Power Bowl', 'type': 'energizing', 'reason': 'Sustain your energy'},
            {'name': 'Fresh Juice', 'type': 'beverage', 'reason': 'Vitamin boost'},
            {'name': 'Protein Meal', 'type': 'meal', 'reason': 'Fuel for activity'}
        ]
        activity_recommendations = [
            {'name': 'Exercise', 'duration': 45, 'reason': 'Channel that energy'},
            {'name': 'Dance Party', 'duration': 30, 'reason': 'Fun movement'},
            {'name': 'Social Activity', 'duration': 60, 'reason': 'Share the vibes'}
        ]
        music_recommendations = [
            {'title': 'Upbeat Pop', 'genre': 'pop', 'mood': 'energetic'},
            {'title': 'Dance Hits', 'genre': 'electronic', 'mood': 'hyped'}
        ]

    # Weather-based adjustments (iteration through activities)
    if weather:
        temp = weather.get('temp', 20)
        description = weather.get('description', '').lower()

        # Iterate through activities and adjust based on weather (AP CSP: Iteration)
        for activity in activity_recommendations:
            if temp < 10:  # Cold weather
                if 'walk' in activity['name'].lower() or 'outdoor' in activity.get('type', '').lower():
                    activity['note'] = '⚠️ Bundle up! It\'s cold outside'
            elif temp > 30:  # Hot weather
                if 'exercise' in activity['name'].lower():
                    activity['note'] = '☀️ Stay hydrated! It\'s hot'

            if 'rain' in description:
                if 'outdoor' in activity.get('type', '').lower():
                    activity['alternative'] = 'Consider indoor option due to rain'

    # Time-based adjustments (selection)
    if current_hour < 11:
        # Morning
        for food in food_recommendations:
            food['meal_time'] = 'breakfast'
    elif current_hour < 15:
        # Afternoon
        for food in food_recommendations:
            food['meal_time'] = 'lunch'
    else:
        # Evening
        for food in food_recommendations:
            food['meal_time'] = 'dinner'

    # Add location info if available
    location_info = None
    if location:
        location_info = {
            'city': location.city,
            'region': location.region,
            'country': location.country
        }

    return {
        'food': food_recommendations,
        'activities': activity_recommendations,
        'music': music_recommendations,
        'location': location_info,
        'weather': weather,
        'mood_category': mood_category,
        'generated_at': datetime.now().isoformat()
    }


# Register API resources
api.add_resource(LocationAPI, '')
api.add_resource(LocationHistoryAPI, '/history')
api.add_resource(WeatherAPI, '/weather')
api.add_resource(RecommendationsAPI, '/recommendations')
