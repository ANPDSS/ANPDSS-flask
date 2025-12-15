# api/moodmeal_gemini.py

import os
import json

from flask import g
from dotenv import load_dotenv

from model.moodmeal_mood import MoodMealMood
from model.moodmeal_preferences import MoodMealPreferences

import google.generativeai as genai

# Load .env once
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def get_latest_mood_for_user(user_id: int) -> dict | None:
    """
    Returns the most recent mood entry as a dict using MoodMealMood.read().
    """
    mood = (
        MoodMealMood.query
        .filter_by(_user_id=user_id)
        .order_by(MoodMealMood._timestamp.desc())
        .first()
    )
    return mood.read() if mood else None


def get_mood_by_id_for_user(user_id: int, mood_id: int) -> dict | None:
    """
    Returns a specific mood entry for this user, or None.
    """
    mood = MoodMealMood.query.filter_by(id=mood_id, _user_id=user_id).first()
    return mood.read() if mood else None


def get_preferences_for_user(user) -> dict:
    """
    Returns preferences JSON for the authenticated user.
    Always returns a plain dict (never jsonify).
    """
    prefs = MoodMealPreferences.query.filter_by(_user_id=user.id).first()
    if not prefs:
        # match PreferencesAPI default structure
        return {
            "user_id": user.id,
            "dietary": [],
            "allergies": [],
            "cuisines": [],
            "music": [],
            "activities": []
        }
    return prefs.read()


def build_gemini_prompt(mood: dict, preferences: dict) -> str:
    """
    Converts DB mood + preferences into a Gemini-ready prompt.
    Forces JSON-only output so we can parse reliably.
    """

    mood_score = mood.get("mood_score")
    mood_category = mood.get("mood_category") or "Unknown"
    mood_tags = mood.get("mood_tags") or []

    dietary = preferences.get("dietary") or []
    allergies = preferences.get("allergies") or []
    cuisines = preferences.get("cuisines") or []
    music = preferences.get("music") or []
    activities = preferences.get("activities") or []

    return f"""
You are MoodMeal. Generate recommendations using the user's mood + preferences.

User mood:
- mood_score: {mood_score}
- mood_category: {mood_category}
- mood_tags: {mood_tags}

User preferences:
- dietary: {dietary}
- allergies: {allergies}
- cuisines: {cuisines}
- music: {music}
- activities: {activities}

Return ONLY valid JSON, no markdown, no explanation.

Schema:
{{
  "meals": [
    {{
      "title": "string",
      "why": "string",
      "time_minutes": 0,
      "difficulty": "easy|medium|hard"
    }}
  ],
  "activities": [
    {{
      "name": "string",
      "why": "string",
      "energy": "low|medium|high"
    }}
  ],
  "music": [
    {{
      "song": "string",
      "artist": "string",
      "why": "string"
    }}
  ]
}}
"""


def call_gemini_and_parse(prompt: str) -> dict:
    """
    Calls Gemini and parses JSON output.
    Uses the newer google-genai client and a current model ID.
    """
    import json
    import os
    from google import genai

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing. Check your .env and load_dotenv().")

    # Use stable API behavior by using the new client
    client = genai.Client(api_key=api_key)

    # Use a current model id from Gemini docs
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    text = (response.text or "").strip()

    # Parse JSON safely
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise RuntimeError(f"Gemini did not return JSON. Raw output:\n{text}")
        return json.loads(text[start:end+1])



def generate_moodmeal_plan(user_id: int, mood_id: int | None = None) -> dict:
    """
    If mood_id is provided, use that mood entry.
    Otherwise use the latest mood entry for the user.

    Returns a plain dict (JSON-serializable), never a Flask Response.
    """

    # pick mood
    if mood_id is not None:
        mood = get_mood_by_id_for_user(user_id, mood_id)
    else:
        mood = get_latest_mood_for_user(user_id)

    if mood is None:
        # return JSON-serializable error object (your API can choose status code)
        return {
            "message": "No mood found. POST /api/moodmeal/mood first.",
            "user_id": user_id
        }

    prefs = get_preferences_for_user(g.current_user)

    prompt = build_gemini_prompt(mood, prefs)
    generated = call_gemini_and_parse(prompt)

    return {
        "user_id": user_id,
        "mood_used": mood,
        "preferences_used": prefs,
        "generated": generated
    }
