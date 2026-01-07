"""
Test script to set up friend relationships for demonstration
"""
from main import app, db
from model.user import User
from model.friend import Friend, FriendRequest
from model.moodmeal_preferences import MoodMealPreferences

with app.app_context():
    print("Setting up test friend data...\n")

    # Get test users
    user1 = User.query.filter_by(_uid='admin').first()
    user2 = User.query.filter_by(_uid='user').first()
    user3 = User.query.filter_by(_uid='niko').first()
    user4 = User.query.filter_by(_uid='demo123').first()

    if not all([user1, user2, user3, user4]):
        print("Error: Not all test users found")
        exit(1)

    print(f"Found users:")
    print(f"  - {user1.uid} (ID: {user1.id})")
    print(f"  - {user2.uid} (ID: {user2.id})")
    print(f"  - {user3.uid} (ID: {user3.id})")
    print(f"  - {user4.uid} (ID: {user4.id})")
    print()

    # Add some interests for better recommendations
    print("Adding interests for users...")

    # Admin interests
    prefs1 = MoodMealPreferences.query.filter_by(_user_id=user1.id).first()
    if not prefs1:
        prefs1 = MoodMealPreferences(
            user_id=user1.id,
            cuisines=['Italian', 'Japanese', 'Mexican'],
            music=['Rock', 'Jazz', 'Classical'],
            activities=['Reading', 'Coding', 'Gaming']
        )
        prefs1.create()
        print(f"  ✓ Created interests for {user1.uid}")

    # User interests (similar to admin)
    prefs2 = MoodMealPreferences.query.filter_by(_user_id=user2.id).first()
    if not prefs2:
        prefs2 = MoodMealPreferences(
            user_id=user2.id,
            cuisines=['Italian', 'Japanese', 'Chinese'],
            music=['Rock', 'Pop', 'Jazz'],
            activities=['Reading', 'Gaming', 'Sports']
        )
        prefs2.create()
        print(f"  ✓ Created interests for {user2.uid}")

    # Niko interests (different)
    prefs3 = MoodMealPreferences.query.filter_by(_user_id=user3.id).first()
    if not prefs3:
        prefs3 = MoodMealPreferences(
            user_id=user3.id,
            cuisines=['French', 'Italian', 'Thai'],
            music=['Classical', 'Electronic', 'Jazz'],
            activities=['Coding', 'Hiking', 'Photography']
        )
        prefs3.create()
        print(f"  ✓ Created interests for {user3.uid}")

    # Demo interests
    prefs4 = MoodMealPreferences.query.filter_by(_user_id=user4.id).first()
    if not prefs4:
        prefs4 = MoodMealPreferences(
            user_id=user4.id,
            cuisines=['Mexican', 'Japanese', 'Thai'],
            music=['Pop', 'Rock', 'Hip Hop'],
            activities=['Gaming', 'Sports', 'Music']
        )
        prefs4.create()
        print(f"  ✓ Created interests for {user4.uid}")

    print()

    # Create some friend requests
    print("Creating friend requests...")

    # User -> Admin (pending)
    req1 = FriendRequest.query.filter_by(_sender_id=user2.id, _receiver_id=user1.id).first()
    if not req1:
        req1 = FriendRequest(user2.id, user1.id)
        req1.create()
        print(f"  ✓ {user2.uid} → {user1.uid} (pending)")
    else:
        print(f"  - {user2.uid} → {user1.uid} (already exists)")

    # Niko -> Admin (pending)
    req2 = FriendRequest.query.filter_by(_sender_id=user3.id, _receiver_id=user1.id).first()
    if not req2:
        req2 = FriendRequest(user3.id, user1.id)
        req2.create()
        print(f"  ✓ {user3.uid} → {user1.uid} (pending)")
    else:
        print(f"  - {user3.uid} → {user1.uid} (already exists)")

    # Create an accepted friendship (Demo and User are already friends)
    print("\nCreating friendships...")

    if not Friend.are_friends(user2.id, user4.id):
        friendship = Friend(user2.id, user4.id)
        friendship.create()
        print(f"  ✓ {user2.uid} ↔ {user4.uid} (friends)")
    else:
        print(f"  - {user2.uid} ↔ {user4.uid} (already friends)")

    print("\n" + "="*50)
    print("TEST DATA SETUP COMPLETE!")
    print("="*50)

    # Show current state
    print("\nCurrent Friend Requests:")
    all_requests = FriendRequest.query.filter_by(_status='pending').all()
    for req in all_requests:
        print(f"  {req.sender._uid} → {req.receiver._uid} (Status: {req.status})")

    print("\nCurrent Friendships:")
    all_friends = Friend.query.all()
    for f in all_friends:
        u1 = User.query.get(f.user_id1)
        u2 = User.query.get(f.user_id2)
        if u1 and u2:
            print(f"  {u1.uid} ↔ {u2.uid}")

    print("\n" + "="*50)
    print("You can now test the Friends feature!")
    print("="*50)
    print(f"\n1. Login as '{user1.uid}' and check the 'Requests' tab")
    print(f"2. You should see friend requests from {user2.uid} and {user3.uid}")
    print(f"3. Accept them to create friendships!")
    print(f"4. Check 'My Friends' tab to see your friends list")
    print(f"\n5. To see the data in the database:")
    print(f"   sqlite3 instance/volumes/user_management.db")
    print(f"   SELECT * FROM friends;")
    print(f"   SELECT * FROM friend_requests;")
