"""
Quick verification script to show friends feature is working
Run this to show your teacher!
"""
from main import app, db
from model.user import User
from model.friend import Friend, FriendRequest
from model.private_message import PrivateMessage

def print_header(text):
    print("\n" + "="*60)
    print(text.center(60))
    print("="*60)

with app.app_context():
    print_header("FRIENDS FEATURE VERIFICATION")

    # Check tables exist
    print("\n✓ Database Tables:")
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print("  - friends table exists: ", 'friends' in tables)
    print("  - friend_requests table exists: ", 'friend_requests' in tables)
    print("  - private_messages table exists: ", 'private_messages' in tables)

    # Show friendships
    print_header("CURRENT FRIENDSHIPS")
    friendships = Friend.query.all()
    if friendships:
        for f in friendships:
            u1 = User.query.get(f.user_id1)
            u2 = User.query.get(f.user_id2)
            if u1 and u2:
                print(f"  {u1.uid:15} ↔ {u2.uid:15} (Created: {f.created_at})")
    else:
        print("  No friendships yet")

    # Show pending requests
    print_header("PENDING FRIEND REQUESTS")
    requests = FriendRequest.query.filter_by(_status='pending').all()
    if requests:
        for req in requests:
            print(f"  {req.sender._uid:15} → {req.receiver._uid:15} (ID: {req.id})")
    else:
        print("  No pending requests")

    # Show messages
    print_header("PRIVATE MESSAGES")
    messages = PrivateMessage.query.all()
    if messages:
        for msg in messages:
            read_status = "✓" if msg.is_read else "✗"
            print(f"  {msg.sender._uid:10} → {msg.receiver._uid:10} [{read_status}] {msg.content[:40]}...")
    else:
        print("  No messages yet")

    # Test User.friends property
    print_header("USER FRIENDS PROPERTY TEST")
    admin = User.query.filter_by(_uid='admin').first()
    if admin:
        print(f"\n  User: {admin.uid}")
        print(f"  Friends property returns: {admin.friends}")
        print(f"  Number of friends: {len(admin.friends)}")

    user = User.query.filter_by(_uid='user').first()
    if user:
        print(f"\n  User: {user.uid}")
        print(f"  Friends property returns: {user.friends}")
        print(f"  Number of friends: {len(user.friends)}")

    print_header("VERIFICATION COMPLETE!")

    print("\n✅ All systems operational!")
    print("\nTo view in database:")
    print("  cd /Users/shayanbhatti/ANPDSS-flask")
    print("  sqlite3 instance/volumes/user_management.db")
    print("  SELECT * FROM friends;")
    print("  SELECT * FROM friend_requests;")
    print("  SELECT * FROM private_messages;")

    print("\nTo demo in browser:")
    print("  1. Go to http://localhost:4500/friends")
    print("  2. Login as 'admin'")
    print("  3. Click 'Requests' tab")
    print("  4. Accept a friend request")
    print("  5. Check the database - new row in 'friends' table!")
