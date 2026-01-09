"""
Message API - Endpoints for private messaging between friends
"""

from flask import Blueprint, request, g
from flask_restful import Api, Resource
from api.jwt_authorize import token_required
from model.user import User
from model.friend import Friend
from model.private_message import PrivateMessage

message_api = Blueprint('message_api', __name__, url_prefix='/api/message')
api = Api(message_api)


class SendMessageAPI(Resource):
    @token_required()
    def post(self):
        """Send a private message to a friend"""
        current_user = g.current_user
        try:
            data = request.get_json()
            receiver_id = data.get('receiver_id')
            content = data.get('content', '').strip()

            if not receiver_id:
                return {'message': 'Receiver ID is required'}, 400

            # Convert receiver_id to integer
            try:
                receiver_id = int(receiver_id)
            except (ValueError, TypeError):
                return {'message': 'Invalid receiver ID'}, 400

            if not content:
                return {'message': 'Message content cannot be empty'}, 400

            # Verify receiver exists
            receiver = User.query.get(receiver_id)
            if not receiver:
                return {'message': 'User not found'}, 404

            # Verify they are friends
            if not Friend.are_friends(current_user.id, receiver_id):
                return {'message': 'You can only message friends'}, 403

            # Create message
            message = PrivateMessage(current_user.id, receiver_id, content)
            result = message.create()

            if not result:
                return {'message': 'Failed to send message'}, 500

            return result.read(), 201

        except ValueError as e:
            return {'message': str(e)}, 400
        except Exception as e:
            return {'message': f'Error sending message: {str(e)}'}, 500


class ConversationAPI(Resource):
    @token_required()
    def get(self, friend_id):
        """Get conversation with a specific friend"""
        current_user = g.current_user
        try:
            # Ensure friend_id is an integer (URL parameters are strings)
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
                return {'message': 'You can only view conversations with friends'}, 403

            # Get conversation
            limit = request.args.get('limit', 50, type=int)
            messages = PrivateMessage.get_conversation(current_user.id, friend_id, limit)

            # Mark messages as read
            PrivateMessage.mark_conversation_as_read(current_user.id, friend_id)

            # Convert to dict and reverse (oldest first)
            messages_data = [msg.read() for msg in reversed(messages)]

            return {
                'conversation_with': {
                    'id': friend.id,
                    'uid': friend._uid,
                    'name': friend._name
                },
                'messages': messages_data,
                'count': len(messages_data)
            }

        except Exception as e:
            return {'message': f'Error getting conversation: {str(e)}'}, 500


class ConversationsListAPI(Resource):
    @token_required()
    def get(self):
        """Get all conversations for current user"""
        current_user = g.current_user
        try:
            # Conversations are already sorted by the model method
            conversations = PrivateMessage.get_conversations_for_user(current_user.id)

            return {
                'conversations': conversations,
                'count': len(conversations)
            }

        except Exception as e:
            return {'message': f'Error getting conversations: {str(e)}'}, 500


class UnreadCountAPI(Resource):
    @token_required()
    def get(self):
        """Get unread message count for current user"""
        current_user = g.current_user
        try:
            count = PrivateMessage.get_unread_count(current_user.id)

            return {
                'unread_count': count
            }

        except Exception as e:
            return {'message': f'Error getting unread count: {str(e)}'}, 500


class DeleteMessageAPI(Resource):
    @token_required()
    def delete(self, message_id):
        """Delete a message (only sender can delete)"""
        current_user = g.current_user
        try:
            # Ensure message_id is an integer
            try:
                message_id = int(message_id)
            except (ValueError, TypeError):
                return {'message': 'Invalid message ID'}, 400

            message = PrivateMessage.query.get(message_id)

            if not message:
                return {'message': 'Message not found'}, 404

            # Verify current user is the sender
            if message.sender_id != current_user.id:
                return {'message': 'You can only delete your own messages'}, 403

            if message.delete():
                return {'message': 'Message deleted successfully'}, 200
            else:
                return {'message': 'Failed to delete message'}, 500

        except Exception as e:
            return {'message': f'Error deleting message: {str(e)}'}, 500


# Register API Resources
api.add_resource(SendMessageAPI, '/send')
api.add_resource(ConversationAPI, '/conversation/<int:friend_id>')
api.add_resource(ConversationsListAPI, '/conversations')
api.add_resource(UnreadCountAPI, '/unread')
api.add_resource(DeleteMessageAPI, '/delete/<int:message_id>')
