"""
FitBuddy - AI-Powered Fitness Planner
FastAPI-equivalent backend built with Flask + SQLite + Google Gemini AI
"""

import os
import json
import logging
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, render_template, redirect, url_for

# ─── Logging Setup ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("fitbuddy.log")
    ]
)
logger = logging.getLogger("fitbuddy")

# ─── App Init ───────────────────────────────────────────────────
app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["SECRET_KEY"] = "fitbuddy-secret-2024"

DB_PATH = "fitbuddy.db"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# ─── Database Setup ─────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                weight REAL NOT NULL,
                height REAL,
                goal TEXT NOT NULL,
                intensity TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS workout_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                plan_json TEXT NOT NULL,
                nutrition_tip TEXT,
                feedback TEXT,
                version INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)
    logger.info("Database initialized: %s", DB_PATH)

# ─── AI Plan Generation ─────────────────────────────────────────
def call_gemini(prompt: str) -> str:
    """Call Google Gemini API. Falls back to mock if no API key."""
    if not GEMINI_API_KEY:
        logger.warning("No GEMINI_API_KEY set – using mock response")
        return generate_mock_plan(prompt)

    try:
        import urllib.request
        import urllib.error

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        payload = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2048}
        }).encode("utf-8")

        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        logger.error("Gemini API error: %s", e)
        return generate_mock_plan(prompt)


def generate_mock_plan(prompt: str) -> str:
    """Structured mock plan for demonstration when API key is absent."""
    if "nutrition" in prompt.lower() or "tip" in prompt.lower():
        return generate_mock_tip(prompt)

    plan = {
        "days": [
            {"day": "Day 1", "focus": "Full Body Activation", "exercises": [
                "Warm-up: 5 min brisk walk", "3x15 Bodyweight Squats",
                "3x12 Push-ups", "3x12 Dumbbell Rows", "2x20 Jumping Jacks", "Cool-down stretch 5 min"
            ]},
            {"day": "Day 2", "focus": "Cardio & Core", "exercises": [
                "20 min moderate jogging", "3x15 Bicycle Crunches",
                "3x30s Plank Hold", "3x15 Leg Raises", "3x20 Mountain Climbers"
            ]},
            {"day": "Day 3", "focus": "Active Recovery", "exercises": [
                "30 min yoga or stretching", "10 min foam rolling",
                "Breathing exercises", "Light 15 min walk"
            ]},
            {"day": "Day 4", "focus": "Lower Body Strength", "exercises": [
                "4x12 Goblet Squats", "3x15 Reverse Lunges each leg",
                "3x12 Romanian Deadlifts", "3x20 Glute Bridges", "3x15 Calf Raises"
            ]},
            {"day": "Day 5", "focus": "Upper Body & HIIT", "exercises": [
                "4x10 Dumbbell Press", "3x12 Lateral Raises",
                "3x12 Tricep Dips", "3x10 Bicep Curls",
                "HIIT: 8 rounds 30s work / 15s rest"
            ]},
            {"day": "Day 6", "focus": "Cardio Endurance", "exercises": [
                "40 min steady-state cardio (bike/swim/jog)",
                "2x20 Jump Rope", "3x15 Burpees", "Cool-down walk 5 min"
            ]},
            {"day": "Day 7", "focus": "Rest & Mobility", "exercises": [
                "Full body stretch routine (20 min)",
                "Meditation or mindfulness (10 min)",
                "Hydration & nutrition planning for next week"
            ]}
        ],
        "summary": "A balanced 7-day plan tailored to your goal and intensity level."
    }
    return json.dumps(plan)


def generate_mock_tip(prompt: str) -> str:
    tips = {
        "weight loss": {
            "icon": "🔥",
            "tip": "Focus on a caloric deficit of 300–500 kcal/day. Prioritize high-fiber foods (vegetables, legumes, whole grains) to stay full longer. Drink 2–3L of water daily—sometimes thirst is mistaken for hunger. Time your largest meal around your workout for optimal energy and recovery. Avoid ultra-processed foods and liquid calories. A protein intake of 1.6g/kg body weight helps preserve muscle while losing fat."
        },
        "muscle gain": {
            "icon": "💪",
            "tip": "Consume 1.8–2.2g of protein per kg of bodyweight daily. Prioritize post-workout nutrition within 45 minutes—combine fast-digesting protein (whey) with carbohydrates (banana, rice). Eat in a slight caloric surplus (200–300 kcal above maintenance). Don't skip sleep—80% of muscle repair happens during deep sleep. Creatine monohydrate (5g/day) is one of the most well-researched performance supplements."
        },
        "general wellness": {
            "icon": "🌿",
            "tip": "Embrace the Mediterranean diet—rich in olive oil, fish, legumes, and fresh vegetables. Prioritize sleep hygiene: 7–9 hours per night supports hormone balance, immune function, and mental clarity. Stay hydrated with water and herbal teas. Incorporate anti-inflammatory foods like turmeric, ginger, and berries. Manage stress through mindfulness—chronic stress elevates cortisol, which can undermine fitness progress."
        },
        "endurance": {
            "icon": "⚡",
            "tip": "Fuel endurance training with complex carbohydrates 2–3 hours before your session. During long sessions (60+ min), consume 30–60g of carbohydrates per hour via gels or sports drinks. Post-workout, replenish glycogen within 30 minutes with a 3:1 carb-to-protein ratio. Electrolyte balance is critical—sodium, potassium, and magnesium prevent cramping. Beet juice (nitrates) has shown measurable VO2 max improvements in studies."
        },
        "flexibility": {
            "icon": "🧘",
            "tip": "Stretch when muscles are warm—ideally post-workout or after a 5-min warm-up. Hold each stretch for 30–60 seconds and breathe into the tension. Incorporate yoga or Pilates 2–3x per week for holistic flexibility gains. Collagen supplementation with vitamin C may support connective tissue health. Foam rolling before stretching increases range of motion by breaking up fascial adhesions. Consistency beats intensity—daily 10-minute sessions outperform weekly marathon stretches."
        }
    }
    for goal, content in tips.items():
        if goal in prompt.lower():
            return json.dumps(content)
    return json.dumps(tips["general wellness"])


def build_plan_prompt(user: dict) -> str:
    return f"""You are FitBuddy, an expert AI fitness coach. Generate a personalized, structured 7-day workout plan.

USER PROFILE:
- Name: {user['name']}
- Age: {user['age']} years
- Weight: {user['weight']} kg
- Height: {user.get('height', 'Not provided')} cm
- Fitness Goal: {user['goal']}
- Workout Intensity: {user['intensity']}

INSTRUCTIONS:
Return ONLY valid JSON with this exact structure (no markdown, no explanation):
{{
  "days": [
    {{"day": "Day 1", "focus": "Focus Area Name", "exercises": ["Exercise 1", "Exercise 2", ...]}},
    ... (7 days total)
  ],
  "summary": "Brief 1-2 sentence plan summary"
}}

Tailor exercises specifically to the goal "{user['goal']}" at "{user['intensity']}" intensity.
Include warm-up and cool-down in relevant days. Make it realistic and safe."""


def build_feedback_prompt(user: dict, current_plan: str, feedback: str) -> str:
    return f"""You are FitBuddy, an expert AI fitness coach. Update the existing workout plan based on user feedback.

USER PROFILE:
- Name: {user['name']}
- Goal: {user['goal']}
- Intensity: {user['intensity']}

CURRENT PLAN SUMMARY:
{current_plan[:500] if current_plan else "Standard 7-day plan"}

USER FEEDBACK:
{feedback}

INSTRUCTIONS:
Regenerate an improved 7-day plan addressing the feedback.
Return ONLY valid JSON:
{{
  "days": [
    {{"day": "Day 1", "focus": "Focus Area", "exercises": ["Exercise 1", "Exercise 2", ...]}},
    ... (7 days total)
  ],
  "summary": "Brief summary noting what changed based on feedback"
}}"""


def build_tip_prompt(goal: str, focus: str) -> str:
    return f"""You are FitBuddy nutrition and recovery expert.
Provide a concise, practical nutrition/recovery tip for someone with the goal: {goal}.
Focus area: {focus}.

Return ONLY valid JSON:
{{"icon": "relevant emoji", "tip": "3-4 sentence practical tip with specific actionable advice"}}"""


def parse_plan_response(raw: str) -> dict:
    """Safely parse AI response to JSON."""
    try:
        # Strip markdown code blocks if present
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1])
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("Failed to parse AI JSON, wrapping as text")
        return {
            "days": [{"day": f"Day {i}", "focus": "See full plan below", "exercises": [raw[:200]]} for i in range(1, 8)],
            "summary": "Plan generated – see details above."
        }


# ─── Routes ─────────────────────────────────────────────────────

@app.route("/")
def index():
    logger.info("GET / – serving index")
    return render_template("index.html")


@app.route("/generate-plan", methods=["POST"])
def generate_plan():
    """Scenario 1: Generate personalized 7-day workout plan."""
    data = request.get_json()
    logger.info("POST /generate-plan payload: %s", data)

    # ── Validation ──
    errors = {}
    name = (data.get("name") or "").strip()
    if not name:
        errors["name"] = "Name is required."
    try:
        age = int(data.get("age", 0))
        if not (10 <= age <= 100):
            raise ValueError
    except (TypeError, ValueError):
        errors["age"] = "Age must be between 10 and 100."
        age = 0
    try:
        weight = float(data.get("weight", 0))
        if not (30 <= weight <= 300):
            raise ValueError
    except (TypeError, ValueError):
        errors["weight"] = "Weight must be between 30 and 300 kg."
        weight = 0
    try:
        height = float(data.get("height") or 0)
        height = height if 100 <= height <= 250 else None
    except (TypeError, ValueError):
        height = None
    goal = data.get("goal", "").strip().lower()
    if goal not in ["weight loss", "muscle gain", "general wellness", "endurance", "flexibility"]:
        errors["goal"] = "Invalid goal selected."
    intensity = data.get("intensity", "").strip().lower()
    if intensity not in ["low", "medium", "high"]:
        errors["intensity"] = "Intensity must be low, medium, or high."

    if errors:
        logger.warning("Validation errors: %s", errors)
        return jsonify({"success": False, "errors": errors}), 422

    user = {"name": name, "age": age, "weight": weight, "height": height, "goal": goal, "intensity": intensity}

    # ── Save user ──
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO users (name, age, weight, height, goal, intensity) VALUES (?,?,?,?,?,?)",
            (name, age, weight, height, goal, intensity)
        )
        user_id = cursor.lastrowid

    # ── Generate plan ──
    prompt = build_plan_prompt(user)
    raw_plan = call_gemini(prompt)
    plan_data = parse_plan_response(raw_plan)

    # ── Generate nutrition tip ──
    tip_prompt = build_tip_prompt(goal, "general")
    raw_tip = call_gemini(tip_prompt)
    try:
        tip_data = json.loads(raw_tip.strip().lstrip("```json").rstrip("```"))
    except Exception:
        tip_data = {"icon": "💡", "tip": raw_tip[:300]}

    # ── Save plan ──
    with get_db() as conn:
        conn.execute(
            "INSERT INTO workout_plans (user_id, plan_json, nutrition_tip) VALUES (?,?,?)",
            (user_id, json.dumps(plan_data), json.dumps(tip_data))
        )

    logger.info("Plan generated for user_id=%s (%s)", user_id, name)
    return jsonify({
        "success": True,
        "user_id": user_id,
        "user_name": name,
        "plan": plan_data,
        "nutrition_tip": tip_data
    })


@app.route("/update-plan", methods=["POST"])
def update_plan():
    """Scenario 2: Update plan based on user feedback."""
    data = request.get_json()
    logger.info("POST /update-plan payload keys: %s", list(data.keys()))

    errors = {}
    name = (data.get("name") or "").strip()
    if not name:
        errors["name"] = "Name is required."
    goal = data.get("goal", "").strip().lower()
    if goal not in ["weight loss", "muscle gain", "general wellness", "endurance", "flexibility"]:
        errors["goal"] = "Invalid goal."
    intensity = data.get("intensity", "medium").strip().lower()
    feedback = (data.get("feedback") or "").strip()
    if not feedback:
        errors["feedback"] = "Feedback cannot be empty."

    if errors:
        return jsonify({"success": False, "errors": errors}), 422

    user = {"name": name, "goal": goal, "intensity": intensity}
    current_plan = data.get("current_plan", "")

    prompt = build_feedback_prompt(user, current_plan, feedback)
    raw_plan = call_gemini(prompt)
    plan_data = parse_plan_response(raw_plan)

    # Save updated plan
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO users (name, age, weight, height, goal, intensity) VALUES (?,?,?,?,?,?)",
            (name, 25, 70, None, goal, intensity)
        )
        user_id = cursor.lastrowid
        conn.execute(
            "INSERT INTO workout_plans (user_id, plan_json, feedback, version) VALUES (?,?,?,?)",
            (user_id, json.dumps(plan_data), feedback, 2)
        )

    logger.info("Plan updated for %s based on feedback", name)
    return jsonify({"success": True, "plan": plan_data, "feedback_applied": feedback})


@app.route("/nutrition-tip", methods=["POST"])
def nutrition_tip():
    """Scenario 3: Get nutrition or recovery tip based on goal."""
    data = request.get_json()
    goal = (data.get("goal") or "general wellness").strip().lower()
    focus = (data.get("focus") or "general").strip()

    if goal not in ["weight loss", "muscle gain", "general wellness", "endurance", "flexibility"]:
        return jsonify({"success": False, "error": "Invalid goal."}), 422

    prompt = build_tip_prompt(goal, focus)
    raw_tip = call_gemini(prompt)

    try:
        cleaned = raw_tip.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1])
        tip_data = json.loads(cleaned)
    except Exception:
        tip_data = {"icon": "💡", "tip": raw_tip[:400]}

    logger.info("Nutrition tip generated for goal=%s focus=%s", goal, focus)
    return jsonify({"success": True, "goal": goal, "focus": focus, "tip": tip_data})


@app.route("/view-all-users")
def view_all_users():
    """Admin panel – view all users and plans."""
    with get_db() as conn:
        users = conn.execute("""
            SELECT u.*, COUNT(w.id) as plan_count
            FROM users u
            LEFT JOIN workout_plans w ON w.user_id = u.id
            GROUP BY u.id ORDER BY u.created_at DESC
        """).fetchall()
        users = [dict(r) for r in users]
    logger.info("Admin: fetched %d users", len(users))
    return render_template("all_users.html", users=users)


@app.route("/api/users/<int:user_id>/plans")
def get_user_plans(user_id):
    """Retrieve plans for a specific user."""
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        if not user:
            return jsonify({"error": "User not found"}), 404
        plans = conn.execute(
            "SELECT * FROM workout_plans WHERE user_id=? ORDER BY created_at DESC",
            (user_id,)
        ).fetchall()
    return jsonify({
        "user": dict(user),
        "plans": [dict(p) for p in plans]
    })


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found", "code": 404}), 404


@app.errorhandler(500)
def server_error(e):
    logger.error("Server error: %s", str(e))
    return jsonify({"error": "Internal server error", "code": 500}), 500


# ─── Entrypoint ─────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    logger.info("🏋️  FitBuddy starting on http://0.0.0.0:%d", port)
    app.run(host="0.0.0.0", port=port, debug=False)
