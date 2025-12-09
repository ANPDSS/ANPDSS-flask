"""
MoodMeal User Preferences Model
Stores user preferences for dietary restrictions, allergies, cuisines, music, and activities
"""
from __init__ import db
from sqlalchemy import Text
import json

class MoodMealPreferences(db.Model):
    """
    MoodMeal Preferences Model

    The MoodMealPreferences class represents user preferences for the MoodMeal application

    Attributes:
        id (int): The primary key for the preference entry
        _user_id (int): Foreign key to the user
        _dietary (Text): JSON string of dietary restrictions
        _allergies (Text): JSON string of allergies
        _cuisines (Text): JSON string of favorite cuisines
        _music (Text): JSON string of music preferences
        _activities (Text): JSON string of favorite activities
    """
    __tablename__ = 'moodmeal_preferences'

    id = db.Column(db.Integer, primary_key=True)
    _user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    _dietary = db.Column(Text, default='[]')
    _allergies = db.Column(Text, default='[]')
    _cuisines = db.Column(Text, default='[]')
    _music = db.Column(Text, default='[]')
    _activities = db.Column(Text, default='[]')

    # Relationship to User model
    user = db.relationship('User', backref=db.backref('moodmeal_preferences', uselist=False))

    def __init__(self, user_id, dietary=None, allergies=None, cuisines=None, music=None, activities=None):
        """
        Constructor for MoodMealPreferences object

        Args:
            user_id (int): The user ID
            dietary (list): List of dietary restrictions
            allergies (list): List of allergies
            cuisines (list): List of favorite cuisines
            music (list): List of music preferences
            activities (list): List of favorite activities
        """
        self._user_id = user_id
        self._dietary = json.dumps(dietary if dietary else [])
        self._allergies = json.dumps(allergies if allergies else [])
        self._cuisines = json.dumps(cuisines if cuisines else [])
        self._music = json.dumps(music if music else [])
        self._activities = json.dumps(activities if activities else [])

    @property
    def user_id(self):
        return self._user_id

    @property
    def dietary(self):
        """Get dietary restrictions as a list"""
        return json.loads(self._dietary)

    @dietary.setter
    def dietary(self, value):
        """Set dietary restrictions from a list"""
        self._dietary = json.dumps(value if value else [])

    @property
    def allergies(self):
        """Get allergies as a list"""
        return json.loads(self._allergies)

    @allergies.setter
    def allergies(self, value):
        """Set allergies from a list"""
        self._allergies = json.dumps(value if value else [])

    @property
    def cuisines(self):
        """Get cuisines as a list"""
        return json.loads(self._cuisines)

    @cuisines.setter
    def cuisines(self, value):
        """Set cuisines from a list"""
        self._cuisines = json.dumps(value if value else [])

    @property
    def music(self):
        """Get music preferences as a list"""
        return json.loads(self._music)

    @music.setter
    def music(self, value):
        """Set music preferences from a list"""
        self._music = json.dumps(value if value else [])

    @property
    def activities(self):
        """Get activities as a list"""
        return json.loads(self._activities)

    @activities.setter
    def activities(self, value):
        """Set activities from a list"""
        self._activities = json.dumps(value if value else [])

    def create(self):
        """Create a new preferences entry in the database"""
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            print(f"Error creating preferences: {e}")
            return None

    def read(self):
        """Read preferences as a dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'dietary': self.dietary,
            'allergies': self.allergies,
            'cuisines': self.cuisines,
            'music': self.music,
            'activities': self.activities
        }

    def update(self, data):
        """Update preferences from a dictionary"""
        if 'dietary' in data:
            self.dietary = data['dietary']
        if 'allergies' in data:
            self.allergies = data['allergies']
        if 'cuisines' in data:
            self.cuisines = data['cuisines']
        if 'music' in data:
            self.music = data['music']
        if 'activities' in data:
            self.activities = data['activities']

        try:
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            print(f"Error updating preferences: {e}")
            return None

    def delete(self):
        """Delete preferences from the database"""
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting preferences: {e}")
            return False
