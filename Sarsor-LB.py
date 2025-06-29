import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import hashlib
import streamlit.components.v1 as components
import json
from PIL import Image
import base64
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import time
st.set_page_config(page_title="Monthly Leaderboard", layout="wide")

DEFAULT_PARTICIPANTS = ['Eman', 'Nader', 'Desha','Youssef',
                       'Menna', 'Gasser', 'Hager', 'Sondos', 'Schrödinger', 'Khaled']
MAX_DAILY_BASE = 100
MAX_BONUS = 50

CATEGORIES = {
    'Academic Performance': 30,
    'Project Task Completion': 25,
    'Collaborative Skills': 20,
    'Innovation and Initiative': 15,
    'Presentation and Communication': 10
}

DATA_FILE = 'leaderboard_data.csv'
BADGES_FILE = 'badges.json'
PARTICIPANT_BADGES_FILE = 'participant_badges.json'
ACHIEVEMENT_FILE = 'achievements.json'
STREAKS_FILE = 'streaks_data.json'
CHALLENGES_FILE = 'challenges.json'

load_dotenv()

ADMIN_HASH = os.getenv('ADMIN_HASH')
if not ADMIN_HASH:
    raise ValueError("Admin hash not configured in environment variables")

ADMIN_CODE = "admin"

# Add badge constants and configurations
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

# Add confetti animation CSS
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

# Add secret key detection
if 'key_sequence' not in st.session_state:
    st.session_state.key_sequence = ""

# Hidden input for key sequence
st.markdown("""
    <style>
        #admin-key-input { display: none; }
    </style>
    """, unsafe_allow_html=True)

key_input = st.text_input("Hidden Input", key="admin-key-input", label_visibility="collapsed")

# Check for admin access code
if key_input == ADMIN_CODE:
    st.session_state.show_admin_login = True
    # Reset the input
    st.query_params.clear()

# Initialize session state for keyboard shortcut
if 'keyboard_shortcut' not in st.session_state:
    st.session_state.keyboard_shortcut = False

# Handle the keyboard shortcut event
if 'keyboard_shortcut' in st.session_state and st.session_state.keyboard_shortcut:
    st.session_state.show_admin_login = True
    st.session_state.keyboard_shortcut = False

# Security functions
def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

# Improve verify_password with better error handling
def verify_password(password):
    try:
        if not password or not isinstance(password, str):
            return False

        current_time = datetime.now()
        if 'last_login_attempt' in st.session_state:
            time_diff = (current_time - st.session_state.last_login_attempt).total_seconds()
            if time_diff < 2:  # 2 second delay between attempts
                st.error("Please wait before trying again")
                return False

        st.session_state.last_login_attempt = current_time
        return hashlib.sha256(password.encode('utf-8')).hexdigest() == ADMIN_HASH
    except Exception as e:
        st.error(f"Login error occurred: {str(e)}")
        return False

# Data management
# Improve error handling in load_data
def load_data():
    try:
        if os.path.exists(DATA_FILE):
            df = pd.read_csv(DATA_FILE)
            # Handle different date formats more flexibly
            df['Date'] = pd.to_datetime(df['Date'], format='mixed')
            df['Month'] = pd.to_datetime(df['Date']).dt.to_period('M')
            return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")

    # Return empty DataFrame with correct columns
    return pd.DataFrame(columns=[
        'Name', 'Date', 'Month', 'Base Points', 'Bonus Points', 'Total Points'
    ] + list(CATEGORIES.keys()))

def save_data(df):
    # Ensure date is in consistent format before saving
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
    df.to_csv(DATA_FILE, index=False)

def initialize_month():
    current_date = pd.Timestamp(datetime.now().date()).strftime('%Y-%m-%d')
    new_month = pd.Period(datetime.now(), freq='M')
    return pd.DataFrame([{
        'Name': name,
        'Date': current_date,
        'Month': new_month,
        'Base Points': 0,
        'Bonus Points': 0,
        'Total Points': 0,
        **{k: 0 for k in CATEGORIES}
    } for name in DEFAULT_PARTICIPANTS])

# Add helper function to update points - moved from bottom to here
def update_participant_points(participant, points):
    current_date = datetime.now().strftime('%Y-%m-%d')  # Format date consistently
    new_entry = {
        'Name': participant,
        'Date': current_date,
        'Month': pd.Period(current_date, freq='M'),
        'Base Points': 0,
        'Bonus Points': points,
        'Total Points': points,
        **{k: 0 for k in CATEGORIES}  # Add CATEGORIES fields with default 0
    }

    st.session_state.df = pd.concat([
        st.session_state.df,
        pd.DataFrame([new_entry])
    ], ignore_index=True)

    save_data(st.session_state.df)
    trigger_milestone_and_streak_checks(participant)

# Add badge management functions
def load_badges():
    if os.path.exists(PARTICIPANT_BADGES_FILE):
        with open(PARTICIPANT_BADGES_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_badges(badges_data):
    with open(PARTICIPANT_BADGES_FILE, 'w') as f:
        json.dump(badges_data, f)

def show_confetti():
    st.markdown(CONFETTI_CSS, unsafe_allow_html=True)
    confetti_js = """
    <script>
    function createConfetti() {
        const colors = ['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff'];
        for (let i = 0; i < 50; i++) {
            const confetti = document.createElement('div');
            confetti.className = 'confetti';
            confetti.style.left = Math.random() * 100 + 'vw';
            confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
            confetti.style.width = '10px';
            confetti.style.height = '10px';
            document.body.appendChild(confetti);
            setTimeout(() => confetti.remove(), 3000);
        }
    }
    createConfetti();
    </script>
    """
    components.html(confetti_js, height=0)

# Add display functions
def display_leaderboard(cumulative_df, badges_data):
    cols = st.columns([3, 1])

    with cols[0]:
        if not cumulative_df.empty:
            # Ensure all required columns exist
            display_df = cumulative_df[['Name', 'Rank', 'Base Points', 'Bonus Points', 'Total Points']]

            st.dataframe(
                display_df.style
                .background_gradient(subset=['Total Points'], cmap='YlGn')
                .format({'Base Points': '{:.0f}', 'Bonus Points': '{:.0f}', 'Total Points': '{:.0f}'}),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No data to display")

    with cols[1]:
        st.markdown("### 🏅 Top 3 Performers")
        top_3 = cumulative_df.head(3)
        if not top_3.empty:
            for idx, row in top_3.iterrows():
                medal = "🥇" if row['Rank'] == 1 else "🥈" if row['Rank'] == 2 else "🥉"
                st.markdown(f"{medal} {row['Name']} - {int(row['Total Points'])} pts")
                if row['Name'] in badges_data:
                    st.markdown(" ".join(badges_data[row['Name']]))
        else:
            st.info("No performers to display")

def badge_management():
    st.markdown("### 🏅 Badge Management")
    badges_data = load_badges()

    tabs = st.tabs(["Award/Remove Badges", "Apply Punishment", "Current Badges"])

    with tabs[0]:
        mode = st.radio("Mode", ["Award Badge", "Remove Badge"], key="badge_mode")
        selected_participant = st.selectbox(
            "Select Participant",
            DEFAULT_PARTICIPANTS,
            key="badge_mgmt_participant"
        )

        if mode == "Award Badge":
            selected_badge = st.selectbox(
                "Select Badge",
                list(BADGES.keys()),
                key="badge_mgmt_type"
            )
            if st.button("Award Badge"):
                if selected_participant not in badges_data:
                    badges_data[selected_participant] = []
                if selected_badge not in badges_data[selected_participant]:
                    badges_data[selected_participant].append(selected_badge)
                    save_badges(badges_data)
                    show_confetti()
                    st.success(f"Badge awarded to {selected_participant}!")
        else:
            if selected_participant in badges_data and badges_data[selected_participant]:
                selected_badge = st.selectbox(
                    "Select Badge to Remove",
                    badges_data[selected_participant],
                    key="badge_remove_select"
                )
                if st.button("Remove Badge"):
                    badges_data[selected_participant].remove(selected_badge)
                    if not badges_data[selected_participant]:
                        del badges_data[selected_participant]
                    save_badges(badges_data)
                    st.success(f"Badge removed from {selected_participant}")
            else:
                st.info("No badges to remove for this participant")

    with tabs[1]:
        st.markdown("### ⚠️ Apply Punishment")
        punishment_participant = st.selectbox(
            "Select Participant",
            DEFAULT_PARTICIPANTS,
            key="punishment_participant"
        )
        punishment_type = st.selectbox(
            "Select Punishment",
            list(PUNISHMENT_BADGES.keys()),
            key="punishment_type"
        )
        if st.button("Apply Punishment"):
            points = PUNISHMENT_BADGES[punishment_type]
            update_participant_points(punishment_participant, points)
            st.success(f"Applied {punishment_type} ({points} points) to {punishment_participant}")

    with tabs[2]:
        st.markdown("### Current Badges")
        for participant, badges in badges_data.items():
            if badges:
                st.markdown(f"**{participant}**: {' '.join(badges)}")

def display_badge_analytics(badges_data):
    # ...existing analytics code...
    st.markdown("### 🏅 Badge Statistics")

    if badges_data:
        badge_counts = {}
        for badges in badges_data.values():
            for badge in badges:
                badge_counts[badge] = badge_counts.get(badge, 0) + 1

        badge_df = pd.DataFrame(list(badge_counts.items()), columns=['Badge', 'Count'])
        fig = px.bar(badge_df, x='Badge', y='Count', title='Badge Distribution')
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### 👑 Top Badge Earners")
        earner_counts = {participant: len(badges) for participant, badges in badges_data.items()}
        earner_df = pd.DataFrame(list(earner_counts.items()), columns=['Participant', 'Badges'])
        earner_df = earner_df.sort_values('Badges', ascending=False).head(5)

        for _, row in earner_df.iterrows():
            st.markdown(f"**{row['Participant']}**: {row['Badges']} badges")
            if row['Participant'] in badges_data:
                st.markdown(" ".join(badges_data[row['Participant']]))
                
# Add new constants after existing constants
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

WARNING_BADGES = {
    "⚠️ Performance Alert": "Ranked in bottom 2 positions",
    "📉 Declining Trend": "Decreasing performance for 3 consecutive months",
    "❌ Missed Goals": "Failed to meet minimum requirements"
}

# Add punishment badges
PUNISHMENT_BADGES = {
    "⚠️ Minor Warning": -10,
    "❌ Major Warning": -20,
    "💀 Critical Warning": -30
}

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

# Add class definitions after constants
class AchievementSystem:
    def __init__(self):
        self.achievements = ACHIEVEMENTS
        self.badge_levels = BADGE_LEVELS
        self.badge_categories = BADGE_CATEGORIES
        self.data = self.load_achievements()

    def load_achievements(self):
        if os.path.exists(ACHIEVEMENT_FILE):
            with open(ACHIEVEMENT_FILE, 'r') as f:
                return json.load(f)
        return {}

    def save_achievements(self):
        with open(ACHIEVEMENT_FILE, 'w') as f:
            json.dump(self.data, f)

    def check_achievements(self, participant, points, rank, streak):
        for category, achievements in self.achievements.items():
            for achievement, details in achievements.items():
                if details['criteria'](points if category == 'performance' else rank if category == 'rank' else streak):
                    self.award_badge(participant, category, achievement)

    def award_badge(self, participant, category, achievement):
        if participant not in self.data:
            self.data[participant] = {}
        if category not in self.data[participant]:
            self.data[participant][category] = {}
        if achievement not in self.data[participant][category]:
            self.data[participant][category][achievement] = 0
        self.data[participant][category][achievement] += 1
        self.save_achievements()

class ChallengeSystem:
    def __init__(self):
        self.challenges = {}
        self.pending_requests = {}
        data = self.load_challenges()
        self.challenges = data.get('challenges', {})
        self.pending_requests = data.get('pending', {})

    def load_challenges(self):
        if os.path.exists(CHALLENGES_FILE):
            with open(CHALLENGES_FILE, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return {'challenges': {}, 'pending': {}}
        return {'challenges': {}, 'pending': {}}

    def save_challenges(self):
        with open(CHALLENGES_FILE, 'w') as f:
            json.dump({
                'challenges': self.challenges,
                'pending': self.pending_requests
            }, f)

    def add_challenge(self, challenge):
        self.challenges[challenge['name']] = {
            'name': challenge['name'],
            'description': challenge['description'],
            'bonus_points': challenge['bonus_points'],
            'participants': [],
            'completed': []
        }
        self.save_challenges()

    def request_join(self, participant, challenge_name):
        if challenge_name not in self.pending_requests:
            self.pending_requests[challenge_name] = []
        if participant not in self.pending_requests[challenge_name]:
            self.pending_requests[challenge_name].append(participant)
            self.save_challenges()
            return True
        return False

    def approve_request(self, participant, challenge_name, points):
        if challenge_name in self.pending_requests and participant in self.pending_requests[challenge_name]:
            self.pending_requests[challenge_name].remove(participant)
            if challenge_name in self.challenges:
                self.challenges[challenge_name]['completed'].append({
                    'participant': participant,
                    'points': points,
                    'date': datetime.now().strftime('%Y-%m-%d')
                })
            self.save_challenges()
            return True
        return False

    def reject_request(self, participant, challenge_name):
        if challenge_name in self.pending_requests and participant in self.pending_requests[challenge_name]:
            self.pending_requests[challenge_name].remove(participant)
            self.save_challenges()
            return True
        return False

    def remove_challenge(self, challenge_name):
        """Remove a challenge and its pending requests"""
        if challenge_name in self.challenges:
            del self.challenges[challenge_name]
            if challenge_name in self.pending_requests:
                del self.pending_requests[challenge_name]
            self.save_challenges()
            return True
        return False

# Add new functions for streaks and milestones
def load_streaks_data():
    try:
        with open(STREAKS_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {"participants": {}, "milestones_awarded": {}}

def save_streaks_data(streaks_data):
    with open(STREAKS_FILE, 'w') as f:
        json.dump(streaks_data, f, indent=2)

def check_milestones(participant_name):
    streaks_data = load_streaks_data()
    milestones = streaks_data.get('milestones_awarded', {})
    awarded = milestones.get(participant_name, [])
    total_points = st.session_state.df[st.session_state.df['Name'] == participant_name]['Total Points'].sum()
    new_badges = []
    for tier, threshold in MILESTONE_TIERS.items():
        if total_points >= threshold and tier not in awarded:
            award_badge(participant_name, tier)
            new_badges.append(tier)
            awarded.append(tier)
    if new_badges:
        milestones[participant_name] = awarded
        streaks_data['milestones_awarded'] = milestones
        save_streaks_data(streaks_data)
    return new_badges

def check_streaks(participant_name):
    streaks_data = load_streaks_data()
    p = streaks_data['participants'].get(participant_name, {
        'current_streak': 0,
        'longest_streak': 0,
        'last_activity_date': None
    })
    df = st.session_state.df[st.session_state.df['Name'] == participant_name]
    if df.empty:
        return []
    dates = pd.to_datetime(df['Date']).dt.date.sort_values(ascending=False).unique()
    if len(dates) == 0:
        return []
    today = datetime.now().date()
    streak = 0
    last_date = None
    for d in dates:
        if last_date is None:
            if (today - d).days > 1:
                break
            streak = 1
            last_date = d
        else:
            if (last_date - d).days == 1:
                streak += 1
                last_date = d
            else:
                break
    p['current_streak'] = streak
    p['longest_streak'] = max(p.get('longest_streak', 0), streak)
    p['last_activity_date'] = str(dates[0])
    streaks_data['participants'][participant_name] = p
    save_streaks_data(streaks_data)
    new_badges = []
    for days, badge in STREAK_BADGES.items():
        if streak >= days and badge not in get_badges(participant_name):
            award_badge(participant_name, badge)
            new_badges.append(badge)
    return new_badges

def trigger_milestone_and_streak_checks(participant_name):
    new_milestones = check_milestones(participant_name)
    new_streaks = check_streaks(participant_name)
    if new_milestones or new_streaks:
        show_confetti()
        st.experimental_rerun()

# Important: Session state initialization
# Initialize session state more robustly
def initialize_session_state():
    if 'df' not in st.session_state:
        st.session_state.df = load_data()
    if 'admin' not in st.session_state:
        st.session_state.admin = False
    if 'show_admin_login' not in st.session_state:
        st.session_state.show_admin_login = False
    if 'achievement_system' not in st.session_state:
        st.session_state.achievement_system = AchievementSystem()
    if 'challenge_system' not in st.session_state:
        st.session_state.challenge_system = ChallengeSystem()
    if 'last_login_attempt' not in st.session_state:
        st.session_state.last_login_attempt = datetime.min

# Call initialization at startup
initialize_session_state()

# Initialize user session state
if 'user' not in st.session_state:
    if not st.session_state.admin:
        st.session_state.user = st.selectbox(
            "Select Your Name",
            DEFAULT_PARTICIPANTS,
            key="user_select"
        )

# Handle messages from JS
def handle_js_message(msg):
    if msg.get('type') == 'streamlit:keyboardShortcut':
        st.session_state.keyboard_shortcut = True
        st.session_state.show_admin_login = True
        st.rerun()

st.title('📊 Monthly Cumulative Leaderboard')

# Admin login handling
if st.session_state.show_admin_login:
    with st.sidebar.expander("🔐 Admin Login", expanded=True):
        password = st.text_input("Password", type="password", key="admin_pass")
        if st.button("Login"):
            if verify_password(password):
                st.session_state.admin = True
                st.session_state.show_admin_login = False
                st.rerun()
            else:
                st.error("Incorrect password")

# Admin logout button
if st.session_state.admin:
    with st.sidebar:
        if st.button("Logout"):
            st.session_state.admin = False
            st.rerun()

# Main tabs
tabs = ["🏅 Leaderboard", "📈 Analytics", "🎖️ Badges", "🏆 Achievements", "⚔️ Challenges"]
if st.session_state.admin:
    tabs.insert(1, "📊 Admin Dashboard")  # Insert after Leaderboard
    tabs += ["➕✏️ Add/Edit Entries", "🏅 Manage Badges", "⚔️ Manage Challenges"]

current_tab = st.tabs(tabs)

def calculate_cumulative_points(df, current_month):
    try:
        # Create a copy of the dataframe to avoid modifications to original
        df = df.copy()

        # Ensure Date column is datetime with flexible parsing
        df['Date'] = pd.to_datetime(df['Date'], format='mixed')

        # Convert current_month to Period if needed
        if isinstance(current_month, str):
            current_month = pd.Period(current_month)

        # Filter for current month
        monthly_df = df[df['Month'] == current_month].copy()

        if monthly_df.empty:
            return pd.DataFrame(columns=['Name', 'Rank', 'Base Points', 'Bonus Points', 'Total Points'])

        # Calculate daily totals
        daily_totals = monthly_df.groupby(['Name', 'Date']).agg({
            'Base Points': 'last',
            'Bonus Points': 'last',
            'Total Points': 'sum'
        }).reset_index()

        # Calculate cumulative totals
        cumulative_points = {}
        for _, row in daily_totals.iterrows():
            name = row['Name']
            if name not in cumulative_points:
                cumulative_points[name] = {
                    'Name': name,
                    'Base Points': row['Base Points'],
                    'Bonus Points': row['Bonus Points'],
                    'Total Points': 0
                }
            cumulative_points[name]['Total Points'] += row['Total Points']

        # Convert to DataFrame
        cumulative_df = pd.DataFrame.from_dict(cumulative_points, orient='index').reset_index(drop=True)

        # Ensure all required columns exist
        required_columns = ['Name', 'Base Points', 'Bonus Points', 'Total Points']
        for col in required_columns:
            if col not in cumulative_df.columns:
                cumulative_df[col] = 0

        # Calculate ranks
        cumulative_df['Rank'] = cumulative_df['Total Points'].rank(method='min', ascending=False).astype(int)

        return cumulative_df[['Name', 'Rank', 'Base Points', 'Bonus Points', 'Total Points']].sort_values('Rank')

    except Exception as e:
        st.error(f"Error calculating points: {str(e)}")
        return pd.DataFrame(columns=['Name', 'Rank', 'Base Points', 'Bonus Points', 'Total Points'])

def get_filtered_dataframe(df, filter_mode):
    today = datetime.now().date()
    if filter_mode == 'This Week':
        week_ago = today - pd.Timedelta(days=6)
        mask = pd.to_datetime(df['Date']).dt.date.between(week_ago, today)
        return df[mask]
    elif filter_mode == 'This Month':
        month_start = today.replace(day=1)
        mask = pd.to_datetime(df['Date']).dt.date >= month_start
        return df[mask]
    else:
        return df

def calculate_filtered_leaderboard(df, filter_mode):
    filtered = get_filtered_dataframe(df, filter_mode)
    return calculate_cumulative_points(filtered)

with current_tab[0]:  # Leaderboard tab
    if 'leaderboard_filter' not in st.session_state:
        st.session_state.leaderboard_filter = 'This Month'
    filter_mode = st.radio(
        "Time Period:",
        ["This Month", "This Week", "All Time"],
        index=["This Month", "This Week", "All Time"].index(st.session_state.leaderboard_filter),
        horizontal=True,
        key="leaderboard_time_filter"
    )
    st.session_state.leaderboard_filter = filter_mode
    if not st.session_state.df.empty:
        cumulative_df = calculate_filtered_leaderboard(st.session_state.df, filter_mode)
        st.subheader(f"Leaderboard - {filter_mode}")
        badges_data = load_badges()
        display_leaderboard(cumulative_df, badges_data)

        for _, participant_data in cumulative_df.iterrows():
            # Ensure proper date handling for historical data
            historical_data = st.session_state.df[
                st.session_state.df['Name'] == participant_data['Name']
            ].copy()

            # Convert Date column to datetime if it isn't already
            if 'Date' in historical_data.columns:
                historical_data['Date'] = pd.to_datetime(historical_data['Date'])
                historical_data = historical_data.sort_values('Date', ascending=False)

            warning_badges = check_warning_badges(participant_data, historical_data)
            if warning_badges:
                with st.expander(f"⚠️ Warnings for {participant_data['Name']}"):
                    for warning in warning_badges:
                        st.markdown(f"- {warning}")

# Determine correct tab index for Analytics
analytics_tab_index = 2 if st.session_state.admin else 1
with current_tab[analytics_tab_index]:
    st.subheader("Monthly Analytics")

    current_month = datetime.now().strftime('%Y-%m')
    monthly_df = st.session_state.df[st.session_state.df['Month'] == current_month]

    if not monthly_df.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.write("### Progress Over Time")
            fig = px.line(
                monthly_df,
                x='Date',
                y='Total Points',
                color='Name',
                markers=True
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.write("### Points Composition")
            fig = px.sunburst(
                monthly_df,
                path=['Name'],
                values='Total Points',
                color='Base Points'
            )
            st.plotly_chart(fig, use_container_width=True)

        badges_data = load_badges()
        display_badge_analytics(badges_data)
        display_advanced_analytics(st.session_state.achievement_system, st.session_state.challenge_system)
    else:
        st.warning("No data to display")

badges_tab_index = 3 if st.session_state.admin else 2
with current_tab[badges_tab_index]:
    badges_data = load_badges()
    st.markdown("### 🏅 Available Badges")

    for badge, description in BADGES.items():
        st.markdown(f"**{badge}**: {description}")

    st.markdown("### 🏆 Awarded Badges")
    for participant, badges in badges_data.items():
        if badges:
            st.markdown(f"**{participant}**:")
            st.markdown(" ".join(badges))

achievements_tab_index = 4 if st.session_state.admin else 3
with current_tab[achievements_tab_index]:  # Achievements tab
    selected_participant = st.selectbox(
        "Select Participant",
        DEFAULT_PARTICIPANTS,
        key="achievement_view_participant"  # Added unique key
    )
    display_achievements(st.session_state.achievement_system, selected_participant)

challenges_tab_index = 5 if st.session_state.admin else 4
with current_tab[challenges_tab_index]:  # Challenges tab
    if not st.session_state.admin:
        # User selector at the top of challenges tab
        selected_user = st.selectbox(
            "Select Your Name",
            DEFAULT_PARTICIPANTS,
            key="challenge_user_select"
        )
        st.session_state.user = selected_user

    st.markdown("### ⚔️ Active Challenges")
    if st.session_state.challenge_system.challenges:
        for challenge_name, challenge in st.session_state.challenge_system.challenges.items():
            with st.expander(f"📌 {challenge_name}"):
                st.markdown(f"**Description**: {challenge.get('description', 'No description')}")
                st.markdown(f"**Bonus Points**: {challenge.get('bonus_points', 0)}")

                # Show participants and pending requests
                st.markdown("**Current Participants:**")
                participants = challenge.get('participants', [])
                if participants:
                    for participant in participants:
                        st.markdown(f"- {participant}")
                else:
                    st.markdown("_No participants yet_")

                # Show pending requests
                pending = st.session_state.challenge_system.pending_requests.get(challenge_name, [])
                if pending:
                    st.markdown("**Pending Requests:**")
                    for p in pending:
                        st.markdown(f"- {p} _(pending approval)_")

                # Add apply button for users
                if not st.session_state.admin:
                    if st.session_state.user not in participants and st.session_state.user not in pending:
                        if st.button("Apply for Challenge", key=f"apply_{challenge_name}"):
                            if st.session_state.challenge_system.request_join(st.session_state.user, challenge_name):
                                st.success("Application submitted for approval!")
                                st.rerun()
                    else:
                        st.info("You have already applied or are participating in this challenge")
    else:
        st.info("No active challenges")

if st.session_state.admin:
    with current_tab[6]:  # Add/Edit Entries
        st.subheader("Entry Management")

        # Add tabs for adding new entries and editing existing ones
        entry_tabs = st.tabs(["Add New Entry", "Edit Existing Entry"])

        with entry_tabs[0]:
            # Existing new entry code
            edit_date = st.date_input("Select Date", datetime.now(), key="new_entry_date")
            selected_name = st.selectbox(
                "Select Participant",
                DEFAULT_PARTICIPANTS,
                key="new_entry_participant"
            )

            col1, col2 = st.columns(2)
            with col1:
                st.write("### Base Points")
                base_points = {}
                total_base = 0
                for category, max_points in CATEGORIES.items():
                    base_points[category] = st.slider(
                        f"{category} ({max_points})",
                        0, max_points,
                        key=f"new_{category}"
                    )
                    total_base += base_points[category]

                st.metric("Total Base Points", f"{total_base}/100")

            with col2:
                st.write("### Bonus Points")
                bonus_points = st.slider(
                    "Bonus Points", 0, MAX_BONUS,
                    key="new_bonus_points"
                )
                total_points = total_base + bonus_points
                st.metric("Total Points", f"{total_points}/150")

            if st.button("Save Entry"):
                new_entry = {
                    'Name': selected_name,
                    'Date': edit_date.strftime('%Y-%m-%d'),  # Format date consistently
                    'Month': pd.Period(edit_date, freq='M'),
                    **base_points,
                    'Base Points': total_base,
                    'Bonus Points': bonus_points,
                    'Total Points': total_points
                }

                st.session_state.df = pd.concat([
                    st.session_state.df,
                    pd.DataFrame([new_entry])
                ], ignore_index=True)

                save_data(st.session_state.df)
                trigger_milestone_and_streak_checks(selected_name)
                st.success("Entry saved successfully!")

        with entry_tabs[1]:
            # Edit existing entry
            st.subheader("Edit Existing Entry")

            # Convert dates properly and create unique entries list
            try:
                # Ensure Date column is datetime
                st.session_state.df['Date'] = pd.to_datetime(st.session_state.df['Date'])

                # Get unique dates and sort them
                available_dates = sorted(
                    st.session_state.df['Date'].dt.date.unique(),
                    reverse=True
                )

                if available_dates:
                    selected_date = st.selectbox(
                        "Select Date to Edit",
                        available_dates,
                        key="edit_entry_date"
                    )

                    # Filter entries for selected date
                    mask = st.session_state.df['Date'].dt.date == selected_date
                    date_entries = st.session_state.df[mask].copy()

                    if not date_entries.empty:
                        selected_entry_name = st.selectbox(
                            "Select Participant to Edit",
                            sorted(date_entries['Name'].unique()),
                            key="edit_entry_participant"
                        )

                        # Get the selected entry
                        entry_mask = (date_entries['Name'] == selected_entry_name)
                        if entry_mask.any():
                            entry_to_edit = date_entries[entry_mask].iloc[0]

                            col1, col2 = st.columns(2)
                            with col1:
                                st.write("### Base Points")
                                base_points = {}
                                total_base = 0
                                for category, max_points in CATEGORIES.items():
                                    current_value = int(entry_to_edit.get(category, 0))
                                    base_points[category] = st.slider(
                                        f"{category} ({max_points})",
                                        0, max_points,
                                        value=current_value,
                                        key=f"edit_{category}"
                                    )
                                    total_base += base_points[category]

                                st.metric("Total Base Points", f"{total_base}/100")

                            with col2:
                                st.write("### Bonus Points")
                                bonus_points = st.slider(
                                    "Bonus Points", 0, MAX_BONUS,
                                    value=int(entry_to_edit.get('Bonus Points', 0)),
                                    key="edit_bonus_points"
                                )
                                total_points = total_base + bonus_points
                                st.metric("Total Points", f"{total_points}/150")

                            if st.button("Update Entry"):
                                try:
                                    # Remove existing entry
                                    remove_mask = ~((st.session_state.df['Date'].dt.date == selected_date) &
                                                 (st.session_state.df['Name'] == selected_entry_name))
                                    st.session_state.df = st.session_state.df[remove_mask]

                                    # Create updated entry
                                    updated_entry = {
                                        'Name': selected_entry_name,
                                        'Date': pd.to_datetime(selected_date),
                                        'Month': pd.Period(selected_date, freq='M'),
                                        **base_points,
                                        'Base Points': total_base,
                                        'Bonus Points': bonus_points,
                                        'Total Points': total_points
                                    }

                                    # Add the updated entry
                                    st.session_state.df = pd.concat([
                                        st.session_state.df,
                                        pd.DataFrame([updated_entry])
                                    ], ignore_index=True)

                                    # Save the updated dataframe
                                    save_data(st.session_state.df)
                                    trigger_milestone_and_streak_checks(selected_entry_name)
                                    st.success("Entry updated successfully!")

                                    # Force rerun to refresh the display
                                    time.sleep(1)  # Small delay to ensure save completes
                                    st.rerun()

                                except Exception as e:
                                    st.error(f"Error updating entry: {str(e)}")
                        else:
                            st.warning("Selected entry not found")
                    else:
                        st.info("No entries found for selected date")
                else:
                    st.info("No existing entries to edit")

            except Exception as e:
                st.error(f"Error loading entries: {str(e)}")

# Admin Dashboard Tab (only visible to admins)
if st.session_state.admin and len(current_tab) > 1:
    with current_tab[1]:  # Admin Dashboard
        st.subheader("📊 Admin Dashboard")
        col1, col2 = st.columns(2)
        with col1:
            today = datetime.now().date()
            today_mask = pd.to_datetime(st.session_state.df['Date']).dt.date == today
            total_points_today = st.session_state.df[today_mask]['Total Points'].sum()
            st.metric("Total Points Awarded Today", int(total_points_today))
        with col2:
            active_participants_today = st.session_state.df[today_mask]['Name'].nunique()
            st.metric("Active Participants Today", int(active_participants_today))
        st.subheader("📈 Total Points Awarded Per Day (Last 30 Days)")
        last_30 = datetime.now() - pd.Timedelta(days=29)
        df_30 = st.session_state.df[pd.to_datetime(st.session_state.df['Date']) >= last_30]
        if not df_30.empty:
            daily = df_30.groupby(pd.to_datetime(df_30['Date']).dt.date)['Total Points'].sum().reset_index()
            import plotly.express as px
            fig = px.line(daily, x='Date', y='Total Points', markers=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data for the last 30 days.")

if st.session_state.admin:
    with current_tab[6]:
        badge_management()

if st.session_state.admin:
    with current_tab[7]:  # Manage Challenges tab
        admin_challenge_interface(st.session_state.challenge_system)

# Admin controls
if st.session_state.admin:
    with st.sidebar.expander("Admin Controls"):
        if st.button("Initialize New Month"):
            st.session_state.df = initialize_month()
            save_data(st.session_state.df)
            st.success("New month initialized!")

        st.download_button(
            "Export Full Data",
            data=st.session_state.df.to_csv().encode('utf-8'),
            file_name='leaderboard_full_data.csv',
            mime='text/csv'
        )

# Handle JS messages
try:
    if st.query_params and 'Message' in st.query_params:
        handle_js_message(st.query_params['Message'])
except Exception as e:
    st.warning(f"Failed to process JS message: {e}")

def display_achievements(achievement_system, participant):
    st.markdown(f"### 🏆 Achievements for {participant}")
    data = achievement_system.data.get(participant, {})
    if not data:
        st.info("No achievements yet.")
        return
    for category, achievements in data.items():
        st.markdown(f"#### {category.title()}")
        for achievement, count in achievements.items():
            st.markdown(f"- **{achievement}**: {count}")
