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

st.set_page_config(page_title="Monthly Leaderboard", layout="wide")

# Core configuration - Edit these values to customize the leaderboard
DEFAULT_PARTICIPANTS = ['Sama', 'Nader', 'Desha', 'Sara', 'Youssef',
                       'Menna', 'Gasser', 'Hams', 'Rowan', 'Nada', 'Khaled']
MAX_DAILY_BASE = 100
MAX_BONUS = 50

# Performance categories and their maximum points
CATEGORIES = {
    'Academic Performance': 30,
    'Project Task Completion': 25,
    'Collaborative Skills': 20,
    'Innovation and Initiative': 15,
    'Presentation and Communication': 10
}

# File paths for data storage
DATA_FILE = 'leaderboard_data.csv'
BADGES_FILE = 'badges.json'
PARTICIPANT_BADGES_FILE = 'participant_badges.json'
ACHIEVEMENT_FILE = 'achievements.json'
STREAKS_FILE = 'streaks.json'
CHALLENGES_FILE = 'challenges.json'

# Security settings
load_dotenv()

# Ensure ADMIN_HASH is properly configured
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
            df = pd.read_csv(DATA_FILE, parse_dates=['Date'], dayfirst=True)
            
            # Ensure required columns exist
            required_columns = ['Name', 'Date', 'Month', 'Base Points', 'Bonus Points', 'Total Points'] + list(CATEGORIES.keys())
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
            
            # Convert date columns
            if not pd.api.types.is_datetime64_any_dtype(df['Date']):
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            
            # Remove invalid dates
            df = df.dropna(subset=['Date'])
            df['Month'] = df['Date'].dt.to_period('M')
            
            return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
    
    # Return empty DataFrame with correct columns if loading fails
    return pd.DataFrame(columns=[
        'Name', 'Date', 'Month', 'Base Points', 'Bonus Points', 'Total Points'
    ] + list(CATEGORIES.keys()))

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def initialize_month():
    current_date = pd.Timestamp(datetime.now().date())  # Convert to Pandas Timestamp
    new_month = current_date.to_period('M')
    return pd.DataFrame([{
        'Name': name,
        'Date': current_date,  # Store as Timestamp
        'Month': new_month,
        'Base Points': 0,
        'Bonus Points': 0,
        'Total Points': 0,
        **{k: 0 for k in CATEGORIES}
    } for name in DEFAULT_PARTICIPANTS])

# Add helper function to update points - moved from bottom to here
def update_participant_points(participant, points):
    current_date = datetime.now().date()
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

# Add new display functions
def display_achievements(achievement_system, participant):
    st.markdown(f"### 🏆 Achievements for {participant}")
    if participant in achievement_system.data:
        for category, achievements in achievement_system.data[participant].items():
            st.markdown(f"#### {achievement_system.badge_categories[category]} {category.capitalize()}")
            for achievement, count in achievements.items():
                level = next((lvl for lvl, req in achievement_system.badge_levels.items() if count >= req), None)
                if level:
                    st.markdown(f"- {achievement_system.badge_levels[level]} {achievement} ({count})")
    else:
        st.markdown("No achievements yet.")

def display_challenges(challenge_system):
    st.markdown("### ⚔️ Active Challenges")
    for challenge_name, challenge in challenge_system.challenges.items():
        st.markdown(f"#### {challenge_name}")
        st.markdown(f"- **Description**: {challenge['description']}")
        st.markdown(f"- **Participants**: {', '.join(challenge.get('participants', []))}")

def check_warning_badges(participant_data, historical_data):
    warnings = []
    if participant_data['Rank'] >= len(DEFAULT_PARTICIPANTS) - 1:
        warnings.append(WARNING_BADGES["⚠️ Performance Alert"])
    if len(historical_data) >= 3 and all(historical_data[i]['Total Points'] > historical_data[i+1]['Total Points'] for i in range(-3, -1)):
        warnings.append(WARNING_BADGES["📉 Declining Trend"])
    if participant_data['Total Points'] < 50:
        warnings.append(WARNING_BADGES["❌ Missed Goals"])
    return warnings

def display_advanced_analytics(achievement_system, challenge_system):
    st.markdown("### 🏆 Achievement Analytics")
    achievement_counts = {}
    for participant, categories in achievement_system.data.items():
        for category, achievements in categories.items():
            for achievement, count in achievements.items():
                if achievement not in achievement_counts:
                    achievement_counts[achievement] = 0
                achievement_counts[achievement] += count
    achievement_df = pd.DataFrame(list(achievement_counts.items()), columns=['Achievement', 'Count'])
    fig = px.bar(achievement_df, x='Achievement', y='Count', title='Achievement Distribution')
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### ⚔️ Challenge Analytics")
    challenge_counts = {name: len(challenge.get('participants', [])) for name, challenge in challenge_system.challenges.items()}
    challenge_df = pd.DataFrame(list(challenge_counts.items()), columns=['Challenge', 'Participants'])
    fig = px.bar(challenge_df, x='Challenge', y='Participants', title='Challenge Participation')
    st.plotly_chart(fig, use_container_width=True)

def admin_challenge_interface(challenge_system):
    st.markdown("### ⚔️ Manage Challenges")
    
    tabs = st.tabs(["Create Challenge", "Review Requests", "Manage Challenges"])
    
    with tabs[0]:
        challenge_name = st.text_input("Challenge Name")
        challenge_description = st.text_area("Challenge Description")
        bonus_points = st.number_input("Bonus Points", min_value=0, max_value=50)
        if st.button("Add Challenge"):
            challenge_system.add_challenge({
                "name": challenge_name,
                "description": challenge_description,
                "bonus_points": bonus_points
            })
            st.success("Challenge added!")
    
    with tabs[1]:
        for challenge_name, requests in challenge_system.pending_requests.items():
            if requests:
                st.markdown(f"#### {challenge_name}")
                for participant in requests:
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.write(participant)
                    with col2:
                        points = st.number_input(
                            "Points",
                            min_value=0,
                            max_value=50,
                            key=f"points_{challenge_name}_{participant}"
                        )
                    with col3:
                        if st.button("Approve", key=f"approve_{challenge_name}_{participant}"):
                            if challenge_system.approve_request(participant, challenge_name, points):
                                # Update participant's points in the database
                                update_participant_points(participant, points)
                                st.success("Request approved and points awarded!")
                        if st.button("Reject", key=f"reject_{challenge_name}_{participant}"):
                            if challenge_system.reject_request(participant, challenge_name):
                                st.success("Request rejected!")
    
    with tabs[2]:
        st.markdown("### Remove Challenges")
        if challenge_system.challenges:
            for challenge_name, challenge in challenge_system.challenges.items():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{challenge_name}**")
                    st.markdown(f"_{challenge.get('description', 'No description')}_")
                with col2:
                    if st.button("Remove", key=f"remove_{challenge_name}"):
                        if challenge_system.remove_challenge(challenge_name):
                            st.success(f"Challenge '{challenge_name}' removed!")
                            st.rerun()
        else:
            st.info("No challenges to manage")

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
    tabs += ["➕✏️ Add/Edit Entries", "🏅 Manage Badges", "⚔️ Manage Challenges"]
    
current_tab = st.tabs(tabs)

def calculate_cumulative_points(df, current_month):
    try:
        # Convert current_month to Period if needed
        if isinstance(current_month, str):
            current_month = pd.Period(current_month)
        
        # Ensure date comparison compatibility
        monthly_df = df[df['Month'] == current_month].copy()
        
        if monthly_df.empty:
            # Return empty DataFrame with correct columns
            return pd.DataFrame(columns=['Name', 'Rank', 'Base Points', 'Bonus Points', 'Total Points'])
        
        monthly_df['Date'] = pd.to_datetime(monthly_df['Date']).dt.date  # Normalize dates
        monthly_df = monthly_df.sort_values('Date')
        
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
                    'Name': name,  # Add Name explicitly
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
        
        # Return sorted DataFrame with specific columns
        return cumulative_df[['Name', 'Rank', 'Base Points', 'Bonus Points', 'Total Points']].sort_values('Rank')
    
    except Exception as e:
        st.error(f"Error calculating points: {str(e)}")
        # Return empty DataFrame with correct columns
        return pd.DataFrame(columns=['Name', 'Rank', 'Base Points', 'Bonus Points', 'Total Points'])

with current_tab[0]:
    current_month = datetime.now().strftime('%Y-%m')
    if not st.session_state.df.empty:
        cumulative_df = calculate_cumulative_points(st.session_state.df, current_month)
        st.subheader(f"Monthly Leaderboard - {current_month}")
        badges_data = load_badges()
        display_leaderboard(cumulative_df, badges_data)
        
        for _, participant_data in cumulative_df.iterrows():
            historical_data = st.session_state.df[
                st.session_state.df['Name'] == participant_data['Name']
            ].sort_values('Date')
            warning_badges = check_warning_badges(participant_data, historical_data.to_dict('records'))
            if warning_badges:
                with st.expander(f"⚠️ Warnings for {participant_data['Name']}"):
                    for warning in warning_badges:
                        st.markdown(f"- {warning}")
    else:
        st.warning("No entries for current month")

with current_tab[1]:
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

with current_tab[2]:
    badges_data = load_badges()
    st.markdown("### 🏅 Available Badges")
    
    for badge, description in BADGES.items():
        st.markdown(f"**{badge}**: {description}")
    
    st.markdown("### 🏆 Awarded Badges")
    for participant, badges in badges_data.items():
        if badges:
            st.markdown(f"**{participant}**:")
            st.markdown(" ".join(badges))

with current_tab[3]:  # Achievements tab
    selected_participant = st.selectbox(
        "Select Participant", 
        DEFAULT_PARTICIPANTS,
        key="achievement_view_participant"  # Added unique key
    )
    display_achievements(st.session_state.achievement_system, selected_participant)

with current_tab[4]:  # Challenges tab
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
    with current_tab[5]:
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
                    'Date': edit_date,
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
                st.success("Entry saved successfully!")
        
        with entry_tabs[1]:
            # Edit existing entry
            st.subheader("Edit Existing Entry")
            
            # Date filter for existing entries
            available_dates = pd.to_datetime(st.session_state.df['Date'].unique()).date
            if len(available_dates) > 0:
                selected_date = st.selectbox(
                    "Select Date to Edit",
                    sorted(available_dates, reverse=True),
                    key="edit_entry_date"
                )
                
                # Get entries for selected date
                date_entries = st.session_state.df[
                    st.session_state.df['Date'].dt.date == selected_date
                ]
                
                if not date_entries.empty:
                    selected_entry_name = st.selectbox(
                        "Select Participant to Edit",
                        date_entries['Name'].unique(),
                        key="edit_entry_participant"
                    )
                    
                    # Get the selected entry
                    entry_to_edit = date_entries[date_entries['Name'] == selected_entry_name].iloc[0]
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("### Base Points")
                        base_points = {}
                        total_base = 0
                        for category, max_points in CATEGORIES.items():
                            base_points[category] = st.slider(
                                f"{category} ({max_points})",
                                0, max_points,
                                value=int(entry_to_edit[category]),
                                key=f"edit_{category}"
                            )
                            total_base += base_points[category]
                        
                        st.metric("Total Base Points", f"{total_base}/100")
                    
                    with col2:
                        st.write("### Bonus Points")
                        bonus_points = st.slider(
                            "Bonus Points", 0, MAX_BONUS,
                            value=int(entry_to_edit['Bonus Points']),
                            key="edit_bonus_points"
                        )
                        total_points = total_base + bonus_points
                        st.metric("Total Points", f"{total_points}/150")
                    
                    if st.button("Update Entry"):
                        # Remove existing entry
                        st.session_state.df = st.session_state.df[
                            ~((st.session_state.df['Date'].dt.date == selected_date) &
                              (st.session_state.df['Name'] == selected_entry_name))
                        ]
                        
                        # Add updated entry
                        updated_entry = {
                            'Name': selected_entry_name,
                            'Date': selected_date,
                            'Month': pd.Period(selected_date, freq='M'),
                            **base_points,
                            'Base Points': total_base,
                            'Bonus Points': bonus_points,
                            'Total Points': total_points
                        }
                        
                        st.session_state.df = pd.concat([
                            st.session_state.df,
                            pd.DataFrame([updated_entry])
                        ], ignore_index=True)
                        
                        save_data(st.session_state.df)
                        st.success("Entry updated successfully!")
                        st.rerun()
                else:
                    st.info("No entries found for selected date")
            else:
                st.info("No existing entries to edit")

# Add badge management tab for admins
if st.session_state.admin and len(current_tab) > 6:
    with current_tab[6]:
        badge_management()

if st.session_state.admin and len(current_tab) > 7:
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
