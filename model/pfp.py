"""
==============================================================================
PROFILE PICTURE (PFP) MODEL & HELPER FUNCTIONS - model/pfp.py
==============================================================================

Programming Constructs:
- Sequencing: Code executes in order through CRUD operations
- Selection: if/else for validation and conditional database operations
- Iteration: Loops for batch operations and data validation
- Lists: Arrays storing valid image types and user IDs for bulk operations

This file handles profile pictures using BASE64 stored directly in the DATABASE.

=== WHERE IS THE DATA STORED? ===

DATABASE (user_management.db):
├── Table: "pfps" (NEW TABLE - stores the actual base64 image data)
│   ├── id (INTEGER PRIMARY KEY)
│   ├── _user_id (INTEGER FOREIGN KEY → users.id)
│   └── _base64_data (TEXT - stores the full base64 string)
│
└── Table: "users" (existing table)
    └── _pfp column is NO LONGER USED for base64 storage

=== FLOW DIAGRAM ===

UPLOAD (Frontend → Database):
┌──────────┐    base64 string    ┌───────────┐    calls    ┌─────────────┐
│ Frontend │ ──────────────────► │ api/pfp.py│ ──────────► │ model/pfp.py│
└──────────┘   PUT /api/id/pfp   └───────────┘             └─────────────┘
                                                                  │
                                                                  ▼
                                                    ┌─────────────────────────┐
                                                    │  ProfilePicture.save()  │
                                                    │  Stores base64 in DB    │
                                                    └─────────────────────────┘
                                                                  │
                                                                  ▼
                                                    ┌─────────────────────────┐
                                                    │   user_management.db    │
                                                    │   Table: pfps           │
                                                    │   _base64_data = "..."  │
                                                    └─────────────────────────┘

RETRIEVE (Database → Frontend):
┌──────────┐   base64 string    ┌───────────┐    calls    ┌─────────────┐
│ Frontend │ ◄───────────────── │ api/pfp.py│ ◄────────── │ model/pfp.py│
└──────────┘  GET /api/id/pfp   └───────────┘             └─────────────┘
                                                                  │
                                                                  ▼
                                                    ┌─────────────────────────┐
                                                    │ ProfilePicture.get_by   │
                                                    │ _user_id()              │
                                                    │ Returns base64 from DB  │
                                                    └─────────────────────────┘

==============================================================================
"""

from __init__ import db, app
from sqlalchemy.exc import IntegrityError

# List: Valid image format prefixes for base64 validation
VALID_IMAGE_PREFIXES = ['/9j/', 'iVBORw0KGgo', 'R0lGOD', 'UklGR']

# List: Maximum allowed sizes (in characters) for different image types
IMAGE_SIZE_LIMITS = [
    {'type': 'thumbnail', 'max_chars': 50000},
    {'type': 'small', 'max_chars': 200000},
    {'type': 'medium', 'max_chars': 500000},
    {'type': 'large', 'max_chars': 1000000}
]


def validate_base64_image(base64_data: str) -> dict:
    """
    Validate base64 image data format and size.
    Demonstrates iteration through lists with selection.
    """
    result = {'valid': False, 'format': None, 'size_category': None}

    # Iteration: Check image format by looping through valid prefixes
    for prefix in VALID_IMAGE_PREFIXES:
        # Selection: Check if data starts with valid prefix
        if base64_data.startswith(prefix):
            result['valid'] = True
            result['format'] = prefix
            break

    # Selection: Only check size if format is valid
    if result['valid']:
        data_length = len(base64_data)
        # Iteration: Determine size category
        for size_limit in IMAGE_SIZE_LIMITS:
            if data_length <= size_limit['max_chars']:
                result['size_category'] = size_limit['type']
                break

    return result


def get_pfps_for_user_ids(user_ids: list) -> dict:
    """
    Get profile pictures for multiple users at once.
    Demonstrates iteration for batch database operations.
    """
    pfp_map = {}

    # Iteration: Loop through each user ID
    for user_id in user_ids:
        # Selection: Check if user_id is valid
        if user_id and isinstance(user_id, int):
            pfp = ProfilePicture.query.filter_by(_user_id=user_id).first()
            if pfp:
                pfp_map[user_id] = pfp.base64_data
            else:
                pfp_map[user_id] = None

    return pfp_map


class ProfilePicture(db.Model):
    """
    ===========================================================================
    ProfilePicture Model - Stores base64 image data directly in the database
    ===========================================================================

    TABLE NAME: pfps

    This table stores profile pictures as base64 encoded strings.
    Each user can have ONE profile picture (one-to-one relationship with users).

    COLUMNS:
    - id: Primary key
    - _user_id: Foreign key to users table (UNIQUE - one pfp per user)
    - _base64_data: The actual base64 encoded image string (can be very large)

    ===========================================================================
    """
    __tablename__ = 'pfps'

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Foreign key to users table - UNIQUE ensures one PFP per user
    _user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)

    # The base64 encoded image data - stored as TEXT (can hold large strings)
    # Example: "iVBORw0KGgoAAAANSUhEUgAA..." (can be 100,000+ characters)
    _base64_data = db.Column(db.Text, nullable=False)

    # Relationship to User model
    user = db.relationship('User', backref=db.backref('profile_picture', uselist=False))

    def __init__(self, user_id, base64_data):
        """
        Create a new ProfilePicture record.

        Parameters:
        - user_id (int): The user's database ID
        - base64_data (str): The base64 encoded image string
        """
        self._user_id = user_id
        self._base64_data = base64_data

    # ===== PROPERTIES =====

    @property
    def user_id(self):
        return self._user_id

    @property
    def base64_data(self):
        return self._base64_data

    @base64_data.setter
    def base64_data(self, value):
        self._base64_data = value

    # ===== CRUD OPERATIONS =====

    def create(self):
        """Save this profile picture to the database."""
        try:
            db.session.add(self)
            db.session.commit()
            return self
        except IntegrityError:
            db.session.rollback()
            return None
        except Exception as e:
            db.session.rollback()
            print(f"Error creating profile picture: {e}")
            return None

    def update(self, base64_data):
        """Update the base64 data for this profile picture."""
        try:
            self._base64_data = base64_data
            db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            print(f"Error updating profile picture: {e}")
            return None

    def delete(self):
        """Delete this profile picture from the database."""
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting profile picture: {e}")
            return False

    def read(self):
        """Return profile picture data as a dictionary."""
        return {
            'id': self.id,
            'user_id': self._user_id,
            'base64_data': self._base64_data
        }

    # ===== STATIC METHODS FOR QUERIES =====

    @staticmethod
    def get_by_user_id(user_id):
        """
        Get a profile picture by user ID.

        Parameters:
        - user_id (int): The user's database ID

        Returns:
        - ProfilePicture object or None
        """
        return ProfilePicture.query.filter_by(_user_id=user_id).first()

    @staticmethod
    def save_for_user(user_id, base64_data):
        """
        Save or update a profile picture for a user.
        If user already has a PFP, update it. Otherwise, create new.

        Parameters:
        - user_id (int): The user's database ID
        - base64_data (str): The base64 encoded image string

        Returns:
        - ProfilePicture object or None on error
        """
        existing = ProfilePicture.get_by_user_id(user_id)

        if existing:
            # Update existing PFP
            return existing.update(base64_data)
        else:
            # Create new PFP
            new_pfp = ProfilePicture(user_id, base64_data)
            return new_pfp.create()

    @staticmethod
    def delete_for_user(user_id):
        """
        Delete a user's profile picture.

        Parameters:
        - user_id (int): The user's database ID

        Returns:
        - True if deleted, False if not found or error
        """
        existing = ProfilePicture.get_by_user_id(user_id)
        if existing:
            return existing.delete()
        return False


# ==============================================================================
# HELPER FUNCTIONS (for backwards compatibility with api/pfp.py)
# ==============================================================================

def pfp_base64_decode(user_uid, user_pfp=None):
    """
    ===========================================================================
    GET BASE64 FROM DATABASE (for sending to frontend)
    ===========================================================================

    Retrieves the base64 encoded profile picture from the database.

    Parameters:
    - user_uid (str): The user's UID (username)
    - user_pfp: IGNORED (kept for backwards compatibility)

    Returns:
    - str: The base64 encoded image string
    - None: If user has no profile picture

    CALLED BY:
    - api/pfp.py → GET /api/id/pfp
    - api/friend_api.py → when including pfp in friend data
    ===========================================================================
    """
    from model.user import User

    # Find the user by UID
    user = User.query.filter_by(_uid=user_uid).first()
    if not user:
        print(f"User not found: {user_uid}")
        return None

    # Get their profile picture from the database
    pfp = ProfilePicture.get_by_user_id(user.id)
    if pfp:
        return pfp.base64_data

    return None


def pfp_base64_upload(base64_image, user_uid):
    """
    ===========================================================================
    SAVE BASE64 TO DATABASE (from frontend upload)
    ===========================================================================

    Saves the base64 encoded profile picture to the database.

    Parameters:
    - base64_image (str): The base64 encoded image string from frontend
    - user_uid (str): The user's UID (username)

    Returns:
    - str: A success indicator (the user_uid) - for backwards compatibility
    - None: If an error occurs

    CALLED BY:
    - api/pfp.py → PUT /api/id/pfp
    ===========================================================================
    """
    from model.user import User

    # Find the user by UID
    user = User.query.filter_by(_uid=user_uid).first()
    if not user:
        print(f"User not found: {user_uid}")
        return None

    # Save to database
    result = ProfilePicture.save_for_user(user.id, base64_image)
    if result:
        # Also update the user's pfp field for backwards compatibility
        user.pfp = f"{user_uid}.png"
        db.session.commit()
        return f"{user_uid}.png"

    return None


def pfp_file_delete(user_uid, filename=None):
    """
    ===========================================================================
    DELETE BASE64 FROM DATABASE
    ===========================================================================

    Deletes the profile picture from the database.

    Parameters:
    - user_uid (str): The user's UID (username)
    - filename: IGNORED (kept for backwards compatibility)

    Returns:
    - True: Successfully deleted
    - False: Error or not found

    CALLED BY:
    - api/pfp.py → DELETE /api/id/pfp
    ===========================================================================
    """
    from model.user import User

    # Find the user by UID
    user = User.query.filter_by(_uid=user_uid).first()
    if not user:
        print(f"User not found: {user_uid}")
        return False

    # Delete from database
    return ProfilePicture.delete_for_user(user.id)


# ==============================================================================
# INITIALIZE TABLE
# ==============================================================================

def init_pfp_table():
    """
    Create the pfps table in the database if it doesn't exist.
    Call this once when setting up the application.
    """
    with app.app_context():
        db.create_all()
        print("ProfilePicture table (pfps) created/verified.")


"""
==============================================================================
SUMMARY: DATABASE STORAGE
==============================================================================

TABLE: pfps (in user_management.db)
┌────────────────┬─────────────────┬────────────────────────────────────────┐
│ Column         │ Type            │ Description                            │
├────────────────┼─────────────────┼────────────────────────────────────────┤
│ id             │ INTEGER (PK)    │ Primary key                            │
│ _user_id       │ INTEGER (FK)    │ Foreign key to users.id (UNIQUE)       │
│ _base64_data   │ TEXT            │ The base64 encoded image string        │
└────────────────┴─────────────────┴────────────────────────────────────────┘

EXAMPLE DATA:
┌────┬──────────┬─────────────────────────────────────────────────────────┐
│ id │ _user_id │ _base64_data                                            │
├────┼──────────┼─────────────────────────────────────────────────────────┤
│ 1  │ 1        │ iVBORw0KGgoAAAANSUhEUgAAA... (thousands of characters) │
│ 2  │ 5        │ /9j/4AAQSkZJRgABAQEASABIA... (thousands of characters) │
└────┴──────────┴─────────────────────────────────────────────────────────┘

==============================================================================
"""
