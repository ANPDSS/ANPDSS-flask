# Friends System Demo Guide

This guide helps you demonstrate the Friends system features with predefined test data.

## Quick Start

1. **Initialize test data** (if not already done):
   ```bash
   python scripts/init_friends_data.py
   ```

2. **Start the backend** on port 8302:
   ```bash
   python main.py
   ```

3. **Log in to the frontend** with any test account:
   - Username: `emma_r` (or any other test user)
   - Password: `password123`

## Test Accounts & Features to Demo

### 1. Emma Rodriguez (@emma_r)
**Best for demonstrating:**
- ✅ **Existing Friendships** - Has 2 friends (Marcus, Jordan)
- ✅ **Messaging** - Has active conversations
- ✅ **Friend Requests** - Has 1 pending request from Aisha
- ✅ **Recommendations** - Will see mood-based recommendations

**Demo Flow:**
1. Log in as Emma
2. Go to Friends page (`/friends`)
3. Check "My Friends" tab - shows Marcus and Jordan
4. Check "Requests" tab - see request from Aisha
5. Check "Messages" tab - view conversations
6. Try sending a message to Marcus or Jordan
7. Check "Recommendations" - see users with similar mood scores

### 2. Marcus Chen (@marcus_c)
**Best for demonstrating:**
- ✅ **High Energy Mood** - Energetic/Excited mood category (85-90 score)
- ✅ **Mood-Based Matching** - Will be recommended to Ryan (similar energy)
- ✅ **Friend Requests** - Has 1 pending request from Liam
- ✅ **Active Messages** - Has conversations with Emma and Ryan

**Demo Flow:**
1. Log in as Marcus
2. Check "Recommendations" - Ryan should appear with high match % (similar energy levels)
3. Check "Requests" - see request from Liam, accept it
4. Check "Messages" - view/send messages

### 3. Sophia Kim (@sophia_k) & Zoe Anderson (@zoe_a)
**Best for demonstrating:**
- ✅ **Low Energy Mood Matching** - Both have Tired/Low Energy moods (52-60 score)
- ✅ **Mood Similarity** - They are friends because of similar mood patterns
- ✅ **Empathy Messages** - Their messages reflect their tired state

**Demo Flow:**
1. Log in as Sophia
2. Check "My Friends" - see Zoe (matched due to similar tired moods)
3. Check "Messages" - see their conversation about being tired
4. Check "Recommendations" - should see other low-energy users

### 4. Aisha Patel (@aisha_p)
**Best for demonstrating:**
- ✅ **Stressed/Anxious Mood** - Shows the lowest mood category (32-40 score)
- ✅ **Pending Request** - Has sent a request to Emma
- ✅ **Finding Support** - Will see recommendations for users who might understand

**Demo Flow:**
1. Log in as Aisha
2. Check "Requests" - see her sent request to Emma
3. Check "Recommendations" - see who she might connect with
4. Note her mood data reflects stress/anxiety

## Key Features to Highlight

### 🎭 Mood-Based Friend Matching
- The system now matches friends based on **similar mood patterns**, not interests
- Users with similar:
  - **Mood scores** (60% weight) - e.g., both around 75/100
  - **Mood categories** (40% weight) - e.g., both "Happy/Neutral"
- Examples:
  - Emma (75) matches Jordan (70) - both Happy/Neutral
  - Marcus (85) matches Ryan (88) - both Energetic/Excited
  - Sophia (55) matches Zoe (58) - both Tired/Low Energy

### 💬 Messaging System
- Friends can send direct messages
- Message history is preserved
- Conversations show in the Messages tab
- Each message shows timestamp
- Can click to view full conversation

### 🤝 Friend Requests
- Send requests to recommended users or search results
- Receive requests from others
- Accept or reject requests
- Cancel sent requests
- Requests are pending until accepted/rejected

### 🔍 Search & Recommendations
- **Recommendations tab**: Shows users with similar moods
- **Search tab**: Find users by name, username, or school
- **Match scores**: See % compatibility based on mood patterns

## Mood Categories Explained

| Mood Score | Category | Example Users |
|-----------|----------|---------------|
| 0-40 | Stressed/Anxious | Aisha Patel (32-40) |
| 41-60 | Tired/Low Energy | Sophia Kim, Zoe Anderson (52-60) |
| 61-80 | Happy/Neutral | Emma, Jordan, Liam (68-77) |
| 81-100 | Energetic/Excited | Marcus, Ryan (82-92) |

## Test Data Summary

- **8 test users** with diverse mood patterns
- **32 mood entries** (4 per user, spanning past week)
- **5 existing friendships** between mood-compatible users
- **3 pending friend requests**
- **11 messages** across different conversations

## Frontend URL

Navigate to: **`/friends`** on your frontend site

The navigation bar should now be visible at the top (fixed issue).

## Troubleshooting

### Messages not showing?
- Make sure you're logged in as a user who has friends
- Check that the backend is running on port 8302
- Try Emma or Marcus who have active message threads

### Recommendations empty?
- User needs mood data to get recommendations
- All test users have mood data, so this should work
- If empty, try logging in with a different test user

### Navigation bar hidden?
- This has been fixed - the page now has `padding-top: 100px` to account for the fixed nav bar
- Both Friends and Messages pages have been updated

## Re-running the Script

The initialization script is safe to re-run:
```bash
python scripts/init_friends_data.py
```

It will:
- Skip users that already exist
- Skip friendships that already exist
- Skip friend requests that already exist
- Create new messages (so run once only, or clear messages first)
