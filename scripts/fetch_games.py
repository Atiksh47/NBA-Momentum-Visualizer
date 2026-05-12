"""
Phase 1: NBA Momentum Engine
Fetches play-by-play via nba_api (PlayByPlayV3) and computes momentum + energy curves.
Outputs one JSON file per game to ../data/
"""

import json
import time
import math
from pathlib import Path
from nba_api.stats.endpoints import playbyplayv3

OUT_DIR = Path(__file__).parent.parent / "data"
OUT_DIR.mkdir(exist_ok=True)

GAMES = [
    {
        "gameId": "0041500407",
        "title": "2016 Finals Game 7",
        "subtitle": "The Comeback. The Block. The Shot.",
        "date": "2016-06-19",
        "homeTeam": "GSW",
        "awayTeam": "CLE",
        "homeColor": "#1D428A",
        "awayColor": "#860038",
        "homeColorSecondary": "#FFC72C",
        "awayColorSecondary": "#FDBB30",
    },
    {
        "gameId": "0021501228",
        "title": "Kobe's Last Game",
        "subtitle": "60 points. Curtain call.",
        "date": "2016-04-13",
        "homeTeam": "LAL",
        "awayTeam": "UTA",
        "homeColor": "#552583",
        "awayColor": "#00471B",
        "homeColorSecondary": "#FDB927",
        "awayColorSecondary": "#F9A01B",
    },
    {
        "gameId": "0021501226",
        "title": "Warriors Win 73",
        "subtitle": "The regular season record that defined an era.",
        "date": "2016-04-13",
        "homeTeam": "GSW",
        "awayTeam": "MEM",
        "homeColor": "#1D428A",
        "awayColor": "#5D76A9",
        "homeColorSecondary": "#FFC72C",
        "awayColorSecondary": "#12173F",
    },
    {
        "gameId": "0021500568",
        "title": "Christmas 2015 - Warriors vs Cavs",
        "subtitle": "The rematch. Curry vs LeBron.",
        "date": "2015-12-25",
        "homeTeam": "GSW",
        "awayTeam": "CLE",
        "homeColor": "#1D428A",
        "awayColor": "#860038",
        "homeColorSecondary": "#FFC72C",
        "awayColorSecondary": "#FDBB30",
    },
    {
        "gameId": "0042100306",
        "title": "2022 Finals Game 6 - Curry 43",
        "subtitle": "Curry claims his Finals MVP.",
        "date": "2022-06-16",
        "homeTeam": "BOS",
        "awayTeam": "GSW",
        "homeColor": "#007A33",
        "awayColor": "#1D428A",
        "homeColorSecondary": "#BA9653",
        "awayColorSecondary": "#FFC72C",
    },
]


def fetch_playbyplay(game_id: str) -> list[dict]:
    pbp = playbyplayv3.PlayByPlayV3(game_id=game_id, timeout=60)
    df = pbp.get_data_frames()[0]
    return df.to_dict("records")


def parse_clock(clock_str: str) -> float:
    """Parse 'PT12M00.00S' or 'MM:SS' format -> seconds remaining in period."""
    if not clock_str:
        return 720.0
    # PT format from v3
    if clock_str.startswith("PT"):
        s = clock_str[2:].replace("S", "")
        if "M" in s:
            m, sec = s.split("M")
            return float(m) * 60 + float(sec)
        return float(s)
    # MM:SS fallback
    parts = clock_str.split(":")
    return int(parts[0]) * 60 + float(parts[1])


def event_to_seconds(period: int, clock_str: str) -> float:
    """Convert period + clock -> total seconds elapsed in game."""
    period_start = (period - 1) * 720.0
    remaining = parse_clock(clock_str)
    return period_start + (720.0 - remaining)


def normalize_events(raw: list[dict]) -> list[dict]:
    events = []
    for row in raw:
        period = int(row.get("period", 1))
        clock = str(row.get("clock", "PT12M00.00S"))
        t = event_to_seconds(period, clock)

        action = str(row.get("actionType", "")).lower()
        sub = str(row.get("subType", "")).lower()
        desc = str(row.get("description", ""))

        # Map to our event types (V3 uses title-case action names)
        if action == "made shot":
            etype = "score"
        elif action == "missed shot":
            etype = "miss"
        elif action == "free throw":
            etype = "free_throw" if "made" in desc.lower() else "miss"
        elif action == "rebound":
            etype = "rebound"
        elif action == "turnover":
            etype = "turnover"
        elif action == "foul":
            etype = "foul"
        elif action == "timeout":
            etype = "timeout"
        elif action in ("period", "jump ball", "violation", "substitution", "instant replay"):
            etype = action.replace(" ", "_")
        else:
            etype = "other"

        # Score
        home_score = 0
        away_score = 0
        try:
            hs = row.get("scoreHome")
            aws = row.get("scoreAway")
            if hs and str(hs).strip():
                home_score = int(hs)
            if aws and str(aws).strip():
                away_score = int(aws)
        except (ValueError, TypeError):
            pass

        # Team
        tricode = row.get("teamTricode") or ""
        location = str(row.get("location", ""))
        team = "home" if location == "h" else ("away" if location == "v" else "neutral")

        try:
            shot_val = int(row.get("shotValue") or 0)
        except (ValueError, TypeError):
            shot_val = 0
        if etype == "score":
            score_delta = shot_val if shot_val > 0 else (3 if "3PT" in desc or "3pt" in desc else 2)
        elif etype == "free_throw":
            score_delta = 1
        else:
            score_delta = 0

        events.append({
            "t": round(t, 1),
            "period": period,
            "type": etype,
            "team": team,
            "teamTricode": tricode,
            "scoreDelta": score_delta,
            "homeScore": home_score,
            "awayScore": away_score,
            "desc": desc[:80],
        })

    return sorted(events, key=lambda e: e["t"])


def fill_scores(events: list[dict], n: int, sample_rate: float) -> tuple[list[float], list[float]]:
    """Build per-second home/away score arrays by forward-filling."""
    home_scores = [0.0] * n
    away_scores = [0.0] * n
    last_home, last_away = 0, 0
    ei = 0
    for s in range(n):
        t = s * sample_rate
        while ei < len(events) and events[ei]["t"] <= t:
            if events[ei]["homeScore"] > 0 or events[ei]["awayScore"] > 0:
                last_home = events[ei]["homeScore"]
                last_away = events[ei]["awayScore"]
            ei += 1
        home_scores[s] = last_home
        away_scores[s] = last_away
    return home_scores, away_scores


def compute_momentum(events: list[dict], game_duration: float) -> dict:
    SAMPLE_RATE = 1.0
    n = int(game_duration / SAMPLE_RATE) + 1
    home_scores, away_scores = fill_scores(events, n, SAMPLE_RATE)

    WINDOW_SHORT = 120  # 2-min rolling run window
    WINDOW_LONG  = 300  # 5-min baseline

    momentum = [0.0] * n
    energy   = [0.0] * n

    # Pre-index events by second for pace calculation
    events_by_second: list[list] = [[] for _ in range(n)]
    for e in events:
        s = min(int(e["t"]), n - 1)
        events_by_second[s].append(e)

    for s in range(n):
        t = s * SAMPLE_RATE

        ws = max(0, s - WINDOW_SHORT)
        wl = max(0, s - WINDOW_LONG)

        home_run_short = home_scores[s] - home_scores[ws]
        away_run_short = away_scores[s] - away_scores[ws]
        home_run_long  = home_scores[s] - home_scores[wl]
        away_run_long  = away_scores[s] - away_scores[wl]

        # Positive = away team leading momentum (consistent sign convention)
        run_diff = (
            2 * (away_run_short - home_run_short) +
            1 * (away_run_long  - home_run_long)
        )
        raw_momentum = math.tanh(run_diff / 15.0)

        # Score differential: closeness = tension
        diff = abs(away_scores[s] - home_scores[s])
        closeness = math.exp(-diff / 8.0)

        # Time pressure: last 2 minutes of any period
        time_in_period = t % 720
        time_pressure = 1.0 + 2.5 * max(0.0, (time_in_period - 600) / 120)

        # Pace: action events in last 60 seconds
        pace_events = sum(
            1 for ss in range(max(0, s - 60), s)
            for e in events_by_second[ss]
            if e["type"] in ("score", "turnover", "foul", "rebound")
        )
        pace = min(1.0, pace_events / 10.0)

        total_run_short = max(home_run_short, away_run_short)

        raw_energy = (
            0.30 * pace +
            0.30 * closeness +
            0.20 * min(1.0, total_run_short / 12.0) +
            0.20 * min(1.0, (time_pressure - 1.0) / 2.5)
        )

        momentum[s] = round(max(-1.0, min(1.0, raw_momentum * time_pressure)), 4)
        energy[s]   = round(min(1.0, max(0.0, raw_energy)), 4)

    return {
        "momentum": momentum,
        "energy": energy,
        "sampleRate": SAMPLE_RATE,
        "duration": game_duration,
    }


def detect_key_moments(events: list[dict], momentum: list[float], energy: list[float]) -> list[dict]:
    moments = []
    last_lead = "tied"
    home_run = 0
    away_run = 0
    last_scorer = None
    run_start_t = 0.0
    last_home, last_away = 0, 0

    for e in events:
        if e["type"] == "timeout":
            s = min(int(e["t"]), len(energy) - 1)
            if energy[s] > 0.5:
                moments.append({"t": e["t"], "label": "Timeout", "type": "timeout", "intensity": round(energy[s], 3)})
            continue

        if e["type"] not in ("score", "free_throw"):
            continue

        hs, aws = e["homeScore"], e["awayScore"]
        if hs == 0 and aws == 0:
            continue

        scorer = e["team"]
        delta = e["scoreDelta"]

        # Scoring run tracking
        if scorer == last_scorer:
            if scorer == "home":
                home_run += delta
            elif scorer == "away":
                away_run += delta
        else:
            run_pts = home_run if last_scorer == "home" else away_run
            if run_pts >= 8 and last_scorer in ("home", "away"):
                team_label = e.get("teamTricode") or last_scorer.capitalize()
                moments.append({
                    "t": run_start_t,
                    "label": f"{run_pts}-0 run",
                    "type": "run_start",
                    "intensity": round(min(1.0, run_pts / 15.0), 3),
                })
            home_run = delta if scorer == "home" else 0
            away_run = delta if scorer == "away" else 0
            run_start_t = e["t"]
            last_scorer = scorer

        # Lead change
        new_lead = "tied" if hs == aws else ("home" if hs > aws else "away")
        if new_lead != last_lead and new_lead != "tied" and last_lead != "tied":
            moments.append({
                "t": e["t"],
                "label": f"Lead change  {hs}-{aws}",
                "type": "lead_change",
                "intensity": 0.7,
            })
        last_lead = new_lead
        last_home, last_away = hs, aws

        # Clutch 3 in high-energy moment
        s = min(int(e["t"]), len(energy) - 1)
        if delta == 3 and energy[s] > 0.65:
            moments.append({
                "t": e["t"],
                "label": "Three!",
                "type": "clutch_shot",
                "intensity": round(energy[s], 3),
            })

    # Deduplicate: no two moments within 20 seconds
    moments.sort(key=lambda m: m["t"])
    deduped = []
    last_t = -999.0
    for m in moments:
        if m["t"] - last_t >= 20:
            deduped.append(m)
            last_t = m["t"]

    return deduped


def process_game(game: dict) -> dict:
    print(f"  Fetching {game['gameId']}...")
    raw = fetch_playbyplay(game["gameId"])
    print(f"  Got {len(raw)} raw rows")

    events = normalize_events(raw)
    scored = [e for e in events if e["homeScore"] > 0 or e["awayScore"] > 0]
    print(f"  Normalized: {len(events)} events, {len(scored)} with scores")

    if not events:
        raise ValueError("No events parsed")

    periods = max(e["period"] for e in events)
    game_duration = periods * 720.0
    print(f"  Duration: {game_duration/60:.1f} min ({periods} periods)")

    curves = compute_momentum(events, game_duration)
    key_moments = detect_key_moments(events, curves["momentum"], curves["energy"])
    print(f"  Key moments: {len(key_moments)}")

    last_scored = next((e for e in reversed(events) if e["homeScore"] > 0), None)
    final_home = last_scored["homeScore"] if last_scored else 0
    final_away = last_scored["awayScore"] if last_scored else 0
    print(f"  Final: {game['homeTeam']} {final_home} - {game['awayTeam']} {final_away}")

    return {
        "gameId":             game["gameId"],
        "title":              game["title"],
        "subtitle":           game["subtitle"],
        "date":               game["date"],
        "homeTeam":           game["homeTeam"],
        "awayTeam":           game["awayTeam"],
        "homeColor":          game["homeColor"],
        "awayColor":          game["awayColor"],
        "homeColorSecondary": game["homeColorSecondary"],
        "awayColorSecondary": game["awayColorSecondary"],
        "finalScore":         {"home": final_home, "away": final_away},
        "duration":           game_duration,
        "sampleRate":         curves["sampleRate"],
        "momentumCurve":      curves["momentum"],
        "energyCurve":        curves["energy"],
        "keyMoments":         key_moments,
        "events":             events,
    }


def main():
    print(f"Processing {len(GAMES)} games -> {OUT_DIR}\n")
    for game in GAMES:
        print(f"[{game['gameId']}] {game['title']}")
        try:
            result = process_game(game)
            out_path = OUT_DIR / f"{game['gameId']}.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(result, f, separators=(",", ":"))
            size_kb = out_path.stat().st_size / 1024
            print(f"  Saved: {out_path.name} ({size_kb:.1f} KB)\n")
        except Exception as ex:
            import traceback
            print(f"  ERROR: {ex}")
            traceback.print_exc()
            print()
        time.sleep(2)

    print("Done.")


if __name__ == "__main__":
    main()
