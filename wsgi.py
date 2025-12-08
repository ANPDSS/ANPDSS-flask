import sys
import os

# Add your project directory to the sys.path
project_home = '/home/YOUR_USERNAME/ANPDSS-flask'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Set environment variables if needed
os.environ['FLASK_PORT'] = '5000'  # PythonAnywhere handles the actual port

# Import the Flask app
from main import app as application
