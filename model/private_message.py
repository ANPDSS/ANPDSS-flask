"""
PrivateMessage model for user-to-user direct messaging
"""

from __init__ import db
from datetime import datetime
from sqlalchemy.exc import IntegrityError


class PrivateMessage(db.Model):
    """
    PrivateMessage Model for direct messages between friends
    """
    __tablename__ = 'private_messages'

    id = db.Column(db.Integer, primary_key=True)
    _sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    _receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    _content = db.Column(db.Text, nullable=False)
    _is_read = db.Column(db.Boolean, default=False)
    _created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    sender = db.relationship('User', foreign_keys=[_sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[_receiver_id], backref='received_messages')

    def __init__(self, sender_id, receiver_id, content):
        """Initialize a private message"""
        if sender_id == receiver_id:
            raise ValueError("Users cannot send messages to themselves")

        if not content or len(content.strip()) == 0:
            raise ValueError("Message content cannot be empty")

        self._sender_id = sender_id
        self._receiver_id = receiver_id
        self._content = content
        self._is_read = False

    @property
    def sender_id(self):
        return self._sender_id

    @property
    def receiver_id(self):
        return self._receiver_id

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, value):
        if not value or len(value.strip()) == 0:
            raise ValueError("Message content cannot be empty")
        self._content = value

    @property
    def is_read(self):
        return self._is_read

    @is_read.setter
    def is_read(self, value):
        self._is_read = bool(value)

    @property
    def created_at(self):
        return self._created_at.strftime('%Y-%m-%d %H:%M:%S') if self._created_at else None

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
            "content": self._content,
            "is_read": self._is_read,
            "created_at": self.created_at
        }

    def create(self):
        """Create a new message in the database"""
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except Exception:
            db.session.rollback()
            return None

    def update(self):
        """Update the message (mainly for marking as read)"""
        try:
            db.session.commit()
            return self
        except Exception:
            db.session.rollback()
            return None

    def delete(self):
        """Delete the message"""
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False

    @staticmethod
    def get_conversation(user_id1, user_id2, limit=50):
        """Get conversation between two users, ordered by time"""
        return PrivateMessage.query.filter(
            ((PrivateMessage._sender_id == user_id1) & (PrivateMessage._receiver_id == user_id2)) |
            ((PrivateMessage._sender_id == user_id2) & (PrivateMessage._receiver_id == user_id1))
        ).order_by(PrivateMessage._created_at.desc()).limit(limit).all()

    @staticmethod
    def get_conversations_for_user(user_id):
        """Get all unique conversations for a user with message counts"""
        # Get all messages where user is sender or receiver
        messages = PrivateMessage.query.filter(
            (PrivateMessage._sender_id == user_id) | (PrivateMessage._receiver_id == user_id)
        ).all()

        # Group by conversation partner
        conversations = {}
        for msg in messages:
            partner_id = msg._receiver_id if msg._sender_id == user_id else msg._sender_id

            if partner_id not in conversations:
                conversations[partner_id] = {
                    'partner_id': partner_id,
                    'partner_name': msg.receiver._name if msg._sender_id == user_id else msg.sender._name,
                    'partner_uid': msg.receiver._uid if msg._sender_id == user_id else msg.sender._uid,
                    'last_message': msg._content,
                    'last_message_time': msg._created_at,
                    'unread_count': 0,
                    'total_messages': 0
                }

            conversations[partner_id]['total_messages'] += 1

            # Count unread messages sent TO the current user
            if msg._receiver_id == user_id and not msg._is_read:
                conversations[partner_id]['unread_count'] += 1

            # Update last message if this message is newer
            if msg._created_at > conversations[partner_id]['last_message_time']:
                conversations[partner_id]['last_message'] = msg._content
                conversations[partner_id]['last_message_time'] = msg._created_at

        # Format datetime objects to strings for JSON serialization
        for conv in conversations.values():
            if conv['last_message_time']:
                conv['last_message_time'] = conv['last_message_time'].strftime('%Y-%m-%d %H:%M:%S')

        return list(conversations.values())

    @staticmethod
    def mark_conversation_as_read(user_id, partner_id):
        """Mark all messages from partner_id to user_id as read"""
        try:
            messages = PrivateMessage.query.filter_by(
                _sender_id=partner_id,
                _receiver_id=user_id,
                _is_read=False
            ).all()

            for msg in messages:
                msg._is_read = True

            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False

    @staticmethod
    def get_unread_count(user_id):
        """Get total unread message count for a user"""
        return PrivateMessage.query.filter_by(
            _receiver_id=user_id,
            _is_read=False
        ).count()


def init_private_messages():
    """Initialize the PrivateMessage table"""
    with db.session.begin():
        db.create_all()
