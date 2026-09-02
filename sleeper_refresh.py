#!/usr/bin/env python3
"""Refresh the current Sleeper season from the public API so every downstream build is automatic.

Writes/updates (all under data/history/):
  history_raw.json            <CONF>_<year> -> {league_id, settings, users, rosters, matchups{week:[...]}, winners_bracket, losers_bracket}
  transactions/sleeper_<year>_<CONF>.json
  sleeper_drafts/<year>_<CONF>_picks.json
  sleeper_identities.json     user_id -> {year: {conf, team, avatar, handle}}
  sleeper_players.json        full player DB (refreshed when older than PLAYERS_MAX_AGE_DAYS)
  history_processed.json      games / playoffs / champions / latest_name / current / pair / records (all Sleeper seasons)
  champions.json              Super Bowl auto-detected once both conference finals are decided (source: auto)
Run: python3 sleeper_refresh.py            (safe to run any time; idempotent)
"""
import json, sys, time, urllib.request
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent
HIST = ROOT / "data" / "history"
API = "https://api.sleeper.app/v1"
PLAYERS_MAX_AGE_DAYS = 6

# Current-season leagues (both conferences). Past seasons are already stored and are never re-fetched.
LEAGUES = {"AFC": "1309769596663795712", "NFC": "1309769564652855296"}

def get(path, default=None, tries=3):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(f"{API}{path}", headers={"User-Agent": "theleague2k-site"}), timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa
            if i == tries - 1:
                print(f"  ! {path}: {e}", file=sys.stderr)
                return default
            time.sleep(2 * (i + 1))

def jload(p, default):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default

def jdump(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")

state = get("/state/nfl", {}) or {}
season = str(state.get("season") or state.get("league_season") or time.strftime("%Y"))
current_week = int(state.get("week") or 1)
print(f"NFL state: season {season}, week {current_week}, {state.get('season_type')}")

raw = jload(HIST / "history_raw.json", {})
identities = jload(HIST / "sleeper_identities.json", {})
OVERRIDES = {k: v for k, v in jload(HIST / "roster_owner_overrides.json", {}).items() if not k.startswith("_")}
def owner_map(key, rec):
    """roster_id -> managing user_id, honoring commissioner-login overrides."""
    ov = OVERRIDES.get(key, {})
    return {r["roster_id"]: str(ov.get(str(r["roster_id"])) or r.get("owner_id")) for r in rec.get("rosters", [])}

for conf, lid in LEAGUES.items():
    league = get(f"/league/{lid}")
    if not league:
        print(f"{conf}: league fetch failed, keeping stored data"); continue
    yr = str(league.get("season") or season)
    settings = league.get("settings") or {}
    playoff_start = int(settings.get("playoff_week_start") or 14)
    users = get(f"/league/{lid}/users", []) or []
    rosters = get(f"/league/{lid}/rosters", []) or []
    key = f"{conf}_{yr}"
    rec = raw.get(key) or {}
    rec.update(league_id=lid, settings=settings, status=league.get("status"), users=users, rosters=rosters,
               playoff_week_start=playoff_start, draft_id=league.get("draft_id"))
    # Matchups for every week that could have been played (last_scored_leg or current week). Weeks with no points are kept out.
    last_leg = int(settings.get("last_scored_leg") or 0) or current_week
    matchups = {}
    for wk in range(1, min(max(last_leg, current_week), 18) + 1):
        ms = get(f"/league/{lid}/matchups/{wk}", []) or []
        if any(float(m.get("points") or 0) > 0 for m in ms):
            matchups[str(wk)] = ms
    rec["matchups"] = matchups
    rec["winners_bracket"] = get(f"/league/{lid}/winners_bracket", []) or []
    rec["losers_bracket"] = get(f"/league/{lid}/losers_bracket", []) or []
    raw[key] = rec
    # Transactions per week
    tx = []
    for wk in range(1, min(max(last_leg, current_week), 18) + 1):
        for t in (get(f"/league/{lid}/transactions/{wk}", []) or []):
            t["_week"] = wk; tx.append(t)
    if tx or not (HIST / "transactions" / f"sleeper_{yr}_{conf}.json").exists():
        jdump(HIST / "transactions" / f"sleeper_{yr}_{conf}.json", tx)
    # Draft picks (auction)
    if league.get("draft_id"):
        picks = get(f"/draft/{league['draft_id']}/picks", []) or []
        if picks:
            jdump(HIST / "sleeper_drafts" / f"{yr}_{conf}_picks.json", picks)
    print(f"{conf} {yr}: {len(users)} users, {len(matchups)} scored weeks, {len(tx)} transactions, bracket games {len(rec['winners_bracket'])}")

jdump(HIST / "history_raw.json", raw)

# Identities for every stored season: a user who is in both leagues (the commissioner) is credited to the league where
# they actually hold a roster; a manager who ran a roster registered under the commissioner login (override) gets that roster.
for key, rec in raw.items():
    conf, yr = key.split("_")
    omap = owner_map(key, rec)
    holders = set(omap.values())
    users = {str(u["user_id"]): u for u in rec.get("users", [])}
    for uid, u in users.items():
        md = u.get("metadata") or {}
        has_roster = uid in holders
        existing = identities.get(uid, {}).get(yr)
        if existing and existing.get("_roster") and not has_roster:
            continue  # keep the league where they manage a team
        identities.setdefault(uid, {})[yr] = dict(
            conf=conf, team=(md.get("team_name") or u.get("display_name") or "").strip(),
            avatar=md.get("avatar") or (f"https://sleepercdn.com/avatars/thumbs/{u['avatar']}" if u.get("avatar") else ""),
            handle=u.get("display_name", ""), _roster=has_roster)
    for rid, uid in omap.items():
        if uid not in users and uid in identities:  # override manager not a member of this league's user list: still credit the season
            base = next(iter(identities[uid].values()))
            identities[uid][yr] = dict(conf=conf, team=base.get("handle", ""), avatar=base.get("avatar", ""), handle=base.get("handle", ""), _roster=True)
for uid in identities:
    for yr in identities[uid]:
        identities[uid][yr].pop("_roster", None)
jdump(HIST / "sleeper_identities.json", identities)

# Player DB (14MB) refreshed weekly
pf = HIST / "sleeper_players.json"
if not pf.exists() or (time.time() - pf.stat().st_mtime) > PLAYERS_MAX_AGE_DAYS * 86400:
    players = get("/players/nfl")
    if players:
        jdump(pf, players); print("players db refreshed:", len(players))

# ---------------- history_processed.json (every Sleeper season) ----------------
games, playoffs, champions = [], [], {}
latest_name, current = {}, {}
pair = defaultdict(lambda: [0, 0, []])
records = defaultdict(lambda: defaultdict(lambda: [0, 0, 0.0]))
years = sorted({k.split("_")[1] for k in raw})
for key, rec in sorted(raw.items(), key=lambda kv: kv[0].split("_")[1]):
    conf, yr = key.split("_")
    playoff_start = int(rec.get("playoff_week_start") or ((rec.get("settings") or {}).get("playoff_week_start")) or 14)
    owner_of = owner_map(key, rec)
    for u in rec.get("users", []):
        latest_name[str(u["user_id"])] = u.get("display_name", "")
    if yr == years[-1]:
        current[conf] = [owner_of[r["roster_id"]] for r in rec.get("rosters", [])]
    for wk, ms in sorted((rec.get("matchups") or {}).items(), key=lambda kv: int(kv[0])):
        wk = int(wk)
        if wk >= playoff_start:
            continue
        by = defaultdict(list)
        for m in ms:
            if m.get("matchup_id") is not None:
                by[m["matchup_id"]].append(m)
        for pr in by.values():
            if len(pr) != 2:
                continue
            a, b = pr
            pa, pb = float(a.get("points") or 0), float(b.get("points") or 0)
            if pa == 0 and pb == 0:
                continue
            u1, u2 = owner_of.get(a["roster_id"]), owner_of.get(b["roster_id"])
            games.append(dict(conf=conf, season=yr, week=wk, u1=u1, p1=pa, u2=u2, p2=pb))
            for me, opp, mine, theirs in ((u1, u2, pa, pb), (u2, u1, pb, pa)):
                r = records[conf][me]
                r[0] += mine > theirs; r[1] += mine < theirs; r[2] += mine
            lo, hi = sorted([u1, u2])
            pk = pair[f"{conf}|{lo}|{hi}"]
            if pa != pb:
                w = u1 if pa > pb else u2
                pk[0 if w == lo else 1] += 1
            pk[2].append(round(abs(pa - pb), 2))
    for g in rec.get("winners_bracket") or []:
        if g.get("w") and g.get("l"):
            playoffs.append(dict(conf=conf, season=yr, round=g.get("r"), place=g.get("p"), winner=owner_of.get(g["w"]), loser=owner_of.get(g["l"])))
            if g.get("p") == 1:
                champions[key] = dict(winner=owner_of.get(g["w"]), loser=owner_of.get(g["l"]))
processed = dict(latest_name=latest_name, current=current, pair=dict(pair), records={c: dict(v) for c, v in records.items()},
                 games=games, playoffs=playoffs, champions=champions)
jdump(HIST / "history_processed.json", processed)
print(f"processed: {len(games)} regular-season games, {len(playoffs)} playoff games, champions {sorted(champions)}")

# ---------------- Super Bowl auto-detect for the current season ----------------
# The two conference champions are compared on the week after the conference finals (bracket final round + 1).
ch = jload(HIST / "champions.json", {"super_bowls": {}, "champions_by_year": {}, "current_champion": None})
people = jload(HIST / "identities.json", {"people": {}})["people"]
handle_to_person = {(p.get("sleeper") or "").lower(): pid for pid, p in people.items() if p.get("sleeper")}
yr = years[-1] if years else season
if f"AFC_{yr}" in champions and f"NFC_{yr}" in champions and yr not in ch["super_bowls"]:
    finals_round = max(int(g.get("r") or 0) for k in (f"AFC_{yr}", f"NFC_{yr}") for g in raw[k].get("winners_bracket", []))
    sb_week = int(raw[f"AFC_{yr}"].get("playoff_week_start") or 14) + finals_round
    pts = {}
    for conf in ("AFC", "NFC"):
        rec = raw[f"{conf}_{yr}"]
        owner_of = owner_map(f"{conf}_{yr}", rec)
        champ_uid = champions[f"{conf}_{yr}"]["winner"]
        for m in (rec.get("matchups") or {}).get(str(sb_week), []):
            if owner_of.get(m["roster_id"]) == champ_uid and float(m.get("points") or 0) > 0:
                pts[conf] = (float(m["points"]), champ_uid)
    if len(pts) == 2 and pts["AFC"][0] != pts["NFC"][0]:
        win_conf = "AFC" if pts["AFC"][0] > pts["NFC"][0] else "NFC"
        lose_conf = "NFC" if win_conf == "AFC" else "AFC"
        def person(uid):
            pid = handle_to_person.get((latest_name.get(uid) or "").lower())
            return pid, (people.get(pid, {}).get("name") or latest_name.get(uid) or uid)
        wp, wn = person(pts[win_conf][1]); lp, ln = person(pts[lose_conf][1])
        ch["super_bowls"][yr] = dict(champ=wn, champ_id=wp, runner=ln, runner_id=lp, week=sb_week,
                                     score={win_conf: pts[win_conf][0], lose_conf: pts[lose_conf][0]}, source="auto")
        ch["champions_by_year"][yr] = wp
        ch["current_champion"] = wp
        jdump(HIST / "champions.json", ch)
        print(f"SUPER BOWL {yr}: {wn} ({win_conf}) over {ln} — week {sb_week} {pts[win_conf][0]}–{pts[lose_conf][0]}")
print("refresh complete")
