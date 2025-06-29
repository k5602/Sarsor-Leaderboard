
from datetime import datetime
import pandas as pd
import streamlit as st
from data_manager import load_streaks_data, save_streaks_data, load_badges, save_badges
from config import MILESTONE_TIERS, STREAK_BADGES
from utils import show_confetti

class StreakSystem:
    def __init__(self):
        self.data = load_streaks_data()

    def _save(self):
        save_streaks_data(self.data)

    def award_badge(self, participant_name, badge):
        """Awards a badge to a participant.""" 
        badges_data = load_badges()
        if participant_name not in badges_data:
            badges_data[participant_name] = []
        if badge not in badges_data[participant_name]:
            badges_data[participant_name].append(badge)
            save_badges(badges_data)

    def get_badges(self, participant_name):
        """Gets all badges for a participant."""
        badges_data = load_badges()
        return badges_data.get(participant_name, [])

    def check_milestones(self, participant_name):
        """Checks for and awards milestone badges."""
        milestones = self.data.get('milestones_awarded', {})
        awarded = milestones.get(participant_name, [])
        total_points = st.session_state.df[st.session_state.df['Name'] == participant_name]['Total Points'].sum()
        new_badges = []

        for tier, threshold in MILESTONE_TIERS.items():
            if total_points >= threshold and tier not in awarded:
                self.award_badge(participant_name, tier)
                new_badges.append(tier)
                awarded.append(tier)
        
        if new_badges:
            milestones[participant_name] = awarded
            self.data['milestones_awarded'] = milestones
            self._save()
        
        return new_badges

    def check_streaks(self, participant_name):
        """Checks for and awards streak badges."""
        p_data = self.data['participants'].get(participant_name, {
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
        
        p_data['current_streak'] = streak
        p_data['longest_streak'] = max(p_data.get('longest_streak', 0), streak)
        p_data['last_activity_date'] = str(dates[0])
        self.data['participants'][participant_name] = p_data
        self._save()

        new_badges = []
        for days, badge in STREAK_BADGES.items():
            if streak >= days and badge not in self.get_badges(participant_name):
                self.award_badge(participant_name, badge)
                new_badges.append(badge)
        
        return new_badges

    def trigger_milestone_and_streak_checks(self, participant_name):
        """Triggers all checks and shows confetti if new badges are awarded."""
        new_milestones = self.check_milestones(participant_name)
        new_streaks = self.check_streaks(participant_name)
        if new_milestones or new_streaks:
            show_confetti()
            st.experimental_rerun()
