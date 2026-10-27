import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import database as db
import simulator as sim
import data_fetcher as dfetch
import backtest_engine as btest

# 1. Page Configuration
st.set_page_config(
    page_title="SARACEN EDGE // Quantitative Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

db.init_db()

# ---------------------------------------------------------
# PRO SPORTSBOOK CUSTOM CSS STYLING
# ---------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background: transparent !important;}
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2.5rem !important;
        max-width: 1440px;
    }

    [data-testid="stSidebar"] {
        background-color: #0F131A !important;
        border-right: 1px solid #1E2430;
    }

    .brand-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: linear-gradient(90deg, #121722 0%, #0E121A 100%);
        border: 1px solid #1F2937;
        border-left: 4px solid #10B981;
        border-radius: 10px;
        padding: 16px 24px;
        margin-bottom: 20px;
    }
    .brand-title {
        font-size: 1.35rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        color: #F9FAFB;
        margin: 0;
    }
    .brand-sub {
        font-size: 0.8rem;
        color: #9CA3AF;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 3px;
    }
    .live-pill {
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(16, 185, 129, 0.4);
        color: #10B981;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 6px 12px;
        border-radius: 999px;
    }

    .sec-header {
        font-size: 0.85rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #9CA3AF;
        margin: 18px 0 10px 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    div[data-testid="stMetric"] {
        background: #131822;
        border: 1px solid #1F2735;
        border-radius: 10px;
        padding: 14px 18px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.72rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #8B95A5 !important;
    }
    div[data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 1.55rem !important;
        font-weight: 700 !important;
        color: #F9FAFB !important;
    }

    .scoreboard-banner {
        background: #131822;
        border: 1px solid #222B3A;
        border-radius: 12px;
        padding: 18px 26px;
        margin-bottom: 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .sb-team-block {
        display: flex;
        flex-direction: column;
    }
    .sb-team-name {
        font-size: 1.15rem;
        font-weight: 700;
        color: #F9FAFB;
    }
    .sb-team-rec {
        font-size: 0.78rem;
        color: #8B95A5;
        font-family: 'JetBrains Mono', monospace;
    }
    .sb-proj-box {
        text-align: center;
        background: #0D1118;
        border: 1px solid #1F2937;
        border-radius: 8px;
        padding: 8px 18px;
    }
    .sb-proj-label {
        font-size: 0.68rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #8B95A5;
    }
    .sb-proj-val {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.1rem;
        font-weight: 700;
        color: #10B981;
    }

    .market-card {
        background: #131822;
        border: 1px solid #222B3A;
        border-radius: 12px;
        padding: 18px;
        transition: all 0.15s ease-in-out;
        height: 100%;
    }
    .market-card-ev {
        background: linear-gradient(180deg, rgba(16, 185, 129, 0.08) 0%, #131822 100%);
        border: 1px solid #10B981;
        box-shadow: 0 0 20px rgba(16, 185, 129, 0.08);
    }
    .mc-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    .mc-type {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #8B95A5;
    }
    .mc-badge-pos {
        background: rgba(16, 185, 129, 0.15);
        color: #10B981;
        border: 1px solid rgba(16, 185, 129, 0.35);
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 4px;
    }
    .mc-badge-neg {
        background: rgba(107, 114, 128, 0.12);
        color: #9CA3AF;
        border: 1px solid rgba(107, 114, 128, 0.25);
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 4px;
    }
    .mc-pick-row {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        background: #0B0E14;
        border: 1px solid #1E2532;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 14px;
    }
    .mc-pick-name {
        font-size: 1.05rem;
        font-weight: 700;
        color: #FFFFFF;
    }
    .mc-odds {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.95rem;
        font-weight: 700;
        color: #10B981;
    }
    .mc-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        border-top: 1px solid #1E2532;
        padding-top: 12px;
    }
    .mc-stat-label {
        font-size: 0.68rem;
        color: #8B95A5;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .mc-stat-val {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.9rem;
        font-weight: 600;
        color: #E5E7EB;
    }
    .mc-footer {
        margin-top: 12px;
        padding-top: 10px;
        border-top: 1px dashed #222B3A;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.75rem;
        color: #9CA3AF;
    }
    .mc-stake {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        color: #F9FAFB;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=900)
def load_league_slate(league_name: str):
    return dfetch.fetch_live_slate(league_name)


bets_df = db.get_all_bets()
starting_bankroll = db.get_starting_bankroll()

if not bets_df.empty:
    graded_df = bets_df[bets_df["status"].isin(["Won", "Lost", "Push"])]
    realized_profit = float(graded_df["profit"].sum())
    pending_exposure = float(bets_df[bets_df["status"] == "Pending"]["stake"].sum())
else:
    graded_df = pd.DataFrame()
    realized_profit = 0.0
    pending_exposure = 0.0

current_bankroll = starting_bankroll + realized_profit

# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚡ SARACEN // EDGE")
    st.caption("QUANTITATIVE PRICING & KELLY DESK")

    selected_league = st.segmented_control(
        "LEAGUE SLATE",
        options=["NFL", "CFB"],
        default="NFL",
        selection_mode="single"
    )
    if not selected_league:
        selected_league = "NFL"

    if st.button("↻ Sync Live Market Feed", use_container_width=True):
        st.cache_data.clear()
        for k in list(st.session_state.keys()):
            if k.startswith("slate_"):
                del st.session_state[k]
        st.rerun()

    st.divider()
    st.metric(
        label="Active Bankroll",
        value=f"${current_bankroll:,.2f}",
        delta=f"{realized_profit:+,.2f} Net P&L"
    )
    st.caption(f"Open Risk Exposure: **${pending_exposure:,.2f}**")

    st.divider()
    st.markdown("##### RISK PARAMETERS")
    new_start_br = st.number_input(
        "Starting Bankroll ($)",
        min_value=50.0,
        max_value=1000000.0,
        value=float(starting_bankroll),
        step=50.0
    )
    if new_start_br != starting_bankroll:
        db.set_starting_bankroll(new_start_br)
        st.rerun()

    kelly_fraction = st.slider(
        "Kelly Multiplier",
        min_value=0.10,
        max_value=1.00,
        value=0.25,
        step=0.05,
        help="0.25x (Quarter Kelly) is standard institutional sizing."
    )
    st.caption(f"Sizing Engine: **{int(kelly_fraction * 100)}% Kelly** on **${current_bankroll:,.2f}**")

state_key = f"slate_{selected_league}"
if state_key not in st.session_state:
    st.session_state[state_key] = load_league_slate(selected_league)

active_games = st.session_state[state_key]

# ---------------------------------------------------------
# TOP BRAND HEADER BAR
# ---------------------------------------------------------
st.markdown(f"""
<div class="brand-bar">
    <div>
        <div class="brand-title">BETSARACEN QUANTITATIVE EDGE TERMINAL</div>
        <div class="brand-sub">{selected_league} LIVE SLATE • 10,000-GAME MONTE CARLO ENGINE • LOCAL SQLITE VAULT</div>
    </div>
    <div class="live-pill">● {len(active_games)} {selected_league} GAMES ACTIVE</div>
</div>
""", unsafe_allow_html=True)

tab_board, tab_tracker, tab_backtest = st.tabs([
    f"TRADING BOARD & SIMULATOR ({selected_league})",
    f"PORTFOLIO & ROI LEDGER ({len(bets_df)})",
    "📊 HISTORICAL BACKTEST ENGINE"
])

# =========================================================
# TAB 1: TRADING BOARD & SIMULATOR
# =========================================================
with tab_board:
    with st.expander(f"⚙️ MARKET LINE MANAGER — View or Override Live {selected_league} Lines & Projections ({len(active_games)} Matchups)", expanded=False):
        st.caption("Double-click any cell to adjust a BetSaracen spread, total, or juice. All simulations below recalculate immediately.")

        slate_df = pd.DataFrame(active_games)
        editable_cols = [
            "matchup", "status", "away_record", "home_record",
            "away_proj", "home_proj", "book_home_spread",
            "home_spread_odds", "away_spread_odds", "book_total", "over_odds", "under_odds"
        ]

        edited_slate = st.data_editor(
            slate_df[editable_cols],
            use_container_width=True,
            hide_index=True,
            disabled=["matchup", "status", "away_record", "home_record"],
            column_config={
                "matchup": st.column_config.TextColumn("Matchup", width="medium"),
                "status": st.column_config.TextColumn("Kickoff", width="small"),
                "away_record": st.column_config.TextColumn("Away", width="small"),
                "home_record": st.column_config.TextColumn("Home", width="small"),
                "away_proj": st.column_config.NumberColumn("Away Proj", step=0.5, format="%.1f"),
                "home_proj": st.column_config.NumberColumn("Home Proj", step=0.5, format="%.1f"),
                "book_home_spread": st.column_config.NumberColumn("Book Home Line", step=0.5, format="%+.1f"),
                "home_spread_odds": st.column_config.NumberColumn("Home Odds", step=5, format="%+d"),
                "away_spread_odds": st.column_config.NumberColumn("Away Odds", step=5, format="%+d"),
                "book_total": st.column_config.NumberColumn("Book Total", step=0.5, format="%.1f"),
                "over_odds": st.column_config.NumberColumn("Over Odds", step=5, format="%+d"),
                "under_odds": st.column_config.NumberColumn("Under Odds", step=5, format="%+d"),
            },
            key=f"editor_{selected_league}"
        )

        for idx, row in edited_slate.iterrows():
            active_games[idx]["away_proj"] = float(row["away_proj"])
            active_games[idx]["home_proj"] = float(row["home_proj"])
            active_games[idx]["book_home_spread"] = float(row["book_home_spread"])
            active_games[idx]["book_away_spread"] = float(-row["book_home_spread"])
            active_games[idx]["home_spread_odds"] = int(row["home_spread_odds"])
            active_games[idx]["away_spread_odds"] = int(row["away_spread_odds"])
            active_games[idx]["book_total"] = float(row["book_total"])
            active_games[idx]["over_odds"] = int(row["over_odds"])
            active_games[idx]["under_odds"] = int(row["under_odds"])

    all_market_sims = []
    game_sim_map = {}

    for g in active_games:
        four_markets = sim.simulate_game_all_markets(
            game=g,
            bankroll=current_bankroll,
            kelly_fraction=kelly_fraction
        )
        game_sim_map[g["matchup"]] = four_markets
        all_market_sims.extend(four_markets)

    all_market_sims_sorted = sorted(all_market_sims, key=lambda x: x["ev_pct"], reverse=True)
    pos_ev_plays = [m for m in all_market_sims_sorted if m["ev_pct"] > 0]
    prime_ev_plays = [m for m in all_market_sims_sorted if m["edge_pct"] >= 3.0]
    best_ev = all_market_sims_sorted[0]["ev_pct"] if all_market_sims_sorted else 0.0

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Markets Simulated", f"{len(all_market_sims)}", f"{len(active_games) * 10000:,} total sims")
    s2.metric("Positive +EV Plays", f"{len(pos_ev_plays)}", "EV > 0.0%")
    s3.metric("Prime Edge Plays", f"{len(prime_ev_plays)}", "Edge >= +3.0%")
    s4.metric("Top Slate EV %", f"{best_ev:+.2f}%", all_market_sims_sorted[0]["pick_label"] if all_market_sims_sorted else "N/A")

    st.markdown('<div class="sec-header">⚡ TOP MATHEMATICAL EDGES — RANKED BY EXPECTED VALUE (+EV %)</div>', unsafe_allow_html=True)

    f_col1, f_col2 = st.columns([2, 4])
    with f_col1:
        only_positive_ev = st.toggle("Filter Positive +EV Only", value=True)
    with f_col2:
        st.caption("Select the **Ticket** checkbox on any row below to log plays directly to your SQLite ledger.")

    filtered_sims = [m for m in all_market_sims_sorted if (m["ev_pct"] > 0 or not only_positive_ev)]

    if not filtered_sims:
        st.info("No positive +EV plays at current lines.")
    else:
        top_table_rows = []
        for m in filtered_sims:
            default_stake = m["recommended_stake"] if m["recommended_stake"] > 0 else 25.0
            signal = "PRIME +EV" if m["edge_pct"] >= 3.0 else ("LEAN +EV" if m["edge_pct"] > 0 else "PASS")
            top_table_rows.append({
                "Log Bet": False,
                "Signal": signal,
                "Matchup": m["short_matchup"],
                "Kickoff": m["status"],
                "Bet Type": m["bet_type"],
                "Recommended Pick": m["pick_label"],
                "Book Line": m["book_line"],
                "Model Fair": m["model_fair_line"],
                "Odds": int(m["book_odds"]),
                "Sim Cover %": m["win_prob_pct"],
                "Breakeven %": m["implied_prob_pct"],
                "Edge %": m["edge_pct"],
                "EV %": m["ev_pct"],
                "Stake ($)": default_stake,
                "Full Matchup": m["matchup"]
            })

        top_df = pd.DataFrame(top_table_rows)

        edited_top_df = st.data_editor(
            top_df.drop(columns=["Full Matchup"]),
            use_container_width=True,
            hide_index=True,
            disabled=[
                "Signal", "Matchup", "Kickoff", "Bet Type", "Recommended Pick",
                "Book Line", "Model Fair", "Odds", "Sim Cover %",
                "Breakeven %", "Edge %", "EV %"
            ],
            column_config={
                "Log Bet": st.column_config.CheckboxColumn("Ticket", width="small"),
                "Signal": st.column_config.TextColumn("Signal", width="small"),
                "Matchup": st.column_config.TextColumn("Game", width="small"),
                "Kickoff": st.column_config.TextColumn("Kickoff", width="small"),
                "Bet Type": st.column_config.TextColumn("Market", width="small"),
                "Recommended Pick": st.column_config.TextColumn("Play", width="medium"),
                "Book Line": st.column_config.NumberColumn("Book", format="%.1f"),
                "Model Fair": st.column_config.NumberColumn("Model Fair", format="%.1f"),
                "Odds": st.column_config.NumberColumn("Odds", format="%+d"),
                "Sim Cover %": st.column_config.NumberColumn("Win Prob", format="%.1f%%"),
                "Breakeven %": st.column_config.NumberColumn("Implied", format="%.1f%%"),
                "Edge %": st.column_config.NumberColumn("Edge", format="%+.2f%%"),
                "EV %": st.column_config.ProgressColumn("Expected Value", format="%+.2f%%", min_value=-5.0, max_value=15.0),
                "Stake ($)": st.column_config.NumberColumn("Stake ($)", min_value=1.0, step=5.0, format="$%.2f")
            },
            key=f"top_ev_table_{selected_league}"
        )

        selected_indices = edited_top_df[edited_top_df["Log Bet"] == True].index.tolist()
        if selected_indices:
            if st.button(f"LOCK IN {len(selected_indices)} SELECTED TICKET(S) TO VAULT", type="primary"):
                for idx in selected_indices:
                    orig_row = top_df.loc[idx]
                    db.log_bet(
                        league=selected_league,
                        matchup=str(orig_row["Full Matchup"]),
                        bet_type=str(orig_row["Bet Type"]),
                        pick=str(orig_row["Recommended Pick"]),
                        line=float(orig_row["Book Line"]),
                        odds=int(orig_row["Odds"]),
                        stake=float(edited_top_df.loc[idx, "Stake ($)"]),
                        sim_prob=float(orig_row["Sim Cover %"]),
                        edge=float(orig_row["Edge %"]),
                        status="Pending"
                    )
                st.success(f"Locked in {len(selected_indices)} ticket(s) to SQLite ledger.")
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="sec-header">🎯 MATCHUP DEEP DIVE — 4-WAY MARKET PRICING & SCORE DISTRIBUTIONS</div>', unsafe_allow_html=True)

    matchup_options = [g["matchup"] for g in active_games]
    selected_matchup = st.selectbox("SELECT MATCHUP TO INSPECT", matchup_options, label_visibility="collapsed")

    selected_game = next(g for g in active_games if g["matchup"] == selected_matchup)
    four_res = game_sim_map[selected_matchup]

    fair_home_spread = -(selected_game["home_proj"] - selected_game["away_proj"])
    fair_total = selected_game["home_proj"] + selected_game["away_proj"]

    st.markdown(f"""
    <div class="scoreboard-banner">
        <div class="sb-team-block">
            <span class="sb-team-rec">AWAY • {selected_game['away_record']}</span>
            <span class="sb-team-name">{selected_game['away_team']}</span>
        </div>
        <div class="sb-proj-box">
            <div class="sb-proj-label">MODEL PROJECTED SCORE</div>
            <div class="sb-proj-val">{selected_game['away_abbr']} {selected_game['away_proj']:.1f}  —  {selected_game['home_abbr']} {selected_game['home_proj']:.1f}</div>
        </div>
        <div class="sb-proj-box">
            <div class="sb-proj-label">MODEL FAIR LINE / TOTAL</div>
            <div class="sb-proj-val">{selected_game['home_abbr']} {fair_home_spread:+.1f}  |  O/U {fair_total:.1f}</div>
        </div>
        <div class="sb-team-block" style="text-align: right;">
            <span class="sb-team-rec">HOME • {selected_game['home_record']} • {selected_game['status']}</span>
            <span class="sb-team-name">{selected_game['home_team']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    card_cols = st.columns(4)
    for col, r in zip(card_cols, four_res):
        is_ev = r["ev_pct"] > 0
        card_class = "market-card market-card-ev" if is_ev else "market-card"
        badge_class = "mc-badge-pos" if is_ev else "mc-badge-neg"
        badge_text = f"{r['ev_pct']:+.2f}% EV" if is_ev else f"{r['ev_pct']:+.1f}% EV"
        fair_str = f"{r['model_fair_line']:+.1f}" if "Spread" in r["bet_type"] else f"{r['model_fair_line']:.1f}"

        with col:
            st.markdown(f"""
            <div class="{card_class}">
                <div class="mc-top">
                    <span class="mc-type">{r['bet_type']}</span>
                    <span class="{badge_class}">{badge_text}</span>
                </div>
                <div class="mc-pick-row">
                    <span class="mc-pick-name">{r['pick_label']}</span>
                    <span class="mc-odds">{int(r['book_odds']):+d}</span>
                </div>
                <div class="mc-grid">
                    <div>
                        <div class="mc-stat-label">Sim Cover %</div>
                        <div class="mc-stat-val">{r['win_prob_pct']:.1f}%</div>
                    </div>
                    <div>
                        <div class="mc-stat-label">Model Fair</div>
                        <div class="mc-stat-val">{fair_str}</div>
                    </div>
                    <div>
                        <div class="mc-stat-label">Edge vs Vig</div>
                        <div class="mc-stat-val" style="color: {'#10B981' if r['edge_pct'] > 0 else '#9CA3AF'};">{r['edge_pct']:+.2f}%</div>
                    </div>
                    <div>
                        <div class="mc-stat-label">10k Sim Split</div>
                        <div class="mc-stat-val">{r['wins']}W-{r['losses']}L</div>
                    </div>
                </div>
                <div class="mc-footer">
                    <span>{int(kelly_fraction*100)}% Kelly Sizing</span>
                    <span class="mc-stake">${r['recommended_stake']:,.2f}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    hist_col1, hist_col2 = st.columns(2)
    home_spread_res = next(r for r in four_res if r["bet_type"] == "Home Spread")
    over_res = next(r for r in four_res if r["bet_type"] == "Over")

    with hist_col1:
        fig_spread = go.Figure()
        fig_spread.add_trace(go.Histogram(
            x=home_spread_res["dist_data"],
            nbinsx=42,
            marker=dict(color="#10B981", line=dict(color="#0B0E14", width=1)),
            opacity=0.85,
            name="Home Margin"
        ))
        target_margin = -float(selected_game["book_home_spread"])
        fig_spread.add_vline(
            x=target_margin,
            line_width=2.5,
            line_dash="dash",
            line_color="#F59E0B",
            annotation_text=f"Book Line: {selected_game['home_abbr']} {selected_game['book_home_spread']:+.1f}",
            annotation_font=dict(family="JetBrains Mono", size=12, color="#F59E0B"),
            annotation_position="top right"
        )
        fig_spread.update_layout(
            title=dict(text=f"SPREAD DISTRIBUTION // {selected_game['home_abbr']} MARGIN (10,000 SIMS)", font=dict(size=13, color="#9CA3AF")),
            xaxis=dict(title=f"{selected_game['home_abbr']} Margin of Victory", gridcolor="#1E2532", zerolinecolor="#374151"),
            yaxis=dict(title="Frequency", gridcolor="#1E2532"),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#131822",
            font=dict(family="Inter", color="#9CA3AF"),
            height=330,
            margin=dict(l=15, r=15, t=45, b=15)
        )
        st.plotly_chart(fig_spread, use_container_width=True)

    with hist_col2:
        fig_total = go.Figure()
        fig_total.add_trace(go.Histogram(
            x=over_res["dist_data"],
            nbinsx=42,
            marker=dict(color="#3B82F6", line=dict(color="#0B0E14", width=1)),
            opacity=0.85,
            name="Total Points"
        ))
        fig_total.add_vline(
            x=float(selected_game["book_total"]),
            line_width=2.5,
            line_dash="dash",
            line_color="#F59E0B",
            annotation_text=f"O/U Line: {selected_game['book_total']:.1f}",
            annotation_font=dict(family="JetBrains Mono", size=12, color="#F59E0B"),
            annotation_position="top right"
        )
        fig_total.update_layout(
            title=dict(text=f"TOTAL POINTS DISTRIBUTION // {selected_game['short_matchup']} (10,000 SIMS)", font=dict(size=13, color="#9CA3AF")),
            xaxis=dict(title="Combined Total Points", gridcolor="#1E2532"),
            yaxis=dict(title="Frequency", gridcolor="#1E2532"),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#131822",
            font=dict(family="Inter", color="#9CA3AF"),
            height=330,
            margin=dict(l=15, r=15, t=45, b=15)
        )
        st.plotly_chart(fig_total, use_container_width=True)

# =========================================================
# TAB 2: PORTFOLIO & ROI ANALYTICS
# =========================================================
with tab_tracker:
    st.markdown('<div class="sec-header">📈 PORTFOLIO PERFORMANCE & BANKROLL ANALYTICS</div>', unsafe_allow_html=True)

    if bets_df.empty:
        st.info("Your SQLite vault has no logged tickets yet.")
    else:
        total_staked_graded = float(graded_df["stake"].sum()) if not graded_df.empty else 0.0
        roi_pct = (realized_profit / total_staked_graded * 100.0) if total_staked_graded > 0 else 0.0

        decided_df = graded_df[graded_df["status"].isin(["Won", "Lost"])] if not graded_df.empty else pd.DataFrame()
        total_wins = int((decided_df["status"] == "Won").sum()) if not decided_df.empty else 0
        total_losses = int((decided_df["status"] == "Lost").sum()) if not decided_df.empty else 0
        win_rate_pct = (total_wins / (total_wins + total_losses) * 100.0) if (total_wins + total_losses) > 0 else 0.0

        p1, p2, p3, p4, p5 = st.columns(5)
        p1.metric("Active Bankroll", f"${current_bankroll:,.2f}", f"Start: ${starting_bankroll:,.2f}")
        p2.metric("Realized P&L", f"${realized_profit:+,.2f}", f"{len(graded_df)} Settled Tickets")
        p3.metric("Return on Investment", f"{roi_pct:+.2f}%", f"${total_staked_graded:,.2f} Volume")
        p4.metric("ATS Win Rate", f"{win_rate_pct:.1f}%", f"{total_wins}W - {total_losses}L")
        p5.metric("Open Bets", f"{len(bets_df[bets_df['status']=='Pending'])}", "Pending Action")

        st.dataframe(bets_df, use_container_width=True, hide_index=True)

        g_col1, g_col2, g_col3, g_col4 = st.columns([2, 2, 2, 2])
        bet_ids = bets_df["id"].tolist()

        with g_col1:
            selected_id = st.selectbox("Ticket #", bet_ids)
        with g_col2:
            new_status = st.selectbox("Settlement Status", ["Pending", "Won", "Lost", "Push"])
        with g_col3:
            st.write("")
            st.write("")
            if st.button("SETTLE TICKET", type="primary", use_container_width=True):
                db.update_bet_status(int(selected_id), new_status)
                st.rerun()
        with g_col4:
            st.write("")
            st.write("")
            if st.button("VOID / DELETE TICKET", use_container_width=True):
                db.delete_bet(int(selected_id))
                st.rerun()

# =========================================================
# TAB 3: HISTORICAL BACKTEST ENGINE
# =========================================================
with tab_backtest:
    st.markdown('<div class="sec-header">📊 MULTI-WEEK HISTORICAL BACKTESTING ENGINE</div>', unsafe_allow_html=True)
    st.caption("Simulate how your $1,000 starting bankroll would have compounded across past weeks of the 2026 season using our Monte Carlo model and Quarter-Kelly sizing.")

    bt_col1, bt_col2, bt_col3, bt_col4 = st.columns(4)
    with bt_col1:
        bt_league = st.selectbox("Backtest League", ["NFL", "CFB"], key="bt_league")
    with bt_col2:
        bt_start_week = st.number_input("Start Week", min_value=1, max_value=15, value=1, step=1)
    with bt_col3:
        bt_end_week = st.number_input("End Week", min_value=1, max_value=16, value=8, step=1)
    with bt_col4:
        st.write("")
        st.write("")
        run_bt = st.button("🚀 RUN MULTI-WEEK BACKTEST", type="primary", use_container_width=True)

    if run_bt:
        if bt_start_week > bt_end_week:
            st.error("Start week cannot be greater than end week.")
        else:
            with st.spinner(f"Simulating weeks {bt_start_week} through {bt_end_week} for {bt_league}..."):
                bt_results = btest.run_historical_backtest(
                    league=bt_league,
                    start_week=bt_start_week,
                    end_week=bt_end_week,
                    starting_bankroll=starting_bankroll,
                    kelly_fraction=kelly_fraction
                )

            st.markdown("<br>", unsafe_allow_html=True)
            
            # Summary Metrics
            bm1, bm2, bm3, bm4 = st.columns(4)
            bm1.metric("Initial Bankroll", f"${starting_bankroll:,.2f}", f"Week {bt_start_week} Start")
            bm2.metric("Ending Bankroll", f"${bt_results['final_bankroll']:,.2f}", f"Week {bt_end_week} End")
            bm3.metric("Net Backtest P&L", f"${bt_results['total_profit']:+,.2f}", f"Total Profit")
            
            total_bt_staked = sum(w["Volume Staked"] for w in bt_results["weekly_summary"])
            bt_roi = (bt_results["total_profit"] / total_bt_staked * 100.0) if total_bt_staked > 0 else 0.0
            bm4.metric("Backtest ROI %", f"{bt_roi:+.2f}%", f"${total_bt_staked:,.2f} Total Volume")

            st.markdown("<br>", unsafe_allow_html=True)
            
            # Weekly Performance Table & Equity Curve
            w_col1, w_col2 = st.columns([2, 3])

            with w_col1:
                st.markdown("##### Weekly Performance Breakdown")
                st.dataframe(pd.DataFrame(bt_results["weekly_summary"]), use_container_width=True, hide_index=True)

            with w_col2:
                # Cumulative Equity Curve Chart
                summary_df = pd.DataFrame(bt_results["weekly_summary"])
                if not summary_df.empty:
                    x_weeks = ["Start"] + summary_df["Week"].tolist()
                    y_banks = [starting_bankroll] + summary_df["Ending Bankroll"].tolist()

                    fig_bt = go.Figure()
                    fig_bt.add_trace(go.Scatter(
                        x=x_weeks,
                        y=y_banks,
                        mode="lines+markers",
                        line=dict(color="#10B981", width=3),
                        fill="tozeroy",
                        fillcolor="rgba(16, 185, 129, 0.08)",
                        name="Backtested Bankroll"
                    ))
                    fig_bt.add_hline(y=starting_bankroll, line_dash="dot", line_color="#6B7280", annotation_text="Starting Bankroll")
                    fig_bt.update_layout(
                        title=dict(text=f"BACKTEST EQUITY CURVE // WEEKS {bt_start_week}–{bt_end_week}", font=dict(size=13, color="#9CA3AF")),
                        xaxis=dict(title="Season Week", gridcolor="#1E2532"),
                        yaxis=dict(title="Bankroll ($)", gridcolor="#1E2532"),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="#131822",
                        font=dict(family="Inter", color="#9CA3AF"),
                        height=310,
                        margin=dict(l=15, r=15, t=40, b=15)
                    )
                    st.plotly_chart(fig_bt, use_container_width=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("##### Master Backtest Bet Ledger")
            st.dataframe(pd.DataFrame(bt_results["bets_log"]), use_container_width=True, hide_index=True)
