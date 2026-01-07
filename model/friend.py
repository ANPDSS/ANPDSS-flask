"""
Friend and FriendRequest models for managing user friendships
"""

from __init__ import db
from datetime import datetime
from sqlalchemy.exc import IntegrityError


class Friend(db.Model):
    """
    Friend Model representing bidirectional friendships between users
    """
    __tablename__ = 'friends'

    id = db.Column(db.Integer, primary_key=True)
    _user_id1 = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    _user_id2 = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    _created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Ensure unique friendship pairs (prevent duplicates)
    __table_args__ = (
        db.UniqueConstraint('_user_id1', '_user_id2', name='unique_friendship'),
        db.CheckConstraint('_user_id1 < _user_id2', name='ordered_friendship')
    )

    def __init__(self, user_id1, user_id2):
        """Initialize a friendship, always storing IDs in ascending order"""
        if user_id1 == user_id2:
            raise ValueError("Users cannot be friends with themselves")

        # Store IDs in ascending order to prevent duplicate entries
        self._user_id1 = min(user_id1, user_id2)
        self._user_id2 = max(user_id1, user_id2)

    @property
    def user_id1(self):
        return self._user_id1

    @property
    def user_id2(self):
        return self._user_id2

    @property
    def created_at(self):
        return self._created_at.strftime('%Y-%m-%d %H:%M:%S') if self._created_at else None

    def read(self):
        """Convert object to dictionary"""
        return {
            "id": self.id,
            "user_id1": self._user_id1,
            "user_id2": self._user_id2,
            "created_at": self.created_at
        }

    def create(self):
        """Create a new friendship in the database"""
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except IntegrityError:
            db.session.rollback()
            return None

    def delete(self):
        """Delete the friendship"""
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False

    @staticmethod
    def are_friends(user_id1, user_id2):
        """Check if two users are friends"""
        min_id, max_id = min(user_id1, user_id2), max(user_id1, user_id2)
        return Friend.query.filter_by(_user_id1=min_id, _user_id2=max_id).first() is not None

    @staticmethod
    def get_friends_for_user(user_id):
        """Get all friend IDs for a given user"""
        friends = Friend.query.filter(
            (Friend._user_id1 == user_id) | (Friend._user_id2 == user_id)
        ).all()

        friend_ids = []
        for friendship in friends:
            # Add the ID that isn't the current user
            friend_ids.append(
                friendship._user_id2 if friendship._user_id1 == user_id else friendship._user_id1
            )

        return friend_ids


class FriendRequest(db.Model):
    """
    FriendRequest Model representing pending friend requests
    """
    __tablename__ = 'friend_requests'

    id = db.Column(db.Integer, primary_key=True)
    _sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    _receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    _status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    _created_at = db.Column(db.DateTime, default=datetime.utcnow)
    _updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sender = db.relationship('User', foreign_keys=[_sender_id], backref='sent_requests')
    receiver = db.relationship('User', foreign_keys=[_receiver_id], backref='received_requests')

    # Prevent duplicate requests
    __table_args__ = (
        db.UniqueConstraint('_sender_id', '_receiver_id', name='unique_friend_request'),
    )

    def __init__(self, sender_id, receiver_id):
        """Initialize a friend request"""
        if sender_id == receiver_id:
            raise ValueError("Users cannot send friend requests to themselves")

        self._sender_id = sender_id
        self._receiver_id = receiver_id
        self._status = 'pending'

    @property
    def sender_id(self):
        return self._sender_id

    @property
    def receiver_id(self):
        return self._receiver_id

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        if value not in ['pending', 'accepted', 'rejected']:
            raise ValueError(f"Invalid status: {value}")
        self._status = value

    @property
    def created_at(self):
        return self._created_at.strftime('%Y-%m-%d %H:%M:%S') if self._created_at else None

    @property
    def updated_at(self):
        return self._updated_at.strftime('%Y-%m-%d %H:%M:%S') if self._updated_at else None

    def read(self):
        """Convert object to dictionary"""
        return {
            "id": self.id,
            "sender_id": self._sender_id,
            "sender_name": self.sender._name if self.sender else None,
            "sender_uid": self.sender._uid if self.sender else None,
            "receiver_id": self._receiver_id,
            "receiver_name": self.receiver._name if self.receiver else None,
            "receiver_uid": self.receiver._uid if self.receiver else None,
            "status": self._status,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    def create(self):
        """Create a new friend request"""
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except IntegrityError:
            db.session.rollback()
            return None

    def update(self):
        """Update the friend request"""
        try:
            self._updated_at = datetime.utcnow()
            db.session.commit()
            return self
        except Exception:
            db.session.rollback()
            return None

    def delete(self):
        """Delete the friend request"""
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False

    @staticmethod
    def get_pending_requests_for_user(user_id):
        """Get all pending friend requests received by a user"""
        return FriendRequest.query.filter_by(
            _receiver_id=user_id,
            _status='pending'
        ).all()

    @staticmethod
    def get_sent_requests_for_user(user_id):
        """Get all friend requests sent by a user"""
        return FriendRequest.query.filter_by(_sender_id=user_id).all()

    @staticmethod
    def has_pending_request(sender_id, receiver_id):
        """Check if there's already a pending request between two users"""
        return FriendRequest.query.filter(
            ((FriendRequest._sender_id == sender_id) & (FriendRequest._receiver_id == receiver_id)) |
            ((FriendRequest._sender_id == receiver_id) & (FriendRequest._receiver_id == sender_id))
        ).filter_by(_status='pending').first() is not None


def init_friends():
    """Initialize the Friend and FriendRequest tables"""
    with db.session.begin():
        db.create_all()
