"""
Friend API - Endpoints for friend management, recommendations, and search
"""

from flask import Blueprint, request, g
from flask_restful import Api, Resource
from api.jwt_authorize import token_required
from model.user import User
from model.friend import Friend, FriendRequest
from model.moodmeal_preferences import MoodMealPreferences
from model.moodmeal_mood import MoodMealMood
from __init__ import db

friend_api = Blueprint('friend_api', __name__, url_prefix='/api/friend')
api = Api(friend_api)


class FriendRecommendationAlgorithm:
    """
    Advanced friend recommendation algorithm based on similar mood patterns
    and shared preferences (music, activities, cuisines)
    """

    @staticmethod
    def calculate_list_overlap(list1, list2):
        """Calculate overlap between two lists as a ratio (0-1)"""
        if not list1 or not list2:
            return 0.0
        set1, set2 = set(list1), set(list2)
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union > 0 else 0.0

    @staticmethod
    def calculate_similarity_score(user_moods, other_moods, user_prefs, other_prefs):
        """
        Calculate similarity score between two users based on mood patterns and preferences

        Algorithm weights:
        - Mood score similarity: 25%
        - Mood category overlap: 15%
        - Music preferences overlap: 20%
        - Activities overlap: 20%
        - Cuisines overlap: 20%
        """
        scores = {}

        # Mood-based scoring (40% total)
        if user_moods and other_moods:
            # Average mood score similarity
            user_avg_score = sum([m.mood_score for m in user_moods]) / len(user_moods)
            other_avg_score = sum([m.mood_score for m in other_moods]) / len(other_moods)
            score_diff = abs(user_avg_score - other_avg_score)
            scores['mood_score'] = max(0, 1 - (score_diff / 100))

            # Mood category overlap
            user_categories = set([m.mood_category for m in user_moods if m.mood_category])
            other_categories = set([m.mood_category for m in other_moods if m.mood_category])
            if user_categories and other_categories:
                scores['mood_category'] = len(user_categories.intersection(other_categories)) / len(user_categories.union(other_categories))
            else:
                scores['mood_category'] = 0.0
        else:
            scores['mood_score'] = 0.0
            scores['mood_category'] = 0.0

        # Preferences-based scoring (60% total)
        if user_prefs and other_prefs:
            scores['music'] = FriendRecommendationAlgorithm.calculate_list_overlap(
                user_prefs.music, other_prefs.music
            )
            scores['activities'] = FriendRecommendationAlgorithm.calculate_list_overlap(
                user_prefs.activities, other_prefs.activities
            )
            scores['cuisines'] = FriendRecommendationAlgorithm.calculate_list_overlap(
                user_prefs.cuisines, other_prefs.cuisines
            )
        else:
            scores['music'] = 0.0
            scores['activities'] = 0.0
            scores['cuisines'] = 0.0

        # Weighted final score
        final_score = (
            scores['mood_score'] * 0.25 +
            scores['mood_category'] * 0.15 +
            scores['music'] * 0.20 +
            scores['activities'] * 0.20 +
            scores['cuisines'] * 0.20
        )

        return final_score, scores

    @staticmethod
    def get_recommendations(user_id, limit=10):
        """
        Get friend recommendations for a user based on mood similarity and shared preferences

        Algorithm:
        1. Get user's recent moods (last 30 entries) and preferences
        2. Find all users with mood data or preferences
        3. Exclude existing friends and pending requests
        4. Calculate combined similarity scores
        5. Return top matches sorted by score with detailed compatibility info
        """
        # Get current user's data
        user_moods = MoodMealMood.query.filter_by(_user_id=user_id).order_by(MoodMealMood._timestamp.desc()).limit(30).all()
        user_prefs = MoodMealPreferences.query.filter_by(_user_id=user_id).first()

        # Get existing friends to exclude
        friend_ids = Friend.get_friends_for_user(user_id)

        # Get pending requests (both sent and received) to exclude
        sent_requests = FriendRequest.get_sent_requests_for_user(user_id)
        received_requests = FriendRequest.get_pending_requests_for_user(user_id)

        excluded_ids = set(friend_ids)
        excluded_ids.add(user_id)  # Exclude self

        for req in sent_requests:
            if req.status == 'pending':
                excluded_ids.add(req.receiver_id)

        for req in received_requests:
            excluded_ids.add(req.sender_id)

        # Get all users with mood data OR preferences
        mood_user_ids = set([uid[0] for uid in db.session.query(MoodMealMood._user_id).distinct().all()])
        pref_user_ids = set([uid[0] for uid in db.session.query(MoodMealPreferences._user_id).distinct().all()])
        all_user_ids = mood_user_ids.union(pref_user_ids)
        all_user_ids = [uid for uid in all_user_ids if uid not in excluded_ids]

        # If user has no data, return users who do have data
        if not user_moods and not user_prefs:
            users = User.query.filter(User.id.in_(all_user_ids)).limit(limit).all()
            return [{
                'user': user,
                'score': 0.0,
                'shared_mood_categories': [],
                'avg_mood_score': None,
                'shared_music': [],
                'shared_activities': [],
                'shared_cuisines': []
            } for user in users]

        # Calculate similarity scores
        recommendations = []
        for other_user_id in all_user_ids:
            # Get other user's data
            other_moods = MoodMealMood.query.filter_by(_user_id=other_user_id).order_by(MoodMealMood._timestamp.desc()).limit(30).all()
            other_prefs = MoodMealPreferences.query.filter_by(_user_id=other_user_id).first()

            # Skip if other user has no data at all
            if not other_moods and not other_prefs:
                continue

            score, score_breakdown = FriendRecommendationAlgorithm.calculate_similarity_score(
                user_moods, other_moods, user_prefs, other_prefs
            )

            # Include users with any similarity
            if score > 0:
                user = User.query.get(other_user_id)
                if user:
                    # Calculate shared mood categories
                    shared_categories = []
                    other_avg_mood = None
                    if user_moods and other_moods:
                        user_categories = set([m.mood_category for m in user_moods if m.mood_category])
                        other_categories = set([m.mood_category for m in other_moods if m.mood_category])
                        shared_categories = list(user_categories.intersection(other_categories))
                        other_avg_mood = round(sum([m.mood_score for m in other_moods]) / len(other_moods), 1)

                    # Calculate shared preferences
                    shared_music = []
                    shared_activities = []
                    shared_cuisines = []
                    if user_prefs and other_prefs:
                        shared_music = list(set(user_prefs.music or []).intersection(set(other_prefs.music or [])))
                        shared_activities = list(set(user_prefs.activities or []).intersection(set(other_prefs.activities or [])))
                        shared_cuisines = list(set(user_prefs.cuisines or []).intersection(set(other_prefs.cuisines or [])))

                    recommendations.append({
                        'user': user,
                        'score': score,
                        'score_breakdown': score_breakdown,
                        'shared_mood_categories': shared_categories,
                        'avg_mood_score': other_avg_mood,
                        'shared_music': shared_music[:5],  # Limit to top 5
                        'shared_activities': shared_activities[:5],
                        'shared_cuisines': shared_cuisines[:5]
                    })

        # Sort by score (highest first)
        recommendations.sort(key=lambda x: x['score'], reverse=True)

        # Return top matches
        return recommendations[:limit]


class FriendRecommendationsAPI(Resource):
    @token_required()
    def get(self):
        """Get friend recommendations for current user based on mood and preference similarity"""
        current_user = g.current_user
        try:
            limit = request.args.get('limit', 10, type=int)
            recommendations = FriendRecommendationAlgorithm.get_recommendations(
                current_user.id, limit
            )

            result = []
            for rec in recommendations:
                user_data = {
                    'id': rec['user'].id,
                    'uid': rec['user']._uid,
                    'name': rec['user']._name,
                    'email': rec['user']._email,
                    'school': rec['user']._school,
                    'similarity_score': round(rec['score'] * 100, 1),  # Convert to percentage
                    'mood_compatibility': {
                        'shared_mood_categories': rec['shared_mood_categories'],
                        'avg_mood_score': rec['avg_mood_score']
                    },
                    'shared_interests': {
                        'music': rec.get('shared_music', []),
                        'activities': rec.get('shared_activities', []),
                        'cuisines': rec.get('shared_cuisines', [])
                    }
                }
                result.append(user_data)

            return {
                'recommendations': result,
                'count': len(result)
            }

        except Exception as e:
            return {'message': f'Error getting recommendations: {str(e)}'}, 500


class FriendSearchAPI(Resource):
    @token_required()
    def get(self):
        """Search for users by username, name, or school"""
        current_user = g.current_user
        try:
            query = request.args.get('q', '').strip()

            if not query or len(query) < 2:
                return {'message': 'Search query must be at least 2 characters'}, 400

            # Search in username, name, and school
            users = User.query.filter(
                (User._uid.ilike(f'%{query}%')) |
                (User._name.ilike(f'%{query}%')) |
                (User._school.ilike(f'%{query}%'))
            ).filter(User.id != current_user.id).limit(20).all()

            # Get friend status for each user
            result = []
            friend_ids = Friend.get_friends_for_user(current_user.id)

            for user in users:
                # Check friendship status
                is_friend = user.id in friend_ids

                # Check pending requests
                has_pending = FriendRequest.has_pending_request(current_user.id, user.id)

                user_data = {
                    'id': user.id,
                    'uid': user._uid,
                    'name': user._name,
                    'email': user._email,
                    'school': user._school,
                    'is_friend': is_friend,
                    'has_pending_request': has_pending
                }
                result.append(user_data)

            return {
                'users': result,
                'count': len(result),
                'query': query
            }

        except Exception as e:
            return {'message': f'Error searching users: {str(e)}'}, 500


class FriendRequestAPI(Resource):
    @token_required()
    def post(self):
        """Send a friend request"""
        current_user = g.current_user
        try:
            data = request.get_json()
            receiver_id = data.get('receiver_id')

            if not receiver_id:
                return {'message': 'Receiver ID is required'}, 400

            # Convert receiver_id to integer
            try:
                receiver_id = int(receiver_id)
            except (ValueError, TypeError):
                return {'message': 'Invalid receiver ID'}, 400

            # Check if receiver exists
            receiver = User.query.get(receiver_id)
            if not receiver:
                return {'message': 'User not found'}, 404

            # Check if already friends
            if Friend.are_friends(current_user.id, receiver_id):
                return {'message': 'Already friends with this user'}, 400

            # Check if request already exists
            if FriendRequest.has_pending_request(current_user.id, receiver_id):
                return {'message': 'Friend request already pending'}, 400

            # Create friend request
            friend_request = FriendRequest(current_user.id, receiver_id)
            result = friend_request.create()

            if not result:
                return {'message': 'Failed to create friend request'}, 500

            return result.read(), 201

        except ValueError as e:
            return {'message': str(e)}, 400
        except Exception as e:
            return {'message': f'Error sending friend request: {str(e)}'}, 500

    @token_required()
    def get(self):
        """Get friend requests (sent and received)"""
        current_user = g.current_user
        try:
            # Get received requests
            received = FriendRequest.get_pending_requests_for_user(current_user.id)
            received_data = [req.read() for req in received]

            # Get sent requests
            sent = FriendRequest.get_sent_requests_for_user(current_user.id)
            sent_data = [req.read() for req in sent]

            return {
                'received': received_data,
                'sent': sent_data
            }

        except Exception as e:
            return {'message': f'Error getting friend requests: {str(e)}'}, 500


class FriendRequestActionAPI(Resource):
    @token_required()
    def put(self, request_id):
        """Accept or reject a friend request"""
        current_user = g.current_user
        try:
            # Ensure request_id is an integer
            try:
                request_id = int(request_id)
            except (ValueError, TypeError):
                return {'message': 'Invalid request ID'}, 400

            data = request.get_json()
            action = data.get('action')  # 'accept' or 'reject'

            if action not in ['accept', 'reject']:
                return {'message': 'Invalid action. Use "accept" or "reject"'}, 400

            # Get the friend request
            friend_request = FriendRequest.query.get(request_id)

            if not friend_request:
                return {'message': 'Friend request not found'}, 404

            # Verify current user is the receiver
            if friend_request.receiver_id != current_user.id:
                return {'message': 'Unauthorized'}, 403

            # Verify request is still pending
            if friend_request.status != 'pending':
                return {'message': 'Friend request already processed'}, 400

            if action == 'accept':
                # Create friendship
                friendship = Friend(friend_request.sender_id, friend_request.receiver_id)
                if not friendship.create():
                    return {'message': 'Failed to create friendship'}, 500

                # Update request status
                friend_request.status = 'accepted'
                friend_request.update()

                return {
                    'message': 'Friend request accepted',
                    'friendship': friendship.read()
                }, 200

            else:  # reject
                friend_request.status = 'rejected'
                friend_request.update()

                return {
                    'message': 'Friend request rejected'
                }, 200

        except Exception as e:
            return {'message': f'Error processing friend request: {str(e)}'}, 500

    @token_required()
    def delete(self, request_id):
        """Cancel a sent friend request"""
        current_user = g.current_user
        try:
            # Ensure request_id is an integer
            try:
                request_id = int(request_id)
            except (ValueError, TypeError):
                return {'message': 'Invalid request ID'}, 400

            friend_request = FriendRequest.query.get(request_id)

            if not friend_request:
                return {'message': 'Friend request not found'}, 404

            # Verify current user is the sender
            if friend_request.sender_id != current_user.id:
                return {'message': 'Unauthorized'}, 403

            if friend_request.delete():
                return {'message': 'Friend request cancelled'}, 200
            else:
                return {'message': 'Failed to cancel friend request'}, 500

        except Exception as e:
            return {'message': f'Error cancelling friend request: {str(e)}'}, 500


class FriendsListAPI(Resource):
    @token_required()
    def get(self):
        """Get list of current user's friends"""
        current_user = g.current_user
        try:
            friend_ids = Friend.get_friends_for_user(current_user.id)

            friends = []
            for friend_id in friend_ids:
                user = User.query.get(friend_id)
                if user:
                    friends.append({
                        'id': user.id,
                        'uid': user._uid,
                        'name': user._name,
                        'email': user._email,
                        'school': user._school
                    })

            return {
                'friends': friends,
                'count': len(friends)
            }

        except Exception as e:
            return {'message': f'Error getting friends list: {str(e)}'}, 500


class UnfriendAPI(Resource):
    @token_required()
    def delete(self, friend_id):
        """Remove a friend"""
        current_user = g.current_user
        try:
            # Ensure friend_id is an integer
            try:
                friend_id = int(friend_id)
            except (ValueError, TypeError):
                return {'message': 'Invalid friend ID'}, 400

            # Verify friend exists
            friend = User.query.get(friend_id)
            if not friend:
                return {'message': 'User not found'}, 404

            # Verify they are friends
            if not Friend.are_friends(current_user.id, friend_id):
                return {'message': 'Not friends with this user'}, 400

            # Get the friendship record
            min_id, max_id = min(current_user.id, friend_id), max(current_user.id, friend_id)
            friendship = Friend.query.filter_by(_user_id1=min_id, _user_id2=max_id).first()

            if friendship and friendship.delete():
                return {'message': 'Friend removed successfully'}, 200
            else:
                return {'message': 'Failed to remove friend'}, 500

        except Exception as e:
            return {'message': f'Error removing friend: {str(e)}'}, 500


# Register API Resources
api.add_resource(FriendRecommendationsAPI, '/recommendations')
api.add_resource(FriendSearchAPI, '/search')
api.add_resource(FriendRequestAPI, '/request')
api.add_resource(FriendRequestActionAPI, '/request/<int:request_id>')
api.add_resource(FriendsListAPI, '/list')
api.add_resource(UnfriendAPI, '/unfriend/<int:friend_id>')
