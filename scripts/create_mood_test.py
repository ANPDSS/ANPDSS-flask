#!/usr/bin/env python3
import requests
import os

BASE = os.environ.get('BASE_URL', 'http://127.0.0.1:8587')
AUTH_URL = f"{BASE}/api/authenticate"
MOOD_URL = f"{BASE}/api/moodmeal/mood"

session = requests.Session()

print('Authenticating testuser...')
resp = session.post(AUTH_URL, json={'uid': 'testuser', 'password': '123456'})
print('Auth status:', resp.status_code)
try:
    print('Auth response:', resp.json())
except Exception:
    print('Auth response not JSON:', resp.text)

if resp.status_code not in (200, 201):
    print('Authentication failed; aborting')
    raise SystemExit(1)

mood_payload = {
    'mood_score': 75,
    'mood_tags': ['energetic', 'focused'],
    'mood_category': 'productive'
}

print('Posting mood entry...')
resp2 = session.post(MOOD_URL, json=mood_payload)
print('Mood POST status:', resp2.status_code)
try:
    print('Mood POST response:', resp2.json())
except Exception:
    print('Mood POST response not JSON:', resp2.text)

# Print location of mood if returned
if resp2.status_code in (200, 201):
    print('Done')
else:
    print('Failed to create mood entry')
