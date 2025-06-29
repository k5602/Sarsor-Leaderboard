
import hashlib
import streamlit as st
from datetime import datetime
from config import ADMIN_HASH

def hash_password(password: str) -> str:
    """Hash password using SHA256."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def verify_password(password: str) -> bool:
    """Verify the provided password against the stored admin hash."""
    try:
        if not password or not isinstance(password, str):
            return False

        current_time = datetime.now()
        if 'last_login_attempt' in st.session_state:
            time_diff = (current_time - st.session_state.last_login_attempt).total_seconds()
            if time_diff < 2:  # 2-second delay between attempts
                st.error("Please wait before trying again.")
                return False

        st.session_state.last_login_attempt = current_time
        return hash_password(password) == ADMIN_HASH
    except Exception as e:
        st.error(f"Login error occurred: {str(e)}")
        return False

def initialize_auth_state():
    """Initialize session state variables for authentication."""
    if 'admin' not in st.session_state:
        st.session_state.admin = False
    if 'show_admin_login' not in st.session_state:
        st.session_state.show_admin_login = False
    if 'last_login_attempt' not in st.session_state:
        st.session_state.last_login_attempt = datetime.min

def login_user(password: str):
    """Logs in the user if the password is correct."""
    if verify_password(password):
        st.session_state.admin = True
        st.session_state.show_admin_login = False
        st.rerun()
    else:
        st.error("Incorrect password")

def logout_user():
    """Logs out the current user."""
    st.session_state.admin = False
    st.rerun()
