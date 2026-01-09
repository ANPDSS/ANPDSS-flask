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
    """

    @staticmethod
    def calculate_similarity_score(user_moods, other_moods):
        """
        Calculate similarity score between two users based on their mood patterns

        Algorithm:
        - Compare average mood scores (60% weight)
        - Compare mood categories overlap (40% weight)
        """
        if not user_moods or not other_moods:
            return 0.0

        # Calculate average mood scores
        user_avg_score = sum([m.mood_score for m in user_moods]) / len(user_moods)
        other_avg_score = sum([m.mood_score for m in other_moods]) / len(other_moods)

        # Calculate mood score similarity (closer scores = higher similarity)
        score_diff = abs(user_avg_score - other_avg_score)
        score_similarity = max(0, 1 - (score_diff / 100))  # Normalize to 0-1

        # Calculate mood category overlap
        user_categories = set([m.mood_category for m in user_moods if m.mood_category])
        other_categories = set([m.mood_category for m in other_moods if m.mood_category])

        if user_categories and other_categories:
            category_overlap = len(user_categories.intersection(other_categories)) / len(user_categories.union(other_categories))
        else:
            category_overlap = 0.0

        # Weighted final score: 60% score similarity, 40% category overlap
        final_score = (score_similarity * 0.6) + (category_overlap * 0.4)

        return final_score

    @staticmethod
    def get_recommendations(user_id, limit=10):
        """
        Get friend recommendations for a user based on mood similarity

        Algorithm:
        1. Get user's recent moods (last 30 entries)
        2. Find all users with mood data
        3. Exclude existing friends and pending requests
        4. Calculate mood similarity scores
        5. Return top matches sorted by score
        """
        from datetime import datetime, timedelta

        # Get current user's recent moods (last 30 entries)
        user_moods = MoodMealMood.query.filter_by(_user_id=user_id).order_by(MoodMealMood._timestamp.desc()).limit(30).all()

        if not user_moods:
            # User has no mood data, return random active users
            users = User.query.filter(User.id != user_id).limit(limit).all()
            return [{
                'user': user,
                'score': 0.0,
                'shared_mood_categories': [],
                'avg_mood_score': None
            } for user in users]

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

        # Get all users with mood data
        all_user_ids = db.session.query(MoodMealMood._user_id).distinct().all()
        all_user_ids = [uid[0] for uid in all_user_ids if uid[0] not in excluded_ids]

        # Calculate similarity scores
        recommendations = []
        for other_user_id in all_user_ids:
            # Get other user's recent moods
            other_moods = MoodMealMood.query.filter_by(_user_id=other_user_id).order_by(MoodMealMood._timestamp.desc()).limit(30).all()

            if not other_moods:
                continue

            score = FriendRecommendationAlgorithm.calculate_similarity_score(
                user_moods, other_moods
            )

            if score > 0:  # Only include users with some similarity
                user = User.query.get(other_user_id)
                if user:
                    # Calculate shared mood categories
                    user_categories = set([m.mood_category for m in user_moods if m.mood_category])
                    other_categories = set([m.mood_category for m in other_moods if m.mood_category])
                    shared_categories = list(user_categories.intersection(other_categories))

                    # Calculate other user's average mood
                    other_avg_mood = sum([m.mood_score for m in other_moods]) / len(other_moods)

                    recommendations.append({
                        'user': user,
                        'score': score,
                        'shared_mood_categories': shared_categories,
                        'avg_mood_score': round(other_avg_mood, 1)
                    })

        # Sort by score (highest first)
        recommendations.sort(key=lambda x: x['score'], reverse=True)

        # Return top matches
        return recommendations[:limit]


class FriendRecommendationsAPI(Resource):
    @token_required()
    def get(self):
        """Get friend recommendations for current user based on mood similarity"""
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
