import numpy as np

LEAGUE_STD_DEV = {
    "NFL": 13.5,
    "CFB": 17.5,
    "NCAAB": 11.5
}

NFL_KEY_NUMBERS = {
    3: "🔥 Key #3 (~15% of NFL games)",
    7: "🔥 Key #7 (~9% of NFL games)",
    6: "⚠️ Key #6 (~5% of NFL games)",
    10: "⚠️ Key #10 (~4% of NFL games)",
    4: "⚠️ Key #4 (~4% of NFL games)",
    14: "⚠️ Key #14 (~3% of NFL games)"
}


def american_to_implied_prob(odds: int) -> float:
    if odds < 0:
        return abs(odds) / (abs(odds) + 100.0)
    else:
        return 100.0 / (odds + 100.0)


def american_to_decimal_payout(odds: int) -> float:
    if odds < 0:
        return 100.0 / abs(odds)
    else:
        return odds / 100.0


def check_key_number_alert(league: str, bet_type: str, model_fair_line: float, book_line: float) -> str:
    if league != "NFL" or "Spread" not in bet_type:
        return "Standard distribution"

    low = min(abs(model_fair_line), abs(book_line))
    high = max(abs(model_fair_line), abs(book_line))

    crossed_keys = []
    for key_num, desc in NFL_KEY_NUMBERS.items():
        if low <= key_num <= high:
            crossed_keys.append(desc)

    if crossed_keys:
        return " | ".join(crossed_keys)
    return "No key numbers crossed"


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
    margin_std = LEAGUE_STD_DEV.get(league, 13.5)
    team_std = margin_std / np.sqrt(2.0)

    rng = np.random.default_rng(42)
    sim_home_scores = np.clip(np.round(rng.normal(loc=home_proj, scale=team_std, size=num_sims)), 0, None)
    sim_away_scores = np.clip(np.round(rng.normal(loc=away_proj, scale=team_std, size=num_sims)), 0, None)

    sim_margins = sim_home_scores - sim_away_scores
    sim_totals = sim_home_scores + sim_away_scores

    if bet_type == "Home Spread":
        outcomes = sim_margins + book_line
        model_fair_line = -(home_proj - away_proj)
        dist_data = sim_margins
    elif bet_type == "Away Spread":
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

    decided_games = wins + losses
    win_prob = (wins / decided_games) if decided_games > 0 else 0.0
    loss_prob = 1.0 - win_prob

    implied_prob = american_to_implied_prob(book_odds)
    edge_pct = (win_prob - implied_prob) * 100.0

    b = american_to_decimal_payout(book_odds)
    win_rate_all = wins / num_sims
    loss_rate_all = losses / num_sims
    ev_pct = ((win_rate_all * b) - (loss_rate_all * 1.0)) * 100.0

    full_kelly_pct = ((b * win_prob) - loss_prob) / b if b > 0 else 0.0
    recommended_kelly_pct = max(0.0, full_kelly_pct * kelly_fraction)
    recommended_stake = round(bankroll * recommended_kelly_pct, 2)

    key_number_note = check_key_number_alert(league, bet_type, model_fair_line, book_line)

    return {
        "bet_type": bet_type,
        "book_line": book_line,
        "book_odds": book_odds,
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


def simulate_game_all_markets(
    game: dict,
    bankroll: float = 1000.0,
    kelly_fraction: float = 0.25,
    num_sims: int = 10000
) -> list:
    league = game["league"]
    home_proj = float(game["home_proj"])
    away_proj = float(game["away_proj"])
    home_team = game["home_team"]
    away_team = game["away_team"]

    markets_to_run = [
        ("Away Spread", float(game["book_away_spread"]), int(game.get("away_spread_odds", -110)), f"{away_team} {float(game['book_away_spread']):+.1f}"),
        ("Home Spread", float(game["book_home_spread"]), int(game.get("home_spread_odds", -110)), f"{home_team} {float(game['book_home_spread']):+.1f}"),
        ("Over", float(game["book_total"]), int(game.get("over_odds", -110)), f"Over {float(game['book_total']):.1f}"),
        ("Under", float(game["book_total"]), int(game.get("under_odds", -110)), f"Under {float(game['book_total']):.1f}")
    ]

    results = []
    for b_type, b_line, b_odds, pick_label in markets_to_run:
        res = run_monte_carlo(
            league=league,
            home_proj=home_proj,
            away_proj=away_proj,
            bet_type=b_type,
            book_line=b_line,
            book_odds=b_odds,
            bankroll=bankroll,
            kelly_fraction=kelly_fraction,
            num_sims=num_sims
        )
        res["game_id"] = game["game_id"]
        res["league"] = league
        res["matchup"] = game["matchup"]
        res["short_matchup"] = game["short_matchup"]
        res["status"] = game["status"]
        res["pick_label"] = pick_label
        res["away_proj"] = away_proj
        res["home_proj"] = home_proj
        results.append(res)

    return results
