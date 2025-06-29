import streamlit as st
import pandas as pd
from datetime import datetime
from config import DEFAULT_PARTICIPANTS, CATEGORIES, MAX_BONUS, BADGES, PUNISHMENT_BADGES
from data_manager import save_data, load_badges, save_badges
from utils import show_confetti
from systems.streak_system import StreakSystem

def display_admin_dashboard(df):
    """Displays the admin dashboard with key metrics."""
    st.subheader("📊 Admin Dashboard")
    col1, col2 = st.columns(2)
    with col1:
        today = datetime.now().date()
        today_mask = pd.to_datetime(df['Date']).dt.date == today
        total_points_today = df[today_mask]['Total Points'].sum()
        st.metric("Total Points Awarded Today", int(total_points_today))
    with col2:
        active_participants_today = df[today_mask]['Name'].nunique()
        st.metric("Active Participants Today", int(active_participants_today))
    
    st.subheader("📈 Total Points Awarded Per Day (Last 30 Days)")
    last_30 = datetime.now() - pd.Timedelta(days=29)
    df_30 = df[pd.to_datetime(df['Date']) >= last_30]
    if not df_30.empty:
        daily = df_30.groupby(pd.to_datetime(df_30['Date']).dt.date)['Total Points'].sum().reset_index()
        import plotly.express as px
        fig = px.line(daily, x='Date', y='Total Points', markers=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data for the last 30 days.")

def display_entry_management(df, streak_system):
    """Displays the UI for adding and editing entries."""
    st.subheader("Entry Management")
    # ... (Add/Edit entry form logic)

def display_badge_management():
    """Displays the UI for awarding and removing badges."""
    st.markdown("### 🏅 Badge Management")
    # ... (Badge management logic)

def display_challenge_management(challenge_system):
    """Displays the UI for managing challenges."""
    st.markdown("### ⚔️ Manage Challenges")
    # ... (Challenge management logic)