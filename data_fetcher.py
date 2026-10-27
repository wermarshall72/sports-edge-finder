import requests
import re
from datetime import datetime

ESPN_URLS = {
    "NFL": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
    "CFB": "https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard?groups=80&limit=100",
    "NCAAB": "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?limit=100"
}


def parse_win_pct(record_str: str) -> float:
    if not record_str:
        return 0.500
    parts = [int(x) for x in re.findall(r"\d+", str(record_str))]
    if len(parts) >= 2 and (parts[0] + parts[1]) > 0:
        return parts[0] / (parts[0] + parts[1])
    return 0.500


def extract_advanced_efficiency(competitor: dict, league: str) -> dict:
    default_ppg = 75.0 if league == "NCAAB" else 5.5
    metrics = {
        "primary_metric": default_ppg,
        "secondary_metric": 0.60
    }
    
    for stat in competitor.get("statistics", []):
        name = stat.get("name", "").lower()
        val_str = stat.get("displayValue", "0")
        try:
            val = float(re.findall(r"[\d\.]+", val_str)[0])
            if "points" in name or "ppg" in name or "avg" in name:
                if league == "NCAAB" and 50.0 <= val <= 105.0:
                    metrics["primary_metric"] = val
                elif league != "NCAAB" and 3.0 <= val <= 8.5:
                    metrics["primary_metric"] = val
        except (ValueError, IndexError, TypeError):
            pass
            
    return metrics


def parse_home_spread(details_str: str, home_abbr: str, away_abbr: str, default_spread: float) -> float:
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
    url = ESPN_URLS.get(league, ESPN_URLS["NFL"])
    default_total = 148.5 if league == "NCAAB" else (45.5 if league == "NFL" else 53.5)
    hfa = 3.5 if league == "NCAAB" else (2.0 if league == "NFL" else 3.0)

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

        home_eff = extract_advanced_efficiency(home_comp, league)
        away_eff = extract_advanced_efficiency(away_comp, league)

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

        rating_scale = 14.0 if league == "NCAAB" else (10.0 if league == "NFL" else 17.0)
        stat_fair_margin = ((home_wp - away_wp) * rating_scale) + hfa

        if book_home_spread is None:
            book_home_spread = round(-stat_fair_margin * 2.0) / 2.0

        market_implied_margin = -book_home_spread
        model_expected_margin = (0.45 * stat_fair_margin) + (0.55 * market_implied_margin)

        base_half = book_total / 2.0
        h_score_base = home_eff["primary_metric"] if home_eff["primary_metric"] != (75.0 if league=="NCAAB" else 5.5) else base_half
        a_score_base = away_eff["primary_metric"] if away_eff["primary_metric"] != (75.0 if league=="NCAAB" else 5.5) else base_half
        
        stat_total = h_score_base + a_score_base
        model_expected_total = (0.60 * book_total) + (0.40 * stat_total)

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
    if league == "NCAAB":
        return [
            {
                "game_id": "ncaab_1", "league": "NCAAB",
                "matchup": "Duke Blue Devils @ North Carolina Tar Heels", "short_matchup": "DUKE @ UNC",
                "status": "Wed 8:00 PM", "away_team": "Duke Blue Devils", "home_team": "North Carolina Tar Heels",
                "away_abbr": "DUKE", "home_abbr": "UNC", "away_record": "12-2", "home_record": "11-3",
                "away_proj": 74.5, "home_proj": 76.0, "book_home_spread": -2.5, "book_away_spread": 2.5,
                "book_total": 151.5, "home_spread_odds": -110, "away_spread_odds": -110,
                "over_odds": -110, "under_odds": -110
            }
        ]
    elif league == "NFL":
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
