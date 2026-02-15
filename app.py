from flask import Flask, render_template, request, jsonify, redirect, url_for
import datetime
from random import choice

app = Flask(__name__)

# Demo-only in-memory storage
chat_logs = []
mood_logs = []
conversation_memory = []

PROBLEM_TEMPLATES = [
    {
        "title": "Relationship Stress",
        "emoji": "💞",
        "problem": "Frequent arguments, trust issues, feeling unheard.",
        "solution": "Use calm communication windows, set boundaries, and schedule one honest check-in weekly.",
        "chat_prompt": "I am facing relationship stress and need a detailed solution and weekly schedule."
    },
    {
        "title": "Anxiety Overload",
        "emoji": "😰",
        "problem": "Racing thoughts, panic, overthinking, fear of outcomes.",
        "solution": "Use grounding, breath routines, and break tasks into small 10-minute chunks.",
        "chat_prompt": "I have anxiety and overthinking. Give me a detailed recovery plan and timetable."
    },
    {
        "title": "Financial Pressure",
        "emoji": "💸",
        "problem": "Debt worry, unstable income, fear about future expenses.",
        "solution": "Create a survival budget, reduce non-essentials, and follow weekly money review blocks.",
        "chat_prompt": "I am stressed about financial problems. Give me a practical mental wellness + weekly schedule."
    }
]

CRISIS_KEYWORDS = [
    "suicide", "kill myself", "end my life", "die", "self harm", "self-harm",
    "i want to disappear", "i cannot go on", "hurt myself", "no reason to live"
]

STRESS_RESPONSES = [
    "You're carrying a lot right now. Let's shrink this moment: inhale 4, hold 4, exhale 6. Repeat 3 rounds.",
    "Stress can feel loud, but this step matters: drink water, unclench your jaw, drop your shoulders, breathe slowly.",
    "Let's do a 60-second reset. Place your feet on the ground and name 3 things you can see right now."
]

SAD_RESPONSES = [
    "I'm here with you. You don't need to explain perfectly. What has felt heaviest today?",
    "Thank you for opening up. Even sharing this is a strong step. Want to tell me what triggered this feeling?",
    "You deserve care and rest, not pressure. We can take this one thought at a time."
]

ANXIETY_RESPONSES = [
    "Try the 5-4-3-2-1 grounding exercise: 5 things you see, 4 you feel, 3 you hear, 2 you smell, 1 you taste.",
    "Anxiety rises like a wave. Breathe in slowly through your nose, out longer through your mouth. You're safe in this moment.",
    "Let's focus on control: pick one tiny task you can finish in 2 minutes. Small wins calm the mind."
]

SLEEP_RESPONSES = [
    "If sleep is hard, try a wind-down: dim lights, no scrolling for 20 minutes, and slow breathing.",
    "Racing thoughts at night are exhausting. Keep a note nearby and park thoughts on paper before bed.",
    "Try body scan relaxation: relax forehead, jaw, shoulders, chest, arms, and legs one by one."
]

LONELY_RESPONSES = [
    "Feeling alone can be painful. Is there one person you can text: 'I need a little support today'?",
    "You matter to people, even when the mind says otherwise. Want to plan one low-pressure connection step?",
    "Let's reduce the isolation gently: a short walk, a familiar song, and one kind message to someone you trust."
]

DEFAULT_RESPONSES = [
    "Thank you for sharing this. I'm listening without judgment. Tell me a little more.",
    "You're not alone in this conversation. We can work through this step by step.",
    "Your feelings are valid. If you want, we can focus on one thing that's hardest right now."
]

TOPIC_KEYWORDS = {
    "stress": ["stress", "overwhelm", "pressure", "burnout", "tension"],
    "anxiety": ["anxiety", "panic", "nervous", "fear", "worried"],
    "depression": ["depressed", "depression", "hopeless", "worthless", "empty", "no energy", "low"],
    "sleep": ["sleep", "insomnia", "night", "tired"],
    "loneliness": ["alone", "lonely", "isolated", "nobody"],
    "study": ["exam", "study", "college", "school", "marks"],
    "work": ["job", "office", "deadline", "boss", "career"]
}

DETAIL_TRIGGER_KEYWORDS = [
    "detailed", "plan", "solution", "weekly", "timetable", "routine", "schedule"
]


def contains_any(text, keywords):
    return any(keyword in text for keyword in keywords)


def detect_topics(message_lower):
    topics = []
    for topic, words in TOPIC_KEYWORDS.items():
        if contains_any(message_lower, words):
            topics.append(topic)
    return topics


def summarize_understanding(topics, user_message):
    if topics:
        label = ", ".join(topics)
        return f"I understood that you're dealing with: {label}."
    return f"I understood your concern as: '{user_message[:120]}'."


def should_use_detailed_response(message_lower, mode, topics):
    if mode in ["detailed", "timetable"]:
        return True
    if contains_any(message_lower, DETAIL_TRIGGER_KEYWORDS):
        return True
    # In auto mode, provide detailed structure when a clear topic is detected
    # or when the user writes a longer message likely needing guidance.
    if mode == "auto" and (topics or len(message_lower.split()) >= 8):
        return True
    return False


def depression_support_plan():
    return (
        "💙 Detailed Support Plan for Low/Depressed Mood:\n"
        "1) 🧘 Stabilize now (next 10 minutes): drink water, sit upright, and take 8 slow breaths.\n"
        "2) 📝 Name the thought: write one painful thought and one kinder alternative.\n"
        "3) 🚶 Move for 10-15 minutes: walk, stretch, or sunlight exposure.\n"
        "4) 🍲 Basic reset: eat something simple and protein-rich; avoid skipping meals.\n"
        "5) 📞 Connection step: message one trusted person with: 'I'm having a hard day, can we talk?'\n"
        "6) 🎯 Micro-goal: complete one tiny task (2-5 minutes) to build momentum.\n"
        "7) 🌙 Night care: reduce screen use 30 minutes before sleep and do breathing rounds."
    )


def weekly_timetable(topics):
    focus_line = "Focus of this week: calm body, structure day, reconnect with people."
    if "study" in topics:
        focus_line = "Focus of this week: low-pressure study blocks + mental recovery."
    elif "work" in topics:
        focus_line = "Focus of this week: stress-safe productivity + recovery breaks."

    return (
        "🗓️ Weekly Recovery Timetable (repeatable):\n"
        "Mon: 🌅 10-min walk | 📚 45-min focus block | 🌙 Fixed sleep time\n"
        "Tue: 🧘 Breathing 6 min | 🤝 Talk to one trusted person | 📝 Journal 5 lines\n"
        "Wed: 🚶 20-min movement | 🎯 3 micro tasks | 🌿 Gratitude note\n"
        "Thu: 🌞 Morning sunlight | 🍲 Balanced meals | 📵 30-min digital break\n"
        "Fri: 🎵 Relaxation time | ✅ Review weekly wins | 💬 Emotional check-in\n"
        "Sat: 🧹 Space reset 15 min | ❤️ Hobby time | 😴 Early wind-down\n"
        "Sun: 📊 Mood review | 🗂 Plan next week | ☕ Gentle self-care\n"
        f"{focus_line}"
    )


def detail_answer(user_message, message_lower, mode):
    topics = detect_topics(message_lower)
    understanding = summarize_understanding(topics, user_message)
    memory_note = ""

    if conversation_memory:
        memory_note = f"Based on earlier chat, I also remember concern about: {conversation_memory[-1]}."

    base = [
        "🔎 What I Understood:\n" + understanding,
    ]

    if memory_note:
        base.append("🧠 Context Memory:\n" + memory_note)

    if "depression" in topics:
        base.append(depression_support_plan())

    if mode in ["detailed", "timetable"] or contains_any(message_lower, ["plan", "detailed", "solution", "timetable", "weekly", "routine", "schedule"]):
        base.append(weekly_timetable(topics))

    base.append(
        "🧩 Next Best 3 Steps (today):\n"
        "1) Complete one 5-minute task now.\n"
        "2) Message one trusted person.\n"
        "3) Follow one calm routine tonight (breathing + fixed sleep)."
    )

    base.append(
        "🆘 If things feel unsafe or unbearable:\n"
        "US & Canada: Call or text 988\n"
        "India: Tele-MANAS 14416 or 1-800-891-4416"
    )

    return "\n\n".join(base)


def build_mood_schedule(mood, note=""):
    mood_lower = mood.lower()
    note_lower = note.lower()

    if "stressed" in mood_lower or "frustrated" in mood_lower:
        return (
            "🗓️ Mood-Based Schedule (Stress Relief):\n"
            "Morning: 5-minute breathing + light breakfast + top 1 task.\n"
            "Afternoon: 45-minute focused work + 10-minute break + hydration.\n"
            "Evening: 20-minute walk + no-conflict zone for 30 minutes.\n"
            "Night: screen-off 30 minutes before bed + body scan relaxation."
        )
    if "low" in mood_lower:
        return (
            "🗓️ Mood-Based Schedule (Low Mood Recovery):\n"
            "Morning: open curtains + water + 10-minute sunlight.\n"
            "Afternoon: one small productive task + one connection message.\n"
            "Evening: gentle movement + warm meal + gratitude note.\n"
            "Night: calming audio + fixed sleep time."
        )
    if "hopeful" in mood_lower:
        return (
            "🗓️ Mood-Based Schedule (Momentum Plan):\n"
            "Morning: plan top 3 priorities.\n"
            "Afternoon: deep work block + check-in break.\n"
            "Evening: social or family connection + hobby.\n"
            "Night: review wins and prep tomorrow."
        )
    if "financial" in note_lower:
        return (
            "🗓️ Mood + Financial Stress Schedule:\n"
            "Mon/Wed/Fri: 20-minute budget review and expense tracking.\n"
            "Tue/Thu: 30-minute skill or job search block.\n"
            "Daily: avoid money doom-scrolling; focus only on planned actions."
        )
    return (
        "🗓️ Mood-Based Daily Balance Schedule:\n"
        "Morning: hydration + intention.\n"
        "Afternoon: one focused block + one reset break.\n"
        "Evening: light movement + supportive conversation.\n"
        "Night: low-screen routine + fixed sleep window."
    )


@app.route("/")
def home():
    return render_template("index.html", templates=PROBLEM_TEMPLATES)


@app.route("/chat")
def chat():
    return render_template("chat.html")


@app.route("/mood", methods=["GET", "POST"])
def mood():
    if request.method == "POST":
        mood = request.form["mood"]
        note = request.form.get("note", "").strip()
        plan = build_mood_schedule(mood, note)
        mood_logs.append({
            "mood": mood,
            "note": note,
            "plan": plan,
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        return redirect(url_for("mood"))
    latest_plan = mood_logs[-1]["plan"] if mood_logs else ""
    return render_template("mood.html", moods=mood_logs, latest_plan=latest_plan)


@app.route("/admin")
def admin():
    return render_template("admin.html", chats=chat_logs, moods=mood_logs)


@app.route("/get_response", methods=["POST"])
def get_response():
    payload = request.json or {}
    user_message = payload.get("message", "").strip()
    mode = payload.get("mode", "auto")
    message_lower = user_message.lower()

    if not user_message:
        return jsonify({"response": "I'm here whenever you're ready. You can type how you're feeling in one line. 💬"})

    topics = detect_topics(message_lower)
    if topics:
        conversation_memory.append(", ".join(topics))
        if len(conversation_memory) > 8:
            conversation_memory.pop(0)

    if contains_any(message_lower, CRISIS_KEYWORDS):
        response = (
            "🚨 You are not alone, and your life matters. Please reach immediate support now.\n"
            "US & Canada: Call or text 988 (24/7 Suicide & Crisis Lifeline)\n"
            "India: Tele-MANAS 14416 or 1-800-891-4416\n"
            "If you are in immediate danger, call emergency services now."
        )
    elif should_use_detailed_response(message_lower, mode, topics):
        response = detail_answer(user_message, message_lower, mode)
    elif contains_any(message_lower, ["stress", "overwhelm", "pressure", "burnout"]):
        response = "🫶 " + choice(STRESS_RESPONSES)
    elif contains_any(message_lower, ["sad", "cry"]):
        response = "🌧️ " + choice(SAD_RESPONSES)
    elif contains_any(message_lower, ["anxiety", "panic", "nervous", "fear", "worried"]):
        response = "🌿 " + choice(ANXIETY_RESPONSES)
    elif contains_any(message_lower, ["sleep", "insomnia", "tired", "night"]):
        response = "🌙 " + choice(SLEEP_RESPONSES)
    elif contains_any(message_lower, ["alone", "lonely", "isolated", "nobody"]):
        response = "🤝 " + choice(LONELY_RESPONSES)
    elif contains_any(message_lower, ["thanks", "thank you"]):
        response = "💛 You're welcome. I'm proud of you for reaching out today."
    elif "hope" in message_lower:
        response = "✨ You are still here, and that means strength. One gentle step today is enough."
    else:
        response = "💬 " + choice(DEFAULT_RESPONSES)

    chat_logs.append({
        "user": user_message,
        "bot": response,
        "mode": mode,
        "time": datetime.datetime.now().strftime("%H:%M:%S")
    })

    return jsonify({"response": response})


if __name__ == "__main__":
    app.run(debug=True)
