
import pandas as pd
import json
import os
from datetime import datetime
import streamlit as st
from config import (
    DATA_FILE, PARTICIPANT_BADGES_FILE, ACHIEVEMENT_FILE, STREAKS_FILE, 
    CHALLENGES_FILE, CATEGORIES, DEFAULT_PARTICIPANTS
)

# --- Data Loading ---

def load_data():
    """Loads the main leaderboard data from a CSV file."""
    try:
        if os.path.exists(DATA_FILE):
            df = pd.read_csv(DATA_FILE)
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df['Month'] = df['Date'].dt.to_period('M')
            return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
    
    return pd.DataFrame(columns=[
        'Name', 'Date', 'Month', 'Base Points', 'Bonus Points', 'Total Points'
    ] + list(CATEGORIES.keys()))

def load_json_data(file_path: str, default_data=None):
    """Loads data from a JSON file."""
    if default_data is None:
        default_data = {}
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return default_data
    return default_data

# --- Data Saving ---

def save_data(df):
    """Saves the main leaderboard data to a CSV file."""
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
    df.to_csv(DATA_FILE, index=False)

def save_json_data(file_path: str, data):
    """Saves data to a JSON file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

# --- Data Initialization ---

def initialize_month():
    """Creates a new DataFrame for the current month with default participants."""
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

# --- Specific Data Loaders/Savers ---

def load_badges():
    return load_json_data(PARTICIPANT_BADGES_FILE, default_data={})

def save_badges(badges_data):
    save_json_data(PARTICIPANT_BADGES_FILE, badges_data)

def load_achievements():
    return load_json_data(ACHIEVEMENT_FILE, default_data={})

def save_achievements(data):
    save_json_data(ACHIEVEMENT_FILE, data)

def load_streaks_data():
    return load_json_data(STREAKS_FILE, default_data={"participants": {}, "milestones_awarded": {}})

def save_streaks_data(streaks_data):
    save_json_data(STREAKS_FILE, streaks_data)

def load_challenges():
    return load_json_data(CHALLENGES_FILE, default_data={'challenges': {}, 'pending': {}})

def save_challenges(data):
    save_json_data(CHALLENGES_FILE, data)
