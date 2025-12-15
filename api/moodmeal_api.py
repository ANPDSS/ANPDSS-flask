"""
MoodMeal API
Handles API requests for user preferences and mood data
"""
from flask import Blueprint, request, jsonify, g
from flask_restful import Api, Resource
from api.jwt_authorize import token_required
from model.moodmeal_preferences import MoodMealPreferences
from model.moodmeal_mood import MoodMealMood
from model.user import User
import os
import requests

moodmeal_api = Blueprint('moodmeal_api', __name__, url_prefix='/api/moodmeal')
api = Api(moodmeal_api)

class PreferencesAPI(Resource):
    """API for managing user preferences"""

    @token_required()
    def get(self):
        """Get user preferences"""
        current_user = g.current_user
        preferences = MoodMealPreferences.query.filter_by(_user_id=current_user.id).first()

        if not preferences:
            # Return default empty preferences if none exist
            return jsonify({
                'user_id': current_user.id,
                'dietary': [],
                'allergies': [],
                'cuisines': [],
                'music': [],
                'activities': []
            })

        return jsonify(preferences.read())

    @token_required()
    def post(self):
        """Create or update user preferences"""
        current_user = g.current_user
        body = request.get_json()

        # Check if preferences already exist
        preferences = MoodMealPreferences.query.filter_by(_user_id=current_user.id).first()

        if preferences:
            # Update existing preferences
            preferences.update(body)
            return jsonify(preferences.read())
        else:
            # Create new preferences
            new_preferences = MoodMealPreferences(
                user_id=current_user.id,
                dietary=body.get('dietary', []),
                allergies=body.get('allergies', []),
                cuisines=body.get('cuisines', []),
                music=body.get('music', []),
                activities=body.get('activities', [])
            )

            result = new_preferences.create()
            if result:
                return jsonify(result.read()), 201
            else:
                return {'message': 'Failed to create preferences'}, 500

    @token_required()
    def delete(self):
        """Delete user preferences"""
        current_user = g.current_user
        preferences = MoodMealPreferences.query.filter_by(_user_id=current_user.id).first()

        if not preferences:
            return {'message': 'Preferences not found'}, 404

        if preferences.delete():
            return {'message': 'Preferences deleted successfully'}, 200
        else:
            return {'message': 'Failed to delete preferences'}, 500


class MoodAPI(Resource):
    """API for managing mood entries"""

    @token_required()
    def get(self):
        """Get user mood history"""
        current_user = g.current_user

        # Get optional query parameters
        limit = request.args.get('limit', type=int)

        # Query mood entries for the user
        query = MoodMealMood.query.filter_by(_user_id=current_user.id).order_by(MoodMealMood._timestamp.desc())

        if limit:
            query = query.limit(limit)

        moods = query.all()

        return jsonify([mood.read() for mood in moods])

    @token_required()
    def post(self):
        """Create a new mood entry"""
        current_user = g.current_user
        body = request.get_json()

        # Validate required fields
        if 'mood_score' not in body:
            return {'message': 'mood_score is required'}, 400

        mood_score = body.get('mood_score')
        if not isinstance(mood_score, int) or mood_score < 0 or mood_score > 100:
            return {'message': 'mood_score must be an integer between 0 and 100'}, 400

        # Create new mood entry
        new_mood = MoodMealMood(
            user_id=current_user.id,
            mood_score=mood_score,
            mood_tags=body.get('mood_tags', []),
            mood_category=body.get('mood_category'),
            timestamp=body.get('timestamp')
        )

        result = new_mood.create()
        if result:
            return jsonify(result.read()), 201
        else:
            return {'message': 'Failed to create mood entry'}, 500


class MoodByIdAPI(Resource):
    """API for managing individual mood entries"""

    @token_required()
    def get(self, mood_id):
        """Get a specific mood entry"""
        current_user = g.current_user
        mood = MoodMealMood.query.filter_by(id=mood_id, _user_id=current_user.id).first()

        if not mood:
            return {'message': 'Mood entry not found'}, 404

        return jsonify(mood.read())

    @token_required()
    def put(self, mood_id):
        """Update a specific mood entry"""
        current_user = g.current_user
        mood = MoodMealMood.query.filter_by(id=mood_id, _user_id=current_user.id).first()

        if not mood:
            return {'message': 'Mood entry not found'}, 404

        body = request.get_json()
        result = mood.update(body)

        if result:
            return jsonify(result.read())
        else:
            return {'message': 'Failed to update mood entry'}, 500

    @token_required()
    def delete(self, mood_id):
        """Delete a specific mood entry"""
        current_user = g.current_user
        mood = MoodMealMood.query.filter_by(id=mood_id, _user_id=current_user.id).first()

        if not mood:
            return {'message': 'Mood entry not found'}, 404

        if mood.delete():
            return {'message': 'Mood entry deleted successfully'}, 200
        else:
            return {'message': 'Failed to delete mood entry'}, 500


class MoodStatsAPI(Resource):
    """API for mood statistics"""

    @token_required()
    def get(self):
        """Get mood statistics for the user"""
        current_user = g.current_user

        # Get all mood entries for the user
        moods = MoodMealMood.query.filter_by(_user_id=current_user.id).all()

        if not moods:
            return jsonify({
                'total_entries': 0,
                'average_mood': None,
                'most_common_category': None,
                'most_common_tags': []
            })

        # Calculate statistics
        total_entries = len(moods)
        average_mood = sum(mood.mood_score for mood in moods) / total_entries

        # Most common category
        categories = {}
        for mood in moods:
            cat = mood.mood_category
            categories[cat] = categories.get(cat, 0) + 1
        most_common_category = max(categories, key=categories.get) if categories else None

        # Most common tags
        tag_counts = {}
        for mood in moods:
            for tag in mood.mood_tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        most_common_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return jsonify({
            'total_entries': total_entries,
            'average_mood': round(average_mood, 2),
            'most_common_category': most_common_category,
            'most_common_tags': [{'tag': tag, 'count': count} for tag, count in most_common_tags]
        })


# Register API resources
api.add_resource(PreferencesAPI, '/preferences')
api.add_resource(MoodAPI, '/mood')
api.add_resource(MoodByIdAPI, '/mood/<int:mood_id>')
api.add_resource(MoodStatsAPI, '/mood/stats')
