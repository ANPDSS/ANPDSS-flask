# Friends System Test Data Initialization

This script creates predefined test data for demonstrating the Friends system features including:
- Test users with mood data
- Friend relationships
- Pending friend requests
- Sample messages between friends

## How to Run

From the root of the ANPDSS-flask directory:

```bash
python scripts/init_friends_data.py
```

## Test Users Created

The script creates 8 test users with different mood patterns:

1. **Emma Rodriguez** (@emma_r) - Happy/Neutral mood (75-80 score)
   - School: Del Norte High School
   - Friends with: Marcus, Jordan

2. **Marcus Chen** (@marcus_c) - Energetic/Excited (82-88 score)
   - School: Westview High School
   - Friends with: Emma, Ryan

3. **Sophia Kim** (@sophia_k) - Tired/Low Energy (52-60 score)
   - School: Del Norte High School
   - Friends with: Zoe

4. **Jordan Taylor** (@jordan_t) - Happy/Neutral (68-75 score)
   - School: Poway High School
   - Friends with: Emma, Liam

5. **Aisha Patel** (@aisha_p) - Stressed/Anxious (32-40 score)
   - School: Rancho Bernardo High School
   - Has pending request to: Emma

6. **Ryan Martinez** (@ryan_m) - Energetic/Excited (85-92 score)
   - School: Mt Carmel High School
   - Friends with: Marcus

7. **Zoe Anderson** (@zoe_a) - Tired/Low Energy (53-60 score)
   - School: Del Norte High School
   - Friends with: Sophia
   - Has pending request to: Jordan

8. **Liam O'Brien** (@liam_o) - Happy/Neutral (71-77 score)
   - School: Poway High School
   - Friends with: Jordan
   - Has pending request to: Marcus

## Login Credentials

All test users have the same password: **password123**

Example logins:
- Username: `emma_r` Password: `password123`
- Username: `marcus_c` Password: `password123`
- etc.

## Features Demonstrated

### Friend Recommendations (Mood-Based Matching)
- Users with similar mood patterns will appear as recommendations
- Emma and Jordan both have Happy/Neutral moods (~70-75)
- Marcus and Ryan both have Energetic/Excited moods (~85-90)
- Sophia and Zoe both have Tired/Low Energy moods (~55-60)

### Friend Relationships
- 5 established friendships between users with similar moods
- Messages between friends demonstrate the messaging feature

### Friend Requests
- 3 pending friend requests to demonstrate the request system
- Can accept/reject requests to see the workflow

### Messages
- Sample conversations between friends
- Different message timestamps (1-3 days ago)
- Demonstrates both read and unread messages

## What Gets Created

- **8 test users** with diverse mood patterns
- **~32 mood entries** (4 per user over the past week)
- **5 friendships** between compatible users
- **3 pending friend requests**
- **11 messages** across different conversations

## Notes

- The script checks for existing users before creating duplicates
- Mood entries are timestamped over the past week
- Messages are timestamped 1-3 days ago for realism
- All data is safe to re-run (won't create duplicates)
