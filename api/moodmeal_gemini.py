# api/moodmeal_gemini.py

import os
import json

from flask import g
from dotenv import load_dotenv

from model.moodmeal_mood import MoodMealMood
from model.moodmeal_preferences import MoodMealPreferences

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


def build_gemini_prompt(mood: dict, preferences: dict, weather: dict | None = None) -> str:
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
    # Normalize a short weather summary for the prompt
    if weather:
        # Try common OpenWeather keys if present
        w_main = weather.get('weather') or weather.get('weather_main')
        if isinstance(w_main, list) and w_main:
            w_main = w_main[0].get('main') or w_main[0].get('description')
        temp = None
        if weather.get('main') and isinstance(weather.get('main'), dict):
            temp = weather['main'].get('temp')
        # fallback keys
        temp = temp or weather.get('temp') or weather.get('temperature')
        weather_summary = f"condition: {w_main}, temp: {temp}"
    else:
        weather_summary = "Unknown"

    # Build the prompt header with variable values (always executed)
    header = (
        "You are MoodMeal. Generate recommendations using the user's mood + preferences.\n\n"
        f"User mood:\n- mood_score: {mood_score}\n- mood_category: {mood_category}\n- mood_tags: {mood_tags}\n\n"
        f"User preferences:\n- dietary: {dietary}\n- allergies: {allergies}\n- cuisines: {cuisines}\n- music: {music}\n- activities: {activities}\n\n"
        f"Current weather (if provided):\n- {weather_summary}\n\n"
        "Return ONLY valid JSON, no markdown, no explanation.\n\nSchema:\n"
    )

    # Static schema string (keep braces literal here)
    schema = '''{
  "meals": [
    {
      "title": "string",
      "why": "string",
      "time_minutes": 0,
      "difficulty": "easy|medium|hard"
    }
  ],
  "activities": [
    {
      "name": "string",
      "why": "string",
      "energy": "low|medium|high"
    }
  ],
  "music": [
    {
      "song": "string",
      "artist": "string",
      "why": "string"
    }
  ],
  "clothing": [
    {
      "item": "string",
      "why": "string",
      "layers": "single|light|medium|heavy"
    }
  ]
}'''

    return header + schema


def call_gemini_and_parse(prompt: str) -> dict:
    """
    Calls Gemini and parses JSON output.
    Uses the newer google-genai client and a current model ID.
    """
    import os
    import httpx
    from google import genai

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing. Check your .env and load_dotenv().")

    # Allow overriding the base URL if needed; otherwise use the default public endpoint.
    base_url = os.getenv("GEMINI_API_BASE_URL") or "https://generativelanguage.googleapis.com/"
    client = genai.Client(api_key=api_key, http_options={"base_url": base_url})

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
    except httpx.ConnectError as exc:
        raise RuntimeError(
            f"Failed to reach Gemini (base_url={base_url}). "
            "Check DNS/network access to generativelanguage.googleapis.com or any custom base URL."
        ) from exc
    except Exception as exc:
        # Return a controlled error so the API can surface it to the client.
        raise RuntimeError(f"Gemini request failed: {exc}") from exc

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



def generate_moodmeal_plan(user_id: int, mood_id: int | None = None, weather: dict | None = None) -> dict:
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

    prompt = build_gemini_prompt(mood, prefs, weather)
    try:
        generated = call_gemini_and_parse(prompt)
    except RuntimeError as exc:
        # Pass back a structured error so the API layer can set a proper status.
        return {
            "error": "gemini_request_failed",
            "message": str(exc),
            "user_id": user_id,
            "mood_used": mood,
            "preferences_used": prefs,
            "weather_used": weather,
            "status_code": 502
        }

    return {
        "user_id": user_id,
        "mood_used": mood,
        "preferences_used": prefs,
        "weather_used": weather,
        "generated": generated
    }
