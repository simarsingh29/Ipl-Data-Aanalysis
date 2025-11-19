import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# -------------------------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------------------------
st.set_page_config(
    page_title="IPL Analytics Dashboard",
    page_icon="🏏",
    layout="wide",
)

# -------------------------------------------------------------------
# GLOBAL STYLING
# -------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Remove Streamlit default padding */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1.5rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    /* Card style */
    .metric-card {
        padding: 1rem 1.5rem;
        border-radius: 0.75rem;
        background-color: #0e1117;
        border: 1px solid #262730;
    }
    .metric-value {
        font-size: 1.7rem;
        font-weight: 700;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #b3b3b3;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------
# LOAD DATA HELPERS
# (Replace CSV paths with your actual data files used in notebooks)
# -------------------------------------------------------------------
@st.cache_data
def load_matches():
    return pd.read_csv("data/matches.csv")

@st.cache_data
def load_deliveries():
    return pd.read_csv("data/deliveries.csv")

@st.cache_data
def load_auction():
    return pd.read_csv("data/auction.csv")

matches = load_matches()
deliveries = load_deliveries()
auction = load_auction()

# -------------------------------------------------------------------
# IPL TEAM LOGOS
# -------------------------------------------------------------------
TEAM_LOGOS = {
    "Chennai Super Kings": "logos/csk.png",
    "Mumbai Indians": "logos/mi.png",
    "Kolkata Knight Riders": "logos/kkr.png",
    "Rajasthan Royals": "logos/rr.png",
    "Royal Challengers Bangalore": "logos/rcb.png",
    "Sunrisers Hyderabad": "logos/srh.png",
    "Punjab Kings": "logos/pbks.png",
    "Delhi Capitals": "logos/dc.png",
    "Gujarat Titans": "logos/gt.png",
    "Lucknow Super Giants": "logos/lsg.png",
}

# Put your attached WhatsApp images in a `logos/` folder
# and name them as above (csk.png, mi.png, etc.).

# -------------------------------------------------------------------
# TOP BAR
# -------------------------------------------------------------------
col_logo, col_title, col_right = st.columns([1, 4, 1])

with col_logo:
    st.image("logos/ipl_official.png", width=70)  # optional, or remove

with col_title:
    st.markdown(
        """
        ### IPL Analytics Dashboard  
        A unified view of teams, players, venues, toss and auction insights
        """,
    )

with col_right:
    st.write("")
    st.write("")
    st.caption("Built with Streamlit")

st.markdown("---")

# -------------------------------------------------------------------
# SIDEBAR – GLOBAL FILTERS
# -------------------------------------------------------------------
st.sidebar.header("Global Filters")

seasons = sorted(matches["season"].unique())
teams = sorted(
    set(matches["team1"]).union(set(matches["team2"]))
)

selected_season = st.sidebar.multiselect(
    "Season",
    seasons,
    default=seasons,
)

selected_team = st.sidebar.multiselect(
    "Team (any side)",
    teams,
    default=teams,
)

# Apply filters
filtered_matches = matches[
    matches["season"].isin(selected_season)
]

if selected_team:
    filtered_matches = filtered_matches[
        (filtered_matches["team1"].isin(selected_team)) |
        (filtered_matches["team2"].isin(selected_team))
    ]

filtered_deliveries = deliveries[
    deliveries["match_id"].isin(filtered_matches["id"])
]

# -------------------------------------------------------------------
# TABS
# -------------------------------------------------------------------
tab_overview, tab_teams, tab_players, tab_venues, tab_toss, tab_auction, tab_logos = st.tabs(
    [
        "Overview",
        "Teams",
        "Players",
        "Venues",
        "Toss",
        "Auction",
        "Team Logos",
    ]
)

# -------------------------------------------------------------------
# OVERVIEW TAB
# -------------------------------------------------------------------
with tab_overview:
    st.subheader("Tournament Overview")

    total_matches = len(filtered_matches)
    total_runs = int(filtered_deliveries["total_runs"].sum())
    total_seasons = len(filtered_matches["season"].unique())
    total_teams = len(teams)

    c1, c2, c3, c4 = st.columns(4)
    for col, value, label in [
        (c1, total_matches, "Matches"),
        (c2, total_runs, "Total Runs"),
        (c3, total_seasons, "Seasons"),
        (c4, total_teams, "Teams"),
    ]:
        with col:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value">{value}</div>
                    <div class="metric-label">{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("")

    c_left, c_right = st.columns(2)

    # 1. Season-wise matches
    with c_left:
        st.markdown("#### Matches by Season")
        season_counts = (
            filtered_matches.groupby("season")["id"]
            .count()
            .reset_index(name="matches")
        )
        fig, ax = plt.subplots(figsize=(8, 4))
        sns.barplot(
            data=season_counts,
            x="season",
            y="matches",
            ax=ax,
            palette="Blues_d",
        )
        ax.set_xlabel("Season")
        ax.set_ylabel("Matches")
        ax.set_title("Matches per Season")
        st.pyplot(fig)

    # 2. Season-wise total runs
    with c_right:
        st.markdown("#### Total Runs by Season")
        merged = filtered_deliveries.merge(
            filtered_matches[["id", "season"]],
            left_on="match_id",
            right_on="id",
            how="left",
        )
        season_runs = (
            merged.groupby("season")["total_runs"]
            .sum()
            .reset_index()
        )
        fig2, ax2 = plt.subplots(figsize=(8, 4))
        sns.lineplot(
            data=season_runs,
            x="season",
            y="total_runs",
            marker="o",
            ax=ax2,
            color="#ffba08",
        )
        ax2.set_xlabel("Season")
        ax2.set_ylabel("Runs")
        ax2.set_title("Total Runs per Season")
        st.pyplot(fig2)

# -------------------------------------------------------------------
# TEAMS TAB
# -------------------------------------------------------------------
with tab_teams:
    st.subheader("Team Analysis")

    team_option = st.selectbox(
        "Select team",
        options=teams,
        index=teams.index(selected_team[0]) if selected_team else 0,
    )

    team_matches = filtered_matches[
        (filtered_matches["team1"] == team_option)
        | (filtered_matches["team2"] == team_option)
    ]

    wins = (team_matches["winner"] == team_option).sum()
    losses = len(team_matches) - wins
    titles_df = (
        team_matches[
            team_matches["winner"] == team_option
        ]
        .groupby("season")
        .size()
        .reset_index(name="titles")
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{len(team_matches)}</div>
                <div class="metric-label">Matches Played</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{wins}</div>
                <div class="metric-label">Wins</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{losses}</div>
                <div class="metric-label">Losses</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    col_left, col_right = st.columns([2, 1])

    # Win percentage by season
    with col_left:
        st.markdown("#### Season-wise Win Percentage")
        season_stats = (
            team_matches.groupby("season")
            .agg(
                matches=("id", "count"),
                wins=("winner", lambda x: (x == team_option).sum()),
            )
            .reset_index()
        )
        season_stats["win_pct"] = (
            season_stats["wins"]
            / season_stats["matches"]
            * 100
        )

        fig3, ax3 = plt.subplots(figsize=(8, 4))
        sns.lineplot(
            data=season_stats,
            x="season",
            y="win_pct",
            marker="o",
            ax=ax3,
            color="#22c55e",
        )
        ax3.set_ylabel("Win %")
        ax3.set_xlabel("Season")
        ax3.set_title(f"{team_option} – Win% by Season")
        st.pyplot(fig3)

    # Titles / trophies summary
    with col_right:
        st.markdown("#### Titles by Season")
        if not titles_df.empty:
            st.dataframe(titles_df, hide_index=True)
        else:
            st.info("No titles in the selected filter range.")

    # Logo on this tab
    if team_option in TEAM_LOGOS:
        st.image(
            TEAM_LOGOS[team_option],
            width=160,
            caption=team_option,
        )

# -------------------------------------------------------------------
# PLAYERS TAB
# -------------------------------------------------------------------
with tab_players:
    st.subheader("Player Analysis")

    # Example: top run-scorers in filtered data
    batter_runs = (
        filtered_deliveries.groupby("batter")["batsman_runs"]
        .sum()
        .reset_index()
        .rename(columns={"batsman_runs": "runs"})
        .sort_values("runs", ascending=False)
        .head(15)
    )

    bowler_wkts = (
        filtered_deliveries[filtered_deliveries["is_wicket"] == 1]
        .groupby("bowler")["is_wicket"]
        .sum()
        .reset_index()
        .rename(columns={"is_wicket": "wickets"})
        .sort_values("wickets", ascending=False)
        .head(15)
    )

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("#### Top Run Scorers")
        fig4, ax4 = plt.subplots(figsize=(8, 5))
        sns.barplot(
            data=batter_runs,
            x="runs",
            y="batter",
            ax=ax4,
            palette="viridis",
        )
        ax4.set_xlabel("Runs")
        ax4.set_ylabel("")
        st.pyplot(fig4)

    with c2:
        st.markdown("#### Top Wicket Takers")
        fig5, ax5 = plt.subplots(figsize=(8, 5))
        sns.barplot(
            data=bowler_wkts,
            x="wickets",
            y="bowler",
            ax=ax5,
            palette="magma",
        )
        ax5.set_xlabel("Wickets")
        ax5.set_ylabel("")
        st.pyplot(fig5)

# -------------------------------------------------------------------
# VENUES TAB
# -------------------------------------------------------------------
with tab_venues:
    st.subheader("Venue Analysis")

    venue_option = st.selectbox(
        "Select venue",
        options=sorted(filtered_matches["venue"].unique()),
    )

    venue_matches = filtered_matches[
        filtered_matches["venue"] == venue_option
    ]

    st.markdown(
        f"**Total matches at venue:** {len(venue_matches)}"
    )

    # Average first innings score at venue
    first_innings = filtered_deliveries[
        (filtered_deliveries["inning"] == 1)
        & (filtered_deliveries["match_id"].isin(venue_matches["id"]))
    ]
    venue_scores = (
        first_innings.groupby("match_id")["total_runs"]
        .sum()
        .reset_index()
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### First Innings Scores Distribution")
        fig6, ax6 = plt.subplots(figsize=(7, 4))
        sns.histplot(
            venue_scores["total_runs"],
            bins=15,
            kde=True,
            ax=ax6,
            color="#3b82f6",
        )
        ax6.set_xlabel("First Innings Runs")
        st.pyplot(fig6)

    with col2:
        st.markdown("#### Average First Innings Score")
        avg_score = int(venue_scores["total_runs"].mean())
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{avg_score}</div>
                <div class="metric-label">Average First Innings Score</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# -------------------------------------------------------------------
# TOSS TAB
# -------------------------------------------------------------------
with tab_toss:
    st.subheader("Toss Analysis")

    toss_df = filtered_matches.copy()
    toss_df["toss_win_and_match_win"] = np.where(
        toss_df["toss_winner"] == toss_df["winner"],
        "Yes",
        "No",
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Toss Decision")
        decision_counts = (
            toss_df["toss_decision"]
            .value_counts()
            .reset_index()
            .rename(columns={"index": "decision", "toss_decision": "count"})
        )
        fig7, ax7 = plt.subplots(figsize=(6, 4))
        ax7.pie(
            decision_counts["count"],
            labels=decision_counts["decision"],
            autopct="%1.1f%%",
            startangle=90,
        )
        ax7.axis("equal")
        st.pyplot(fig7)

    with col2:
        st.markdown("#### Impact of Winning Toss")
        impact_counts = (
            toss_df["toss_win_and_match_win"]
            .value_counts()
            .reset_index()
            .rename(columns={"index": "result", "toss_win_and_match_win": "count"})
        )
        fig8, ax8 = plt.subplots(figsize=(6, 4))
        sns.barplot(
            data=impact_counts,
            x="result",
            y="count",
            ax=ax8,
            palette=["#22c55e", "#ef4444"],
        )
        ax8.set_xlabel("Won Toss & Match?")
        ax8.set_ylabel("Matches")
        st.pyplot(fig8)

# -------------------------------------------------------------------
# AUCTION TAB
# -------------------------------------------------------------------
with tab_auction:
    st.subheader("Auction Analysis")

    st.markdown("#### Highest Auction Buys")

    # Example assumes auction has columns: Player, Amount, Year, Team
    top_buys = (
        auction.sort_values("Amount", ascending=False)
        .head(20)
    )

    st.dataframe(top_buys, hide_index=True)

    fig9, ax9 = plt.subplots(figsize=(10, 5))
    sns.barplot(
        data=top_buys,
        x="Amount",
        y="Player",
        ax=ax9,
        palette="flare",
    )
    ax9.set_xlabel("Amount (Cr)")
    ax9.set_ylabel("")
    st.pyplot(fig9)

# -------------------------------------------------------------------
# TEAM LOGOS GALLERY TAB
# -------------------------------------------------------------------
with tab_logos:
    st.subheader("IPL Team Logos")

    cols = st.columns(5)

    i = 0
    for team, logo_path in TEAM_LOGOS.items():
        with cols[i % 5]:
            st.image(logo_path, use_column_width=True)
            st.caption(team)
        i += 1

    st.info(
        "Logos are loaded from the local `logos/` folder. "
        "Ensure all files exist with the correct names."
    )
