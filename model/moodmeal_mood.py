"""
MoodMeal Mood Data Model
Stores user mood entries with scores, tags, and categories
"""
from __init__ import db
from sqlalchemy import Text
from datetime import datetime
import json

class MoodMealMood(db.Model):
    """
    MoodMeal Mood Model

    The MoodMealMood class represents mood entries for the MoodMeal application

    Attributes:
        id (int): The primary key for the mood entry
        _user_id (int): Foreign key to the user
        _mood_score (int): Mood score from 0-100
        _mood_tags (Text): JSON string of mood tags
        _mood_category (str): Mood category (Stressed/Anxious, Tired/Low Energy, etc.)
        _timestamp (DateTime): When the mood was recorded
    """
    __tablename__ = 'moodmeal_moods'

    id = db.Column(db.Integer, primary_key=True)
    _user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    _mood_score = db.Column(db.Integer, nullable=False)
    _mood_tags = db.Column(Text, default='[]')
    _mood_category = db.Column(db.String(50))
    _timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to User model
    user = db.relationship('User', backref=db.backref('moodmeal_moods', lazy=True))

    def __init__(self, user_id, mood_score, mood_tags=None, mood_category=None, timestamp=None):
        """
        Constructor for MoodMealMood object

        Args:
            user_id (int): The user ID
            mood_score (int): Mood score (0-100)
            mood_tags (list): List of mood tags
            mood_category (str): Mood category
            timestamp (datetime): When the mood was recorded (defaults to now)
        """
        self._user_id = user_id
        self._mood_score = mood_score
        self._mood_tags = json.dumps(mood_tags if mood_tags else [])
        self._mood_category = mood_category or self._calculate_category(mood_score)
        self._timestamp = timestamp or datetime.utcnow()

    @staticmethod
    def _calculate_category(score):
        """Calculate mood category from score"""
        if score <= 40:
            return 'Stressed/Anxious'
        elif score <= 60:
            return 'Tired/Low Energy'
        elif score <= 80:
            return 'Happy/Neutral'
        else:
            return 'Energetic/Excited'

    @property
    def user_id(self):
        return self._user_id

    @property
    def mood_score(self):
        return self._mood_score

    @mood_score.setter
    def mood_score(self, value):
        self._mood_score = value
        # Auto-update category when score changes
        self._mood_category = self._calculate_category(value)

    @property
    def mood_tags(self):
        """Get mood tags as a list"""
        return json.loads(self._mood_tags)

    @mood_tags.setter
    def mood_tags(self, value):
        """Set mood tags from a list"""
        self._mood_tags = json.dumps(value if value else [])

    @property
    def mood_category(self):
        return self._mood_category

    @mood_category.setter
    def mood_category(self, value):
        self._mood_category = value

    @property
    def timestamp(self):
        return self._timestamp

    def create(self):
        """Create a new mood entry in the database"""
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            print(f"Error creating mood entry: {e}")
            return None

    def read(self):
        """Read mood entry as a dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'mood_score': self.mood_score,
            'mood_tags': self.mood_tags,
            'mood_category': self.mood_category,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

    def update(self, data):
        """Update mood entry from a dictionary"""
        if 'mood_score' in data:
            self.mood_score = data['mood_score']
        if 'mood_tags' in data:
            self.mood_tags = data['mood_tags']
        if 'mood_category' in data:
            self.mood_category = data['mood_category']

        try:
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            print(f"Error updating mood entry: {e}")
            return None

    def delete(self):
        """Delete mood entry from the database"""
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting mood entry: {e}")
            return False
