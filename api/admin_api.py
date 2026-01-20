"""
Admin API for Mood Meal Dashboard

This module provides endpoints for the Mood Meal admin dashboard:
- /api/admin/check - Verify if current user is a mood meal admin
- /api/admin/users - Get all users with their admin status
- /api/admin/make-admin - Grant or revoke mood meal admin privileges
"""

import os
import json
from flask import Blueprint, request, jsonify, g, current_app
from flask_restful import Api, Resource
from api.jwt_authorize import token_required
from model.user import User

admin_api = Blueprint('admin_api', __name__, url_prefix='/api/admin')
api = Api(admin_api)

# Superadmin UID - this user always has admin access and can grant admin to others
SUPERADMIN_UID = "Shayanb1"

def get_admins_file_path():
    """Get the path to the mood meal admins JSON file."""
    volumes_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'volumes')
    if not os.path.exists(volumes_dir):
        os.makedirs(volumes_dir)
    return os.path.join(volumes_dir, 'moodmeal_admins.json')

def load_moodmeal_admins():
    """Load the list of mood meal admin UIDs from file."""
    filepath = get_admins_file_path()
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                return set(data.get('admins', []))
        except (json.JSONDecodeError, IOError):
            pass
    # Default: superadmin is always an admin
    return {SUPERADMIN_UID}

def save_moodmeal_admins(admins_set):
    """Save the list of mood meal admin UIDs to file."""
    filepath = get_admins_file_path()
    # Always ensure superadmin is in the list
    admins_set.add(SUPERADMIN_UID)
    with open(filepath, 'w') as f:
        json.dump({'admins': list(admins_set)}, f, indent=2)

def is_moodmeal_admin(uid):
    """Check if a user is a mood meal admin."""
    if uid == SUPERADMIN_UID:
        return True
    admins = load_moodmeal_admins()
    return uid in admins


class AdminCheck(Resource):
    """Check if the current user is a mood meal admin."""

    @token_required()
    def get(self):
        """
        Verify admin status of the current user.

        Returns:
            JSON with is_admin boolean, user info, and profile picture URL.
        """
        current_user = g.current_user
        uid = current_user.uid

        is_admin = is_moodmeal_admin(uid)

        # Build profile picture URL
        admin_pfp = None
        if current_user.pfp:
            admin_pfp = f"/uploads/{uid}/{current_user.pfp}"

        return jsonify({
            'is_admin': is_admin,
            'uid': uid,
            'name': current_user.name,
            'admin_pfp': admin_pfp
        })


class AdminUsers(Resource):
    """Get all users with their mood meal admin status."""

    @token_required()
    def get(self):
        """
        Retrieve all users for the admin dashboard.

        Only accessible by mood meal admins.

        Returns:
            JSON with list of users and total count.
        """
        current_user = g.current_user

        # Check if current user is a mood meal admin
        if not is_moodmeal_admin(current_user.uid):
            return {'message': 'Access denied. Mood Meal admin privileges required.'}, 403

        # Get all users
        users = User.query.all()
        admins_set = load_moodmeal_admins()

        users_data = []
        for user in users:
            user_info = {
                'id': user.id,
                'uid': user.uid,
                'name': user.name,
                'email': user.email,
                'role': user.role,
                'school': user.school,
                'is_moodmeal_admin': user.uid in admins_set or user.uid == SUPERADMIN_UID,
                'sections': []
            }

            # Add sections info
            if hasattr(user, 'sections') and user.sections:
                for section in user.sections:
                    user_info['sections'].append({
                        'id': section.id,
                        'name': section._name,
                        'abbreviation': section.abbreviation
                    })

            users_data.append(user_info)

        return jsonify({
            'users': users_data,
            'total': len(users_data)
        })


class AdminMakeAdmin(Resource):
    """Grant or revoke mood meal admin privileges."""

    @token_required()
    def post(self):
        """
        Grant or revoke mood meal admin status for a user.

        Only the superadmin (Shayanb1) can perform this action.

        Request body:
            uid: The user ID to modify
            grant: Boolean - True to grant admin, False to revoke

        Returns:
            JSON with success message or error.
        """
        current_user = g.current_user

        # Only superadmin can grant/revoke admin privileges
        if current_user.uid != SUPERADMIN_UID:
            return {'message': 'Access denied. Only the superadmin can grant or revoke admin privileges.'}, 403

        body = request.get_json()
        if not body:
            return {'message': 'Request body is required'}, 400

        target_uid = body.get('uid')
        grant = body.get('grant', False)

        if not target_uid:
            return {'message': 'User ID (uid) is required'}, 400

        # Cannot modify superadmin status
        if target_uid == SUPERADMIN_UID:
            return {'message': 'Cannot modify superadmin privileges'}, 400

        # Verify target user exists
        target_user = User.query.filter_by(_uid=target_uid).first()
        if not target_user:
            return {'message': f'User {target_uid} not found'}, 404

        # Load current admins and update
        admins_set = load_moodmeal_admins()

        if grant:
            admins_set.add(target_uid)
            message = f'Successfully granted mood meal admin privileges to {target_uid}'
        else:
            admins_set.discard(target_uid)
            message = f'Successfully revoked mood meal admin privileges from {target_uid}'

        save_moodmeal_admins(admins_set)

        return jsonify({
            'message': message,
            'uid': target_uid,
            'is_moodmeal_admin': target_uid in admins_set
        })


# Register API resources
api.add_resource(AdminCheck, '/check')
api.add_resource(AdminUsers, '/users')
api.add_resource(AdminMakeAdmin, '/make-admin')
