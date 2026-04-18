# Moodlife – Backend (Flask)

**Moodlife** is a mood and wellness tracking application built by the ANPDSS team. This repository contains the Flask backend that powers the Moodlife platform, providing REST APIs for user authentication, mood logging, meal/activity recommendations via AI, and social features.

The backend pairs with the [Moodlife frontend](https://github.com/ANPDSS/ANPDSS-Pages) (GitHub Pages / Jekyll).

## Project Overview

Moodlife helps users track and reflect on their emotional wellbeing over time. The backend is responsible for:

- User registration, login, and JWT-based authentication
- Storing and retrieving mood entries and user preferences via SQLAlchemy
- Generating personalized meal, activity, music, and clothing recommendations using the Google Gemini API (via `POST /api/moodmeal/plan`)
- Serving a MicroBlog / social feed API for community interaction
- Supporting deployment via AWS, Docker, docker-compose, and Nginx

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Web Framework | Flask (Python) |
| Database ORM | SQLAlchemy (SQLite locally, AWS RDS in production) |
| Authentication | JWT cookies |
| AI Integration | Google Gemini API (`moodmeal_gemini.py`) |
| Deployment | Docker, docker-compose, Nginx, WSGI |

---

## Getting Started

> Requires Python 3.9+. Works on macOS, WSL Ubuntu, and Ubuntu.

### 1. Clone the repository

```bash
git clone https://github.com/ANPDSS/ANPDSS-flask.git
cd ANPDSS-flask
```

### 2. Set up a virtual environment and install dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```shell
# Port configuration
FLASK_PORT=8001
# Admin user
ADMIN_USER='Thomas Edison'
ADMIN_UID='toby'
ADMIN_PASSWORD='123Toby!'
ADMIN_PFP='toby.png'
# Default user
DEFAULT_USER='Grace Hopper'
DEFAULT_UID='hop'
DEFAULT_USER_PASSWORD='123Hop!'
DEFAULT_USER_PFP='hop.png'
DEFAULT_PASSWORD='123Qwerty!'
# Google Gemini AI (used by /api/moodmeal/plan)
GEMINI_API_KEY=xxxxx
GEMINI_API_BASE_URL=https://generativelanguage.googleapis.com/
# GitHub
GITHUB_TOKEN=ghp_xxx
GITHUB_TARGET_TYPE=user
GITHUB_TARGET_NAME=ANPDSS
# DB (AWS RDS for production)
DB_USERNAME='admin'
DB_PASSWORD='xxxxx'
```

### 4. Initialize the database

```bash
./scripts/db_init.py
```

### 5. Run the app

Open `main.py` in VSCode and click the Play button, or:

```bash
python main.py
```

Click the localhost URL shown in the terminal to open the app.

---

## API Reference

### User Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/authenticate` | Log in — authenticates user and sets JWT cookie |
| GET | `/api/id` | Get the currently logged-in user's profile |
| POST | `/api/user` | Sign up — create a new user account |

---

### MoodMeal – Mood Logging (`/api/moodmeal`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/moodmeal/mood` | Get mood history (supports `?limit=N`) |
| POST | `/api/moodmeal/mood` | Log a new mood entry |
| GET | `/api/moodmeal/mood/<id>` | Get a specific mood entry by ID |
| PUT | `/api/moodmeal/mood/<id>` | Update a specific mood entry |
| DELETE | `/api/moodmeal/mood/<id>` | Delete a specific mood entry |
| GET | `/api/moodmeal/mood/stats` | Get mood statistics (average, most common category/tags) |

**POST `/api/moodmeal/mood` body:**
```json
{
  "mood_score": 75,
  "mood_category": "Happy/Neutral",
  "mood_tags": ["relaxed", "focused"],
  "timestamp": "2026-04-18 12:00:00"
}
```
Valid `mood_category` values: `Happy/Neutral`, `Energetic/Excited`, `Tired/Low Energy`, `Stressed/Anxious`

---

### MoodMeal – User Preferences (`/api/moodmeal/preferences`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/moodmeal/preferences` | Get the current user's saved preferences |
| POST | `/api/moodmeal/preferences` | Create or update preferences |
| DELETE | `/api/moodmeal/preferences` | Delete preferences |

**POST `/api/moodmeal/preferences` body:**
```json
{
  "dietary": ["vegetarian"],
  "allergies": ["nuts"],
  "cuisines": ["Italian", "Japanese"],
  "music": ["lo-fi", "jazz"],
  "activities": ["yoga", "walking"]
}
```

---

### MoodMeal – AI Recommendations (`/api/moodmeal/plan`)

Calls `moodmeal_gemini.py` internally to generate personalized recommendations using the user's latest mood and saved preferences.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/moodmeal/plan` | Generate meal, activity, music & clothing recommendations |

**POST body (all fields optional):**
```json
{
  "mood_id": 42,
  "weather": { "weather": [{"main": "Cloudy"}], "main": {"temp": 65} },
  "refresh": true,
  "feedback": "I don't want pasta suggestions"
}
```

**Response shape:**
```json
{
  "user_id": 1,
  "mood_used": { "mood_score": 75, "mood_category": "Happy/Neutral", "mood_tags": ["relaxed"] },
  "preferences_used": { "dietary": ["vegetarian"], "cuisines": ["Italian"] },
  "weather_used": { ... },
  "generated": {
    "meals": [{ "title": "...", "why": "...", "time_minutes": 20, "difficulty": "easy" }],
    "activities": [{ "name": "...", "why": "...", "energy": "medium" }],
    "music": [{ "song": "...", "artist": "...", "why": "..." }],
    "clothing": [{ "item": "...", "why": "...", "layers": "light" }]
  }
}
```

---

### MicroBlog / Social Feed (`/api/microblog`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/microblog` | Create a new post |
| GET | `/api/microblog` | Get posts (supports `?topicId`, `?userId`, `?search`, `?limit`) |
| PUT | `/api/microblog` | Update a post |
| DELETE | `/api/microblog` | Delete a post |
| POST | `/api/microblog/reply` | Add a reply to a post |
| POST | `/api/microblog/reaction` | Add a reaction (👍, ❤️, etc.) |
| DELETE | `/api/microblog/reaction` | Remove a reaction |
| GET | `/api/microblog/page/<page_key>` | Get posts for a specific page |
| POST | `/api/microblog/topics/auto-create` | Auto-create a topic for a page |
| GET | `/api/microblog/topics?pagePath=X` | Get topic by page path |

---

## Project Structure

```
ANPDSS-flask/
├── main.py                    # Flask app entry point & blueprint registration
├── api/
│   ├── moodmeal_api.py        # /api/moodmeal/* — mood, preferences, plan endpoints
│   ├── moodmeal_gemini.py     # Gemini AI integration for /api/moodmeal/plan
│   ├── microblog_api.py       # /api/microblog/* — social feed
│   ├── user.py                # /api/user, /api/authenticate, /api/id
│   ├── gemini_api.py          # General-purpose Gemini chat endpoint
│   ├── friend_api.py          # Friend requests and connections
│   ├── message_api.py         # Private messaging
│   ├── group_api.py           # Group management
│   └── ...                    # Other feature APIs
├── model/
│   ├── moodmeal_mood.py       # MoodMealMood SQLAlchemy model
│   ├── moodmeal_preferences.py# MoodMealPreferences SQLAlchemy model
│   ├── user.py                # User model with JWT auth
│   └── ...
├── templates/                 # Jinja2 admin UI templates
├── static/                    # Static assets
├── scripts/                   # DB init and utility scripts
└── instance/volumes/          # SQLite database (local dev)
```

---

## Deployment

The backend supports production deployment using Docker and Nginx as a WSGI server. See `docker-compose.yml` and the deployment scripts in the repository for details.

---

## Related Repositories

| Repository | Purpose |
|------------|---------|
| [ANPDSS-flask](https://github.com/ANPDSS/ANPDSS-flask) | This repo — Moodlife backend (Flask REST API) |
| [ANPDSS-Pages](https://github.com/ANPDSS/ANPDSS-Pages) | Moodlife frontend (GitHub Pages / Jekyll) |

---

## Changelog

### 2025–2026
- Added `moodmeal_gemini.py` — AI-powered mood-based recommendations (meals, activities, music, clothing) via `/api/moodmeal/plan`
- Added MicroBlog / social feed APIs
- Added friend, messaging, and group APIs

### 2024–2025
- Full JWT cookie-based authentication
- CRUD endpoints for users and posts
- SQLite (dev) and AWS RDS (production) support
- Minimal Jinja2 admin UI

### 2023–2024
- JWT security hardening
- SQLite schema migration support (`migrate.sh`)

### 2021–2022
- Initial Flask / WSGI server with Jinja2 templates
