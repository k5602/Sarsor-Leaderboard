
import os
from dotenv import load_dotenv

load_dotenv()

# --- General Settings ---
APP_TITLE = "Monthly Leaderboard"

# --- Participants ---
DEFAULT_PARTICIPANTS = [
    'Eman', 'Nader', 'Desha', 'Youssef', 'Menna', 'Gasser', 'Hager', 'Sondos',
    'Schrödinger', 'Khaled'
]

# --- Scoring ---
MAX_DAILY_BASE = 100
MAX_BONUS = 50
CATEGORIES = {
    'Academic Performance': 30,
    'Project Task Completion': 25,
    'Collaborative Skills': 20,
    'Innovation and Initiative': 15,
    'Presentation and Communication': 10
}

# --- File Paths ---
DATA_FILE = 'leaderboard_data.csv'
BADGES_FILE = 'badges.json'
PARTICIPANT_BADGES_FILE = 'participant_badges.json'
ACHIEVEMENT_FILE = 'achievements.json'
STREAKS_FILE = 'streaks_data.json'
CHALLENGES_FILE = 'challenges.json'

# --- Admin ---
ADMIN_HASH = os.getenv('ADMIN_HASH')
if not ADMIN_HASH:
    raise ValueError("Admin hash not configured in environment variables")
ADMIN_CODE = "admin"

# --- Badges ---
BADGES = {
    "🏆 Top Performer": "Awarded for consistently high performance",
    "⭐ Rising Star": "Shows remarkable improvement",
    "🎯 Goal Crusher": "Exceeds target goals",
    "🤝 Team Player": "Excellence in collaboration",
    "💡 Innovator": "Creative problem-solving",
    "🎓 Academic Excellence": "Outstanding academic achievement",
    "🚀 Quick Learner": "Rapid skill acquisition",
    "👑 Leadership": "Demonstrates leadership qualities",
    "🌟 Perfect Attendance": "100% attendance record",
    "🎨 Creative Genius": "Exceptional creativity"
}

BADGE_LEVELS = {
    "bronze": "🥉",
    "silver": "🥈",
    "gold": "🥇"
}

BADGE_CATEGORIES = {
    "achievement": "🏆",
    "performance": "📈",
    "streak": "🔥",
    "challenge": "⚔️",
    "warning": "⚠️"
}

WARNING_BADGES = {
    "⚠️ Performance Alert": "Ranked in bottom 2 positions",
    "📉 Declining Trend": "Decreasing performance for 3 consecutive months",
    "❌ Missed Goals": "Failed to meet minimum requirements"
}

PUNISHMENT_BADGES = {
    "⚠️ Minor Warning": -10,
    "❌ Major Warning": -20,
    "💀 Critical Warning": -30
}

# --- Milestones & Streaks ---
MILESTONE_TIERS = {
    'First 1000': 1000,
    '5000 Club': 5000,
    '10000 Master': 10000,
    '25000 Legend': 25000
}

STREAK_BADGES = {
    3: '🔥 3-Day Streak',
    7: '🔥 Week Warrior',
    14: '🔥 Fortnight Fighter',
    30: '🔥 Monthly Master'
}

# --- Achievements ---
ACHIEVEMENTS = {
    "performance": {
        "Perfect Score": {
            "criteria": lambda points: points >= 150,
            "levels": {
                "bronze": 1,
                "silver": 3,
                "gold": 5
            }
        },
        "Top Performer": {
            "criteria": lambda rank: rank == 1,
            "levels": {
                "bronze": 1,
                "silver": 3,
                "gold": 5
            }
        }
    },
    "streak": {
        "Consistency King": {
            "criteria": lambda streak: streak >= 3,
            "levels": {
                "bronze": 3,
                "silver": 6,
                "gold": 12
            }
        }
    }
}

# --- UI ---
CONFETTI_CSS = """
<style>
@keyframes confetti {
    0% { transform: translateY(0) rotateX(0) rotateY(0); }
    100% { transform: translateY(100vh) rotateX(360deg) rotateY(360deg); }
}
.confetti {
    position: fixed;
    animation: confetti 3s linear forwards;
    z-index: 9999;
}
</style>
"""
