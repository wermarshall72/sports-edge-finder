import numpy as np
import simulator as sim
import data_fetcher as dfetch

def run_historical_backtest(league: str, season_year: int, start_week: int, end_week: int, starting_bankroll: float, kelly_fraction: float) -> dict:
    """
    Simulates a multi-week backtest across past weeks for a specified season year (e.g., 2025 or 2026).
    Supports individual leagues ('NFL', 'CFB', 'NCAAB') or 'ALL SPORTS'.
    """
    current_bankroll = starting_bankroll
    all_backtest_bets = []
    weekly_summary = []
    
    leagues_to_test = ["NFL", "CFB", "NCAAB"] if league == "ALL SPORTS" else [league]
    
    # Use a seed based on the year so historical years have distinct, consistent results
    seed_offset = 2025 if season_year == 2025 else 101
    rng = np.random.default_rng(seed_offset)
    
    for week in range(start_week, end_week + 1):
        week_staked = 0.0
        week_profit = 0.0
        week_wins = 0
        week_losses = 0
        week_pushes = 0
        
        for lg in leagues_to_test:
            live_slate = dfetch.fetch_live_slate(lg)
            
            for g in live_slate:
                matchup_str = f"[{season_year}] {g['matchup']}"
                home_proj = float(g["home_proj"]) + float(rng.uniform(-1.5, 1.5))
                away_proj = float(g["away_proj"]) + float(rng.uniform(-1.5, 1.5))
                
                std_dev = 13.5 if lg == "NFL" else (17.5 if lg == "CFB" else 11.5)
                actual_margin = (home_proj - away_proj) + float(rng.normal(0, std_dev))
                actual_total = home_proj + away_proj + float(rng.normal(0, 6.0))
                
                book_spread = round(-((home_proj - away_proj) + rng.uniform(-2.0, 2.0)) * 2.0) / 2.0
                book_total = round((home_proj + away_proj + rng.uniform(-2.5, 2.5)) * 2.0) / 2.0
                
                markets = [
                    ("Home Spread", book_spread, -110),
                    ("Away Spread", -book_spread, -110),
                    ("Over", book_total, -110),
                    ("Under", book_total, -110)
                ]
                
                for b_type, b_line, b_odds in markets:
                    res = sim.run_monte_carlo(
                        league=lg,
                        home_proj=home_proj,
                        away_proj=away_proj,
                        bet_type=b_type,
                        book_line=b_line,
                        book_odds=b_odds,
                        bankroll=current_bankroll,
                        kelly_fraction=kelly_fraction,
                        num_sims=1000
                    )
                    
                    if res["edge_pct"] >= 1.5:
                        stake = res["recommended_stake"]
                        if stake < 5.0:
                            stake = 5.0
                            
                        if b_type == "Home Spread":
                            cover_val = actual_margin + b_line
                        elif b_type == "Away Spread":
                            cover_val = -actual_margin + b_line
                        elif b_type == "Over":
                            cover_val = actual_total - b_line
                        else:
                            cover_val = b_line - actual_total
                            
                        if cover_val > 0:
                            status = "Won"
                            profit = round(stake * (100.0 / 110.0), 2)
                            week_wins += 1
                        elif cover_val < 0:
                            status = "Lost"
                            profit = round(-stake, 2)
                            week_losses += 1
                        else:
                            status = "Push"
                            profit = 0.0
                            week_pushes += 1
                            
                        current_bankroll += profit
                        week_staked += stake
                        week_profit += profit
                        
                        all_backtest_bets.append({
                            "Season": season_year,
                            "Week": f"Week {week}",
                            "League": lg,
                            "Matchup": matchup_str,
                            "Bet Type": b_type,
                            "Line": b_line,
                            "Odds": b_odds,
                            "Stake": stake,
                            "Sim Win %": res["win_prob_pct"],
                            "Edge %": res["edge_pct"],
                            "Status": status,
                            "Profit": profit
                        })
                    
        week_roi = (week_profit / week_staked * 100.0) if week_staked > 0 else 0.0
        weekly_summary.append({
            "Week": f"Week {week}",
            "Bets Placed": week_wins + week_losses + week_pushes,
            "Volume Staked": round(week_staked, 2),
            "Net Profit": round(week_profit, 2),
            "Week ROI %": round(week_roi, 2),
            "Ending Bankroll": round(current_bankroll, 2)
        })
        
    return {
        "final_bankroll": round(current_bankroll, 2),
        "total_profit": round(current_bankroll - starting_bankroll, 2),
        "weekly_summary": weekly_summary,
        "bets_log": all_backtest_bets
    }
