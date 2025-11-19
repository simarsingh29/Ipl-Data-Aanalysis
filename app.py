import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="IPL Analytics Dashboard",
    page_icon="🏏",
    layout="wide"
)

# --- ROBUST CSV LOADING FUNCTION ---
def robust_csv_load(file_path):
    """
    Handles CSV files where the entire row is wrapped in quotes, 
    causing pandas to read it as a single column.
    
    This version includes a fix for mismatched column counts between 
    the header and data rows.
    """
    
    # 1. Read the file assuming potential single-column structure
    df_temp = pd.read_csv(file_path, header=None, encoding='utf-8')
    
    if df_temp.shape[1] == 1:
        data_series = df_temp.iloc[:, 0]
        
        # Clean the header (first element) to get the true column names
        header_str = data_series.iloc[0].strip().strip('"')
        new_cols = [col.strip().strip('"') for col in header_str.split(',')]
        
        # Create a new DataFrame by splitting the remaining rows (data)
        data_rows = data_series.iloc[1:]
        
        # Split and clean each row string, expanding into multiple columns
        new_data = data_rows.str.strip().str.strip('"').str.split(',', expand=True)
        
        # Slice the data columns to match the length of the cleaned header
        num_header_cols = len(new_cols)
        
        if new_data.shape[1] != num_header_cols:
            new_data = new_data.iloc[:, :num_header_cols]
        
        new_data.columns = new_cols
        
        # Convert known numeric columns
        numeric_cols = ['id', 'match_id', 'season', 'batsman_runs', 'extra_runs', 'total_runs', 'is_wicket', 'result_margin', 'target_runs', 'target_overs']
        for col in numeric_cols:
            if col in new_data.columns:
                new_data[col] = pd.to_numeric(new_data[col], errors='coerce')
        
        return new_data
    else:
        # If the file was read correctly, return it
        return df_temp

@st.cache_data
def load_data():
    # Load data using the robust function with your local paths
    match_path = "C:\\Users\\simar\\OneDrive\\Desktop\\data\\matches (2).csv"
    deliv_path = "C:\\Users\\simar\\OneDrive\\Desktop\\data\\deliveries (1).csv"
    
    matches = robust_csv_load(match_path)
    deliveries = robust_csv_load(deliv_path)
    
    # FIX APPLIED HERE: Ensure 'season' is a float before conversion below
    if 'season' in matches.columns and matches['season'].dtype == object:
        # This extracts the year (e.g., '2007/08' -> 2008.0)
        matches['season'] = pd.to_numeric(matches['season'].astype(str).str.extract(r'(\d{4})')[0], errors='coerce')
        
    return matches, deliveries

# Load data, suppressing the error that occurred previously
try:
    matches, deliveries = load_data()
except ValueError as e:
    st.error(f"Data Loading Error: {e}. Please ensure your CSV files are correctly formatted and the paths are accurate.")
    st.stop() 


if "date" in matches.columns:
    matches["date"] = pd.to_datetime(matches["date"])

st.title("🏏 IPL Analytics Dashboard")

st.markdown(
    """
Interactive dashboard using IPL match and ball-by-ball data.  
Use the sidebar filters and tabs to explore teams, players, venues and seasons.
"""
)

st.sidebar.header("Filters")

# FIX APPLIED HERE: Convert seasons to integer (or string) after cleaning NaNs
if "season" in matches.columns:
    # Drop NaN, convert to int (which removes the .0), and then sort
    seasons = sorted(matches["season"].dropna().astype(int).unique())
else:
    seasons = []
    
selected_seasons = st.sidebar.multiselect(
    "Select Seasons",
    options=seasons,
    default=seasons
)

teams = sorted(
    pd.unique(
        pd.concat(
            [
                matches["team1"],
                matches["team2"],
                matches["winner"]
            ],
            axis=0
        ).dropna()
    )
)

selected_team = st.sidebar.selectbox(
    "Focus Team (optional)",
    options=["All"] + teams,
    index=0
)

if selected_seasons:
    matches_f = matches[matches["season"].isin(selected_seasons)]
else:
    matches_f = matches.copy()

deliveries_f = deliveries[deliveries["match_id"].isin(matches_f["id"])]

tab1, tab2, tab3, tab4 = st.tabs(
    ["Overview", "Team Analysis", "Batting Analysis", "Bowling Analysis"]
)
# ----------------------------------------------------------------------
## Tab 1: Overview
# ----------------------------------------------------------------------
with tab1:
    st.subheader("Overall Tournament Overview")

    col1, col2, col3, col4 = st.columns(4)
    total_matches = len(matches_f)
    total_seasons = matches_f["season"].nunique() if "season" in matches_f.columns else 0
    total_venues = matches_f["venue"].nunique() if "venue" in matches_f.columns else 0
    total_teams = len(teams)

    col1.metric("Total Matches", total_matches)
    col2.metric("Seasons", total_seasons)
    col3.metric("Venues", total_venues)
    col4.metric("Teams", total_teams)

    if "season" in matches_f.columns:
        matches_per_season = (
            matches_f.groupby("season")["id"]
            .count()
            .reset_index()
            .rename(columns={"id": "matches"})
        )
        # Ensure x-axis values are integers for display
        matches_per_season['season'] = matches_per_season['season'].astype(int)
        
        fig_mps = px.bar(
            matches_per_season,
            x="season",
            y="matches",
            title="Matches per Season",
            text="matches"
        )
        fig_mps.update_traces(textposition="outside")
        st.plotly_chart(fig_mps, use_container_width=True)

    if "toss_decision" in matches_f.columns:
        toss_counts = matches_f["toss_decision"].value_counts().reset_index()
        toss_counts.columns = ["toss_decision", "toss_count"]
        toss_counts = toss_counts.rename(columns={"toss_decision": "decision"})

        fig_toss = px.pie(
            toss_counts,
            names="decision",
            values="toss_count",
            title="Toss Decision (Bat vs Field)",
            hole=0.4
        )
        st.plotly_chart(fig_toss, use_container_width=True)

    if "result" in matches_f.columns:
        result_counts = matches_f["result"].value_counts().reset_index()
        result_counts.columns = ["result_type", "result_count"]

        fig_res = px.bar(
            result_counts,
            x="result_type",
            y="result_count",
            title="Result Type Distribution",
            text="result_count",
            labels={"result_type": "Result", "result_count": "Count"}
        )
        fig_res.update_traces(textposition="outside")
        st.plotly_chart(fig_res, use_container_width=True)

    if "win_by_runs" in matches_f.columns and "win_by_wickets" in matches_f.columns:
        col_a, col_b = st.columns(2)

        with col_a:
            runs_wins = matches_f[matches_f["win_by_runs"] > 0].copy()
            fig_runs = px.histogram(
                runs_wins,
                x="win_by_runs",
                nbins=30,
                title="Distribution of Victory Margin (Runs)",
                labels={"win_by_runs": "Run Margin"}
            )
            st.plotly_chart(fig_runs, use_container_width=True)

        with col_b:
            wk_wins = matches_f[matches_f["win_by_wickets"] > 0].copy()
            fig_wk = px.histogram(
                wk_wins,
                x="win_by_wickets",
                nbins=10,
                title="Distribution of Victory Margin (Wickets)",
                labels={"win_by_wickets": "Wicket Margin"}
            )
            st.plotly_chart(fig_wk, use_container_width=True)

# ----------------------------------------------------------------------
## Tab 2: Team Analysis
# ----------------------------------------------------------------------
with tab2:
    st.subheader("Team Performance Analysis")

    team_matches1 = (
        matches_f.groupby("team1")["id"]
        .count()
        .reset_index()
        .rename(columns={"team1": "team", "id": "matches_home"})
    )
    team_matches2 = (
        matches_f.groupby("team2")["id"]
        .count()
        .reset_index()
        .rename(columns={"team2": "team", "id": "matches_away"})
    )
    team_matches = pd.merge(team_matches1, team_matches2, on="team", how="outer").fillna(0)
    team_matches["matches_played"] = team_matches["matches_home"] + team_matches["matches_away"]

    team_wins = (
        matches_f.groupby("winner")["id"]
        .count()
        .reset_index()
        .rename(columns={"winner": "team", "id": "wins"})
    )

    team_stats = pd.merge(team_matches, team_wins, on="team", how="left").fillna(0)
    team_stats["win_pct"] = np.where(
        team_stats["matches_played"] > 0,
        (team_stats["wins"] / team_stats["matches_played"]) * 100,
        0
    )
    team_stats = team_stats.sort_values("wins", ascending=False)

    if selected_team == "All":
        st.markdown("Showing **overall team comparison** across selected seasons.")
        
        col1, col2 = st.columns(2)

        with col1:
            fig_team_wins = px.bar(
                team_stats,
                x="team",
                y="wins",
                title="Total Wins by Team",
                text="wins"
            )
            fig_team_wins.update_layout(xaxis_tickangle=-45)
            fig_team_wins.update_traces(textposition="outside")
            st.plotly_chart(fig_team_wins, use_container_width=True)

        with col2:
            fig_team_winpct = px.bar(
                team_stats,
                x="team",
                y="win_pct",
                title="Win Percentage by Team",
                labels={"win_pct": "Win %"},
                text="win_pct"
            )
            fig_team_winpct.update_layout(xaxis_tickangle=-45)
            fig_team_winpct.update_traces(textposition="outside")
            st.plotly_chart(fig_team_winpct, use_container_width=True)
            
    else:
        # --- Team Specific Summary ---
        st.markdown(f"### 🏆 **{selected_team} Summary**")

        tm_row = team_stats[team_stats["team"] == selected_team]
        if not tm_row.empty:
            total_played = int(tm_row["matches_played"].iloc[0])
            total_won = int(tm_row["wins"].iloc[0])
            win_pct_val = round(tm_row["win_pct"].iloc[0], 2)

            # Display KPIs
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Matches Played", total_played)
            c2.metric("Matches Won", total_won)
            c3.metric("Win %", f"{win_pct_val}%")
            
            # Calculate win/loss split
            total_loss = total_played - total_won
            wl_df = pd.DataFrame({
                "Result": ["Won", "Lost"],
                "Count": [total_won, total_loss]
            })
            
            # --- Toss/Match Result Analysis ---
            st.markdown("---")
            st.markdown("#### Key Match Metrics")

            team_matches_f = matches_f[(matches_f["team1"] == selected_team) | (matches_f["team2"] == selected_team)].copy()
            
            # 1. Win/Loss Pie Chart
            col_kpi_1, col_kpi_2 = st.columns(2)
            with col_kpi_1:
                fig_wl = px.pie(
                    wl_df,
                    names="Result",
                    values="Count",
                    title=f"{selected_team} Win/Loss Split",
                    hole=0.4
                )
                st.plotly_chart(fig_wl, use_container_width=True)

            # 2. Toss Decision Outcomes
            with col_kpi_2:
                toss_outcomes = team_matches_f[team_matches_f["toss_winner"] == selected_team]
                toss_dec_counts = toss_outcomes["toss_decision"].value_counts().reset_index()
                toss_dec_counts.columns = ["decision", "count"]

                fig_toss_dec = px.bar(
                    toss_dec_counts,
                    x="decision",
                    y="count",
                    title=f"{selected_team} Toss Decisions",
                    text="count"
                )
                fig_toss_dec.update_traces(textposition="outside")
                st.plotly_chart(fig_toss_dec, use_container_width=True)

            # 3. Performance when Chasing vs Defending (Toss Win)
            st.markdown("---")
            st.markdown("#### Toss Performance: Win/Loss after Winning Toss")

            toss_wins = team_matches_f[team_matches_f["toss_winner"] == selected_team]
            
            # Helper to check if the team won the match
            toss_wins['match_won'] = toss_wins['winner'] == selected_team
            
            toss_perf = toss_wins.groupby('toss_decision')['match_won'].agg(['sum', 'count']).reset_index()
            toss_perf['win_pct'] = (toss_perf['sum'] / toss_perf['count']) * 100
            toss_perf = toss_perf.rename(columns={'sum': 'Wins', 'count': 'Total Matches'})

            fig_toss_perf = px.bar(
                toss_perf,
                x='toss_decision',
                y='win_pct',
                title=f"{selected_team} Win % After Winning Toss",
                labels={'toss_decision': 'Toss Decision', 'win_pct': 'Win %'},
                text=toss_perf.apply(lambda row: f"{row['win_pct']:.1f}% ({row['Wins']}/{row['Total Matches']})", axis=1)
            )
            fig_toss_perf.update_traces(textposition="outside")
            st.plotly_chart(fig_toss_perf, use_container_width=True)
            
        else:
            st.warning(f"No match data found for {selected_team} in the selected seasons.")

    if "venue" in matches_f.columns:
        st.markdown("---")
        st.markdown("### Top Venues by Matches Played")
        # Rest of Venue Analysis (remains the same as original)
        venue_match_count = (
            matches_f.groupby("venue")["id"]
            .count()
            .reset_index()
            .rename(columns={"id": "matches"})
            .sort_values("matches", ascending=False)
        )
        top_venues = venue_match_count.head(15)

        fig_venue = px.bar(
            top_venues,
            x="venue",
            y="matches",
            title="Most Used Venues",
            text="matches"
        )
        fig_venue.update_layout(xaxis_tickangle=-60)
        fig_venue.update_traces(textposition="outside")
        st.plotly_chart(fig_venue, use_container_width=True)

        venue_sel = st.selectbox(
            "Select a Venue to see team performance there",
            options=sorted(matches_f["venue"].dropna().unique())
        )

        venue_df = matches_f[matches_f["venue"] == venue_sel]
        venue_team_wins = (
            venue_df.groupby("winner")["id"]
            .count()
            .reset_index()
            .rename(columns={"winner": "team", "id": "wins_at_venue"})
            .sort_values("wins_at_venue", ascending=False)
        )

        fig_venue_team = px.bar(
            venue_team_wins,
            x="team",
            y="wins_at_venue",
            title=f"Wins by Team at {venue_sel}",
            text="wins_at_venue"
        )
        fig_venue_team.update_layout(xaxis_tickangle=-45)
        fig_venue_team.update_traces(textposition="outside")
        st.plotly_chart(fig_venue_team, use_container_width=True)

# ----------------------------------------------------------------------
## Tab 3: Batting Analysis
# ----------------------------------------------------------------------
with tab3:
    st.subheader("Batting Analysis")

    if {"batter", "batsman_runs"}.issubset(deliveries_f.columns):
        batter_runs = (
            deliveries_f.groupby("batter")["batsman_runs"]
            .sum()
            .reset_index()
            .sort_values("batsman_runs", ascending=False)
        )

        top_n_bat = st.slider("Top N batters by runs", 5, 30, 10)
        top_batters = batter_runs.head(top_n_bat)

        top_batters = top_batters.rename(columns={"batsman_runs": "total_runs"})

        fig_top_bat = px.bar(
            top_batters,
            x="batter",
            y="total_runs",
            title=f"Top {top_n_bat} Run Scorers",
            labels={"batter": "Batter", "total_runs": "Runs"},
            text="total_runs"
        )
        fig_top_bat.update_layout(xaxis_tickangle=-45)
        fig_top_bat.update_traces(textposition="outside")
        st.plotly_chart(fig_top_bat, use_container_width=True)

        selected_batter = st.selectbox(
            "Select a batter for detailed view",
            options=top_batters["batter"]
        )

        p_df = deliveries_f[deliveries_f["batter"] == selected_batter]

        total_runs = int(p_df["batsman_runs"].sum())
        total_balls = int(p_df.shape[0])
        fours = int((p_df["batsman_runs"] == 4).sum())
        sixes = int((p_df["batsman_runs"] == 6).sum())
        strike_rate = round((total_runs / total_balls) * 100, 2) if total_balls > 0 else 0

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Runs", total_runs)
        c2.metric("Balls", total_balls)
        c3.metric("4s", fours)
        c4.metric("6s", sixes)
        c5.metric("Strike Rate", strike_rate)

        if "season" in matches_f.columns:
            bat_season = deliveries_f.merge(
                matches_f[["id", "season"]],
                left_on="match_id",
                right_on="id",
                how="left"
            )
            bat_season = bat_season[bat_season["batter"] == selected_batter]
            bat_season_grp = (
                bat_season.groupby("season")["batsman_runs"]
                .sum()
                .reset_index()
                .sort_values("season")
            )
            bat_season_grp = bat_season_grp.rename(columns={"batsman_runs": "season_runs"})

            fig_season_runs = px.line(
                bat_season_grp,
                x="season",
                y="season_runs",
                markers=True,
                title=f"Season-wise Runs: {selected_batter}",
                labels={"season_runs": "Runs"}
            )
            st.plotly_chart(fig_season_runs, use_container_width=True)

        st.markdown("### Boundary Distribution")
        boundary_counts = pd.DataFrame({
            "boundary_type": ["4s", "6s"],
            "boundary_count": [fours, sixes]
        })
        fig_boundary = px.pie(
            boundary_counts,
            names="boundary_type",
            values="boundary_count",
            title=f"Boundary Split for {selected_batter}",
            hole=0.4
        )
        st.plotly_chart(fig_boundary, use_container_width=True)
    else:
        st.write("Required columns for batting analysis are missing in deliveries dataset.")

# ----------------------------------------------------------------------
## Tab 4: Bowling Analysis
# ----------------------------------------------------------------------
with tab4:
    st.subheader("Bowling Analysis")

    needed_cols = {"bowler", "is_wicket", "dismissal_kind", "total_runs"}
    if needed_cols.issubset(deliveries_f.columns):
        wicket_df = deliveries_f[
            (deliveries_f["is_wicket"] == 1) &
            (~deliveries_f["dismissal_kind"].isin(["run out", "retired hurt", "obstructing the field"]))
        ]

        bowler_wk = (
            wicket_df.groupby("bowler")["is_wicket"]
            .count()
            .reset_index()
            .rename(columns={"is_wicket": "wickets_taken"})
            .sort_values("wickets_taken", ascending=False)
        )

        top_n_bowl = st.slider("Top N bowlers by wickets", 5, 30, 10)
        top_bowlers = bowler_wk.head(top_n_bowl)

        fig_top_bowl = px.bar(
            top_bowlers,
            x="bowler",
            y="wickets_taken",
            title=f"Top {top_n_bowl} Wicket Takers",
            labels={"bowler": "Bowler", "wickets_taken": "Wickets"},
            text="wickets_taken"
        )
        fig_top_bowl.update_layout(xaxis_tickangle=-45)
        fig_top_bowl.update_traces(textposition="outside")
        st.plotly_chart(fig_top_bowl, use_container_width=True)

        selected_bowler = st.selectbox(
            "Select a bowler for detailed view",
            options=top_bowlers["bowler"]
        )

        b_df = deliveries_f[deliveries_f["bowler"] == selected_bowler]
        
        # FIX for legal_del calculation
        if 'extras_type' in b_df.columns:
            legal_del = b_df[~b_df["extras_type"].isin(["wides", "noballs", "wide", "noball"])]
        elif 'extra_runs' in b_df.columns:
            # Fallback (using extra_runs=0 as a proxy for legal ball)
            legal_del = b_df[b_df['extra_runs'] == 0]
        else:
             # Last resort: count all balls
            legal_del = b_df 

        runs_conceded = int(b_df["total_runs"].sum())
        balls_bowled = int(legal_del.shape[0])
        overs = balls_bowled / 6 if balls_bowled > 0 else 0
        economy = round(runs_conceded / overs, 2) if overs > 0 else 0
        
        wickets_taken = int(
            wicket_df[wicket_df["bowler"] == selected_bowler].shape[0]
        )

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Wickets", wickets_taken)
        c2.metric("Runs Conceded", runs_conceded)
        c3.metric("Balls", balls_bowled)
        c4.metric("Economy", economy)

        if "season" in matches_f.columns:
            bowl_season = deliveries_f.merge(
                matches_f[["id", "season"]],
                left_on="match_id",
                right_on="id",
                how="left"
            )
            bowl_season = bowl_season[
                (bowl_season["bowler"] == selected_bowler) &
                (bowl_season["is_wicket"] == 1) &
                (~bowl_season["dismissal_kind"].isin(["run out", "retired hurt", "obstructing the field"]))
            ]
            bowl_season_grp = (
                bowl_season.groupby("season")["is_wicket"]
                .count()
                .reset_index()
                .rename(columns={"is_wicket": "season_wickets"})
                .sort_values("season")
            )

            fig_season_wk = px.line(
                bowl_season_grp,
                x="season",
                y="season_wickets",
                markers=True,
                title=f"Season-wise Wickets: {selected_bowler}",
                labels={"season_wickets": "Wickets"}
            )
            st.plotly_chart(fig_season_wk, use_container_width=True)
    else:
        st.write("Required columns for bowling analysis are missing in deliveries dataset.")