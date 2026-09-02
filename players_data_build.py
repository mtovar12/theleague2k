#!/usr/bin/env python3
"""League-wide NFL Player Hall of Fame data: site/players/index.json
From site/seasons/<year>.json lineups (2017-2025) + data/history/transactions/*.
Per player (keyed by Sleeper id when known, else name|pos):
  name, pos, sid, photo, owners (distinct), ownerIds, weeks (roster appearances), starts, pts (starter points),
  winShare (sum over starter weeks in wins of pts / team total), winsContributed (starter appearances in winning lineups),
  playoffWeeks (roster appearances in playoff weeks: week >= 14), best {pts, year, week, ownerId}, seasons (distinct years),
  tx {adds, drops, waivers, trades, total}
Top lists: mostOwners, mostTransactions, winShares, playoffRosters, points, mostWeeks.
Run: python3 players_data_build.py
"""
import json, os, re, unicodedata, glob
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent
HIST = ROOT / "data" / "history"
SEASONS = ROOT / "site" / "seasons"
OUT = ROOT / "site" / "players"
OUT.mkdir(parents=True, exist_ok=True)
PLAYOFF_START = 14  # top 6 per conference; playoffs begin week 14 every year

def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[.'\-]", "", s)
    return " ".join(s.split())

def photo_url(sid, pos):
    if not sid:
        return ""
    if pos in ("DEF", "Def") or (sid.isalpha() and len(sid) <= 3):
        return f"https://sleepercdn.com/images/team_logos/nfl/{sid.lower()}.png"
    return f"https://sleepercdn.com/content/nfl/players/thumb/{sid}.jpg"

P_ALL = json.load(open(HIST / "sleeper_players.json")) if (HIST / "sleeper_players.json").exists() else {}
NAME_INDEX = defaultdict(list)
for _pid, _p in P_ALL.items():
    if _p.get("full_name"):
        NAME_INDEX[norm(_p["full_name"])].append((_pid, _p.get("position") or "", int(_p.get("years_exp") or 0), _p.get("team") or ""))
def sid_for(name, pos=""):
    cands = NAME_INDEX.get(norm(name)) or []
    if not cands:
        return ""
    same = [c for c in cands if c[1] == pos] or cands
    same.sort(key=lambda c: (c[3] != "", c[2]), reverse=True)
    return same[0][0]

players = {}
def key_for(pl):
    return pl.get("sid") or f"{norm(pl.get('name'))}|{pl.get('pos','')}"
def rec_for(pl):
    k = key_for(pl)
    if k not in players:
        players[k] = dict(key=k, name=pl.get("name"), pos=pl.get("pos", ""), sid=pl.get("sid", ""), ownerIds=set(), weeks=0, starts=0, pts=0.0,
                          winShare=0.0, winsContributed=0, playoffWeeks=0, best=dict(pts=0.0, year=None, week=None, ownerId=None), seasons=set(),
                          tx=dict(adds=0, drops=0, waivers=0, trades=0, total=0))
    return players[k]

def ingest_team(team, year, week, won):
    lineup = team.get("lineup") or []
    total = sum(float(p.get("pts") or 0) for p in lineup if p.get("starter")) or 0.0
    for pl in lineup:
        r = rec_for(pl)
        pts = float(pl.get("pts") or 0)
        if team.get("personId"):
            r["ownerIds"].add(team["personId"])
        r["weeks"] += 1
        r["seasons"].add(str(year))
        if week >= PLAYOFF_START:
            r["playoffWeeks"] += 1
        if pl.get("starter"):
            r["starts"] += 1
            r["pts"] += pts
            if won and total > 0:
                r["winShare"] += pts / total
                r["winsContributed"] += 1
            if pts > r["best"]["pts"]:
                r["best"] = dict(pts=pts, year=str(year), week=week, ownerId=team.get("personId"))

for f in sorted(glob.glob(str(SEASONS / "*.json"))):
    s = json.load(open(f))
    year = s["year"]
    for w in s["weeks"]:
        for m in w.get("matchups", []):
            hs, as_ = float(m["home"].get("score") or 0), float(m["away"].get("score") or 0)
            ingest_team(m["home"], year, w["week"], hs > as_)
            ingest_team(m["away"], year, w["week"], as_ > hs)
        for sc in w.get("scores", []):
            ingest_team(sc, year, w["week"], False)

# ---- transactions ----
TX = HIST / "transactions"
# MFL: transaction strings like "1234,|5678," (added,|dropped,) ; type FREE_AGENT / WAIVER / BBID_WAIVER / TRADE
mfl_players = {}
for y in ["2017", "2018", "2019", "2020", "2021"]:
    pf = HIST / f"mfl_players_{y}.json"
    if pf.exists():
        mfl_players[y] = json.load(open(pf))
def mfl_key(y, pid):
    info = mfl_players.get(y, {}).get(pid, {})
    name, pos = info.get("name", ""), info.get("pos", "")
    if pos == "Def":
        return info.get("team", ""), f"{info.get('team','')} D/ST", "DEF"
    sid = sid_for(name, pos)
    return (sid or f"{norm(name)}|{pos}"), name, pos
def bump(k, name, pos, field, sid=""):
    if not name or not k or k in ("|", "|DEF"):
        return
    r = players.get(k)
    if not r:
        r = players[k] = dict(key=k, name=name, pos=pos, sid=sid if sid else (k if k in P_ALL else ""), ownerIds=set(), weeks=0, starts=0, pts=0.0,
                              winShare=0.0, winsContributed=0, playoffWeeks=0, best=dict(pts=0.0, year=None, week=None, ownerId=None), seasons=set(),
                              tx=dict(adds=0, drops=0, waivers=0, trades=0, total=0))
    r["tx"][field] += 1
    r["tx"]["total"] += 1
for y in ["2017", "2018", "2019", "2020", "2021"]:
    tf = TX / f"mfl_{y}.json"
    if not tf.exists():
        continue
    for t in json.load(open(tf)):
        ttype = t.get("type", "")
        body = t.get("transaction", "") or ""
        if ttype in ("FREE_AGENT", "WAIVER", "BBID_WAIVER", "WAIVER_REQUEST"):
            parts = body.split("|")
            added = [x for x in parts[0].split(",") if x] if parts else []
            dropped = [x for x in parts[1].split(",") if x] if len(parts) > 1 else []
            for pid in added:
                k, name, pos = mfl_key(y, pid); bump(k, name, pos, "waivers" if "WAIVER" in ttype else "adds", sid=k if k in P_ALL else "")
            for pid in dropped:
                k, name, pos = mfl_key(y, pid); bump(k, name, pos, "drops", sid=k if k in P_ALL else "")
        elif ttype == "TRADE":
            for part in (t.get("franchise1_gave_up", ""), t.get("franchise2_gave_up", "")):
                for pid in [x for x in str(part).split(",") if x and x.isdigit()]:
                    k, name, pos = mfl_key(y, pid); bump(k, name, pos, "trades", sid=k if k in P_ALL else "")
for tf in sorted(glob.glob(str(TX / "sleeper_*.json"))):
    for t in json.load(open(tf)):
        ttype = t.get("type")
        adds = t.get("adds") or {}
        drops = t.get("drops") or {}
        for pid in adds:
            info = P_ALL.get(pid, {})
            name = info.get("full_name") or (f"{pid} D/ST" if str(pid).isalpha() else pid)
            pos = info.get("position") or ("DEF" if str(pid).isalpha() else "")
            bump(str(pid), name, pos, "trades" if ttype == "trade" else ("waivers" if ttype == "waiver" else "adds"), sid=str(pid))
        for pid in drops:
            if ttype == "trade":
                continue  # a trade's "drops" are the other side's adds
            info = P_ALL.get(pid, {})
            name = info.get("full_name") or (f"{pid} D/ST" if str(pid).isalpha() else pid)
            pos = info.get("position") or ("DEF" if str(pid).isalpha() else "")
            bump(str(pid), name, pos, "drops", sid=str(pid))

# ---- finalize ----
rows = []
for k, r in players.items():
    r = dict(r)
    r["owners"] = len(r["ownerIds"]); r["ownerIds"] = sorted(r["ownerIds"])
    r["seasons"] = sorted(r["seasons"])
    r["pts"] = round(r["pts"], 2); r["winShare"] = round(r["winShare"], 3)
    r["photo"] = photo_url(r.get("sid", ""), r.get("pos", ""))
    rows.append(r)
def top(field, n=25, minweeks=0):
    return [x["key"] for x in sorted([r for r in rows if r["weeks"] >= minweeks], key=lambda r: (-r[field] if not isinstance(r[field], dict) else 0, -r["pts"]))[:n]]
index = dict(
    built=str(Path(__file__).name),
    players={r["key"]: r for r in rows if r["weeks"] >= 4 or r["tx"]["total"] >= 3},
    lists=dict(
        mostOwnersSkill=[x["key"] for x in sorted([r for r in rows if r["weeks"] >= 4 and r["pos"] in ("QB","RB","WR","TE")], key=lambda r: (-r["owners"], -r["pts"]))[:25]],
        mostTransactionsSkill=[x["key"] for x in sorted([r for r in rows if r["pos"] in ("QB","RB","WR","TE")], key=lambda r: -r["tx"]["total"])[:25]],
        mostOwners=top("owners", 25, 4),
        mostTransactions=[x["key"] for x in sorted(rows, key=lambda r: -r["tx"]["total"])[:25]],
        winShares=top("winShare", 25, 4),
        playoffRosters=top("playoffWeeks", 25, 4),
        points=top("pts", 25, 4),
        mostWeeks=top("weeks", 25, 4),
    ),
)
json.dump(index, open(OUT / "index.json", "w"), ensure_ascii=False)
print("players indexed:", len(index["players"]), "of", len(rows))
for name, lst in index["lists"].items():
    r = index["players"][lst[0]]
    print(f"  {name:16s} #1 {r['name']} — owners {r['owners']}, tx {r['tx']['total']}, winShare {r['winShare']}, playoffWeeks {r['playoffWeeks']}, pts {r['pts']}")
