"""
Initialize test data for Friends system
Creates users with mood data, friend relationships, and messages for demo purposes
"""

from datetime import datetime, timedelta
import random
import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from __init__ import app, db
from model.user import User
from model.friend import Friend, FriendRequest
from model.private_message import PrivateMessage
from model.moodmeal_mood import MoodMealMood


def create_test_users():
    """Create test users with mood data"""
    test_users = [
        {
            'name': 'Emma Rodriguez',
            'uid': 'emma_r',
            'email': 'emma.r@example.com',
            'password': 'password123',
            'school': 'Del Norte High School',
            'moods': [
                {'score': 75, 'category': 'Happy/Neutral', 'tags': ['relaxed', 'content']},
                {'score': 80, 'category': 'Happy/Neutral', 'tags': ['happy', 'motivated']},
                {'score': 70, 'category': 'Happy/Neutral', 'tags': ['calm', 'peaceful']},
                {'score': 78, 'category': 'Happy/Neutral', 'tags': ['grateful', 'positive']},
            ]
        },
        {
            'name': 'Marcus Chen',
            'uid': 'marcus_c',
            'email': 'marcus.c@example.com',
            'password': 'password123',
            'school': 'Westview High School',
            'moods': [
                {'score': 85, 'category': 'Energetic/Excited', 'tags': ['energetic', 'excited']},
                {'score': 82, 'category': 'Energetic/Excited', 'tags': ['pumped', 'motivated']},
                {'score': 88, 'category': 'Energetic/Excited', 'tags': ['enthusiastic', 'ready']},
                {'score': 80, 'category': 'Happy/Neutral', 'tags': ['good', 'positive']},
            ]
        },
        {
            'name': 'Sophia Kim',
            'uid': 'sophia_k',
            'email': 'sophia.k@example.com',
            'password': 'password123',
            'school': 'Del Norte High School',
            'moods': [
                {'score': 55, 'category': 'Tired/Low Energy', 'tags': ['tired', 'drained']},
                {'score': 58, 'category': 'Tired/Low Energy', 'tags': ['sleepy', 'low-energy']},
                {'score': 52, 'category': 'Tired/Low Energy', 'tags': ['exhausted', 'worn-out']},
                {'score': 60, 'category': 'Tired/Low Energy', 'tags': ['fatigued', 'meh']},
            ]
        },
        {
            'name': 'Jordan Taylor',
            'uid': 'jordan_t',
            'email': 'jordan.t@example.com',
            'password': 'password123',
            'school': 'Poway High School',
            'moods': [
                {'score': 72, 'category': 'Happy/Neutral', 'tags': ['content', 'stable']},
                {'score': 75, 'category': 'Happy/Neutral', 'tags': ['good', 'balanced']},
                {'score': 68, 'category': 'Happy/Neutral', 'tags': ['okay', 'fine']},
                {'score': 70, 'category': 'Happy/Neutral', 'tags': ['neutral', 'steady']},
            ]
        },
        {
            'name': 'Aisha Patel',
            'uid': 'aisha_p',
            'email': 'aisha.p@example.com',
            'password': 'password123',
            'school': 'Rancho Bernardo High School',
            'moods': [
                {'score': 35, 'category': 'Stressed/Anxious', 'tags': ['stressed', 'anxious']},
                {'score': 38, 'category': 'Stressed/Anxious', 'tags': ['worried', 'tense']},
                {'score': 40, 'category': 'Stressed/Anxious', 'tags': ['overwhelmed', 'nervous']},
                {'score': 32, 'category': 'Stressed/Anxious', 'tags': ['anxious', 'uneasy']},
            ]
        },
        {
            'name': 'Ryan Martinez',
            'uid': 'ryan_m',
            'email': 'ryan.m@example.com',
            'password': 'password123',
            'school': 'Mt Carmel High School',
            'moods': [
                {'score': 88, 'category': 'Energetic/Excited', 'tags': ['excited', 'energized']},
                {'score': 90, 'category': 'Energetic/Excited', 'tags': ['hyped', 'pumped']},
                {'score': 85, 'category': 'Energetic/Excited', 'tags': ['enthusiastic', 'lively']},
                {'score': 92, 'category': 'Energetic/Excited', 'tags': ['thrilled', 'ecstatic']},
            ]
        },
        {
            'name': 'Zoe Anderson',
            'uid': 'zoe_a',
            'email': 'zoe.a@example.com',
            'password': 'password123',
            'school': 'Del Norte High School',
            'moods': [
                {'score': 58, 'category': 'Tired/Low Energy', 'tags': ['tired', 'low']},
                {'score': 55, 'category': 'Tired/Low Energy', 'tags': ['drained', 'sluggish']},
                {'score': 60, 'category': 'Tired/Low Energy', 'tags': ['weary', 'worn']},
                {'score': 53, 'category': 'Tired/Low Energy', 'tags': ['exhausted', 'beat']},
            ]
        },
        {
            'name': 'Liam O\'Brien',
            'uid': 'liam_o',
            'email': 'liam.o@example.com',
            'password': 'password123',
            'school': 'Poway High School',
            'moods': [
                {'score': 73, 'category': 'Happy/Neutral', 'tags': ['happy', 'content']},
                {'score': 77, 'category': 'Happy/Neutral', 'tags': ['good', 'positive']},
                {'score': 71, 'category': 'Happy/Neutral', 'tags': ['satisfied', 'pleased']},
                {'score': 75, 'category': 'Happy/Neutral', 'tags': ['cheerful', 'upbeat']},
            ]
        },
    ]

    created_users = []
    for user_data in test_users:
        # Check if user already exists
        existing = User.query.filter_by(_uid=user_data['uid']).first()
        if existing:
            print(f"User {user_data['uid']} already exists, skipping...")
            created_users.append(existing)
            continue

        # Create user
        user = User(
            name=user_data['name'],
            uid=user_data['uid'],
            password=user_data['password'],
            school=user_data['school']
        )

        try:
            user.create()
            # Update email after creation
            user.update({'email': user_data['email']})
            print(f"Created user: {user_data['name']} (@{user_data['uid']})")
            created_users.append(user)

            # Add mood entries
            for i, mood_data in enumerate(user_data['moods']):
                # Create moods over the past week
                timestamp = datetime.utcnow() - timedelta(days=7-i*2, hours=random.randint(0, 23))
                mood = MoodMealMood(
                    user_id=user.id,
                    mood_score=mood_data['score'],
                    mood_tags=mood_data['tags'],
                    mood_category=mood_data['category'],
                    timestamp=timestamp
                )
                mood.create()

            print(f"  Added {len(user_data['moods'])} mood entries")
        except Exception as e:
            print(f"Error creating user {user_data['uid']}: {e}")
            db.session.rollback()

    return created_users


def create_friendships(users):
    """Create friend relationships between users"""
    friendships = [
        ('emma_r', 'marcus_c'),    # Similar happy/energetic moods
        ('emma_r', 'jordan_t'),    # Similar happy/neutral moods
        ('sophia_k', 'zoe_a'),     # Similar tired moods
        ('marcus_c', 'ryan_m'),    # Both energetic
        ('jordan_t', 'liam_o'),    # Similar neutral moods
    ]

    user_map = {user._uid: user for user in users}

    for uid1, uid2 in friendships:
        if uid1 not in user_map or uid2 not in user_map:
            print(f"Skipping friendship {uid1} <-> {uid2} (users not found)")
            continue

        user1 = user_map[uid1]
        user2 = user_map[uid2]

        # Check if friendship already exists
        if Friend.are_friends(user1.id, user2.id):
            print(f"Friendship already exists: {uid1} <-> {uid2}")
            continue

        try:
            friendship = Friend(user1.id, user2.id)
            friendship.create()
            print(f"Created friendship: {user1._name} <-> {user2._name}")
        except Exception as e:
            print(f"Error creating friendship {uid1} <-> {uid2}: {e}")
            db.session.rollback()


def create_friend_requests(users):
    """Create pending friend requests"""
    requests = [
        ('aisha_p', 'emma_r'),     # Aisha wants to connect with Emma
        ('liam_o', 'marcus_c'),    # Liam wants to connect with Marcus
        ('zoe_a', 'jordan_t'),     # Zoe wants to connect with Jordan
    ]

    user_map = {user._uid: user for user in users}

    for sender_uid, receiver_uid in requests:
        if sender_uid not in user_map or receiver_uid not in user_map:
            print(f"Skipping request {sender_uid} -> {receiver_uid} (users not found)")
            continue

        sender = user_map[sender_uid]
        receiver = user_map[receiver_uid]

        # Check if request already exists or they're already friends
        if Friend.are_friends(sender.id, receiver.id):
            print(f"Already friends: {sender_uid} & {receiver_uid}")
            continue

        if FriendRequest.has_pending_request(sender.id, receiver.id):
            print(f"Request already exists: {sender_uid} -> {receiver_uid}")
            continue

        try:
            request = FriendRequest(sender.id, receiver.id)
            request.create()
            print(f"Created friend request: {sender._name} -> {receiver._name}")
        except Exception as e:
            print(f"Error creating request {sender_uid} -> {receiver_uid}: {e}")
            db.session.rollback()


def create_messages(users):
    """Create sample messages between friends"""
    messages = [
        # Emma & Marcus conversation
        ('emma_r', 'marcus_c', "Hey Marcus! How's it going?", 2),
        ('marcus_c', 'emma_r', "Hey Emma! I'm doing great, feeling super energized today!", 2),
        ('emma_r', 'marcus_c', "That's awesome! Want to study together later?", 1),

        # Sophia & Zoe conversation
        ('sophia_k', 'zoe_a', "Ugh, I'm so tired today...", 3),
        ('zoe_a', 'sophia_k', "Same here! This week has been exhausting", 3),
        ('sophia_k', 'zoe_a', "Want to grab coffee? I need some energy", 2),
        ('zoe_a', 'sophia_k', "Yes please! Meet at Starbucks in 30?", 1),

        # Marcus & Ryan conversation
        ('marcus_c', 'ryan_m', "Dude! Ready for the game tonight?", 2),
        ('ryan_m', 'marcus_c', "SO PUMPED! Let's goooo!", 2),

        # Jordan & Liam conversation
        ('jordan_t', 'liam_o', "Hey, did you finish the homework?", 1),
        ('liam_o', 'jordan_t', "Yeah, just finished. It wasn't too bad", 1),
    ]

    user_map = {user._uid: user for user in users}

    for sender_uid, receiver_uid, content, days_ago in messages:
        if sender_uid not in user_map or receiver_uid not in user_map:
            continue

        sender = user_map[sender_uid]
        receiver = user_map[receiver_uid]

        # Only create message if they're friends
        if not Friend.are_friends(sender.id, receiver.id):
            print(f"Skipping message {sender_uid} -> {receiver_uid} (not friends)")
            continue

        try:
            timestamp = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(0, 23))
            message = PrivateMessage(
                sender_id=sender.id,
                receiver_id=receiver.id,
                content=content
            )
            message.create()
            # Manually set the timestamp
            message._created_at = timestamp
            db.session.commit()
        except Exception as e:
            print(f"Error creating message: {e}")
            db.session.rollback()

    print(f"Created {len([m for m in messages if m[0] in user_map and m[1] in user_map])} messages")


def main():
    """Main function to initialize all test data"""
    with app.app_context():
        print("=" * 60)
        print("Initializing Friends System Test Data")
        print("=" * 60)

        print("\n1. Creating test users with mood data...")
        users = create_test_users()

        print("\n2. Creating friendships...")
        create_friendships(users)

        print("\n3. Creating friend requests...")
        create_friend_requests(users)

        print("\n4. Creating messages...")
        create_messages(users)

        print("\n" + "=" * 60)
        print("✅ Friends system test data initialization complete!")
        print("=" * 60)
        print("\nTest Users Created:")
        for user in users:
            print(f"  - {user._name} (@{user._uid}) - {user._school}")
        print("\nYou can now log in with any of these accounts using:")
        print("  Username: Any uid from above (e.g., 'emma_r')")
        print("  Password: password123")


if __name__ == "__main__":
    main()
