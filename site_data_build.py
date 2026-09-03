#!/usr/bin/env python3
"""Build the browser-ready league data bundle from the historical source files.

The output is deliberately plain JavaScript so the site remains GitHub Pages
compatible. Run from the repository root with: python3 site_data_build.py
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parent
HISTORY = ROOT / "data" / "history"
SITE = ROOT / "site"
CURRENT_YEAR = str(max(int(k.split("_")[1]) for k in json.loads((Path(__file__).resolve().parent / "data" / "history" / "history_raw.json").read_text(encoding="utf-8")) if "_" in k))


def load(name):
    return json.loads((HISTORY / name).read_text(encoding="utf-8"))


def listify(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def number(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def integer(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def compact_number(value):
    return round(number(value), 2)


def read_existing_bundle():
    """Keep editorial cards and the hand-authored current power index intact."""
    path = SITE / "data.js"
    if not path.exists():
        return {}
    raw = path.read_text(encoding="utf-8").strip()
    raw = re.sub(r"^window\.LEAGUE_DATA\s*=\s*", "", raw).rstrip(";")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


identities = load("identities.json")["people"]
lineage = load("mfl_franchise_lineage.json")
sleeper_identities = load("sleeper_identities.json")
CHAMPIONS_FILE = json.loads((HISTORY / "champions.json").read_text(encoding="utf-8")) if (HISTORY / "champions.json").exists() else {"super_bowls": {}, "champions_by_year": {}, "current_champion": None}

sleeper_history = load("history_processed.json")
mfl_raw = load("mfl_raw.json")
existing = read_existing_bundle()


DEFAULT_ERAS = [
    {"years": "2014", "platform": "ESPN", "note": "Founding season. 10 teams, one league."},
    {"years": "2015", "platform": "RT Sports", "note": "Expansion to 20 teams. The AFC and NFC are born."},
    {"years": "2016", "platform": "ESPN ×2", "note": "Two mirrored leagues, one per conference."},
    {"years": "2017–2021", "platform": "MyFantasyLeague", "note": "One 20-team league across the AFC and NFC."},
    {"years": "2022–now", "platform": "Sleeper", "note": "Two 12-team auction leagues and a live Sunday hub."},
]

DEFAULT_RECORDS = [
    {
        "title": "The cmarks214 curse",
        "body": "No Sleeper-era title despite the best record; last ring 2019. Cortney Marks went 36–16 from 2022–25, then lost in the semifinal four straight years to four different managers.",
    },
    {
        "title": "Closest game ever (Sleeper era)",
        "body": "AFC 2024, Week 4: hardy09 107.48 def. Gregh2123 107.37 — a margin of 0.11. Seven other games since 2022 finished under half a point.",
    },
    {
        "title": "Two finals, no ring",
        "body": "Krowbar1269 reached the finals in both conferences (2022 NFC, 2024 AFC) and lost both. Mark Tovar’s last title remains the founding season, 2014.",
    },
    {
        "title": "The 10–0 heartbreak",
        "body": "In 2016, Mark Tovar’s An Ultralight Team started 10–0, led both conferences in points, earned the AFC’s top seed, and lost the semifinal to the eventual champion.",
    },
    {
        "title": "Champions who ran it back",
        "body": "Orlando Aragon owns two AFC titles in three years (2023, 2025). Nick Chestnut eliminated BlueSpruce in back-to-back postseasons.",
    },
    {
        "title": "The defector",
        "body": "Daniel Polverari won the 2025 NFC championship, then moved to the AFC for 2026 — ten years after losing the 2015 Super Bowl as License to Hill.",
    },
    {
        "title": "Mirror drafts",
        "body": "A tradition older than Sleeper: in 2016 Antonio Brown went first overall in both conference drafts. In 2026, 162 players were bought in both auctions.",
    },
    {
        "title": "First-round exits",
        "body": "Daniel Quintana was eliminated in round one in three straight playoff appearances (2022–24). Sam Hardy has four Sleeper-era playoff trips without a conference title.",
    },
]

FALLBACK_RECON = existing.get("recon", {})
FOUNDERS = existing.get(
    "founding",
    ["Mark Tovar", "Sam Hardy", "Orley Aragon", "Danny Jurado", "Josh Jurado", "Jordan Grado", "Jessica Shoeman"],
)

power_rankings = existing.get("powerRankings", {"edition": "2026 preseason", "note": "", "rows": []})
_pr_file = HISTORY / "power_rankings.json"
if _pr_file.exists():
    _pr = json.loads(_pr_file.read_text(encoding="utf-8"))
    if _pr.get("rows"):
        power_rankings = _pr
records = existing.get("records", DEFAULT_RECORDS)
records = [dict(card) for card in records]
for card in records:
    if "cmarks214" in (card.get("title", "") + card.get("body", "")):
        card["body"] = DEFAULT_RECORDS[0]["body"]


people = {}
handle_to_person = {}
mfl_to_person = {}
pre_to_person = {}
for person_id, raw in identities.items():
    handle = raw.get("sleeper") or ""
    public_name = raw.get("name") or handle or person_id
    if public_name.lower().startswith("unknown ("):
        public_name = ""
    public_name = re.sub(r"\s*\(\d{4},\s*franchise\s+\d+\)$", "", public_name, flags=re.I)
    people[person_id] = {
        "id": person_id,
        "name": public_name,
        "handle": handle,
        "userId": None,
        "current": None,
        "seasons": [],
        "h2h": {},
        "summary": {},
    }
    if handle:
        handle_to_person[handle.casefold()] = person_id
    for year, franchise_id in raw.get("mfl", {}).items():
        mfl_to_person[(str(year), str(franchise_id).zfill(4))] = person_id
    for year, team in raw.get("pre", {}).items():
        pre_to_person[(str(year), re.sub(r"\s+", " ", team).strip().casefold())] = person_id


user_to_person = {}
for user_id, seasons in sleeper_identities.items():
    person_id = None
    for season in seasons.values():
        person_id = handle_to_person.get(str(season.get("handle", "")).casefold())
        if person_id:
            break
    if not person_id:
        latest = sleeper_history.get("latest_name", {}).get(user_id, "")
        person_id = handle_to_person.get(latest.casefold())
    if person_id:
        user_to_person[user_id] = person_id
        people[person_id]["userId"] = user_id


logo_by_key = {}
for logo in (SITE / "assets" / "logos" / "mfl").glob("*_*.*"):
    year, franchise = logo.stem.split("_", 1)
    logo_by_key[(year, franchise)] = logo.relative_to(SITE).as_posix()


def add_person_season(person_id, season):
    if not person_id:
        return
    people[person_id]["seasons"].append(season)


def find_person_by_pre_team(year, team):
    clean = re.sub(r"\s+", " ", str(team)).strip().casefold()
    if (year, clean) in pre_to_person:
        return pre_to_person[(year, clean)]
    for (mapped_year, mapped_team), person_id in pre_to_person.items():
        if mapped_year == year and (mapped_team in clean or clean in mapped_team):
            return person_id
    return None


def mfl_conference(year, franchise):
    division = str(franchise.get("division", ""))
    if year == "2017":
        return "AFC" if division in {"00", "01"} else "NFC"
    return "AFC" if division == "00" else "NFC"


def mfl_team(year, franchise_id, fallback=""):
    return lineage.get(franchise_id, {}).get(year, fallback).strip()


def new_h2h():
    return {"wins": 0, "losses": 0, "ties": 0, "pf": 0.0, "pa": 0.0, "games": 0, "playoffWins": 0, "playoffLosses": 0}


h2h = defaultdict(new_h2h)
rivalry_games = []
rivalry_playoffs = []


playoff_record = defaultdict(lambda: {"wins": 0, "losses": 0, "pf": 0.0, "pa": 0.0, "games": 0})  # keys: person_id and (person_id, year)


def add_playoff_record(person_id, year, scored, allowed):
    if not person_id:
        return
    for key in (person_id, (person_id, str(year))):
        rec = playoff_record[key]
        rec["games"] += 1
        rec["wins"] += scored > allowed
        rec["losses"] += scored < allowed
        rec["pf"] += scored
        rec["pa"] += allowed


def add_h2h(person_a, person_b, score_a, score_b, *, playoff=False, meta=None):
    if not person_a or not person_b or person_a == person_b:
        return
    score_a, score_b = number(score_a), number(score_b)
    a = h2h[(person_a, person_b)]
    b = h2h[(person_b, person_a)]
    if playoff:
        if meta and meta.get("year"):
            add_playoff_record(person_a, meta["year"], score_a, score_b)
            add_playoff_record(person_b, meta["year"], score_b, score_a)
        if score_a > score_b:
            a["playoffWins"] += 1
            b["playoffLosses"] += 1
        elif score_b > score_a:
            b["playoffWins"] += 1
            a["playoffLosses"] += 1
        if meta:
            rivalry_playoffs.append({**meta, "a": person_a, "b": person_b, "scoreA": compact_number(score_a), "scoreB": compact_number(score_b)})
        return
    for item, scored, allowed in ((a, score_a, score_b), (b, score_b, score_a)):
        item["games"] += 1
        item["pf"] += scored
        item["pa"] += allowed
    if score_a > score_b:
        a["wins"] += 1
        b["losses"] += 1
    elif score_b > score_a:
        b["wins"] += 1
        a["losses"] += 1
    else:
        a["ties"] += 1
        b["ties"] += 1
    if meta:
        rivalry_games.append({**meta, "a": person_a, "b": person_b, "scoreA": compact_number(score_a), "scoreB": compact_number(score_b)})


def playoff_games(bracket):
    rounds = listify((bracket or {}).get("playoffRound"))
    output = []
    for round_index, round_data in enumerate(rounds, 1):
        for game in listify(round_data.get("playoffGame")):
            home, away = game.get("home", {}), game.get("away", {})
            if home.get("franchise_id") and away.get("franchise_id"):
                output.append(
                    {
                        "round": round_index,
                        "week": integer(round_data.get("week")),
                        "home": home.get("franchise_id"),
                        "away": away.get("franchise_id"),
                        "homeScore": number(home.get("points")),
                        "awayScore": number(away.get("points")),
                    }
                )
    return output, len(rounds)


weekly_scores = []
blowouts = []
mfl_seasons = {}
mfl_season_lookup = {}

for year in sorted(mfl_raw):
    source = mfl_raw[year]
    league = source["league"]["league"]
    franchises = {item["id"]: item for item in league["franchises"]["franchise"]}
    standings = source["leagueStandings"]["leagueStandings"]["franchise"]
    season_groups = {"AFC": [], "NFC": []}

    # 2019: MFL's final standings leaked the week 13-14 playoff rounds (and later weeks' points) into the regular season.
    # The standings snapshot as of week 12 is the true regular season (doubleheaders weeks 1-10, single games 11-12).
    _fix_file = HISTORY / year / "regular_season_standings.json"
    regular_fix = json.loads(_fix_file.read_text(encoding="utf-8"))["franchises"] if _fix_file.exists() else {}
    _sched_file = HISTORY / year / "schedule_inferred.json"
    inferred_games = json.loads(_sched_file.read_text(encoding="utf-8"))["games"] if _sched_file.exists() else []
    for rank, standing in enumerate(standings, 1):
        franchise_id = str(standing["id"]).zfill(4)
        franchise = franchises[franchise_id]
        conference = mfl_conference(year, franchise)
        person_id = mfl_to_person.get((year, franchise_id))
        if franchise_id in regular_fix:
            fix = regular_fix[franchise_id]
            standing = {**standing, "h2hw": fix["wins"], "h2hl": fix["losses"], "h2ht": fix["ties"], "pf": fix["pf"], "pa": fix["pa"]}
        row = {
            "rank": rank,
            "franchiseId": franchise_id,
            "personId": person_id,
            "conference": conference,
            "team": mfl_team(year, franchise_id, franchise.get("name", "")),
            "logo": logo_by_key.get((year, franchise_id), ""),
            "wins": integer(standing.get("h2hw")),
            "losses": integer(standing.get("h2hl")),
            "ties": integer(standing.get("h2ht")),
            "pf": compact_number(standing.get("pf")),
            "pa": compact_number(standing.get("pa")),
            "playoff": False,
            "finish": "—",
            "champion": False,
            "leagueChampion": False,
            "conferenceChampion": False,
        }
        season_groups[conference].append(row)
        mfl_season_lookup[(year, franchise_id)] = row

    details = source.get("playoffBracketDetail", {})
    main_brackets = ["1", "2"] if year in {"2017", "2018"} else ["1"]
    for bracket_id in main_brackets:
        bracket = details.get(bracket_id, {}).get("playoffBracket", {})
        games, round_count = playoff_games(bracket)
        conference = "AFC" if bracket_id == "1" else "NFC"
        for game in games:
            home, away = game["home"], game["away"]
            for franchise_id in (home, away):
                row = mfl_season_lookup.get((year, franchise_id))
                if row:
                    row["playoff"] = True
            home_won = game["homeScore"] > game["awayScore"]
            winner = home if home_won else away
            loser = away if home_won else home
            loser_row = mfl_season_lookup.get((year, loser))
            if loser_row:
                if game["round"] == round_count:
                    loser_row["finish"] = "Conference finalist" if year in {"2017", "2018"} else "Runner-up"
                elif game["round"] == round_count - 1:
                    loser_row["finish"] = "Semifinal"
                elif game["round"] == 1:
                    loser_row["finish"] = "First round"
                else:
                    loser_row["finish"] = "Quarterfinal"
            if game["round"] == round_count:
                winner_row = mfl_season_lookup.get((year, winner))
                if winner_row:
                    if year in {"2017", "2018"}:
                        winner_row["conferenceChampion"] = True
                        winner_row["champion"] = True
                        winner_row["finish"] = f"{conference} champion"
                    else:
                        winner_row["leagueChampion"] = True
                        winner_row["champion"] = True
                        winner_row["finish"] = "Champion"
            add_h2h(
                mfl_to_person.get((year, home)),
                mfl_to_person.get((year, away)),
                game["homeScore"],
                game["awayScore"],
                playoff=True,
                meta={"year": year, "week": game["week"], "platform": "MFL", "round": f"Playoff round {game['round']}", "conference": conference},
            )

    if year in {"2017", "2018"}:
        super_bowl = details.get("3", {}).get("playoffBracket", {})
        games, _ = playoff_games(super_bowl)
        for game in games:
            home_won = game["homeScore"] > game["awayScore"]
            winner = game["home"] if home_won else game["away"]
            loser = game["away"] if home_won else game["home"]
            winner_row = mfl_season_lookup.get((year, winner))
            loser_row = mfl_season_lookup.get((year, loser))
            if winner_row:
                winner_row.update({"leagueChampion": True, "champion": True, "finish": "Champion"})
            if loser_row:
                loser_row["finish"] = "Runner-up"
            add_h2h(
                mfl_to_person.get((year, game["home"])),
                mfl_to_person.get((year, game["away"])),
                game["homeScore"],
                game["awayScore"],
                playoff=True,
                meta={"year": year, "week": game["week"], "platform": "MFL", "round": "Super Bowl", "conference": "League"},
            )
        # Third-place games between the conference semifinal losers (brackets 5 and 6). The "Loser Bowl" (4) and its
        # third-place game (7) are consolation brackets for non-playoff teams and are not playoff games.
        for bracket_id in ("5", "6"):
            games, _ = playoff_games(details.get(bracket_id, {}).get("playoffBracket", {}))
            for game in games:
                home_row, away_row = mfl_season_lookup.get((year, game["home"])), mfl_season_lookup.get((year, game["away"]))
                if not (home_row and away_row and home_row.get("playoff") and away_row.get("playoff")):
                    continue
                home_won = game["homeScore"] > game["awayScore"]
                winner_row, loser_row = (home_row, away_row) if home_won else (away_row, home_row)
                if winner_row.get("finish") == "Semifinal":
                    winner_row["finish"] = "Third place"
                if loser_row.get("finish") == "Semifinal":
                    loser_row["finish"] = "Fourth place"
                add_h2h(
                    mfl_to_person.get((year, game["home"])),
                    mfl_to_person.get((year, game["away"])),
                    game["homeScore"],
                    game["awayScore"],
                    playoff=True,
                    meta={"year": year, "week": game["week"], "platform": "MFL", "round": "Third place game", "conference": mfl_conference(year, franchises[game["home"]])},
                )

    last_regular = integer(league.get("lastRegularSeasonWeek"), 13)
    seen_scores = set()
    reg_points = defaultdict(lambda: {"pf": 0.0, "pa": 0.0, "games": 0})
    def note_regular(left_id, right_id, left_score, right_score):
        for me, opp, mine, theirs in ((left_id, right_id, left_score, right_score), (right_id, left_id, right_score, left_score)):
            rec = reg_points[me]
            rec["pf"] += mine; rec["pa"] += theirs; rec["games"] += 1
    if inferred_games:
        last_regular = max(game["week"] for game in inferred_games)
    for game in inferred_games:
        week = integer(game["week"])
        left_id, right_id = game["a"], game["b"]
        left_score, right_score = number(game["sa"]), number(game["sb"])
        for franchise_id, score in ((left_id, left_score), (right_id, right_score)):
            if (week, franchise_id) not in seen_scores:
                weekly_scores.append({"score": score, "team": mfl_team(year, franchise_id, franchises.get(franchise_id, {}).get("name", "")), "personId": mfl_to_person.get((year, franchise_id)), "year": year, "week": week, "platform": "MFL"})
            seen_scores.add((week, franchise_id))
        conference = mfl_conference(year, franchises[left_id])
        if conference != mfl_conference(year, franchises[right_id]):
            conference = "Interconference"
        note_regular(left_id, right_id, left_score, right_score)
        add_h2h(mfl_to_person.get((year, left_id)), mfl_to_person.get((year, right_id)), left_score, right_score,
                meta={"year": year, "week": week, "platform": "MFL", "conference": conference})
        blowouts.append({"winner": left_id if left_score >= right_score else right_id, "loser": right_id if left_score >= right_score else left_id, "winnerScore": max(left_score, right_score), "loserScore": min(left_score, right_score), "year": year, "week": week, "platform": "MFL"})
    for week_data in listify(source["schedule"]["schedule"].get("weeklySchedule")):
        week = integer(week_data.get("week"))
        if week > last_regular:
            continue
        for matchup in listify(week_data.get("matchup")):
            sides = listify(matchup.get("franchise"))
            if len(sides) != 2:
                continue
            left, right = sides
            left_id, right_id = str(left.get("id", "")).zfill(4), str(right.get("id", "")).zfill(4)
            left_score, right_score = number(left.get("score")), number(right.get("score"))
            for franchise_id, score in ((left_id, left_score), (right_id, right_score)):
                seen_scores.add((week, franchise_id))
                weekly_scores.append({"score": score, "team": mfl_team(year, franchise_id, franchises.get(franchise_id, {}).get("name", "")), "personId": mfl_to_person.get((year, franchise_id)), "year": year, "week": week, "platform": "MFL"})
            conference = mfl_conference(year, franchises[left_id])
            note_regular(left_id, right_id, left_score, right_score)
            add_h2h(
                mfl_to_person.get((year, left_id)),
                mfl_to_person.get((year, right_id)),
                left_score,
                right_score,
                meta={"year": year, "week": week, "platform": "MFL", "conference": conference},
            )
            blowouts.append({"winner": left_id if left_score >= right_score else right_id, "loser": right_id if left_score >= right_score else left_id, "winnerScore": max(left_score, right_score), "loserScore": min(left_score, right_score), "year": year, "week": week, "platform": "MFL"})

    # 2019's regular-season schedule export is empty, but weekly lineups retain scores.
    results = source.get("weeklyResults", {}).get("allWeeklyResults", {}).get("weeklyResults", [])
    for week_data in listify(results):
        week = integer(week_data.get("week"))
        if week > last_regular:
            continue
        franchises_data = listify(week_data.get("franchise"))
        if not franchises_data:
            for matchup in listify(week_data.get("matchup")):
                franchises_data.extend(listify(matchup.get("franchise")))
        for franchise in franchises_data:
            franchise_id = str(franchise.get("id", "")).zfill(4)
            if not franchise_id or (week, franchise_id) in seen_scores:
                continue
            weekly_scores.append({"score": number(franchise.get("score")), "team": mfl_team(year, franchise_id, franchises.get(franchise_id, {}).get("name", "")), "personId": mfl_to_person.get((year, franchise_id)), "year": year, "week": week, "platform": "MFL"})

    # MFL's standings "pf"/"pa" include every week played (playoffs and consolation): keep regular season only.
    for franchise_id, rec in reg_points.items():
        row = mfl_season_lookup.get((year, franchise_id))
        if row and rec["games"] and franchise_id not in regular_fix:
            row["pf"], row["pa"] = compact_number(rec["pf"]), compact_number(rec["pa"])
    for conference in season_groups:
        season_groups[conference].sort(key=lambda row: (-row["wins"], -row["pf"]))
        for rank, row in enumerate(season_groups[conference], 1):
            row["conferenceRank"] = rank
            add_person_season(
                row["personId"],
                {
                    "year": year,
                    "era": "MFL",
                    "platform": "MFL",
                    "conference": row["conference"],
                    "team": row["team"],
                    "logo": row["logo"],
                    "wins": row["wins"],
                    "losses": row["losses"],
                    "ties": row["ties"],
                    "pf": row["pf"],
                    "pa": row["pa"],
                    "playoff": row["playoff"],
                    "finish": row["finish"],
                    "champion": row["champion"],
                    "leagueChampion": row["leagueChampion"],
                    "conferenceChampion": row["conferenceChampion"],
                },
            )
    mfl_seasons[year] = season_groups


sleeper_seasons = {}
sleeper_season_rows = {}
regular_aggregate = defaultdict(lambda: {"wins": 0, "losses": 0, "ties": 0, "pf": 0.0, "pa": 0.0})
for game in sleeper_history.get("games", []):
    year = str(game["season"])
    conference = game.get("conf", "")
    user_a, user_b = str(game["u1"]), str(game["u2"])
    score_a, score_b = number(game["p1"]), number(game["p2"])
    for user_id, scored, allowed in ((user_a, score_a, score_b), (user_b, score_b, score_a)):
        agg = regular_aggregate[(year, conference, user_id)]
        agg["pf"] += scored
        agg["pa"] += allowed
        if scored > allowed:
            agg["wins"] += 1
        elif scored < allowed:
            agg["losses"] += 1
        else:
            agg["ties"] += 1
    person_a, person_b = user_to_person.get(user_a), user_to_person.get(user_b)
    add_h2h(person_a, person_b, score_a, score_b, meta={"year": year, "week": integer(game["week"]), "platform": "Sleeper", "conference": game.get("conf", "")})
    meta_a = sleeper_identities.get(user_a, {}).get(year, {})
    meta_b = sleeper_identities.get(user_b, {}).get(year, {})
    weekly_scores.extend(
        [
            {"score": score_a, "team": meta_a.get("team") or sleeper_history.get("latest_name", {}).get(user_a, ""), "personId": person_a, "year": year, "week": integer(game["week"]), "platform": "Sleeper"},
            {"score": score_b, "team": meta_b.get("team") or sleeper_history.get("latest_name", {}).get(user_b, ""), "personId": person_b, "year": year, "week": integer(game["week"]), "platform": "Sleeper"},
        ]
    )
    winner_user, loser_user = (user_a, user_b) if score_a >= score_b else (user_b, user_a)
    blowouts.append({"winner": winner_user, "loser": loser_user, "winnerScore": max(score_a, score_b), "loserScore": min(score_a, score_b), "year": year, "week": integer(game["week"]), "platform": "Sleeper"})


playoff_by_year_user = defaultdict(list)
for game in sleeper_history.get("playoffs", []):
    year = str(game["season"])
    conference = game.get("conf", "")
    winner, loser = str(game["winner"]), str(game["loser"])
    playoff_by_year_user[(year, conference, winner)].append(("win", game))
    playoff_by_year_user[(year, conference, loser)].append(("loss", game))
    add_h2h(
        user_to_person.get(winner),
        user_to_person.get(loser),
        game.get("wpts") or 1,
        game.get("lpts") or 0,
        playoff=True,
        meta={"year": year, "week": game.get("week"), "platform": "Sleeper", "round": "Conference final" if game.get("place") == 1 else f"Playoff round {game.get('round')}", "conference": game.get("conf", "")},
    )


def sleeper_finish(year, conference, user_id):
    events = playoff_by_year_user.get((year, conference, user_id), [])
    if year == CURRENT_YEAR and not sleeper_history.get("champions", {}).get(f"{conference}_{year}"):
        return False, "Season live", False
    if not events:
        return False, "—", False
    for result, game in events:
        if game.get("place") == 1:
            return True, "Conference champion" if result == "win" else "Conference runner-up", result == "win"
    for result, game in events:
        if game.get("place") == 3:
            return True, "Third place" if result == "win" else "Fourth place", False
        if game.get("place") == 5:
            return True, "Fifth place" if result == "win" else "Sixth place", False
    lost_round = max((integer(game.get("round")) for result, game in events if result == "loss"), default=0)
    return True, ("Semifinal" if lost_round >= 2 else "First round"), False


historical_sleeper_years = sorted({str(game["season"]) for game in sleeper_history.get("games", [])})
for year in historical_sleeper_years:
    groups = {"AFC": [], "NFC": []}
    season_memberships = sorted(
        (conference, user_id)
        for aggregate_year, conference, user_id in regular_aggregate
        if aggregate_year == year
    )
    for conference, user_id in season_memberships:
        meta = sleeper_identities.get(user_id, {}).get(year, {})
        agg = regular_aggregate.get((year, conference, user_id), {"wins": 0, "losses": 0, "ties": 0, "pf": 0.0, "pa": 0.0})
        playoff, finish, conference_champion = sleeper_finish(year, conference, user_id)
        person_id = user_to_person.get(user_id)
        row = {
            "personId": person_id,
            "userId": user_id,
            "conference": conference,
            "team": meta.get("team") or meta.get("handle") or sleeper_history.get("latest_name", {}).get(user_id, "—"),
            "handle": meta.get("handle") or sleeper_history.get("latest_name", {}).get(user_id, ""),
            "avatar": meta.get("avatar", ""),
            "wins": agg["wins"],
            "losses": agg["losses"],
            "ties": agg["ties"],
            "pf": compact_number(agg["pf"]),
            "pa": compact_number(agg["pa"]),
            "playoff": playoff,
            "finish": finish,
            "champion": conference_champion,
            "leagueChampion": False,
            "conferenceChampion": conference_champion,
        }
        if conference in groups:
            groups[conference].append(row)
        sleeper_season_rows[(year, conference, user_id)] = row
        add_person_season(
            person_id,
            {
                "year": year,
                "era": "Sleeper",
                "platform": "Sleeper",
                "conference": row["conference"],
                "team": row["team"],
                "logo": row["avatar"],
                "wins": row["wins"],
                "losses": row["losses"],
                "ties": row["ties"],
                "pf": row["pf"],
                "pa": row["pa"],
                "playoff": row["playoff"],
                "finish": row["finish"],
                "champion": row["champion"],
                "leagueChampion": False,
                "conferenceChampion": row["conferenceChampion"],
            },
        )
    for conference in groups:
        groups[conference].sort(key=lambda row: (-row["wins"], -row["pf"]))
        for rank, row in enumerate(groups[conference], 1):
            row["rank"] = rank
    sleeper_seasons[year] = groups


# Early era: identities provide participation and team lineage; surviving records are partial.
early_seasons = {"2014": [], "2015": [], "2016": []}
early_conference = {}
recon = FALLBACK_RECON
for conference, key in (("AFC", "playoffsAFC"), ("NFC", "playoffsNFC")):
    for text in recon.get("y2015", {}).get(key, []):
        team = re.sub(r"\s+—.*$", "", text).strip()
        match = re.search(r"\((.*?)\)", team)
        team_name = match.group(1) if match else team
        person_id = find_person_by_pre_team("2015", team_name)
        if person_id:
            early_conference[("2015", person_id)] = conference
for conference, key in (("AFC", "afcWk11"), ("NFC", "nfcWk11")):
    for team, _ in recon.get("y2016", {}).get(key, []):
        person_id = find_person_by_pre_team("2016", team.split(" (")[0])
        if person_id:
            early_conference[("2016", person_id)] = conference

early_finish = {
    ("2014", "mark-tovar"): ("Champion", True, True, True),
    ("2015", "norm-behrens"): ("Champion", True, True, True),
    ("2015", "daniel-polverari"): ("Runner-up", False, True, True),
    ("2016", "sam-hardy"): ("Champion", True, True, True),
    ("2016", "andrew-tovar"): ("Runner-up", False, True, True),
    ("2016", "jordan-grado"): ("Conference finalist", False, False, True),
    ("2016", "ryan-walker"): ("Conference finalist", False, False, True),
    ("2016", "mark-tovar"): ("Semifinal", False, False, True),
    ("2016", "brandon-walker"): ("Semifinal", False, False, True),
    ("2016", "josh-jurado"): ("Semifinal", False, False, True),
    ("2016", "danny-jurado"): ("Semifinal", False, False, True),
}

early_records = {}
for key in ("afcWk11", "nfcWk11"):
    for team_text, record in recon.get("y2016", {}).get(key, []):
        team = team_text.split(" (")[0]
        person_id = find_person_by_pre_team("2016", team)
        if person_id:
            parts = record.split("-")
            early_records[("2016", person_id)] = (integer(parts[0]), integer(parts[1]))

for person_id, raw in identities.items():
    for year, team in raw.get("pre", {}).items():
        year = str(year)
        record = early_records.get((year, person_id), (None, None))
        partial = year == "2016" and record[0] is not None  # 2016 standings come from the Week 11 recap (through Week 10)
        finish, champion, conference_champion, playoff = early_finish.get((year, person_id), ("—", False, False, False))
        season = {
            "year": year,
            "era": "Early",
            "platform": "RT Sports" if year == "2015" else "ESPN",
            "conference": early_conference.get((year, person_id), ""),
            "team": team,
            "logo": "",
            "wins": record[0],
            "losses": record[1],
            "ties": None,
            "pf": None,
            "pa": None,
            "playoff": playoff,
            "finish": finish,
            "champion": champion,
            "leagueChampion": champion and finish == "Champion",
            "conferenceChampion": conference_champion, "partial": partial, "note": ("Through Week 10" if partial else ""),
        }
        add_person_season(person_id, season)
        early_seasons.setdefault(year, []).append({**season, "personId": person_id})

if not any(season["year"] == "2014" for season in people["mark-tovar"]["seasons"]):
    season = {
        "year": "2014", "era": "Early", "platform": "ESPN", "conference": "", "team": "—", "logo": "",
        "wins": None, "losses": None, "ties": None, "pf": None, "pa": None, "playoff": True, "finish": "Champion",
        "champion": True, "leagueChampion": True, "conferenceChampion": False,
    }
    add_person_season("mark-tovar", season)
    early_seasons["2014"].append({**season, "personId": "mark-tovar"})


# Add the current season without pretending that a preseason record is final.
_raw_2026 = json.loads((HISTORY / "history_raw.json").read_text(encoding="utf-8"))
ROSTER_OWNERS_2026 = {str(r["owner_id"]) for key in (f"AFC_{CURRENT_YEAR}", f"NFC_{CURRENT_YEAR}") for r in (_raw_2026.get(key) or {}).get("rosters", [])}
for user_id, seasons in sleeper_identities.items():
    meta = seasons.get(CURRENT_YEAR)
    person_id = user_to_person.get(user_id)
    if not meta or not person_id:
        continue
    if str(user_id) not in ROSTER_OWNERS_2026:
        continue  # commissioners / co-owners without a roster are not current owners
    if any(sn.get("year") == CURRENT_YEAR for sn in people.get(person_id, {}).get("seasons", [])):
        continue  # games have been played: the real row already exists
    current = {
        "year": CURRENT_YEAR,
        "era": "Sleeper",
        "platform": "Sleeper",
        "conference": meta.get("conf", ""),
        "team": meta.get("team") or meta.get("handle") or "—",
        "logo": meta.get("avatar", ""),
        "wins": None,
        "losses": None,
        "ties": None,
        "pf": None,
        "pa": None,
        "playoff": False,
        "finish": "Season live",
        "champion": False,
        "leagueChampion": False,
        "conferenceChampion": False,
    }
    add_person_season(person_id, current)


# The current power index carries the authoritative 2026 team/conference assignment.
for row in power_rankings.get("rows", []):
    if len(row) < 5:
        continue
    _, conference, team, manager, _ = row[:5]
    person_id = handle_to_person.get(str(manager).casefold())
    if not person_id:
        continue
    current = next((season for season in people[person_id]["seasons"] if season["year"] == CURRENT_YEAR), None)
    if not current:
        current = {
            "year": CURRENT_YEAR, "era": "Sleeper", "platform": "Sleeper", "conference": conference, "team": team,
            "logo": "", "wins": None, "losses": None, "ties": None, "pf": None, "pa": None, "playoff": False,
            "finish": "Season live", "champion": False, "leagueChampion": False, "conferenceChampion": False,
        }
        add_person_season(person_id, current)
    current["conference"], current["team"] = conference, team


# Champion ledger: a structured shape makes every known winner linkable.
def entry(person_id, team, conference=""):
    if not person_id:
        return {"personId": None, "name": "", "team": team, "conference": conference}
    return {"personId": person_id, "name": people[person_id]["name"], "team": team, "conference": conference}


champions = [
    {"year": 2014, "type": "league", "winners": [entry("mark-tovar", "")], "runner": None, "score": "", "note": "The founding season."},
    {"year": 2015, "type": "league", "winners": [entry("norm-behrens", "Violating PeaCocks", "NFC")], "runner": entry("daniel-polverari", "License to Hill", "AFC"), "score": "", "note": "The first two-conference season."},
    {"year": 2016, "type": "league", "winners": [entry("sam-hardy", "Suck Brady’s Bell", "AFC")], "runner": entry("andrew-tovar", "Make America Gronk Again", "NFC"), "score": "119.5–73.3", "note": "Hardy upset the 10–0 top seed on the way to the title."},
    {"year": 2017, "type": "league", "winners": [entry(mfl_to_person.get(("2017", "0018")), "Joey Vogl", "NFC")], "runner": entry(mfl_to_person.get(("2017", "0010")), "Bells On Your Chin", "AFC"), "score": "123.24–112.52", "note": "First MyFantasyLeague season."},
    {"year": 2018, "type": "league", "winners": [entry(mfl_to_person.get(("2018", "0004")), "LA Rams Fan: 2017–Present", "AFC")], "runner": entry(mfl_to_person.get(("2018", "0020")), "Kratzy’s Kitties", "NFC"), "score": "120.66–117.26", "note": "The closest title game on record."},
    {"year": 2019, "type": "league", "winners": [entry(mfl_to_person.get(("2019", "0007")), "Cortney")], "runner": entry(mfl_to_person.get(("2019", "0018")), "Joey"), "score": "149.76–128.26", "note": "The combined 12-team playoff bracket begins."},
    {"year": 2020, "type": "league", "winners": [entry(mfl_to_person.get(("2020", "0006")), "GridIron Throne")], "runner": entry(mfl_to_person.get(("2020", "0015")), "Sugar Belle (Daniel Q)"), "score": "116.48–113.48", "note": "A three-point championship."},
    {"year": 2021, "type": "league", "winners": [entry(mfl_to_person.get(("2021", "0010")), "Pickle Ricks")], "runner": entry(mfl_to_person.get(("2021", "0019")), "Kody Hutchins"), "score": "187.53–128.60", "note": "The highest championship score on record."},
]
for year in range(2022, 2026):
    conf_winner = {}
    for conference in ("AFC", "NFC"):
        result = sleeper_history.get("champions", {}).get(f"{conference}_{year}")
        if not result:
            continue
        user_id = str(result["winner"])
        meta = sleeper_identities.get(user_id, {}).get(str(year), {})
        conf_winner[conference] = entry(user_to_person.get(user_id), meta.get("team") or meta.get("handle") or "—", conference)
    sb = CHAMPIONS_FILE.get("super_bowls", {}).get(str(year))
    if sb and conf_winner:
        champ = next((w for w in conf_winner.values() if w["personId"] == sb["champ_id"]), None)
        runner = next((w for w in conf_winner.values() if w["personId"] != sb["champ_id"]), None)
        if champ:
            champions.append({"year": year, "type": "league", "winners": [champ], "runner": runner, "score": "", "note": f"Super Bowl: {champ['conference']} over {runner['conference'] if runner else '—'}."})
            continue
    champions.append({"year": year, "type": "conference", "winners": list(conf_winner.values()), "runner": None, "score": "", "note": "AFC and NFC conference crowns."})

# Mark Super Bowl champions in Sleeper season rows
for year_key, conferences in sleeper_seasons.items():
    sb = CHAMPIONS_FILE.get("super_bowls", {}).get(str(year_key))
    if not sb:
        continue
    for rows in conferences.values():
        for row in rows:
            if row.get("personId") == sb["champ_id"]:
                row.update({"leagueChampion": True, "champion": True, "finish": "Champion"})
            elif row.get("personId") == sb.get("runner_id") and row.get("conferenceChampion"):
                row.update({"finish": "Runner-up"})
    # The owner records hold their own copies of these rows: mark them the same way.
    for person_id, person in people.items():
        for season in person["seasons"]:
            if season.get("year") != str(year_key) or season.get("platform") != "Sleeper":
                continue
            if person_id == sb["champ_id"]:
                season.update({"leagueChampion": True, "champion": True, "finish": "Champion"})
            elif person_id == sb.get("runner_id") and season.get("conferenceChampion"):
                season.update({"finish": "Runner-up"})

for person_id, person in people.items():
    person["seasons"].sort(key=lambda season: int(season["year"]), reverse=True)
    current = next((season for season in person["seasons"] if season["year"] == CURRENT_YEAR), None)
    if not current and person["seasons"]:
        current = person["seasons"][0]
    if current:
        person["current"] = {
            "team": current["team"],
            "conference": current["conference"],
            "avatar": current["logo"],
            "year": current["year"],
        }
    if not person["name"]:
        person["name"] = (current or {}).get("team") or person["handle"] or "—"

    # Mark's ruling (2026-09-02): verified partial seasons (2016 = through Week 10) COUNT toward career totals; they stay labeled.
    completed = [season for season in person["seasons"] if season.get("wins") is not None and season.get("losses") is not None]
    wins = sum(integer(season["wins"]) for season in completed)
    losses = sum(integer(season["losses"]) for season in completed)
    ties = sum(integer(season.get("ties")) for season in completed)
    pf = sum(number(season.get("pf")) for season in completed if season.get("pf") is not None)
    pa_values = [number(season.get("pa")) for season in completed if season.get("pa") is not None]
    titles = sum(bool(season.get("leagueChampion")) for season in person["seasons"])
    conference_titles = sum(bool(season.get("conferenceChampion")) for season in person["seasons"])
    playoff_appearances = sum(bool(season.get("playoff")) for season in person["seasons"])
    best = None
    if completed:
        best = max(
            completed,
            key=lambda season: (
                integer(season["wins"]) / max(1, integer(season["wins"]) + integer(season["losses"]) + integer(season.get("ties"))),
                number(season.get("pf")),
            ),
        )
    for season in person["seasons"]:
        po = playoff_record.get((person_id, str(season["year"])))
        if po:
            season["playoffWins"], season["playoffLosses"] = po["wins"], po["losses"]
            season["playoffPf"], season["playoffPa"] = (round(po["pf"], 1), round(po["pa"], 1)) if po["pf"] > 1 else (None, None)
    po = playoff_record.get(person_id, {"wins": 0, "losses": 0, "pf": 0.0, "pa": 0.0, "games": 0})
    po_pf = round(po["pf"], 1) if po["pf"] > 1 else None  # early Sleeper rows carried only win/loss
    po_pa = round(po["pa"], 1) if po["pf"] > 1 else None
    total_pa = round(sum(pa_values), 1) if pa_values else None
    person["summary"] = {
        "regular": {"wins": wins, "losses": losses, "ties": ties, "pf": round(pf, 1), "pa": total_pa},
        "playoffs": {"wins": po["wins"], "losses": po["losses"], "pf": po_pf, "pa": po_pa},
        "overall": {"wins": wins + po["wins"], "losses": losses + po["losses"], "ties": ties,
                    "pf": round(pf + (po_pf or 0), 1), "pa": (round(total_pa + (po_pa or 0), 1) if total_pa is not None else None)},
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "winPct": round(wins / max(1, wins + losses + ties), 3),
        "pf": round(pf, 1),
        "pa": round(sum(pa_values), 1) if pa_values else None,
        "titles": titles,
        "conferenceTitles": conference_titles,
        "playoffAppearances": playoff_appearances,
        "bestSeason": ({"year": best["year"], "record": f"{best['wins']}–{best['losses']}", "team": best["team"]} if best else None),
    }

    for opponent_id in people:
        if opponent_id == person_id:
            continue
        stats = dict(h2h[(person_id, opponent_id)])
        stats["pf"] = round(stats["pf"], 1)
        stats["pa"] = round(stats["pa"], 1)
        person["h2h"][opponent_id] = stats


def display_for_identifier(identifier, year, platform):
    if platform == "Sleeper":
        meta = sleeper_identities.get(str(identifier), {}).get(str(year), {})
        person_id = user_to_person.get(str(identifier))
        return meta.get("team") or meta.get("handle") or str(identifier), person_id
    franchise_id = str(identifier).zfill(4)
    row = mfl_season_lookup.get((str(year), franchise_id), {})
    return row.get("team") or franchise_id, row.get("personId")


unique_scores = {}
for mark in weekly_scores:
    key = (mark["year"], mark["week"], mark["platform"], mark["team"])
    unique_scores[key] = mark
weekly_scores = list(unique_scores.values())
top_marks = sorted(weekly_scores, key=lambda item: item["score"], reverse=True)[:10]
low_marks = sorted((item for item in weekly_scores if item["score"] > 0), key=lambda item: item["score"])[:10]
blowout_marks = []
for game in sorted(blowouts, key=lambda item: item["winnerScore"] - item["loserScore"], reverse=True)[:10]:
    winner, winner_person = display_for_identifier(game["winner"], game["year"], game["platform"])
    loser, loser_person = display_for_identifier(game["loser"], game["year"], game["platform"])
    blowout_marks.append({**game, "winner": winner, "winnerPersonId": winner_person, "loser": loser, "loserPersonId": loser_person, "margin": round(game["winnerScore"] - game["loserScore"], 1)})


current_people = {"AFC": [], "NFC": []}
for row in power_rankings.get("rows", []):
    if len(row) < 5:
        continue
    person_id = handle_to_person.get(str(row[3]).casefold())
    if person_id and row[1] in current_people and person_id not in current_people[row[1]]:
        current_people[row[1]].append(person_id)


bundle = {
    "built": date.today().isoformat(),
    "currentSeason": integer(CURRENT_YEAR),
    "leagueIds": {"AFC": "1309769596663795712", "NFC": "1309769564652855296"},
    "eras": existing.get("eras", DEFAULT_ERAS),
    "founding": FOUNDERS,
    "recon": recon,
    "records": records,
    "powerRankings": power_rankings,
    "seasonYears": sorted(
        [json.loads(f.read_text(encoding="utf-8"))["year"] for f in (ROOT / "site" / "seasons").glob("*.json")
         if json.loads(f.read_text(encoding="utf-8")).get("weeks")],
        reverse=True,
    ),
    "champions": champions,
    "currentChampion": CHAMPIONS_FILE.get("current_champion"),
    "people": people,
    "handleToPerson": handle_to_person,
    "userToPerson": user_to_person,
    "currentPeople": current_people,
    "sleeperSeasons": sleeper_seasons,
    "mflSeasons": mfl_seasons,
    "earlySeasons": early_seasons,
    "rivalry": {
        "games": sorted(rivalry_games, key=lambda game: (game["year"], game["week"] or 0), reverse=True),
        "playoffs": sorted(rivalry_playoffs, key=lambda game: (game["year"], game.get("week") or 99), reverse=True),
    },
    "marks": {"top": top_marks, "low": low_marks, "blowouts": blowout_marks},
}

output = "window.LEAGUE_DATA=" + json.dumps(bundle, ensure_ascii=False, separators=(",", ":")) + ";\n"
(SITE / "data.js").write_text(output, encoding="utf-8")
print(f"wrote site/data.js ({len(people)} people, {sum(len(v['seasons']) for v in people.values())} person-seasons)")
