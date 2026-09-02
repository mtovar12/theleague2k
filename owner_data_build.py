#!/usr/bin/env python3
"""Per-owner deep history: site/owners/<personId>.json
Built from site/seasons/<year>.json (lineups with points) + draft boards (MFL era) + Sleeper draft picks (2022-26).
Each file: {personId, seasons:[years], players:[{key,name,pos,sid,photo,pts,starts,weeks,best:{pts,year,week},seasons:{year:{pts,starts,weeks}}}],
            hof:[top 12 by pts], frequent:[top 12 by weeks rostered], drafts:{year:{platform, picks:[{round,pick,player,pos,sid,photo,price}]}}}
Run: python3 owner_data_build.py
"""
import json, os, re, unicodedata, glob
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent
HIST = ROOT / "data" / "history"
SEASONS = ROOT / "site" / "seasons"
OUT = ROOT / "site" / "owners"
OUT.mkdir(parents=True, exist_ok=True)

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

identities = json.load(open(HIST / "identities.json"))["people"]
OVERRIDES = {k: v for k, v in (json.load(open(HIST / "roster_owner_overrides.json")) if (HIST / "roster_owner_overrides.json").exists() else {}).items() if not k.startswith("_")}
handle_to_person = {(rec.get("sleeper") or "").lower(): pid for pid, rec in identities.items() if rec.get("sleeper")}
mfl_to_person = {(str(y), fid): pid for pid, rec in identities.items() for y, fid in (rec.get("mfl") or {}).items()}

# Sleeper user_id -> person (any season)
sleeper_ids = json.load(open(HIST / "sleeper_identities.json"))
user_to_person = {}
for uid, seasons in sleeper_ids.items():
    for meta in seasons.values():
        pid = handle_to_person.get((meta.get("handle") or "").lower())
        if pid:
            user_to_person[str(uid)] = pid
            break

# Sleeper player DB for names/ids on draft picks
SCRATCH_PLAYERS = str((Path(__file__).resolve().parent / "data" / "history" / "sleeper_players.json"))
P_ALL = json.load(open(SCRATCH_PLAYERS)) if os.path.exists(SCRATCH_PLAYERS) else {}
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

owners = defaultdict(lambda: dict(players={}, drafts={}, seasons=set()))

def add_lineup(pid, year, week, lineup):
    if not pid:
        return
    o = owners[pid]
    o["seasons"].add(str(year))
    for pl in lineup:
        key = f"{norm(pl.get('name'))}|{pl.get('pos','')}"
        rec = o["players"].setdefault(key, dict(name=pl.get("name"), pos=pl.get("pos", ""), sid=pl.get("sid", ""), pts=0.0, starts=0, weeks=0,
                                                best=dict(pts=0.0, year=None, week=None), seasons={}))
        if pl.get("sid") and not rec["sid"]:
            rec["sid"] = pl["sid"]
        pts = float(pl.get("pts") or 0)
        rec["weeks"] += 1
        season = rec["seasons"].setdefault(str(year), dict(pts=0.0, starts=0, weeks=0))
        season["weeks"] += 1
        if pl.get("starter"):
            rec["pts"] += pts
            rec["starts"] += 1
            season["pts"] += pts
            season["starts"] += 1
            if pts > rec["best"]["pts"]:
                rec["best"] = dict(pts=pts, year=str(year), week=week)

# ---- lineups from season files ----
for f in sorted(glob.glob(str(SEASONS / "*.json"))):
    s = json.load(open(f))
    year = s["year"]
    for w in s["weeks"]:
        for m in w.get("matchups", []):
            for side in ("home", "away"):
                add_lineup(m[side].get("personId"), year, w["week"], m[side].get("lineup", []))
        for sc in w.get("scores", []):
            add_lineup(sc.get("personId"), year, w["week"], sc.get("lineup", []))
    # MFL-era snake drafts from the season file boards (Sleeper auctions come from the picks files below)
    if s.get("drafts") and s.get("platform") != "Sleeper":
        for board in s["drafts"]["boards"]:
            for col in board["columns"]:
                pid = col.get("personId")
                if not pid:
                    continue
                picks = []
                for rnd, player in enumerate(col["picks"], start=1):
                    pos = ""
                    sid = sid_for(player, pos)
                    if player.endswith(" DEF"):
                        sid = player.split()[0]; pos = "DEF"
                    else:
                        pos = (P_ALL.get(sid) or {}).get("position", "") if sid else ""
                    picks.append(dict(round=rnd, pick=None, player=player, pos=pos, sid=sid, photo=photo_url(sid, pos), price=None))
                owners[pid]["drafts"][str(year)] = dict(platform=s["platform"], format="snake", picks=picks)
                owners[pid]["seasons"].add(str(year))

# ---- Sleeper drafts 2022-2026 (auction prices) ----
for f in sorted(glob.glob(str(HIST / "sleeper_drafts" / "*_picks.json"))):
    year, conf = Path(f).name.split("_")[0], Path(f).name.split("_")[1]
    picks = json.load(open(f))
    overrides = OVERRIDES.get(f"{conf}_{year}", {})
    by_owner = defaultdict(list)
    for p in picks:
        pid = user_to_person.get(str(overrides.get(str(p.get("roster_id"))) or p.get("picked_by")))
        if not pid:
            continue
        md = p.get("metadata") or {}
        name = f"{md.get('first_name','')} {md.get('last_name','')}".strip()
        pos = md.get("position") or ""
        sid = str(p.get("player_id") or "")
        if pos == "DEF":
            name = f"{md.get('team') or sid} DEF"
        price = md.get("amount")
        by_owner[pid].append(dict(round=p.get("round"), pick=p.get("pick_no"), player=name, pos=pos, sid=sid, photo=photo_url(sid, pos),
                                  price=int(price) if price not in (None, "") else None))
    for pid, plist in by_owner.items():
        plist.sort(key=lambda x: (-(x["price"] or 0), x["pick"] or 0))
        # An owner can hold a team in both conferences in one year (Mark, 2022): keep both drafts.
        key = year if year not in owners[pid]["drafts"] else f"{year} {conf}"
        owners[pid]["drafts"][key] = dict(platform="Sleeper", format="auction", conference=conf, picks=plist)
        owners[pid]["seasons"].add(year)

# ---- write per-owner files ----
index = {}
for pid, o in owners.items():
    players = []
    for key, rec in o["players"].items():
        rec = dict(rec)
        rec["key"] = key
        rec["pts"] = round(rec["pts"], 2)
        rec["photo"] = photo_url(rec.get("sid", ""), rec.get("pos", ""))
        for yr, sv in rec["seasons"].items():
            sv["pts"] = round(sv["pts"], 2)
        players.append(rec)
    players.sort(key=lambda r: -r["pts"])
    hof = players[:12]
    frequent = sorted(players, key=lambda r: (-r["weeks"], -r["pts"]))[:12]
    out = dict(personId=pid, seasons=sorted(o["seasons"], reverse=True), players=players, hof=hof, frequent=frequent,
               drafts=dict(sorted(o["drafts"].items(), reverse=True)))
    json.dump(out, open(OUT / f"{pid}.json", "w"), ensure_ascii=False)
    index[pid] = dict(players=len(players), seasons=len(o["seasons"]), drafts=len(o["drafts"]))
json.dump(index, open(OUT / "index.json", "w"))
print("owners written:", len(index))
sample = json.load(open(OUT / "mark-tovar.json"))
print("mark-tovar: players", len(sample["players"]), "| HOF #1:", sample["hof"][0]["name"], sample["hof"][0]["pts"], "| drafts:", list(sample["drafts"].keys()))
