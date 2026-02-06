"""
MoodMeal Mood Data Model
Stores user mood entries with scores, tags, and categories

Programming Constructs:
- Sequencing: Code executes in order through CRUD operations
- Selection: if/elif/else for category calculation and validation
- Iteration: Loops for tag validation and mood history processing
- Lists: Arrays storing valid tags, mood categories, and score thresholds
"""
from __init__ import db
from sqlalchemy import Text
from datetime import datetime
import json

# List: Valid mood categories with their score thresholds
MOOD_CATEGORIES = [
    {'name': 'Stressed/Anxious', 'min_score': 0, 'max_score': 40},
    {'name': 'Tired/Low Energy', 'min_score': 41, 'max_score': 60},
    {'name': 'Happy/Neutral', 'min_score': 61, 'max_score': 80},
    {'name': 'Energetic/Excited', 'min_score': 81, 'max_score': 100}
]

# List: Valid mood tags that users can select
VALID_MOOD_TAGS = [
    'happy', 'sad', 'anxious', 'calm', 'energetic',
    'tired', 'stressed', 'relaxed', 'focused', 'creative',
    'social', 'lonely', 'grateful', 'frustrated', 'hopeful'
]


def validate_mood_tags(tags: list) -> list:
    """
    Validate and filter mood tags against the allowed list.
    Demonstrates iteration through a list with selection.
    """
    validated_tags = []

    # Iteration: Loop through each submitted tag
    for tag in tags:
        # Selection: Only keep tags that are in the valid list
        if isinstance(tag, str) and tag.lower().strip() in VALID_MOOD_TAGS:
            validated_tags.append(tag.lower().strip())

    return validated_tags


def get_category_from_score(score: int) -> str:
    """
    Determine mood category by iterating through category thresholds.
    Demonstrates iteration through a list with selection.
    """
    category = 'Unknown'

    # Iteration: Loop through mood categories list
    for cat in MOOD_CATEGORIES:
        # Selection: Check if score falls within this category's range
        if cat['min_score'] <= score <= cat['max_score']:
            category = cat['name']
            break

    return category


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
        """Calculate mood category from score using iteration through categories list."""
        # Iteration + Selection: Use the module-level function that loops through MOOD_CATEGORIES
        return get_category_from_score(score)

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

    @staticmethod
    def get_mood_summary(user_id):
        """
        Get a summary of a user's mood history with category counts.
        Demonstrates iteration through query results and list building.
        """
        moods = MoodMealMood.query.filter_by(_user_id=user_id).all()

        # List: Collect all tags and category counts
        all_tags = []
        category_counts = {}

        # Iteration: Loop through each mood entry
        for mood in moods:
            # Selection: Track category frequency
            cat = mood.mood_category
            if cat in category_counts:
                category_counts[cat] += 1
            else:
                category_counts[cat] = 1

            # Iteration: Loop through tags in each mood entry
            for tag in mood.mood_tags:
                if tag not in all_tags:
                    all_tags.append(tag)

        return {
            'total_entries': len(moods),
            'category_counts': category_counts,
            'unique_tags': all_tags
        }
