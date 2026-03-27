# api/moodmeal_gemini.py
"""
MoodMeal Gemini API Integration

Programming Constructs:
- Sequencing: Code executes in order through prompt building and API calls
- Selection: if/else statements for mood validation and error handling
- Iteration: Loops for processing mood tags, preferences, and recommendations
- Lists: Arrays storing dietary preferences, allergies, cuisines, music, activities
"""

import os
import json
import random

from flask import g
from dotenv import load_dotenv

from model.moodmeal_mood import MoodMealMood
from model.moodmeal_preferences import MoodMealPreferences

# Load .env once
load_dotenv()

# List: Valid mood categories for validation
VALID_MOOD_CATEGORIES = ['Happy/Neutral', 'Energetic/Excited', 'Tired/Low Energy', 'Stressed/Anxious']

# List: Default recommendation counts per category
RECOMMENDATION_LIMITS = {'meals': 3, 'activities': 3, 'music': 3, 'clothing': 2}



# 1. MoodRepository class, access database to get moods

class MoodRepository:
    """
    /**
     * Data Layer — Single Responsibility: database access only.
     *
     * All queries to MoodMealMood and MoodMealPreferences live here.
     * If the database schema or ORM ever changes, this is the only
     * class that needs to be updated. It has no knowledge of the AI layer.
     */
    """

    @staticmethod
    def get_latest_mood_for_user(user_id: int) -> dict | None:
        """
        /**
         * Fetches the most recent mood entry for a given user.
         *
         * @param user_id  - the ID of the authenticated user
         * @return dict with mood data, or None if no entry exists
         */
        """
        # Sequencing: build query then execute to retrieve the most recent mood
        mood = (
            MoodMealMood.query
            .filter_by(_user_id=user_id)
            .order_by(MoodMealMood._timestamp.desc())
            .first()
        )
        # Selection: return result if found, otherwise None
        return mood.read() if mood else None

    @staticmethod
    def get_mood_by_id_for_user(user_id: int, mood_id: int) -> dict | None:
        """
        /**
         * Fetches a specific mood entry by ID for a given user.
         *
         * @param user_id  - the ID of the authenticated user
         * @param mood_id  - the ID of the mood entry to retrieve
         * @return dict with mood data, or None if not found
         */
        """
        # Sequencing: query by id then return
        mood = MoodMealMood.query.filter_by(id=mood_id, _user_id=user_id).first()
        # Selection: present or absent
        return mood.read() if mood else None

    @staticmethod
    def get_preferences_for_user(user) -> dict:
        """
        /**
         * Fetches dietary, allergy, cuisine, music, and activity preferences
         * for the authenticated user. Returns defaults if none are saved.
         *
         * @param user  - the authenticated user object
         * @return dict of preferences (never a Flask Response)
         */
        """
        prefs = MoodMealPreferences.query.filter_by(_user_id=user.id).first()
        # Selection: if no prefs found, return default structure (lists)
        if not prefs:
            # match PreferencesAPI default structure
            return {
                "user_id": user.id,
                "dietary": [],   # List: dietary preferences
                "allergies": [], # List: allergies
                "cuisines": [],  # List: cuisines
                "music": [],     # List: music preferences
                "activities": [] # List: activity preferences
            }
        # Sequencing: read DB object and return a dict
        return prefs.read()



# 2. Gemini class, format prompt and response

class GeminiService:
    """
    /**
     * AI Layer — Single Responsibility: Gemini API communication only.
     *
     * Handles prompt construction and response parsing for the Google Gemini API.
     * Takes plain Python dicts in, returns parsed JSON out.
     * Has no knowledge of the database or SQLAlchemy models.
     */
    """

    @staticmethod
    def validate_mood_category(category: str) -> bool:
        """
        /**
         * Checks whether a mood category string matches a known valid category.
         *
         * @param category  - mood category string to validate
         * @return True if valid, False otherwise
         */
        """
        # Iteration: Loop through valid mood categories
        for valid_category in VALID_MOOD_CATEGORIES:
            # Selection: Check if category matches
            if category.lower() == valid_category.lower():
                return True
        return False

    @staticmethod
    def filter_recommendations_by_limit(recommendations: dict) -> dict:
        """
        /**
         * Trims each recommendation category to its defined max count
         * using the RECOMMENDATION_LIMITS constants.
         *
         * @param recommendations  - raw dict of AI-generated recommendations
         * @return dict with each category capped at its limit
         */
        """
        filtered = {}

        # Iteration: Loop through each recommendation category
        for category, items in recommendations.items():
            # Selection: Check if category has a defined limit
            if category in RECOMMENDATION_LIMITS:
                limit = RECOMMENDATION_LIMITS[category]
                # Iteration: Create new list with limited items
                # Lists: slicing enforces limit on list-type recommendations
                filtered[category] = items[:limit] if isinstance(items, list) else items
            else:
                filtered[category] = items

        return filtered

    @staticmethod
    def build_prompt(mood: dict, preferences: dict, weather: dict | None = None, refresh: bool = False, feedback: str | None = None) -> str:
        """
        /**
         * Builds the full prompt string to send to Gemini.
         * Injects mood data, preferences, weather, and optional refresh/feedback
         * instructions. Forces JSON-only output for reliable parsing.
         *
         * @param mood         - dict of the user's current mood data
         * @param preferences  - dict of the user's saved preferences
         * @param weather      - optional dict of current weather data
         * @param refresh      - if True, instructs Gemini to vary its suggestions
         * @param feedback     - optional user feedback string to guide new results
         * @return prompt string ready to pass to call_and_parse()
         */
        """
        # Lists: mood_tags and preference lists are treated as lists
        mood_score = mood.get("mood_score")
        mood_category = mood.get("mood_category") or "Unknown"
        mood_tags = mood.get("mood_tags") or []

        # Lists: extract preference lists (could be empty lists)
        dietary = preferences.get("dietary") or []
        allergies = preferences.get("allergies") or []
        cuisines = preferences.get("cuisines") or []
        music = preferences.get("music") or []
        activities = preferences.get("activities") or []

        # Normalize a short weather summary for the prompt
        if weather:
            # Selection: different handling depending on weather structure
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

        # Add refresh instruction if user wants different recommendations
        refresh_instruction = ""
        if refresh:
            # Selection: branch when refresh=True
            random_seed = random.randint(1000, 9999)
            refresh_instruction = (
                f"IMPORTANT: The user did NOT like the previous recommendations (variation seed: {random_seed}). "
                "You MUST provide COMPLETELY DIFFERENT and UNIQUE suggestions. "
                "Choose different cuisines, genres, and activity types than typical suggestions. "
                "Be creative and surprising with your recommendations.\n\n"
            )

        # Add user feedback if provided
        feedback_instruction = ""
        if feedback and feedback.strip():
            # Selection: include user feedback when present
            feedback_instruction = (
                f"USER FEEDBACK: The user has provided specific feedback about what they want changed:\n"
                f"\"{feedback.strip()}\"\n\n"
                "Please take this feedback into account and adjust your recommendations accordingly. "
                "Address their concerns and preferences directly.\n\n"
            )

        # Sequencing: assemble header and schema into final prompt string
        header = (
            "You are MoodMeal, a helpful wellness assistant. Generate personalized recommendations based on the user's mood and preferences.\n\n"
            f"{refresh_instruction}"
            f"{feedback_instruction}"
            f"User mood:\n- mood_score: {mood_score}/100\n- mood_category: {mood_category}\n- mood_tags: {mood_tags}\n\n"
            f"User preferences:\n- dietary: {dietary}\n- allergies: {allergies}\n- cuisines: {cuisines}\n- music: {music}\n- activities: {activities}\n\n"
            f"Current weather (if provided):\n- {weather_summary}\n\n"
            "IMPORTANT INSTRUCTIONS:\n"
            "1. For each 'why' field, write 1-2 helpful sentences explaining HOW this recommendation will positively impact the user's current mood.\n"
            "2. Be specific - reference their mood score, category, or tags in your explanations.\n"
            "3. Provide 2-3 items per category.\n\n"
            "Return ONLY valid JSON, no markdown, no explanation.\n\nSchema:\n"
        )

        # Static schema string (keep braces literal here)
        schema = '''{
  "meals": [
    {
      "title": "meal name",
      "why": "1-2 sentences explaining how this meal helps their mood",
      "time_minutes": 15,
      "difficulty": "easy|medium|hard"
    }
  ],
  "activities": [
    {
      "name": "activity name",
      "why": "1-2 sentences explaining how this activity improves their mood",
      "energy": "low|medium|high"
    }
  ],
  "music": [
    {
      "song": "actual song title",
      "artist": "actual artist name",
      "why": "1-2 sentences explaining how this song matches or improves their mood"
    }
  ],
  "clothing": [
    {
      "item": "clothing item",
      "why": "1-2 sentences explaining why this is good for the weather and their mood",
      "layers": "single|light|medium|heavy"
    }
  ]
}'''

        return header + schema

    @staticmethod
    def call_and_parse(prompt: str) -> dict:
        """
        /**
         * Sends a prompt to the Gemini API and parses the JSON response.
         * Handles connection errors and malformed responses.
         *
         * @param prompt  - the fully built prompt string from build_prompt()
         * @return parsed dict of AI recommendations
         * @throws RuntimeError if the API is unreachable or returns non-JSON
         */
        """
        import httpx
        from google import genai

        # Sequencing: check env, create client, call model
        api_key = os.getenv("GEMINI_API_KEY")
        # Selection/error-handling: bail early if key missing
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is missing. Check your .env and load_dotenv().")

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
            raise RuntimeError(f"Gemini request failed: {exc}") from exc

        text = (response.text or "").strip()

        # Parse JSON safely
        try:
            # Selection: try direct JSON parse first
            return json.loads(text)
        except json.JSONDecodeError:
            # Selection/fallback: attempt to extract first {...} block and parse
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end == -1 or end <= start:
                raise RuntimeError(f"Gemini did not return JSON. Raw output:\n{text}")
            return json.loads(text[start:end+1])



# 3. create mood meal plan/organize everything

def generate_moodmeal_plan(user_id: int, mood_id: int | None = None, weather: dict | None = None, refresh: bool = False, feedback: str | None = None) -> dict:
    """
    /**
     * Logic Layer — Single Responsibility: orchestration only.
     *
     * Coordinates MoodRepository and GeminiService to produce a meal plan.
     * Does not contain any database queries or prompt-building logic itself.
     *
     * Flow:
     *   1. MoodRepository  → fetch mood + preferences from the database
     *   2. GeminiService   → build prompt and get AI-generated recommendations
     *   3. Return combined result as a plain dict
     *
     * @param user_id   - the ID of the authenticated user
     * @param mood_id   - optional specific mood entry ID; uses latest if omitted
     * @param weather   - optional weather dict to include in the prompt
     * @param refresh   - if True, tells Gemini to vary recommendations
     * @param feedback  - optional user feedback to guide new results
     * @return dict containing mood, preferences, weather used, and generated plan
     */
    """

    # Step 1 — Data Layer: get mood
    # Selection: pick mood by id if provided, otherwise use latest
    if mood_id is not None:
        mood = MoodRepository.get_mood_by_id_for_user(user_id, mood_id)
    else:
        mood = MoodRepository.get_latest_mood_for_user(user_id)

    # Selection/error: return structured error if no mood
    if mood is None:
        return {
            "message": "No mood found. POST /api/moodmeal/mood first.",
            "user_id": user_id
        }

    # Step 1 (continued) — Data Layer: get preferences
    prefs = MoodRepository.get_preferences_for_user(g.current_user)

    # Step 2 — AI Layer: build prompt and call Gemini
    prompt = GeminiService.build_prompt(mood, prefs, weather, refresh=refresh, feedback=feedback)
    try:
        generated = GeminiService.call_and_parse(prompt)
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

    # Step 3 — Return combined result
    return {
        "user_id": user_id,
        "mood_used": mood,
        "preferences_used": prefs,
        "weather_used": weather,
        "generated": generated
    }
