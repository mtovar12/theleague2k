#!/usr/bin/env python3
"""Bake per-season explorer data: site/seasons/<year>.json
Each file: {year, platform, weeks:[{week, matchups:[{conference, home:{franchise, team, personId, score, lineup:[...]}, away:{...}}]}], drafts:{...}}
MFL 2017-2021 from data/history/mfl_raw.json (+ mfl_players_<year>.json caches).
Sleeper 2022-2025 from data/history/history_raw.json (matchups carry starters/players) + scratch players db.
Run: python3 season_data_build.py
"""
import json, os, re, unicodedata, html
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HIST = ROOT / "data" / "history"
OUT = ROOT / "site" / "seasons"
OUT.mkdir(parents=True, exist_ok=True)

identities = json.load(open(HIST / "identities.json"))["people"]
mfl_to_person = {}
for pid, rec in identities.items():
    for year, fid in (rec.get("mfl") or {}).items():
        mfl_to_person[(str(year), fid)] = pid
sleeper_handle_to_person = {(rec.get("sleeper") or "").lower(): pid for pid, rec in identities.items() if rec.get("sleeper")}

def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[.'\-]", "", s)
    return " ".join(s.split())

SCRATCH_PLAYERS = str((Path(__file__).resolve().parent / "data" / "history" / "sleeper_players.json"))
P_ALL = json.load(open(SCRATCH_PLAYERS)) if os.path.exists(SCRATCH_PLAYERS) else {}
NAME_INDEX = {}
for _pid, _p in P_ALL.items():
    if not _p.get("full_name"):
        continue
    NAME_INDEX.setdefault(norm(_p["full_name"]), []).append((_pid, _p.get("position") or "", int(_p.get("years_exp") or 0), _p.get("team") or ""))
def sleeper_id_for(name, pos):
    cands = NAME_INDEX.get(norm(name)) or []
    if not cands:
        return ""
    same = [c for c in cands if (c[1] == pos) or (pos in ("Def", "DEF") and c[1] == "DEF")]
    pool = same or cands
    pool.sort(key=lambda c: (c[3] != "", c[2]), reverse=True)  # prefer active, then most experienced
    return pool[0][0]

# ---------------- MFL ----------------
M = json.load(open(HIST / "mfl_raw.json"))
INFERRED = {}
for _y in ["2017", "2018", "2019", "2020", "2021"]:
    _f = HIST / _y / "schedule_inferred.json"
    if _f.exists():
        for _g in json.load(open(_f))["games"]:
            INFERRED.setdefault(_y, {}).setdefault(int(_g["week"]), []).append((_g["a"], _g["b"]))
for year in ["2017", "2018", "2019", "2020", "2021"]:
    players = json.load(open(HIST / f"mfl_players_{year}.json"))
    league = M[year]["league"]["league"]
    franchises = {f["id"]: f for f in league["franchises"]["franchise"]}
    divisions = {d["id"]: d["name"] for d in (league.get("divisions", {}).get("division") or [])}
    def conf_of(fid):
        div = franchises[fid].get("division") or ""
        name = divisions.get(div, "")
        if name in ("AFC", "NFC"):
            return name
        # 2017 used four divisions (West/East per conference): 00-01 = AFC, 02-03 = NFC
        return "AFC" if div in ("00", "01") else "NFC"
    def team_of(fid):
        f = franchises[fid]
        return dict(franchise=fid, team=f["name"].strip(), personId=mfl_to_person.get((year, fid)), conference=conf_of(fid),
                    logo=f"assets/logos/mfl/{year}_{fid}{os.path.splitext(f.get('logo') or '.jpg')[1] or '.jpg'}")
    def lineup(entry):
        out = []
        for pl in entry.get("player", []):
            info = players.get(pl["id"], {})
            name = info.get("name", pl["id"])
            if info.get("pos") == "Def":
                name = f"{info.get('team', '')} D/ST"
            sid = info.get("team", "") if info.get("pos") == "Def" else sleeper_id_for(name, info.get("pos", ""))
            out.append(dict(name=name, pos=info.get("pos", ""), nfl=info.get("team", ""), sid=sid,
                            pts=round(float(pl.get("score") or 0), 2), starter=pl.get("status") == "starter"))
        out.sort(key=lambda p: (not p["starter"], -p["pts"]))
        return out
    weeks = []
    for w in M[year]["weeklyResults"]["allWeeklyResults"]["weeklyResults"]:
        wk = int(w["week"])
        entries = {}
        pairs = []
        inferred = INFERRED.get(year, {}).get(wk)
        if inferred and "franchise" in w:
            for f in w["franchise"]:
                entries[f["id"]] = f
            pairs.extend(inferred)
        elif "matchup" in w:
            ms = w["matchup"] if isinstance(w["matchup"], list) else [w["matchup"]]
            for m in ms:
                fr = m["franchise"]
                if len(fr) == 2:
                    pairs.append((fr[0]["id"], fr[1]["id"]))
                for f in fr:
                    entries[f["id"]] = f
        elif "franchise" in w:
            for f in w["franchise"]:
                entries[f["id"]] = f
            # pair via schedule
            sched = [s for s in M[year]["schedule"]["schedule"]["weeklySchedule"] if str(s.get("week")) == str(wk)]
            for s in sched:
                for mu in (s.get("matchup") if isinstance(s.get("matchup"), list) else [s.get("matchup")] if s.get("matchup") else []):
                    fr = mu.get("franchise", [])
                    if len(fr) == 2:
                        pairs.append((fr[0]["id"], fr[1]["id"]))
        matchups = []
        for a, b in pairs:
            if a not in entries or b not in entries:
                continue
            sa, sb = float(entries[a].get("score") or 0), float(entries[b].get("score") or 0)
            if sa == 0 and sb == 0:
                continue
            matchups.append(dict(conference=conf_of(a) if conf_of(a) == conf_of(b) else "Interconference",
                                 home={**team_of(a), "score": round(sa, 2), "lineup": lineup(entries[a])},
                                 away={**team_of(b), "score": round(sb, 2), "lineup": lineup(entries[b])}))
        if matchups:
            weeks.append(dict(week=wk, matchups=matchups))
        elif entries:
            # No pairings recorded (2019 weeks 1-12): keep every team's score + lineup as a weekly scoreboard.
            scores = []
            for fid, e in entries.items():
                sc = float(e.get("score") or 0)
                if sc > 0:
                    scores.append({**team_of(fid), "conference": conf_of(fid), "score": round(sc, 2), "lineup": lineup(e)})
            if scores:
                scores.sort(key=lambda s: -s["score"])
                weeks.append(dict(week=wk, matchups=[], scores=scores))
    drafts = None
    bp = HIST / year / f"draft_{year}_boards.json"
    if bp.exists():
        boards = json.load(open(bp))
        colmap = json.load(open(HIST / year / "draft_column_to_franchise.json")) if (HIST / year / "draft_column_to_franchise.json").exists() else {}
        drafts = dict(format=boards.get("format", ""), boards=[])
        for bk in ("boardA", "boardB"):
            cols = []
            for col, picks in boards[bk].items():
                meta = colmap.get(f"{bk}|{col}", {})
                fid = meta.get("franchise")
                cols.append(dict(label=col, franchise=fid, team=franchises[fid]["name"].strip() if fid else col,
                                 personId=mfl_to_person.get((year, fid)) if fid else None, picks=[html.unescape(str(x)) for x in picks]))
            drafts["boards"].append(dict(name=bk, columns=cols))
    playoff_start = int(league.get("lastRegularSeasonWeek") or 13) + 1
    if INFERRED.get(year):
        playoff_start = max(INFERRED[year]) + 1  # 2019: MFL's setting was off by two; playoffs began week 13
    json.dump(dict(year=int(year), platform="MyFantasyLeague", playoffStart=playoff_start, weeks=weeks, drafts=drafts),
              open(OUT / f"{year}.json", "w"), ensure_ascii=False)
    print(year, "weeks", len(weeks), "matchups", sum(len(w["matchups"]) for w in weeks), "drafts", bool(drafts))

# ---------------- Sleeper ----------------
H = json.load(open(HIST / "history_raw.json"))
OVERRIDES = {k: v for k, v in (json.load(open(HIST / "roster_owner_overrides.json")) if (HIST / "roster_owner_overrides.json").exists() else {}).items() if not k.startswith("_")}
SCRATCH_PLAYERS = str((Path(__file__).resolve().parent / "data" / "history" / "sleeper_players.json"))
P = json.load(open(SCRATCH_PLAYERS)) if os.path.exists(SCRATCH_PLAYERS) else {}
def pinfo(pid):
    p = P.get(pid, {})
    if not p and pid and pid.isalpha():
        return dict(name=f"{pid} D/ST", pos="DEF", nfl=pid)
    return dict(name=p.get("full_name") or pid, pos=p.get("position") or "", nfl=p.get("team") or "")
SLEEPER_YEARS = sorted({k.split("_")[1] for k in H if "_" in k})
for year in SLEEPER_YEARS:
    weeks_by = {}
    for conf in ["AFC", "NFC"]:
        rec = H.get(f"{conf}_{year}")
        if not rec:
            continue
        users = {u["user_id"]: u for u in rec["users"]}
        rosters = {r["roster_id"]: r for r in rec["rosters"]}
        overrides = OVERRIDES.get(f"{conf}_{year}", {})
        def team_of(rid):
            r = rosters.get(rid, {})
            u = users.get(overrides.get(str(rid)) or r.get("owner_id"), {})
            md = u.get("metadata") or {}
            handle = u.get("display_name", "")
            return dict(roster=rid, team=(md.get("team_name") or handle or "—").strip(), personId=sleeper_handle_to_person.get(handle.lower()), conference=conf,
                        logo=md.get("avatar") or (f"https://sleepercdn.com/avatars/thumbs/{u['avatar']}" if u.get("avatar") else ""))
        for wk, ms in rec["matchups"].items():
            by = {}
            for m in ms:
                if m.get("matchup_id") is not None:
                    by.setdefault(m["matchup_id"], []).append(m)
            for pair in by.values():
                if len(pair) != 2:
                    continue
                a, b = pair
                pa, pb = float(a.get("points") or 0), float(b.get("points") or 0)
                if pa == 0 and pb == 0:
                    continue
                def lineup(m):
                    starters = set(m.get("starters") or [])
                    pts = m.get("players_points") or {}
                    out = []
                    for pid in (m.get("players") or []):
                        info = pinfo(pid)
                        out.append(dict(name=info["name"], pos=info["pos"], nfl=info["nfl"], sid=str(pid), pts=round(float(pts.get(pid, 0) or 0), 2), starter=pid in starters))
                    out.sort(key=lambda p: (not p["starter"], -p["pts"]))
                    return out
                weeks_by.setdefault(int(wk), []).append(dict(conference=conf,
                    home={**team_of(a["roster_id"]), "score": round(pa, 2), "lineup": lineup(a)},
                    away={**team_of(b["roster_id"]), "score": round(pb, 2), "lineup": lineup(b)}))
    weeks = [dict(week=w, matchups=weeks_by[w]) for w in sorted(weeks_by)]
    # Sleeper auction drafts -> boards (one per conference); picks rendered as "Player ($amount)"
    drafts = None
    boards = []
    for conf in ["AFC", "NFC"]:
        pf = HIST / "sleeper_drafts" / f"{year}_{conf}_picks.json"
        rec = H.get(f"{conf}_{year}")
        if not pf.exists() or not rec:
            continue
        users = {u["user_id"]: u for u in rec["users"]}
        cols = {}
        overrides = OVERRIDES.get(f"{conf}_{year}", {})
        for p in sorted(json.load(open(pf)), key=lambda x: x.get("pick_no") or 0):
            uid = str(overrides.get(str(p.get("roster_id"))) or p.get("picked_by") or "")
            u = users.get(uid, {})
            md = p.get("metadata") or {}
            name = f"{md.get('first_name','')} {md.get('last_name','')}".strip()
            if md.get("position") == "DEF":
                name = f"{md.get('team') or p.get('player_id')} DEF"
            amt = md.get("amount")
            label = f"{name} (${amt})" if amt not in (None, "") else name
            team = ((u.get("metadata") or {}).get("team_name") or u.get("display_name") or uid).strip()
            cols.setdefault(uid, dict(label=team, franchise=None, team=team, personId=sleeper_handle_to_person.get((u.get("display_name") or "").lower()), picks=[]))
            cols[uid]["picks"].append(label)
        if cols:
            boards.append(dict(name=f"{conf} auction", columns=list(cols.values())))
    if boards:
        drafts = dict(format="auction, $200 budget, 15 roster spots (Sleeper)", boards=boards)
    if not weeks and not drafts:
        continue  # nothing played or drafted yet
    playoff_start = 14
    for conf in ["AFC", "NFC"]:
        rec = H.get(f"{conf}_{year}") or {}
        playoff_start = int(rec.get("playoff_week_start") or (rec.get("settings") or {}).get("playoff_week_start") or 14)
    json.dump(dict(year=int(year), platform="Sleeper", playoffStart=playoff_start, weeks=weeks, drafts=drafts), open(OUT / f"{year}.json", "w"), ensure_ascii=False)
    lu = sum(1 for w in weeks for m in w["matchups"] if m["home"]["lineup"])
    print(year, "weeks", len(weeks), "matchups", sum(len(w["matchups"]) for w in weeks), "with lineups", lu)
print("done ->", OUT)
