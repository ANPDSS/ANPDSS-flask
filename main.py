# imports from flask
from datetime import datetime
from urllib.parse import urljoin, urlparse
from flask import abort, redirect, render_template, request, send_from_directory, url_for, jsonify, current_app, g # import render_template from "public" flask libraries
from flask_login import current_user, login_user, logout_user
from flask.cli import AppGroup
from flask_login import current_user, login_required
from flask import current_app
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
from api.jwt_authorize import token_required
from api.Outfit_location_api import outfit_location_api


# import "objects" from "this" project
from __init__ import app, db, login_manager  # Key Flask objects 
# API endpoints
from api.user import user_api 
from api.python_exec_api import python_exec_api
from api.javascript_exec_api import javascript_exec_api
from api.section import section_api
from api.pfp import pfp_api
from api.stock import stock_api
from api.analytics import analytics_api
from api.student import student_api
from api.groq_api import groq_api
from api.gemini_api import gemini_api
from api.microblog_api import microblog_api
from api.classroom_api import classroom_api
from api.moodmeal_api import moodmeal_api
from api.location_api import location_api
from api.admin_api import admin_api
from hacks.joke import joke_api  # Import the joke API blueprint
from api.post import post_api  # Import the social media post API
from api.friend_api import friend_api  # Import the friend API
from api.message_api import message_api  # Import the messaging API
from api.group_api import group_api  # Import the group API
#from api.announcement import announcement_api ##temporary revert

# database Initialization functions
from model.user import User, initUsers
from model.user import Section;
from model.github import GitHubUser
from model.moodmeal_mood import MoodMealMood
from model.feedback import Feedback
from api.analytics import get_date_range
# from api.grade_api import grade_api
from api.study import study_api
from api.feedback_api import feedback_api
from model.study import Study, initStudies
from model.classroom import Classroom
from model.post import Post, init_posts
from model.microblog import MicroBlog, Topic, init_microblogs
from model.friend import Friend, FriendRequest, init_friends
from model.private_message import PrivateMessage, init_private_messages
from model.group import Group, GroupMember, GroupInvite, GroupMessage, init_groups
from hacks.jokes import initJokes
# from model.announcement import Announcement ##temporary revert

# server only Views

import os
import requests

# Load environment variables
load_dotenv()

app.config['KASM_SERVER'] = os.getenv('KASM_SERVER')
app.config['KASM_API_KEY'] = os.getenv('KASM_API_KEY')
app.config['KASM_API_KEY_SECRET'] = os.getenv('KASM_API_KEY_SECRET')



# =====================================================================
# =====                     SEQUENCING                           =====
# =====================================================================
# Sequencing means executing statements one after another, in order.
# Below, each blueprint is registered in a specific top-to-bottom
# sequence. The order matters because Flask processes them linearly,
# and each line depends on the previous imports completing first.
# This entire block is a clear example of SEQUENCING in action.
# =====================================================================
app.register_blueprint(python_exec_api)
app.register_blueprint(javascript_exec_api)
app.register_blueprint(user_api)
app.register_blueprint(section_api)
app.register_blueprint(pfp_api)
app.register_blueprint(stock_api)
app.register_blueprint(groq_api)
app.register_blueprint(gemini_api)
app.register_blueprint(microblog_api)

app.register_blueprint(analytics_api)
app.register_blueprint(student_api)
# app.register_blueprint(grade_api)
app.register_blueprint(study_api)
app.register_blueprint(classroom_api)
app.register_blueprint(feedback_api)
app.register_blueprint(joke_api)  # Register the joke API blueprint
app.register_blueprint(post_api)  # Register the social media post API
app.register_blueprint(moodmeal_api)  # Register the moodmeal API blueprint
app.register_blueprint(location_api)  # Register the location API blueprint
app.register_blueprint(admin_api)  # Register the admin API blueprint for mood meal dashboard
app.register_blueprint(outfit_location_api)
app.register_blueprint(friend_api)  # Register the friend API blueprint
app.register_blueprint(message_api)  # Register the messaging API blueprint
app.register_blueprint(group_api)  # Register the group API blueprint
# app.register_blueprint(announcement_api) ##temporary revert

# Database initialization
with app.app_context():
    # Create tables if they don't exist
    db.create_all()
    # Run group migrations (adds image_data / mood_snapshot columns if missing)
    init_groups()
    print("Database tables created/verified")

    # Initialize jokes data
    initJokes()

# Tell Flask-Login the view function name of your login route
login_manager.login_view = "login"

@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect(url_for('login', next=request.path))

# register URIs for server pages
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.context_processor
def inject_user():
    return dict(current_user=current_user)

# Helper function to check if the URL is safe for redirects
def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

# =====================================================================
# =====                     SELECTION                            =====
# =====================================================================
# Selection means choosing different paths of execution based on a
# condition (if/elif/else). Below, the login route uses SELECTION
# to check: (1) if the request method is POST, (2) if the user
# exists AND the password is correct, and (3) if the redirect URL
# is safe. Each condition branches the code into a different path.
# This is a textbook example of SELECTION (conditional logic).
# =====================================================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    next_page = request.args.get('next', '') or request.form.get('next', '')
    if request.method == 'POST':
        user = User.query.filter_by(_uid=request.form['username']).first()
        if user and user.is_password(request.form['password']):
            login_user(user)
            if not is_safe_url(next_page):
                return abort(400)
            return redirect(next_page or url_for('index'))
        else:
            error = 'Invalid username or password.'
    return render_template("login.html", error=error, next=next_page)

@app.route('/studytracker')  # route for the study tracker page
def studytracker():
    return render_template("studytracker.html")
    
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.errorhandler(404)  # catch for URL not found
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404

@app.route('/')  # connects default URL to index() function
def index():
    print("Home:", current_user)
    return render_template("index.html")



@app.route('/users/table2')
@login_required
def u2table():
    users = User.query.order_by(User.id).all()
    # Build latest mood mapping for each user (or None)
    latest_moods = {}
    for u in users:
        mood = MoodMealMood.query.filter_by(_user_id=u.id).order_by(MoodMealMood._timestamp.desc()).first()
        latest_moods[u.id] = mood.read() if mood else None
    return render_template("u2table.html", user_data=users, latest_moods=latest_moods)

@app.route('/db/viewer')
@login_required
def db_viewer():
    """Database viewer for viewing all tables in user_management.db"""
    import sqlite3

    # Only allow Admin users to access the database viewer
    if current_user.role != 'Admin':
        return abort(403)

    # Get the database path
    db_path = os.path.join(current_app.instance_path, 'volumes', 'user_management.db')

    # Fallback to default SQLite path if not found
    if not os.path.exists(db_path):
        db_path = os.path.join(current_app.instance_path, 'user_management.db')

    selected_table = request.args.get('table')

    # =====================================================================
    # =====                       LISTS                              =====
    # =====================================================================
    # Lists (and dictionaries) are data structures that store multiple
    # values in a single variable. Below, 'tables', 'columns', 'rows',
    # and 'schema' are all initialized as empty LISTS (using []).
    # 'row_counts' and 'user_id_columns' are dictionaries (key-value
    # pairs). These collections are used to gather and organize data
    # retrieved from the database for display in the viewer.
    # This is a clear example of LISTS being used in Python.
    # =====================================================================
    tables = []
    columns = []
    rows = []
    schema = []
    row_count = 0
    row_counts = {}

    # Tables that have user_id columns we want to replace with usernames
    # Format: {table_name: [list of column names that are user IDs]}
    user_id_columns = {
        'moodmeal_moods': ['_user_id'],
        'moodmeal_preferences': ['_user_id'],
        'friend_requests': ['_sender_id', '_receiver_id'],
        'friends': ['_user_id1', '_user_id2'],
        'private_messages': ['_sender_id', '_receiver_id'],
        'pfps': ['_user_id'],
        'posts': ['_user_id'],
        'microblogs': ['_user_id'],
        'user_locations': ['_user_id'],
        'study': ['_user_id'],
    }

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]

        # Build user_id -> username mapping
        user_map = {}
        try:
            cursor.execute('SELECT id, _uid, _name FROM users')
            for row in cursor.fetchall():
                user_map[row[0]] = f"{row[2]} (@{row[1]})"  # "Name (@username)"
        except:
            pass  # users table might not exist or have different schema

        # =====================================================================
        # =====                    ITERATION                            =====
        # =====================================================================
        # Iteration means repeating a block of code for each item in a
        # collection (looping). Below, the 'for' loop ITERATES over
        # every table name in the 'tables' list. For EACH table, it
        # executes a SQL COUNT query to determine how many rows exist.
        # This is a textbook example of ITERATION (a for loop).
        # =====================================================================
        for table in tables:
            try:
                cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
                row_counts[table] = cursor.fetchone()[0]
            except:
                row_counts[table] = None

        # If a table is selected, get its data
        if selected_table and selected_table in tables:
            # Get schema info
            cursor.execute(f'PRAGMA table_info("{selected_table}")')
            schema_rows = cursor.fetchall()
            schema = [{'cid': r[0], 'name': r[1], 'type': r[2], 'notnull': r[3], 'dflt_value': r[4], 'pk': r[5]} for r in schema_rows]
            columns = [s['name'] for s in schema]

            # Get table data (limit to 1000 rows for performance)
            cursor.execute(f'SELECT * FROM "{selected_table}" LIMIT 1000')
            rows = [list(row) for row in cursor.fetchall()]
            row_count = row_counts.get(selected_table, len(rows))

            # Replace user IDs with usernames for specified tables
            if selected_table in user_id_columns and user_map:
                id_col_names = user_id_columns[selected_table]
                # Find column indices for user_id columns
                id_col_indices = []
                for col_name in id_col_names:
                    if col_name in columns:
                        id_col_indices.append((columns.index(col_name), col_name))

                # Replace user IDs with usernames in rows
                for row in rows:
                    for col_idx, col_name in id_col_indices:
                        user_id = row[col_idx]
                        if user_id and user_id in user_map:
                            row[col_idx] = user_map[user_id]
                        elif user_id:
                            row[col_idx] = f"User #{user_id}"

                # Update column headers to indicate they show usernames
                for col_idx, col_name in id_col_indices:
                    # Change column name from _user_id to user, _sender_id to sender, etc.
                    friendly_name = col_name.replace('_id', '').replace('_', ' ').strip()
                    columns[col_idx] = friendly_name

        conn.close()
    except Exception as e:
        return render_template("error.html", message=f"Database error: {str(e)}"), 500

    return render_template("db_viewer.html",
                           tables=tables,
                           selected_table=selected_table,
                           columns=columns,
                           rows=rows,
                           schema=schema,
                           row_count=row_count,
                           row_counts=row_counts)

@app.route('/sections/')
@login_required
def sections():
    sections = Section.query.all()
    return render_template("sections.html", sections=sections)

# Helper function to extract uploads for a user (ie PFP image)
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
 
@app.route('/users/delete/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        user.delete()
        return jsonify({'message': 'User deleted successfully'}), 200
    return jsonify({'error': 'User not found'}), 404

@app.route('/users/reset_password/<int:user_id>', methods=['POST'])
@login_required
def reset_password(user_id):
    if current_user.role != 'Admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Set the new password
    if user.update({"password": app.config['DEFAULT_PASSWORD']}):
        return jsonify({'message': 'Password reset successfully'}), 200
    return jsonify({'error': 'Password reset failed'}), 500

@app.route('/kasm_users')
def kasm_users():
    # Fetch configuration details from environment or app config
    SERVER = current_app.config.get('KASM_SERVER')
    API_KEY = current_app.config.get('KASM_API_KEY')
    API_KEY_SECRET = current_app.config.get('KASM_API_KEY_SECRET')

    # Validate required configurations
    if not SERVER or not API_KEY or not API_KEY_SECRET:
        return render_template('error.html', message='KASM keys are missing'), 400

    try:
        # Prepare API request details
        url = f"{SERVER}/api/public/get_users"
        data = {
            "api_key": API_KEY,
            "api_key_secret": API_KEY_SECRET
        }

        # Perform the POST request
        response = requests.post(url, json=data, timeout=10)  # Added timeout for reliability

        # Validate the API response
        if response.status_code != 200:
            return render_template(
                'error.html', 
                message='Failed to get users', 
                code=response.status_code
            ), response.status_code

        # Parse the users list from the response
        users = response.json().get('users', [])

        # Process `last_session` and handle potential parsing issues
        for user in users:
            last_session = user.get('last_session')
            try:
                user['last_session'] = datetime.fromisoformat(last_session) if last_session else None
            except ValueError:
                user['last_session'] = None  # Fallback for invalid date formats

        # Sort users by `last_session`, treating `None` as the oldest date
        sorted_users = sorted(
            users, 
            key=lambda x: x['last_session'] or datetime.min, 
            reverse=True
        )

        # Render the sorted users in the template
        return render_template('kasm_users.html', users=sorted_users)

    except requests.RequestException as e:
        # Handle connection errors or other request exceptions
        return render_template(
            'error.html', 
            message=f"Error connecting to KASM API: {str(e)}"
        ), 500
        
        
@app.route('/delete_user/<user_id>', methods=['DELETE'])
def delete_user_kasm(user_id):
    if current_user.role != 'Admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    SERVER = current_app.config.get('KASM_SERVER')
    API_KEY = current_app.config.get('KASM_API_KEY')
    API_KEY_SECRET = current_app.config.get('KASM_API_KEY_SECRET')

    if not SERVER or not API_KEY or not API_KEY_SECRET:
        return {'message': 'KASM keys are missing'}, 400

    try:
        # Kasm API to delete a user
        url = f"{SERVER}/api/public/delete_user"
        data = {
            "api_key": API_KEY,
            "api_key_secret": API_KEY_SECRET,
            "target_user": {"user_id": user_id},
            "force": False
        }
        response = requests.post(url, json=data)

        if response.status_code == 200:
            return {'message': 'User deleted successfully'}, 200
        else:
            return {'message': 'Failed to delete user'}, response.status_code

    except requests.RequestException as e:
        return {'message': 'Error connecting to KASM API', 'error': str(e)}, 500


@app.route('/update_user/<string:uid>', methods=['PUT'])
def update_user(uid):
    # Authorization check
    if current_user.role != 'Admin':
        return jsonify({'error': 'Unauthorized'}), 403

    # Get the JSON data from the request
    data = request.get_json()
    print(f"Request Data: {data}")  # Log the incoming data

    # Find the user in the database
    user = User.query.filter_by(_uid=uid).first()
    if user:
        print(f"Found user: {user.uid}")  # Log the found user's UID
        
        # Update the user using the provided data
        user.update(data)  # Assuming `user.update(data)` is a method on your User model
        
        # Save changes to the database
        return jsonify({"message": "User updated successfully."}), 200
    else:
        print("User not found.")  # Log when user is not found
        return jsonify({"message": "User not found."}), 404



    
# Create an AppGroup for custom commands
custom_cli = AppGroup('custom', help='Custom commands')

# Define a command to run the data generation functions
@custom_cli.command('generate_data')
def generate_data():
    initUsers()
    init_microblogs()

# Register the custom command group with the Flask application
app.cli.add_command(custom_cli)
        
# this runs the flask application on the development server
if __name__ == "__main__":
      # change name for testing
      app.run(debug=True, host="0.0.0.0", port="8309")

