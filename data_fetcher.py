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


def extract_advanced_efficiency(competitor: dict) -> dict:
    """
    Extracts advanced drive-level efficiency metrics from ESPN competitor statistics 
    (Yards Per Play, Red Zone Conversion Rate, Success Rate indicators).
    """
    metrics = {
        "yards_per_play": 5.5,  # Baseline league average
        "red_zone_pct": 0.60,   # Baseline red zone touchdown efficiency
        "explosive_rate": 0.12  # Explosive play frequency
    }
    
    for stat in competitor.get("statistics", []):
        name = stat.get("name", "").lower()
        val_str = stat.get("displayValue", "0")
        try:
            val = float(re.findall(r"[\d\.]+", val_str)[0])
            if "yardsperplay" in name or "ypg" in name or "yards/play" in name:
                if 3.0 <= val <= 8.5:
                    metrics["yards_per_play"] = val
            elif "redzone" in name or "rz" in name:
                if val > 1.0: # If given as percentage like 85.0
                    val = val / 100.0
                if 0.3 <= val <= 1.0:
                    metrics["red_zone_pct"] = val
        except (ValueError, IndexError, TypeError):
            pass
            
    return metrics


def parse_home_spread(details_str: str, home_abbr: str, away_abbr: str, default_spread: float) -> float:
    """Parses ESPN's spread string from the HOME team's perspective."""
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
    Pulls live matchups, sportsbook odds, and integrates advanced drive-level 
    efficiency metrics (Yards per Play, Red Zone conversion) into score projections.
    """
    url = ESPN_URLS.get(league, ESPN_URLS["NFL"])
    default_total = 45.5 if league == "NFL" else 53.5
    hfa = 2.0 if league == "NFL" else 3.0

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

        competitors = comp.get("competitors", [])
        home_comp = next((c for c in competitors if c.get("homeAway") == "home"), None)
        away_comp = next((c for c in competitors if c.get("homeAway") == "away"), None)
        if not home_comp or not away_comp:
            continue

        home_team = home_comp.get("team", {}).get("displayName", "Home Team")
        away_team = away_comp.get("team", {}).get("displayName", "Away Team")
        home_abbr = home_comp.get("team", {}).get("abbreviation", "HOM")
        away_abbr = away_comp.get("team", {}).get("abbreviation", "AWY")

        home_rec = home_comp.get("records", [{}])[0].get("summary", "0-0")
        away_rec = away_comp.get("records", [{}])[0].get("summary", "0-0")

        home_wp = parse_win_pct(home_rec)
        away_wp = parse_win_pct(away_rec)

        # Extract Advanced Efficiency Stats
        home_eff = extract_advanced_efficiency(home_comp)
        away_eff = extract_advanced_efficiency(away_comp)

        # Extract live sportsbook odds
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

        if book_total is None:
            book_total = default_total

        # --- ADVANCED EFFICIENCY BLEND MODEL ---
        # Factor Yards Per Play differential and Red Zone efficiency into power ratings
        ypp_diff = home_eff["yards_per_play"] - away_eff["yards_per_play"]
        rz_diff = home_eff["red_zone_pct"] - away_eff["red_zone_pct"]
        
        efficiency_margin_boost = (ypp_diff * 3.2) + (rz_diff * 4.0)
        
        rating_scale = 10.0 if league == "NFL" else 17.0
        stat_fair_margin = ((home_wp - away_wp) * rating_scale) + hfa + efficiency_margin_boost

        if book_home_spread is None:
            book_home_spread = round(-stat_fair_margin * 2.0) / 2.0

        market_implied_margin = -book_home_spread
        model_expected_margin = (0.50 * stat_fair_margin) + (0.50 * market_implied_margin)

        # Efficiency-adjusted scoring totals
        base_half = book_total / 2.0
        eff_total_modifier = ((home_eff["yards_per_play"] + away_eff["yards_per_play"] - 11.0) * 2.5)
        stat_total = book_total + eff_total_modifier
        model_expected_total = (0.55 * book_total) + (0.45 * stat_total)

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
