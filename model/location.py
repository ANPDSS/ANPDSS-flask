"""
Location Model for MoodMeal
Stores user location data for personalized recommendations
"""
from __init__ import db
from datetime import datetime
import json

class UserLocation(db.Model):
    """
    UserLocation Model

    Stores location data for users to provide location-based recommendations

    Attributes:
        id (int): Primary key
        _user_id (int): Foreign key to user
        _latitude (float): Latitude coordinate (nullable for privacy)
        _longitude (float): Longitude coordinate (nullable for privacy)
        _city (str): City name
        _region (str): State/region
        _country (str): Country
        _method (str): Method used to get location (GPS or IP)
        _timestamp (DateTime): When location was recorded
    """
    __tablename__ = 'user_locations'

    id = db.Column(db.Integer, primary_key=True)
    _user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    _latitude = db.Column(db.Float, nullable=True)  # Nullable for privacy
    _longitude = db.Column(db.Float, nullable=True)
    _city = db.Column(db.String(100))
    _region = db.Column(db.String(100))
    _country = db.Column(db.String(100))
    _method = db.Column(db.String(20))  # 'GPS' or 'IP'
    _timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to User model
    user = db.relationship('User', backref=db.backref('locations', lazy=True))

    def __init__(self, user_id, latitude=None, longitude=None, city=None,
                 region=None, country=None, method='IP'):
        """
        Constructor for UserLocation

        Args:
            user_id (int): User ID
            latitude (float): Latitude (optional for privacy)
            longitude (float): Longitude (optional for privacy)
            city (str): City name
            region (str): State/region
            country (str): Country
            method (str): 'GPS' or 'IP'
        """
        self._user_id = user_id
        self._latitude = latitude
        self._longitude = longitude
        self._city = city
        self._region = region
        self._country = country
        self._method = method
        self._timestamp = datetime.utcnow()

    @property
    def user_id(self):
        return self._user_id

    @property
    def latitude(self):
        return self._latitude

    @property
    def longitude(self):
        return self._longitude

    @property
    def city(self):
        return self._city

    @property
    def region(self):
        return self._region

    @property
    def country(self):
        return self._country

    @property
    def method(self):
        return self._method

    @property
    def timestamp(self):
        return self._timestamp

    def create(self):
        """Save location to database"""
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            print(f"Error creating location: {e}")
            return None

    def read(self):
        """Return location as dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'city': self.city,
            'region': self.region,
            'country': self.country,
            'method': self.method,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

    def update(self, data):
        """Update location from dictionary"""
        if 'latitude' in data:
            self._latitude = data['latitude']
        if 'longitude' in data:
            self._longitude = data['longitude']
        if 'city' in data:
            self._city = data['city']
        if 'region' in data:
            self._region = data['region']
        if 'country' in data:
            self._country = data['country']
        if 'method' in data:
            self._method = data['method']

        try:
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            print(f"Error updating location: {e}")
            return None

    def delete(self):
        """Delete location from database"""
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting location: {e}")
            return False
