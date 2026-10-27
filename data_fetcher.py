import requests
import re
from datetime import datetime

ESPN_URLS = {
    "NFL": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
    "CFB": "https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard?groups=80&limit=100"
}


def parse_win_pct(record_str: str) -> float:
    """Converts a team record string like '6-2' or '5-2-1' into a win percentage (0.0 to 1.0)."""
    if not record_str:
        return 0.500
    parts = [int(x) for x in re.findall(r"\d+", str(record_str))]
    if len(parts) >= 2 and (parts[0] + parts[1]) > 0:
        return parts[0] / (parts[0] + parts[1])
    return 0.500


def extract_team_ppg(competitor: dict, default_ppg: float) -> float:
    """Extracts a team's season points-per-game or estimates it from ESPN competitor statistics."""
    for stat in competitor.get("statistics", []):
        name = stat.get("name", "").lower()
        if "points" in name or "scoring" in name or "avgpoints" in name:
            try:
                val = float(stat.get("displayValue", default_ppg))
                if 7.0 <= val <= 60.0:
                    return val
            except (ValueError, TypeError):
                pass
    return default_ppg


def parse_home_spread(details_str: str, home_abbr: str, away_abbr: str, default_spread: float) -> float:
    """
    Parses ESPN's spread string (e.g., 'BUF -3.5' or 'KC -2.5' or 'EVEN')
    and always returns the spread from the HOME team's perspective.
    """
    if not details_str or "EVEN" in str(details_str).upper() or "PK" in str(details_str).upper():
        return 0.0

    parts = str(details_str).strip().split()
    if len(parts) >= 2:
        fav_abbr = parts[0].upper()
        try:
            line_val = float(parts[-1])
            if fav_abbr == home_abbr.upper():
                return -abs(line_val)
            elif fav_abbr == away_abbr.upper():
                return abs(line_val)
        except ValueError:
            pass
    return default_spread


def fetch_live_slate(league: str = "NFL") -> list:
    """
    Pulls the current week's NFL or CFB matchups, live sportsbook spreads/totals,
    and projects team scores automatically using 2026 team performance metrics.
    """
    url = ESPN_URLS.get(league, ESPN_URLS["NFL"])
    default_total = 45.5 if league == "NFL" else 53.5
    hfa = 2.0 if league == "NFL" else 3.0  # Home Field Advantage in points

    try:
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"⚠️ Live fetch warning ({e}) - using fallback slate.")
        return get_fallback_slate(league)

    games = []
    events = data.get("events", [])

    for ev in events:
        comps = ev.get("competitions", [])
        if not comps:
            continue
        comp = comps[0]

        # Find Home and Away teams
        competitors = comp.get("competitors", [])
        home_comp = next((c for c in competitors if c.get("homeAway") == "home"), None)
        away_comp = next((c for c in competitors if c.get("homeAway") == "away"), None)
        if not home_comp or not away_comp:
            continue

        home_team = home_comp.get("team", {}).get("displayName", "Home Team")
        away_team = away_comp.get("team", {}).get("displayName", "Away Team")
        home_abbr = home_comp.get("team", {}).get("abbreviation", "HOM")
        away_abbr = away_comp.get("team", {}).get("abbreviation", "AWY")

        # Extract overall W-L records
        home_rec_list = home_comp.get("records", [])
        away_rec_list = away_comp.get("records", [])
        home_rec = home_rec_list[0].get("summary", "0-0") if home_rec_list else "0-0"
        away_rec = away_rec_list[0].get("summary", "0-0") if away_rec_list else "0-0"

        home_wp = parse_win_pct(home_rec)
        away_wp = parse_win_pct(away_rec)

        # Extract live sportsbook odds from the feed
        odds_list = comp.get("odds", [])
        book_home_spread = None
        book_total = None
        spread_odds_home = -110
        spread_odds_away = -110
        over_odds = -110
        under_odds = -110

        if odds_list:
            odds_obj = odds_list[0]
            if odds_obj.get("overUnder") is not None:
                try:
                    book_total = float(odds_obj["overUnder"])
                except (ValueError, TypeError):
                    pass

            details = odds_obj.get("details", "")
            if details:
                book_home_spread = parse_home_spread(details, home_abbr, away_abbr, 0.0)

            # Check if specific juice/vig is listed (e.g., -115 / -105)
            try:
                ps = odds_obj.get("pointSpread", {})
                h_close = ps.get("home", {}).get("close", {}).get("odds")
                a_close = ps.get("away", {}).get("close", {}).get("odds")
                if h_close:
                    spread_odds_home = int(float(h_close))
                if a_close:
                    spread_odds_away = int(float(a_close))
            except Exception:
                pass

        # Fallback if a game doesn't have an active line posted yet
        if book_total is None:
            book_total = default_total

        # Build independent statistical power-rating projection
        # Combines team win-rate differential, home-field advantage, and scoring environment
        rating_scale = 11.0 if league == "NFL" else 18.5
        stat_fair_margin = ((home_wp - away_wp) * rating_scale) + hfa

        if book_home_spread is None:
            book_home_spread = round(-stat_fair_margin * 2.0) / 2.0

        # Blend market anchors with our independent statistical efficiency rating
        # so the model reflects real team strength while hunting for value numbers
        market_implied_margin = -book_home_spread
        model_expected_margin = (0.55 * stat_fair_margin) + (0.45 * market_implied_margin)

        # Calculate team PPG or baseline scoring total
        base_half = book_total / 2.0
        h_ppg = extract_team_ppg(home_comp, base_half)
        a_ppg = extract_team_ppg(away_comp, base_half)
        stat_total = (h_ppg + a_ppg) if (h_ppg != base_half or a_ppg != base_half) else (
            book_total + ((home_wp + away_wp - 1.0) * 4.5)
        )
        model_expected_total = (0.65 * book_total) + (0.35 * stat_total)

        home_proj = round((model_expected_total + model_expected_margin) / 2.0, 1)
        away_proj = round((model_expected_total - model_expected_margin) / 2.0, 1)

        status_text = ev.get("status", {}).get("type", {}).get("shortDetail", "Upcoming")

        games.append({
            "game_id": ev.get("id", f"{away_abbr}_{home_abbr}"),
            "league": league,
            "matchup": f"{away_team} @ {home_team}",
            "short_matchup": f"{away_abbr} @ {home_abbr}",
            "status": status_text,
            "away_team": away_team,
            "home_team": home_team,
            "away_abbr": away_abbr,
            "home_abbr": home_abbr,
            "away_record": away_rec,
            "home_record": home_rec,
            "away_proj": away_proj,
            "home_proj": home_proj,
            "book_home_spread": float(book_home_spread),
            "book_away_spread": float(-book_home_spread),
            "book_total": float(book_total),
            "home_spread_odds": int(spread_odds_home),
            "away_spread_odds": int(spread_odds_away),
            "over_odds": int(over_odds),
            "under_odds": int(under_odds)
        })

    return games if games else get_fallback_slate(league)


def get_fallback_slate(league: str = "NFL") -> list:
    """Provides a fallback slate if you ever run the app offline without Wi-Fi."""
    if league == "NFL":
        return [
            {
                "game_id": "nfl_1", "league": "NFL",
                "matchup": "Kansas City Chiefs @ Buffalo Bills", "short_matchup": "KC @ BUF",
                "status": "Sun 3:25 PM", "away_team": "Kansas City Chiefs", "home_team": "Buffalo Bills",
                "away_abbr": "KC", "home_abbr": "BUF", "away_record": "6-1", "home_record": "5-2",
                "away_proj": 23.5, "home_proj": 27.0, "book_home_spread": -2.5, "book_away_spread": 2.5,
                "book_total": 48.5, "home_spread_odds": -110, "away_spread_odds": -110,
                "over_odds": -110, "under_odds": -110
            },
            {
                "game_id": "nfl_2", "league": "NFL",
                "matchup": "Baltimore Ravens @ Cincinnati Bengals", "short_matchup": "BAL @ CIN",
                "status": "Sun 12:00 PM", "away_team": "Baltimore Ravens", "home_team": "Cincinnati Bengals",
                "away_abbr": "BAL", "home_abbr": "CIN", "away_record": "5-2", "home_record": "4-3",
                "away_proj": 27.5, "home_proj": 24.0, "book_home_spread": 2.5, "book_away_spread": -2.5,
                "book_total": 50.5, "home_spread_odds": -110, "away_spread_odds": -110,
                "over_odds": -110, "under_odds": -110
            }
        ]
    else:
        return [
            {
                "game_id": "cfb_1", "league": "CFB",
                "matchup": "LSU Tigers @ Arkansas Razorbacks", "short_matchup": "LSU @ ARK",
                "status": "Sat 6:00 PM", "away_team": "LSU Tigers", "home_team": "Arkansas Razorbacks",
                "away_abbr": "LSU", "home_abbr": "ARK", "away_record": "6-1", "home_record": "5-2",
                "away_proj": 28.0, "home_proj": 26.5, "book_home_spread": 3.5, "book_away_spread": -3.5,
                "book_total": 56.5, "home_spread_odds": -110, "away_spread_odds": -110,
                "over_odds": -110, "under_odds": -110
            }
        ]


if __name__ == "__main__":
    nfl_games = fetch_live_slate("NFL")
    cfb_games = fetch_live_slate("CFB")
    print(f"✅ Automatically fetched {len(nfl_games)} live NFL games and {len(cfb_games)} live CFB games!")
    if nfl_games:
        g = nfl_games[0]
        print(f"   Sample NFL Game : {g['matchup']} ({g['status']})")
        print(f"   Model Projection: {g['away_abbr']} {g['away_proj']} - {g['home_abbr']} {g['home_proj']}")
        print(f"   Live Line       : {g['home_abbr']} {g['book_home_spread']:+.1f} | O/U {g['book_total']}")
