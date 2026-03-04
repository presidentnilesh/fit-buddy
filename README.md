# 🏋️ FitBuddy — AI-Powered Fitness Planner

FitBuddy is a Flask web application powered by **Google Gemini AI** that generates personalized 7-day workout plans, accepts feedback to refine plans, and delivers targeted nutrition/recovery tips.

## Architecture

```
User (Browser)
    ↓
Flask Backend (main.py)
    ├── HTML Templating (Jinja2)         → index.html, all_users.html
    ├── Workout Logic (3 API endpoints)  → /generate-plan, /update-plan, /nutrition-tip
    └── Admin Panel                      → /view-all-users
         ↓
    Gemini 1.5 Flash API (Google Generative AI)
    [Falls back to structured mock data if no API key]
         ↓
    SQLite + Python sqlite3 ORM
    ├── users table
    └── workout_plans table
```

## Setup

### 1. Install dependencies
```bash
pip install flask google-generativeai
```

### 2. Set your Gemini API key (optional but recommended)
```bash
export GEMINI_API_KEY="your-api-key-here"
```
Get a free key at: https://aistudio.google.com/app/apikey

> **Without an API key**, FitBuddy runs in demo mode with high-quality pre-built mock plans and tips.

### 3. Run the server
```bash
cd fitbuddy
python main.py
```

### 4. Open in browser
```
http://localhost:5000
```

Admin panel: `http://localhost:5000/view-all-users`

---

## API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/` | Main UI (index.html) |
| POST | `/generate-plan` | **Scenario 1**: Generate 7-day workout plan |
| POST | `/update-plan` | **Scenario 2**: Regenerate plan from user feedback |
| POST | `/nutrition-tip` | **Scenario 3**: Get goal-specific nutrition tip |
| GET | `/view-all-users` | Admin: view all users & plans |
| GET | `/api/users/<id>/plans` | Retrieve plans for a user (JSON) |

### POST /generate-plan
```json
{
  "name": "Alex Johnson",
  "age": 28,
  "weight": 72,
  "height": 175,
  "goal": "weight loss",
  "intensity": "medium"
}
```

### POST /update-plan
```json
{
  "name": "Alex Johnson",
  "goal": "weight loss",
  "intensity": "medium",
  "current_plan": "3 days cardio, 4 days strength",
  "feedback": "More rest days, include yoga"
}
```

### POST /nutrition-tip
```json
{
  "goal": "muscle gain",
  "focus": "post-workout recovery"
}
```

---

## Database Schema

```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    weight REAL NOT NULL,
    height REAL,
    goal TEXT NOT NULL,
    intensity TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Workout plans table
CREATE TABLE workout_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    plan_json TEXT NOT NULL,
    nutrition_tip TEXT,
    feedback TEXT,
    version INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);
```

---

## Features

- ✅ **Scenario 1**: Personalized 7-day workout plan generation
- ✅ **Scenario 2**: Feedback-based plan regeneration
- ✅ **Scenario 3**: Goal-specific nutrition & recovery tips
- ✅ Frontend + backend input validation
- ✅ SQLite persistence for users and plans
- ✅ Admin panel at `/view-all-users`
- ✅ Graceful fallback to mock AI when no API key
- ✅ Logging to console + `fitbuddy.log`
- ✅ Error handling with JSON error responses
- ✅ Clean, animated dark-theme UI
