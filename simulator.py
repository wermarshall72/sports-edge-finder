import numpy as np


# League-specific margin volatility (Standard Deviation in points)
LEAGUE_STD_DEV = {
    "NFL": 13.5,
    "CFB": 17.5
}

# Key NFL spread numbers (most common final margins of victory in NFL history)
NFL_KEY_NUMBERS = {
    3: "🔥 Key Number 3 (~15% of NFL games land on 3)",
    7: "🔥 Key Number 7 (~9% of NFL games land on 7)",
    6: "⚠️ Secondary Key Number 6 (~5% of NFL games)",
    10: "⚠️ Secondary Key Number 10 (~4% of NFL games)",
    4: "⚠️ Secondary Key Number 4 (~4% of NFL games)",
    14: "⚠️ Secondary Key Number 14 (~3% of NFL games)"
}


def american_to_implied_prob(odds: int) -> float:
    """Converts American odds (e.g., -110 or +120) to Implied Breakeven Probability (0.0 to 1.0)."""
    if odds < 0:
        return abs(odds) / (abs(odds) + 100.0)
    else:
        return 100.0 / (odds + 100.0)


def american_to_decimal_payout(odds: int) -> float:
    """Returns net profit per $1 risked (b in the Kelly Criterion formula)."""
    if odds < 0:
        return 100.0 / abs(odds)
    else:
        return odds / 100.0


def check_key_number_alert(league: str, bet_type: str, model_fair_line: float, book_line: float) -> str:
    """Checks if the discrepancy between our model and BetSaracen crosses a crucial NFL key number."""
    if league != "NFL" or "Spread" not in bet_type:
        return "Standard number distribution."

    low = min(abs(model_fair_line), abs(book_line))
    high = max(abs(model_fair_line), abs(book_line))

    crossed_keys = []
    for key_num, desc in NFL_KEY_NUMBERS.items():
        if low <= key_num <= high:
            crossed_keys.append(desc)

    if crossed_keys:
        return " | ".join(crossed_keys)
    return "No major NFL key numbers crossed between Model and Book line."


def run_monte_carlo(
    league: str,
    home_proj: float,
    away_proj: float,
    bet_type: str,
    book_line: float,
    book_odds: int,
    bankroll: float = 1000.0,
    kelly_fraction: float = 0.25,
    num_sims: int = 10000
) -> dict:
    """
    Runs 10,000 simulated games using NumPy and calculates Cover %, Implied %,
    Edge %, EV %, and Fractional Kelly Criterion recommended stake.
    """
    # 1. Get the league margin standard deviation (13.5 for NFL, 17.5 for CFB)
    margin_std = LEAGUE_STD_DEV.get(league, 13.5)

    # Since Var(Home - Away) = Var(Home) + Var(Away), each team's individual score
    # standard deviation is margin_std / sqrt(2) so their combined margin equals margin_std.
    team_std = margin_std / np.sqrt(2.0)

    # 2. Simulate 10,000 games simultaneously using a fixed random seed for reproducibility
    rng = np.random.default_rng(42)
    sim_home_scores = rng.normal(loc=home_proj, scale=team_std, size=num_sims)
    sim_away_scores = rng.normal(loc=away_proj, scale=team_std, size=num_sims)

    # Prevent negative football scores and round to whole points for push detection
    sim_home_scores = np.clip(np.round(sim_home_scores), 0, None)
    sim_away_scores = np.clip(np.round(sim_away_scores), 0, None)

    # Calculate simulated margins (Home - Away) and Totals (Home + Away)
    sim_margins = sim_home_scores - sim_away_scores
    sim_totals = sim_home_scores + sim_away_scores

    # 3. Grade all 10,000 games based on the selected Bet Type
    if bet_type == "Home Spread":
        # Example: Home -3.0 means (Home - Away) + (-3.0) > 0 to cover
        outcomes = sim_margins + book_line
        model_fair_line = -(home_proj - away_proj)
        dist_data = sim_margins
    elif bet_type == "Away Spread":
        # Example: Away +3.5 means (Away - Home) + (+3.5) > 0 to cover
        outcomes = (-sim_margins) + book_line
        model_fair_line = home_proj - away_proj
        dist_data = -sim_margins
    elif bet_type == "Over":
        outcomes = sim_totals - book_line
        model_fair_line = home_proj + away_proj
        dist_data = sim_totals
    elif bet_type == "Under":
        outcomes = book_line - sim_totals
        model_fair_line = home_proj + away_proj
        dist_data = sim_totals
    else:
        raise ValueError(f"Unknown bet_type: {bet_type}")

    wins = int(np.sum(outcomes > 0))
    losses = int(np.sum(outcomes < 0))
    pushes = int(np.sum(outcomes == 0))

    # 4. Calculate True Cover Probability (excluding pushes, which refund stake)
    decided_games = wins + losses
    win_prob = (wins / decided_games) if decided_games > 0 else 0.0
    loss_prob = 1.0 - win_prob

    # 5. Calculate Implied Breakeven Probability, Edge %, and +EV %
    implied_prob = american_to_implied_prob(book_odds)
    edge_pct = (win_prob - implied_prob) * 100.0

    # Net decimal payout per $1 risked (b)
    b = american_to_decimal_payout(book_odds)

    # Expected Value (EV) including pushes (which have $0 impact)
    win_rate_all = wins / num_sims
    loss_rate_all = losses / num_sims
    ev_pct = ((win_rate_all * b) - (loss_rate_all * 1.0)) * 100.0

    # 6. Calculate Fractional Kelly Criterion Bet Size
    full_kelly_pct = ((b * win_prob) - loss_prob) / b if b > 0 else 0.0
    recommended_kelly_pct = max(0.0, full_kelly_pct * kelly_fraction)
    recommended_stake = round(bankroll * recommended_kelly_pct, 2)

    # Check if an NFL Key Number is involved
    key_number_note = check_key_number_alert(league, bet_type, model_fair_line, book_line)

    return {
        "num_sims": num_sims,
        "wins": wins,
        "losses": losses,
        "pushes": pushes,
        "win_prob_pct": round(win_prob * 100.0, 2),
        "implied_prob_pct": round(implied_prob * 100.0, 2),
        "edge_pct": round(edge_pct, 2),
        "ev_pct": round(ev_pct, 2),
        "model_fair_line": round(model_fair_line, 1),
        "recommended_kelly_pct": round(recommended_kelly_pct * 100.0, 2),
        "recommended_stake": recommended_stake,
        "key_number_note": key_number_note,
        "dist_data": dist_data
    }


if __name__ == "__main__":
    # Quick Self-Test: NFL Game where Model projects Home 27, Away 21 (Fair Spread: Home -6.0)
    # BetSaracen hangs a slow line of Home -3.0 at -110 odds!
    test_result = run_monte_carlo(
        league="NFL",
        home_proj=27.0,
        away_proj=21.0,
        bet_type="Home Spread",
        book_line=-3.0,
        book_odds=-110,
        bankroll=1000.0,
        kelly_fraction=0.25
    )
    print("🏈 10,000-Game Monte Carlo Self-Test (Model: Home -6.0 vs. BetSaracen: Home -3.0 @ -110)")
    print(f"   Simulated Record : {test_result['wins']} Wins - {test_result['losses']} Losses - {test_result['pushes']} Pushes")
    print(f"   Simulated Cover %: {test_result['win_prob_pct']}% (vs. {test_result['implied_prob_pct']}% Implied Breakeven)")
    print(f"   Mathematical Edge: +{test_result['edge_pct']}% | Expected Value (EV): +{test_result['ev_pct']}%")
    print(f"   1/4 Kelly Stake  : ${test_result['recommended_stake']:.2f} ({test_result['recommended_kelly_pct']}% of $1,000 bankroll)")
    print(f"   Key Number Alert : {test_result['key_number_note']}")
