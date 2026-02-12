"""
Group models for friend group creation, membership, invites, and group messaging
"""

from __init__ import db
from datetime import datetime
from sqlalchemy.exc import IntegrityError

MAX_GROUP_MEMBERS = 10  # Max members excluding the creator (so 11 total)


class Group(db.Model):
    """
    Group Model representing a named group created by a user
    """
    __tablename__ = 'groups'

    id = db.Column(db.Integer, primary_key=True)
    _name = db.Column(db.String(100), nullable=False)
    _creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    _created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', foreign_keys=[_creator_id])
    members = db.relationship('GroupMember', backref='group', cascade='all, delete-orphan')
    messages = db.relationship('GroupMessage', backref='group', cascade='all, delete-orphan')
    invites = db.relationship('GroupInvite', backref='group', cascade='all, delete-orphan')

    def __init__(self, name, creator_id):
        if not name or len(name.strip()) == 0:
            raise ValueError("Group name cannot be empty")
        if len(name) > 100:
            raise ValueError("Group name cannot exceed 100 characters")
        self._name = name.strip()
        self._creator_id = creator_id

    @property
    def name(self):
        return self._name

    @property
    def creator_id(self):
        return self._creator_id

    @property
    def created_at(self):
        return self._created_at.strftime('%Y-%m-%d %H:%M:%S') if self._created_at else None

    def member_count(self):
        return GroupMember.query.filter_by(_group_id=self.id).count()

    def is_member(self, user_id):
        return GroupMember.query.filter_by(_group_id=self.id, _user_id=user_id).first() is not None

    def read(self):
        return {
            "id": self.id,
            "name": self._name,
            "creator_id": self._creator_id,
            "creator_name": self.creator._name if self.creator else None,
            "creator_uid": self.creator._uid if self.creator else None,
            "member_count": self.member_count(),
            "created_at": self.created_at
        }

    def create(self):
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except Exception:
            db.session.rollback()
            return None

    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False


class GroupMember(db.Model):
    """
    GroupMember Model representing a user's membership in a group
    """
    __tablename__ = 'group_members'

    id = db.Column(db.Integer, primary_key=True)
    _group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    _user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    _joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[_user_id])

    __table_args__ = (
        db.UniqueConstraint('_group_id', '_user_id', name='unique_group_member'),
    )

    def __init__(self, group_id, user_id):
        self._group_id = group_id
        self._user_id = user_id

    @property
    def group_id(self):
        return self._group_id

    @property
    def user_id(self):
        return self._user_id

    @property
    def joined_at(self):
        return self._joined_at.strftime('%Y-%m-%d %H:%M:%S') if self._joined_at else None

    def read(self):
        return {
            "id": self.id,
            "group_id": self._group_id,
            "user_id": self._user_id,
            "user_name": self.user._name if self.user else None,
            "user_uid": self.user._uid if self.user else None,
            "joined_at": self.joined_at
        }

    def create(self):
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except IntegrityError:
            db.session.rollback()
            return None

    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False


class GroupInvite(db.Model):
    """
    GroupInvite Model representing a pending invite to join a group
    """
    __tablename__ = 'group_invites'

    id = db.Column(db.Integer, primary_key=True)
    _group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    _inviter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    _invitee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    _status = db.Column(db.String(20), default='pending')  # pending, accepted, declined
    _created_at = db.Column(db.DateTime, default=datetime.utcnow)

    inviter = db.relationship('User', foreign_keys=[_inviter_id])
    invitee = db.relationship('User', foreign_keys=[_invitee_id])

    __table_args__ = (
        db.UniqueConstraint('_group_id', '_invitee_id', name='unique_group_invite'),
    )

    def __init__(self, group_id, inviter_id, invitee_id):
        self._group_id = group_id
        self._inviter_id = inviter_id
        self._invitee_id = invitee_id
        self._status = 'pending'

    @property
    def group_id(self):
        return self._group_id

    @property
    def inviter_id(self):
        return self._inviter_id

    @property
    def invitee_id(self):
        return self._invitee_id

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        if value not in ['pending', 'accepted', 'declined']:
            raise ValueError(f"Invalid status: {value}")
        self._status = value

    @property
    def created_at(self):
        return self._created_at.strftime('%Y-%m-%d %H:%M:%S') if self._created_at else None

    def read(self):
        return {
            "id": self.id,
            "group_id": self._group_id,
            "group_name": self.group.name if self.group else None,
            "inviter_id": self._inviter_id,
            "inviter_name": self.inviter._name if self.inviter else None,
            "inviter_uid": self.inviter._uid if self.inviter else None,
            "invitee_id": self._invitee_id,
            "invitee_name": self.invitee._name if self.invitee else None,
            "invitee_uid": self.invitee._uid if self.invitee else None,
            "status": self._status,
            "created_at": self.created_at
        }

    def create(self):
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except IntegrityError:
            db.session.rollback()
            return None

    def update(self):
        try:
            db.session.commit()
            return self
        except Exception:
            db.session.rollback()
            return None

    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False

    @staticmethod
    def get_pending_invites_for_user(user_id):
        return GroupInvite.query.filter_by(_invitee_id=user_id, _status='pending').all()

    @staticmethod
    def has_pending_invite(group_id, invitee_id):
        return GroupInvite.query.filter_by(
            _group_id=group_id,
            _invitee_id=invitee_id,
            _status='pending'
        ).first() is not None


class GroupMessage(db.Model):
    """
    GroupMessage Model for messages sent within a group
    """
    __tablename__ = 'group_messages'

    id = db.Column(db.Integer, primary_key=True)
    _group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    _sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    _content = db.Column(db.Text, nullable=False)
    _image_data = db.Column(db.Text, nullable=True)       # base64 photo from webcam
    _mood_snapshot = db.Column(db.String(500), nullable=True)  # JSON: {score, category, tags}
    _created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[_sender_id])

    def __init__(self, group_id, sender_id, content, image_data=None, mood_snapshot=None):
        # Allow empty text content when an image is attached
        if not image_data and (not content or len(content.strip()) == 0):
            raise ValueError("Message content cannot be empty")
        if content and len(content) > 5000:
            raise ValueError("Message exceeds maximum length of 5000 characters")
        self._group_id = group_id
        self._sender_id = sender_id
        self._content = content or ''
        self._image_data = image_data
        self._mood_snapshot = mood_snapshot

    @property
    def group_id(self):
        return self._group_id

    @property
    def sender_id(self):
        return self._sender_id

    @property
    def content(self):
        return self._content

    @property
    def created_at(self):
        return self._created_at.strftime('%Y-%m-%d %H:%M:%S') if self._created_at else None

    def read(self):
        return {
            "id": self.id,
            "group_id": self._group_id,
            "sender_id": self._sender_id,
            "sender_name": self.sender._name if self.sender else None,
            "sender_uid": self.sender._uid if self.sender else None,
            "content": self._content,
            "image_data": self._image_data,
            "mood_snapshot": self._mood_snapshot,
            "created_at": self.created_at
        }

    def create(self):
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except Exception:
            db.session.rollback()
            return None

    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False

    @staticmethod
    def get_messages(group_id, limit=50):
        return GroupMessage.query.filter_by(_group_id=group_id).order_by(
            GroupMessage._created_at.desc()
        ).limit(limit).all()


def init_groups():
    """Initialize the group tables, and add new columns to existing DBs if needed"""
    db.create_all()
    from sqlalchemy import text
    for col, typedef in [
        ('_image_data', 'TEXT'),
        ('_mood_snapshot', 'VARCHAR(500)')
    ]:
        try:
            db.session.execute(text(f'ALTER TABLE group_messages ADD COLUMN {col} {typedef}'))
            db.session.commit()
        except Exception:
            db.session.rollback()
