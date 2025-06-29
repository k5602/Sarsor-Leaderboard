import streamlit as st
import pandas as pd
import plotly.express as px
from config import DEFAULT_PARTICIPANTS, BADGES, WARNING_BADGES
from data_manager import load_badges

def display_leaderboard(cumulative_df, df):
    """Displays the main leaderboard and top 3 performers."""
    cols = st.columns([3, 1])
    badges_data = load_badges()

    with cols[0]:
        if not cumulative_df.empty:
            display_df = cumulative_df[['Name', 'Rank', 'Base Points', 'Bonus Points', 'Total Points']]
            st.dataframe(
                display_df.style.background_gradient(subset=['Total Points'], cmap='YlGn').format(
                    {'Base Points': '{:.0f}', 'Bonus Points': '{:.0f}', 'Total Points': '{:.0f}'}
                ),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No data to display for the selected period.")

    with cols[1]:
        st.markdown("### 🏅 Top 3 Performers")
        top_3 = cumulative_df.head(3)
        if not top_3.empty:
            for _, row in top_3.iterrows():
                medal = "🥇" if row['Rank'] == 1 else "🥈" if row['Rank'] == 2 else "🥉"
                with st.container():
                    st.markdown(f"<div style='border: 1px solid #FF4B4B; border-radius: 5px; padding: 10px; margin-bottom: 10px;'>"
                                f"<h5>{medal} {row['Name']}</h5>"
                                f"<p>{int(row['Total Points'])} pts</p>"
                                f"</div>", unsafe_allow_html=True)
                    if row['Name'] in badges_data:
                        st.markdown(" ".join(badges_data[row['Name']]))
        else:
            st.info("No performers to display.")

    # --- Warning Badges ---
    for _, participant_data in cumulative_df.iterrows():
        historical_data = df[df['Name'] == participant_data['Name']].copy()
        if 'Date' in historical_data.columns:
            historical_data['Date'] = pd.to_datetime(historical_data['Date'])
            historical_data = historical_data.sort_values('Date', ascending=False)

        warning_badges = check_warning_badges(participant_data, historical_data)
        if warning_badges:
            with st.expander(f"⚠️ Warnings for {participant_data['Name']}"):
                for warning in warning_badges:
                    st.markdown(f"- {warning}")


def check_warning_badges(participant_data, historical_data):
    """Checks for and returns any warning badges for a participant."""
    warnings = []
    # ... (logic for checking warning conditions)
    return warnings

def display_analytics(df, achievement_system, challenge_system):
    """Displays the analytics tab with charts and stats."""
    st.subheader("Monthly Analytics")

    if df.empty or df['Date'].isnull().all():
        st.info("No analytics to display. Add some entries first.")
        return

    # --- Filters ---
    participants = st.multiselect(
        "Select Participants",
        options=df['Name'].unique(),
        default=df['Name'].unique()
    )

    date_range = st.date_input(
        "Select Date Range",
        value=(df['Date'].min(), df['Date'].max()),
        min_value=df['Date'].min(),
        max_value=df['Date'].max(),
    )

    if not participants or not date_range or len(date_range) != 2:
        st.warning("Please select participants and a valid date range.")
        return

    # --- Filtered Data ---
    filtered_df = df[
        df['Name'].isin(participants) &
        (df['Date'].dt.date >= date_range[0]) &
        (df['Date'].dt.date <= date_range[1])
    ]

    if filtered_df.empty:
        st.info("No data available for the selected filters.")
        return

    # --- Charts ---
    col1, col2 = st.columns(2)
    with col1:
        st.write("### Progress Over Time")
        fig = px.line(
            filtered_df,
            x='Date',
            y='Total Points',
            color='Name',
            markers=True,
            title="Points Progression"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.write("### Points Composition")
        fig = px.sunburst(
            filtered_df,
            path=['Name'],
            values='Total Points',
            color='Base Points',
            title="Total Points by Participant"
        )
        st.plotly_chart(fig, use_container_width=True)

def display_badges():
    """Displays the badges tab."""
    badges_data = load_badges()
    st.markdown("### 🏅 Available Badges")
    for badge, description in BADGES.items():
        st.markdown(f"**{badge}**: {description}")

    st.markdown("### 🏆 Awarded Badges")
    for participant, badges in badges_data.items():
        if badges:
            st.markdown(f"**{participant}**: {' '.join(badges)}")

def display_achievements(achievement_system):
    """Displays the achievements tab."""
    selected_participant = st.selectbox("Select Participant", DEFAULT_PARTICIPANTS, key="ach_part_select")
    st.markdown(f"### 🏆 Achievements for {selected_participant}")
    data = achievement_system.data.get(selected_participant, {})
    if not data:
        st.info("No achievements yet.")
        return
    for category, achievements in data.items():
        st.markdown(f"#### {category.title()}")
        for achievement, count in achievements.items():
            st.markdown(f"- **{achievement}**: {count}")

def display_challenges(challenge_system):
    """Displays the challenges tab for users."""
    st.markdown("### ⚔️ Active Challenges")
    if challenge_system.challenges:
        for name, challenge in challenge_system.challenges.items():
            with st.expander(f"📌 {name}"):
                st.markdown(f"**Description**: {challenge.get('description', 'N/A')}")
                st.markdown(f"**Bonus Points**: {challenge.get('bonus_points', 0)}")
                # ... (rest of challenge display logic)
    else:
        st.info("No active challenges.")