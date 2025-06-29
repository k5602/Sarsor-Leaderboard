import streamlit as st
from datetime import datetime
import pandas as pd

from config import APP_TITLE, DEFAULT_PARTICIPANTS
from auth import initialize_auth_state, login_user, logout_user
from data_manager import load_data, save_data, initialize_month
from systems import AchievementSystem, ChallengeSystem, StreakSystem
from ui import (
    display_leaderboard, display_analytics, display_badges, 
    display_achievements, display_challenges,
    display_admin_dashboard, display_entry_management, 
    display_badge_management, display_challenge_management
)

st.set_page_config(page_title=APP_TITLE, layout="wide")

def initialize_session_state():
    """Initializes all necessary session state variables."""
    initialize_auth_state()
    if 'df' not in st.session_state:
        st.session_state.df = load_data()
    if 'achievement_system' not in st.session_state:
        st.session_state.achievement_system = AchievementSystem()
    if 'challenge_system' not in st.session_state:
        st.session_state.challenge_system = ChallengeSystem()
    if 'streak_system' not in st.session_state:
        st.session_state.streak_system = StreakSystem()
    if 'user' not in st.session_state:
        st.session_state.user = None

def calculate_cumulative_points(df, filter_mode):
    # ... (Add the calculate_cumulative_points function here)
    return pd.DataFrame() # Placeholder

def main():
    """Main function to run the Streamlit application."""
    initialize_session_state()

    st.title(f"📊 {APP_TITLE}")

    # Hidden input for admin login trigger
    st.markdown("""
        <style>
            #admin-key-input { display: none; }
        </style>
    """, unsafe_allow_html=True)
    
    key_input = st.text_input("Hidden Input", key="admin-key-input", label_visibility="collapsed")
    if key_input == "admin":
        st.session_state.show_admin_login = True
        # Reset the input to allow re-triggering if needed
        st.query_params.clear()

    # --- User Selection ---
    if not st.session_state.admin:
        st.session_state.user = st.selectbox(
            "Select Your Name",
            DEFAULT_PARTICIPANTS,
            key="user_select"
        )

    # --- Admin Login/Logout ---
    if st.session_state.show_admin_login:
        with st.sidebar.expander("🔐 Admin Login", expanded=True):
            password = st.text_input("Password", type="password", key="admin_pass")
            if st.button("Login"):
                login_user(password)
    
    if st.session_state.admin:
        with st.sidebar:
            if st.button("Logout"):
                logout_user()

    # --- Main Tabs ---
    tabs = ["Leaderboard", "Analytics", "Badges", "Achievements", "Challenges"]
    if st.session_state.admin:
        tabs.insert(1, "Admin Dashboard")
        tabs += ["Add/Edit Entries", "Manage Badges", "Manage Challenges"]

    icons = ["🏅", "📈", "🎖️", "🏆", "⚔️"]
    if st.session_state.admin:
        icons.insert(1, "📊")
        icons += ["➕", "🏅", "⚔️"]

    current_tab = st.tabs([f"{icon} {tab}" for icon, tab in zip(icons, tabs)])

    # --- Tab Content ---
    with current_tab[0]:
        filter_mode = st.radio(
            "Time Period:",
            ["This Month", "This Week", "All Time"],
            horizontal=True,
            key="leaderboard_time_filter"
        )
        cumulative_df = calculate_cumulative_points(st.session_state.df, filter_mode)
        display_leaderboard(cumulative_df, st.session_state.df)

    analytics_tab_index = 2 if st.session_state.admin else 1
    with current_tab[analytics_tab_index]:
        display_analytics(st.session_state.df, st.session_state.achievement_system, st.session_state.challenge_system)

    badges_tab_index = 3 if st.session_state.admin else 2
    with current_tab[badges_tab_index]:
        display_badges()

    achievements_tab_index = 4 if st.session_state.admin else 3
    with current_tab[achievements_tab_index]:
        display_achievements(st.session_state.achievement_system)

    challenges_tab_index = 5 if st.session_state.admin else 4
    with current_tab[challenges_tab_index]:
        display_challenges(st.session_state.challenge_system)

    if st.session_state.admin:
        with current_tab[1]:
            display_admin_dashboard(st.session_state.df)
        with current_tab[6]:
            display_entry_management(st.session_state.df, st.session_state.streak_system)
        with current_tab[7]:
            display_badge_management()
        with current_tab[8]:
            display_challenge_management(st.session_state.challenge_system)

if __name__ == "__main__":
    main()