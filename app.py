import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import os
import base64

# --- Streamlit Page Config ---
st.set_page_config(page_title="Premier League Dashboard", layout="wide")

# --- Custom CSS Styling ---
st.markdown(
    """
    <style>
    .stApp {
        background-color: #37003c;
        color: white;
    }
    .css-1d391kg, .css-1v0mbdj, .st-bb, .st-cd {
        background-color: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }
    .stDataFrame, .stMetric {
        background-color: rgba(255, 255, 255, 0.05);
    }
    h1, h2, h3, h4, h5 {
        color: white;
    }
    .stSidebar {
        background-color: #24002b;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Logo and Title ---
st.image("premier-league.png", width=100)
st.title("Premier League 2023–24 Dashboard")

# --- Load Data ---
@st.cache_data
def load_data():
    df = pd.read_csv("filtered_matches_2324.csv")
    df['Date'] = pd.to_datetime(df['Date'])
    return df

@st.cache_data
def load_fouls_data():
    df = pd.read_csv("fouls_committed (1).csv")
    df['Team'] = df['Team'].str.strip()
    return df

@st.cache_data
def load_yellow_cards():
    df = pd.read_csv("yellow_cards.csv")
    df['Team'] = df['Team'].str.strip()
    return df

@st.cache_data
def load_red_cards():
    df = pd.read_csv("red_cards.csv")
    df['Team'] = df['Team'].str.strip()
    return df


# --- Load Data ---
df = load_data()
fouls_df = load_fouls_data()
yellow_df = load_yellow_cards()
red_df = load_red_cards()

# --- Sidebar Team Selection ---
teams = sorted(df['HomeTeam'].unique())
selected_team = st.sidebar.selectbox("Select a team", teams)

# --- Points Table Calculation ---
teams = df['HomeTeam'].unique()
points_data = []

for team in teams:
    home_matches = df[df['HomeTeam'] == team]
    home_wins = home_matches[home_matches['FullTimeResult'] == 'H'].shape[0]
    home_draws = home_matches[home_matches['FullTimeResult'] == 'D'].shape[0]
    home_losses = home_matches[home_matches['FullTimeResult'] == 'A'].shape[0]

    away_matches = df[df['AwayTeam'] == team]
    away_wins = away_matches[away_matches['FullTimeResult'] == 'A'].shape[0]
    away_draws = away_matches[away_matches['FullTimeResult'] == 'D'].shape[0]
    away_losses = away_matches[away_matches['FullTimeResult'] == 'H'].shape[0]

    total_wins = home_wins + away_wins
    total_draws = home_draws + away_draws
    total_losses = home_losses + away_losses
    total_points = total_wins * 3 + total_draws
    total_matches = total_wins + total_draws + total_losses

    points_data.append({
        'Team': team,
        'Matches': total_matches,
        'Wins': total_wins,
        'Draws': total_draws,
        'Losses': total_losses,
        'Points': total_points
    })

points_df = pd.DataFrame(points_data)
points_df = points_df.sort_values(by=['Points', 'Wins'], ascending=False).reset_index(drop=True)

# --- Get Rank and Logo ---
logo_path = f"team_logos/{selected_team}.png"
rank_row = points_df[points_df['Team'] == selected_team]

if not rank_row.empty:
    position = int(rank_row.index[0]) + 1
    if position == 1:
        position_str = "1st"
    elif position == 2:
        position_str = "2nd"
    elif position == 3:
        position_str = "3rd"
    else:
        position_str = f"{position}th"
else:
    position_str = "N/A"

if os.path.exists(logo_path):
    with open(logo_path, "rb") as f:
        encoded_image = base64.b64encode(f.read()).decode()

    html_code = f"""
    <div style="display: flex; justify-content: center; align-items: center; gap: 30px; margin-top: 20px; flex-wrap: wrap;">
        <img src="data:image/png;base64,{encoded_image}" alt="{selected_team} Logo" width="150" style="border-radius: 12px;"/>
        <div style="
            background-color: silver;
            color: black;
            font-size: 28px;
            font-weight: bold;
            padding: 10px 20px;
            border-radius: 30px;
            box-shadow: 0 0 15px rgba(255, 255, 255, 0.4);
            font-family: 'Segoe UI', sans-serif;
            white-space: nowrap;
        ">
            {position_str} in the Premier League
        </div>
    </div>
    """
    st.markdown(html_code, unsafe_allow_html=True)
else:
    st.warning(f"\u26a0\ufe0f Logo not found for {selected_team}")

# TODO: Add continuation for metrics, match stats, graphs, and interactivity

# --- Filter Data ---
team_df = df[(df['HomeTeam'] == selected_team) | (df['AwayTeam'] == selected_team)]
foul_row = fouls_df[fouls_df['Team'] == selected_team]
yellow_row = yellow_df[yellow_df['Team'] == selected_team]
red_row = red_df[red_df['Team'] == selected_team]

total_yellows = int(yellow_row['TotalYellows'].values[0]) if not yellow_row.empty else 0
total_reds = int(red_row['TotalReds'].values[0]) if not red_row.empty else 0


# --- Calculate Stats ---
goals_scored = (
    team_df[team_df['HomeTeam'] == selected_team]['FullTimeHomeTeamGoals'].sum() +
    team_df[team_df['AwayTeam'] == selected_team]['FullTimeAwayTeamGoals'].sum()
)

goals_conceded = (
    team_df[team_df['HomeTeam'] == selected_team]['FullTimeAwayTeamGoals'].sum() +
    team_df[team_df['AwayTeam'] == selected_team]['FullTimeHomeTeamGoals'].sum()
)

goal_difference = goals_scored - goals_conceded

if not foul_row.empty:
    home_fouls = int(foul_row['HomeFouls'].values[0])
    away_fouls = int(foul_row['AwayFouls'].values[0])
    total_fouls = int(foul_row['TotalFouls'].values[0])
else:
    home_fouls = away_fouls = total_fouls = 0

# --- Animated Metric Function ---
def animated_stat_box(label, value):
    html_code = f"""
    <style>
        .stat-box {{
            background-color: rgba(255,255,255,0.1);
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            color: white;
            font-family: 'Segoe UI';
            transition: all 0.3s ease-in-out;
            cursor: default;
        }}
        .stat-box:hover {{
            background-color: white;
            color: #37003c;
            transform: scale(1.02);
            box-shadow: 0 0 15px rgba(255,255,255,0.3);
        }}
    </style>

    <div class="stat-box">
        <div style="font-size: 1.1rem; font-weight: bold;"> {label}</div>
        <div id="{label}" style="font-size: 2rem; font-weight: bold;">0</div>
    </div>

    <script>
        const el = document.getElementById("{label}");
        let start = 0;
        const end = {value};
        const duration = 1000;
        const frameRate = 30;
        const totalFrames = duration / (1000 / frameRate);
        let frame = 0;

        const counter = setInterval(() => {{
            frame++;
            const progress = frame / totalFrames;
            const current = Math.round(progress * end);
            el.innerText = current;
            if (frame >= totalFrames) clearInterval(counter);
        }}, 1000 / frameRate);
    </script>
    """
    components.html(html_code, height=130)


# --- Display Animated Stats ---
col1, col2, col3 = st.columns(3)
with col1:
    animated_stat_box("Goals Scored", goals_scored )
with col2:
    animated_stat_box("Goals Conceded", goals_conceded)
with col3:
    animated_stat_box("Goal Difference", goal_difference)

col4, col5, col6 = st.columns(3)
with col4:
    animated_stat_box("Home Fouls", home_fouls)
with col5:
    animated_stat_box("Away Fouls", away_fouls)
with col6:
    animated_stat_box("Total Fouls", total_fouls)

# --- Conversion Rate Calculation ---
goals = {}
shots_on_target = {}

for _, row in df.iterrows():
    home = row['HomeTeam']
    away = row['AwayTeam']

    goals[home] = goals.get(home, 0) + row['FullTimeHomeTeamGoals']
    shots_on_target[home] = shots_on_target.get(home, 0) + row['HomeTeamShotsOnTarget']

    goals[away] = goals.get(away, 0) + row['FullTimeAwayTeamGoals']
    shots_on_target[away] = shots_on_target.get(away, 0) + row['AwayTeamShotsOnTarget']

conversion_data = []
for team in goals:
    shots = shots_on_target.get(team, 0)
    conversion = (goals[team] / shots) if shots > 0 else 0
    conversion_data.append({
        'Team': team,
        'Shot Conversion Rate (%)': round(conversion * 100, 2)
    })

conversion_df = pd.DataFrame(conversion_data)
team_conversion = conversion_df[conversion_df['Team'] == selected_team]['Shot Conversion Rate (%)'].values[0]


col7, col8, col9 = st.columns(3)

with col7:
    animated_stat_box("Shot Conversion Rate (%)", team_conversion)
with col8:
    animated_stat_box("Yellow Cards", total_yellows)
with col9:
    animated_stat_box("Red Cards", total_reds)




st.write("### Last 5 Matches Played")

def highlight_result(row):
    # Determine match result from perspective of selected team
    if row['HomeTeam'] == selected_team:
        if row['FullTimeHomeTeamGoals'] > row['FullTimeAwayTeamGoals']:
            return ['background-color: green'] * len(row)
        elif row['FullTimeHomeTeamGoals'] == row['FullTimeAwayTeamGoals']:
            return ['background-color: grey'] * len(row)
        else:
            return ['background-color: red'] * len(row)
    else:
        if row['FullTimeAwayTeamGoals'] > row['FullTimeHomeTeamGoals']:
            return ['background-color: green'] * len(row)
        elif row['FullTimeAwayTeamGoals'] == row['FullTimeHomeTeamGoals']:
            return ['background-color: grey'] * len(row)
        else:
            return ['background-color: red'] * len(row)

# Select last 5 matches
last_5 = team_df[['Date', 'HomeTeam', 'AwayTeam', 'FullTimeHomeTeamGoals', 'FullTimeAwayTeamGoals']].tail(5)
last_5=last_5.reset_index(drop=True)
# Apply styling
styled_last5 = last_5.style.apply(highlight_result, axis=1).hide(axis='index')
st.dataframe(styled_last5, use_container_width=True)


# --- Pie Chart: Match Outcome ---
st.write("### Overall Match Results")
wins = team_df[
    ((team_df['HomeTeam'] == selected_team) & (team_df['FullTimeResult'] == 'H')) |
    ((team_df['AwayTeam'] == selected_team) & (team_df['FullTimeResult'] == 'A'))
].shape[0]

draws = team_df[team_df['FullTimeResult'] == 'D'].shape[0]
total_matches = team_df.shape[0]
losses = total_matches - wins - draws

outcome_data = pd.DataFrame({
    'Result': ['Wins', 'Draws', 'Losses'],
    'Count': [wins, draws, losses]
})

fig = px.pie(
    outcome_data,
    values='Count',
    names='Result',
    title=f'{selected_team} Match Outcomes',
    color='Result',
    hole=0.3,
    color_discrete_map={
        'Wins': '#28a745',
        'Draws': '#ffc107',
        'Losses': '#dc3545'
    }
)

fig.update_traces(
    textinfo='percent+label',
    pull=[0.05, 0.05, 0.05],
    opacity=0.9,
    marker=dict(line=dict(color='white', width=2)),
    hoverlabel=dict(bgcolor="black", font_size=14)
)

fig.update_layout(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    showlegend=True,
    legend_title=None,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.2,
        xanchor="center",
        x=0.5
    )
)

st.plotly_chart(fig, use_container_width=True)


# 🧊 EDA Section - Match Distribution by Month (Line Chart Only)
st.subheader(" Number of Matches Played Each Month")

# Create month column
team_df['Month'] = team_df['Date'].dt.month_name()

# Valid months for a football season
month_order = [
    'August', 'September', 'October', 'November', 'December',
    'January', 'February', 'March', 'April', 'May'
]

# Filter only valid season months
team_df = team_df[team_df['Month'].isin(month_order)]

# Count number of matches per month
monthly_freq = team_df['Month'].value_counts().reindex(month_order, fill_value=0)

# Prepare DataFrame for plot
freq_df = pd.DataFrame({
    'Month': monthly_freq.index,
    'Matches': monthly_freq.values
})

# 📈 Plot line chart
fig_line = px.line(
    freq_df,
    x='Month',
    y='Matches',
    title=f" Monthly Match Distribution for {selected_team}",
    markers=True
)

# ✨ Styling
fig_line.update_traces(
    line=dict(color='#2fe3e0', width=3),
    marker=dict(size=8, color='white', line=dict(width=2, color='#2fe3e0'))
)

fig_line.update_layout(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font_color='white',
    height=450,
    margin=dict(t=60, b=40)
)

# Display chart
st.plotly_chart(fig_line, use_container_width=True)

##_--------------------------------------------------------------------------------------------------------
# --- Calculate Longest Winning Streak ---
team_df = team_df.sort_values(by='Date')  # Ensure chronological order

results = []
streak_matches = []
temp_streak = []

for _, row in team_df.iterrows():
    if row['HomeTeam'] == selected_team:
        is_win = row['FullTimeResult'] == 'H'
    else:
        is_win = row['FullTimeResult'] == 'A'

    if is_win:
        results.append('W')
        temp_streak.append(row)
    else:
        results.append('L')
        if len(temp_streak) > len(streak_matches):
            streak_matches = temp_streak.copy()
        temp_streak = []

# In case the final streak is the longest
if len(temp_streak) > len(streak_matches):
    streak_matches = temp_streak.copy()

longest_streak = len(streak_matches)

# --- Display Animated Stat ---
st.subheader(" Team Performance Insights")
animated_stat_box("Longest Win Streak", longest_streak)

# --- Custom Button Style (White on Hover) ---
st.markdown("""
    <style>
    div.stButton > button:first-child {
        background-color: rgba(255, 255, 255, 0.1);
        color: white;
        border: 1px solid white;
        font-weight: bold;
        transition: 0.3s;
    }
    div.stButton > button:first-child:hover {
        background-color: white;
        color: #37003c;
    }
    </style>
""", unsafe_allow_html=True)

# --- Toggle Logic using session_state ---
if "show_streak" not in st.session_state:
    st.session_state.show_streak = False

if st.button(" Show Longest Win Streak Matches"):
    st.session_state.show_streak = not st.session_state.show_streak

if st.session_state.show_streak:
    streak_df = pd.DataFrame(streak_matches)[[
        'Date', 'HomeTeam', 'AwayTeam', 'FullTimeHomeTeamGoals', 'FullTimeAwayTeamGoals'
    ]]
    st.dataframe(streak_df, use_container_width=True)


import pandas as pd

# Load the data
df = pd.read_csv("filtered_matches_2324.csv")

# Initialize dictionaries
goals = {}
shots_on_target = {}

# Loop through each match
for _, row in df.iterrows():
    home = row['HomeTeam']
    away = row['AwayTeam']

    # Update home team stats
    goals[home] = goals.get(home, 0) + row['FullTimeHomeTeamGoals']
    shots_on_target[home] = shots_on_target.get(home, 0) + row['HomeTeamShotsOnTarget']

    # Update away team stats
    goals[away] = goals.get(away, 0) + row['FullTimeAwayTeamGoals']
    shots_on_target[away] = shots_on_target.get(away, 0) + row['AwayTeamShotsOnTarget']

# Calculate conversion rate
conversion_data = []
for team in goals:
    shots = shots_on_target.get(team, 0)
    conversion = (goals[team] / shots) if shots > 0 else 0
    conversion_data.append({
        'Team': team,
        'Goals': goals[team],
        'Shots on Target': shots,
        'Conversion Rate (%)': round(conversion * 100, 2)
    })

# Create DataFrame
conversion_df = pd.DataFrame(conversion_data)
conversion_df = conversion_df.sort_values(by='Conversion Rate (%)', ascending=False)




# Display




