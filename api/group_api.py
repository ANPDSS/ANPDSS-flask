"""
Group API - Endpoints for group creation, membership, invites, and group messaging
"""

from flask import Blueprint, request, g
from flask_restful import Api, Resource
from api.jwt_authorize import token_required
from model.user import User
from model.friend import Friend
from model.group import Group, GroupMember, GroupInvite, GroupMessage, MAX_GROUP_MEMBERS

group_api = Blueprint('group_api', __name__, url_prefix='/api/group')
api = Api(group_api)


class GroupCreateAPI(Resource):
    @token_required()
    def post(self):
        """Create a new group. Creator is automatically added as a member."""
        current_user = g.current_user
        try:
            data = request.get_json()
            name = data.get('name', '').strip()

            if not name:
                return {'message': 'Group name is required'}, 400

            group = Group(name, current_user.id)
            result = group.create()
            if not result:
                return {'message': 'Failed to create group'}, 500

            # Add creator as member
            member = GroupMember(result.id, current_user.id)
            member.create()

            return result.read(), 201

        except ValueError as e:
            return {'message': str(e)}, 400
        except Exception as e:
            return {'message': f'Error creating group: {str(e)}'}, 500


class GroupListAPI(Resource):
    @token_required()
    def get(self):
        """Get all groups the current user is a member of"""
        current_user = g.current_user
        try:
            memberships = GroupMember.query.filter_by(_user_id=current_user.id).all()
            groups = []
            for m in memberships:
                group = Group.query.get(m.group_id)
                if group:
                    data = group.read()
                    data['is_creator'] = (group.creator_id == current_user.id)
                    groups.append(data)

            return {'groups': groups, 'count': len(groups)}

        except Exception as e:
            return {'message': f'Error getting groups: {str(e)}'}, 500


class GroupDetailAPI(Resource):
    @token_required()
    def get(self, group_id):
        """Get group details including all members"""
        current_user = g.current_user
        try:
            group = Group.query.get(group_id)
            if not group:
                return {'message': 'Group not found'}, 404

            if not group.is_member(current_user.id):
                return {'message': 'You are not a member of this group'}, 403

            members = GroupMember.query.filter_by(_group_id=group_id).all()
            members_data = [m.read() for m in members]

            data = group.read()
            data['members'] = members_data
            data['is_creator'] = (group.creator_id == current_user.id)

            return data

        except Exception as e:
            return {'message': f'Error getting group: {str(e)}'}, 500

    @token_required()
    def delete(self, group_id):
        """Delete a group (only creator can do this)"""
        current_user = g.current_user
        try:
            group = Group.query.get(group_id)
            if not group:
                return {'message': 'Group not found'}, 404

            if group.creator_id != current_user.id:
                return {'message': 'Only the group creator can delete the group'}, 403

            if group.delete():
                return {'message': 'Group deleted successfully'}, 200
            else:
                return {'message': 'Failed to delete group'}, 500

        except Exception as e:
            return {'message': f'Error deleting group: {str(e)}'}, 500


class GroupInviteAPI(Resource):
    @token_required()
    def post(self, group_id):
        """Invite a friend to a group (only friends can be invited, max 10 non-creator members)"""
        current_user = g.current_user
        try:
            group = Group.query.get(group_id)
            if not group:
                return {'message': 'Group not found'}, 404

            # Only current members can invite
            if not group.is_member(current_user.id):
                return {'message': 'You are not a member of this group'}, 403

            data = request.get_json()
            invitee_id = data.get('invitee_id')

            if not invitee_id:
                return {'message': 'Invitee ID is required'}, 400

            try:
                invitee_id = int(invitee_id)
            except (ValueError, TypeError):
                return {'message': 'Invalid invitee ID'}, 400

            # Verify invitee exists
            invitee = User.query.get(invitee_id)
            if not invitee:
                return {'message': 'User not found'}, 404

            # Only friends can be invited
            if not Friend.are_friends(current_user.id, invitee_id):
                return {'message': 'You can only invite friends to a group'}, 403

            # Check if already a member
            if group.is_member(invitee_id):
                return {'message': 'User is already a member of this group'}, 400

            # Check member limit (MAX_GROUP_MEMBERS non-creator members, so total = MAX_GROUP_MEMBERS + 1)
            # The total cap is MAX_GROUP_MEMBERS + 1 (creator counts too)
            current_count = group.member_count()
            if current_count >= MAX_GROUP_MEMBERS + 1:
                return {'message': f'Group is full (maximum {MAX_GROUP_MEMBERS + 1} members)'}, 400

            # Check if invite already pending
            if GroupInvite.has_pending_invite(group_id, invitee_id):
                return {'message': 'Invite already pending for this user'}, 400

            invite = GroupInvite(group_id, current_user.id, invitee_id)
            result = invite.create()
            if not result:
                return {'message': 'Failed to send invite'}, 500

            return result.read(), 201

        except Exception as e:
            return {'message': f'Error sending invite: {str(e)}'}, 500


class GroupInviteListAPI(Resource):
    @token_required()
    def get(self):
        """Get pending group invites for the current user"""
        current_user = g.current_user
        try:
            invites = GroupInvite.get_pending_invites_for_user(current_user.id)
            return {
                'invites': [inv.read() for inv in invites],
                'count': len(invites)
            }
        except Exception as e:
            return {'message': f'Error getting invites: {str(e)}'}, 500


class GroupInviteActionAPI(Resource):
    @token_required()
    def put(self, invite_id):
        """Accept or decline a group invite"""
        current_user = g.current_user
        try:
            invite = GroupInvite.query.get(invite_id)
            if not invite:
                return {'message': 'Invite not found'}, 404

            if invite.invitee_id != current_user.id:
                return {'message': 'Unauthorized'}, 403

            if invite.status != 'pending':
                return {'message': 'Invite already processed'}, 400

            data = request.get_json()
            action = data.get('action')  # 'accept' or 'decline'

            if action not in ['accept', 'decline']:
                return {'message': 'Invalid action. Use "accept" or "decline"'}, 400

            if action == 'accept':
                group = Group.query.get(invite.group_id)
                if not group:
                    return {'message': 'Group no longer exists'}, 404

                # Re-check member limit at accept time
                if group.member_count() >= MAX_GROUP_MEMBERS + 1:
                    return {'message': f'Group is now full'}, 400

                member = GroupMember(invite.group_id, current_user.id)
                if not member.create():
                    return {'message': 'Failed to join group'}, 500

                invite.status = 'accepted'
                invite.update()

                return {'message': 'Joined group successfully', 'group': group.read()}, 200

            else:  # decline
                invite.status = 'declined'
                invite.update()
                return {'message': 'Invite declined'}, 200

        except Exception as e:
            return {'message': f'Error processing invite: {str(e)}'}, 500


class GroupLeaveAPI(Resource):
    @token_required()
    def delete(self, group_id):
        """Leave a group. Creator cannot leave (must delete instead)."""
        current_user = g.current_user
        try:
            group = Group.query.get(group_id)
            if not group:
                return {'message': 'Group not found'}, 404

            if group.creator_id == current_user.id:
                return {'message': 'As the creator, you cannot leave. Delete the group instead.'}, 400

            membership = GroupMember.query.filter_by(
                _group_id=group_id, _user_id=current_user.id
            ).first()

            if not membership:
                return {'message': 'You are not a member of this group'}, 400

            if membership.delete():
                return {'message': 'Left group successfully'}, 200
            else:
                return {'message': 'Failed to leave group'}, 500

        except Exception as e:
            return {'message': f'Error leaving group: {str(e)}'}, 500


class GroupRemoveMemberAPI(Resource):
    @token_required()
    def delete(self, group_id, member_id):
        """Remove a member from a group (only creator can do this)"""
        current_user = g.current_user
        try:
            group = Group.query.get(group_id)
            if not group:
                return {'message': 'Group not found'}, 404

            if group.creator_id != current_user.id:
                return {'message': 'Only the group creator can remove members'}, 403

            if member_id == current_user.id:
                return {'message': 'Cannot remove yourself. Delete the group instead.'}, 400

            membership = GroupMember.query.filter_by(
                _group_id=group_id, _user_id=member_id
            ).first()

            if not membership:
                return {'message': 'User is not a member of this group'}, 404

            if membership.delete():
                return {'message': 'Member removed successfully'}, 200
            else:
                return {'message': 'Failed to remove member'}, 500

        except Exception as e:
            return {'message': f'Error removing member: {str(e)}'}, 500


class GroupMessageAPI(Resource):
    @token_required()
    def post(self, group_id):
        """Send a message to a group (text, photo, or both)"""
        current_user = g.current_user
        try:
            group = Group.query.get(group_id)
            if not group:
                return {'message': 'Group not found'}, 404

            if not group.is_member(current_user.id):
                return {'message': 'You are not a member of this group'}, 403

            data = request.get_json()
            content = data.get('content', '').strip()
            image_data = data.get('image_data')      # base64 webcam photo
            mood_snapshot = data.get('mood_snapshot')  # JSON string with mood info

            if not content and not image_data:
                return {'message': 'Message must have text or a photo'}, 400

            message = GroupMessage(group_id, current_user.id, content,
                                   image_data=image_data, mood_snapshot=mood_snapshot)
            result = message.create()
            if not result:
                return {'message': 'Failed to send message'}, 500

            return result.read(), 201

        except ValueError as e:
            return {'message': str(e)}, 400
        except Exception as e:
            return {'message': f'Error sending message: {str(e)}'}, 500

    @token_required()
    def get(self, group_id):
        """Get messages from a group"""
        current_user = g.current_user
        try:
            group = Group.query.get(group_id)
            if not group:
                return {'message': 'Group not found'}, 404

            if not group.is_member(current_user.id):
                return {'message': 'You are not a member of this group'}, 403

            limit = request.args.get('limit', 50, type=int)
            messages = GroupMessage.get_messages(group_id, limit)
            messages_data = [msg.read() for msg in reversed(messages)]

            return {
                'group_id': group_id,
                'group_name': group.name,
                'messages': messages_data,
                'count': len(messages_data)
            }

        except Exception as e:
            return {'message': f'Error getting messages: {str(e)}'}, 500


# Register API Resources
api.add_resource(GroupCreateAPI, '/create')
api.add_resource(GroupListAPI, '/list')
api.add_resource(GroupDetailAPI, '/<int:group_id>')
api.add_resource(GroupInviteAPI, '/<int:group_id>/invite')
api.add_resource(GroupInviteListAPI, '/invites')
api.add_resource(GroupInviteActionAPI, '/invite/<int:invite_id>')
api.add_resource(GroupLeaveAPI, '/<int:group_id>/leave')
api.add_resource(GroupRemoveMemberAPI, '/<int:group_id>/member/<int:member_id>')
api.add_resource(GroupMessageAPI, '/<int:group_id>/messages')
