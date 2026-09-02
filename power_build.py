#!/usr/bin/env python3
"""In-season power rankings -> data/history/power_rankings.json (consumed by site_data_build.py).
Only written once regular-season games exist for the current season; otherwise the file is removed so the
preseason edition in site/data.js stays. Score (0-100) blends: win% (35%), points-per-game vs league (35%),
last-3-week scoring form (20%), all-play win% (10%). Same row shape as the preseason board: [rank, conf, team, handle, score].
Run: python3 power_build.py
"""
import json, time
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent
HIST = ROOT / "data" / "history"
OUT = HIST / "power_rankings.json"
proc = json.loads((HIST / "history_processed.json").read_text(encoding="utf-8"))
raw = json.loads((HIST / "history_raw.json").read_text(encoding="utf-8"))
ids = json.loads((HIST / "sleeper_identities.json").read_text(encoding="utf-8"))
import os
year = os.environ.get("POWER_YEAR") or str(max(int(k.split("_")[1]) for k in raw if "_" in k))
games = [g for g in proc["games"] if str(g["season"]) == year]
if not games:
    if OUT.exists():
        OUT.unlink()
    print(f"{year}: no regular-season games yet; preseason edition stays"); raise SystemExit

teams = defaultdict(lambda: dict(w=0, l=0, t=0, pf=0.0, pa=0.0, weekly={}, conf=""))
by_week = defaultdict(list)
for g in games:
    for me, opp, mine, theirs in ((g["u1"], g["u2"], g["p1"], g["p2"]), (g["u2"], g["u1"], g["p2"], g["p1"])):
        t = teams[me]; t["conf"] = g["conf"]
        t["w"] += mine > theirs; t["l"] += mine < theirs; t["t"] += mine == theirs
        t["pf"] += mine; t["pa"] += theirs; t["weekly"][g["week"]] = mine
        by_week[(g["conf"], g["week"])].append((me, mine))
last_week = max(g["week"] for g in games)
# all-play: share of same-conference teams you would have beaten each week
allplay = defaultdict(lambda: [0, 0])
for (conf, wk), scores in by_week.items():
    for uid, pts in scores:
        others = [p for u, p in scores if u != uid]
        allplay[uid][0] += sum(pts > p for p in others); allplay[uid][1] += len(others)
def pct(a, b): return a / b if b else 0.0
ppg = {u: pct(t["pf"], len(t["weekly"])) for u, t in teams.items()}
form = {u: pct(sum(v for w, v in t["weekly"].items() if w > last_week - 3), len([w for w in t["weekly"] if w > last_week - 3])) for u, t in teams.items()}
def scale(d):
    lo, hi = min(d.values()), max(d.values())
    return {k: (v - lo) / (hi - lo) if hi > lo else 0.5 for k, v in d.items()}
s_win = {u: pct(t["w"] + 0.5 * t["t"], t["w"] + t["l"] + t["t"]) for u, t in teams.items()}
s_ppg, s_form = scale(ppg), scale(form)
s_all = {u: pct(a[0], a[1]) for u, a in allplay.items()}
rows = []
for u, t in teams.items():
    score = 100 * (0.35 * s_win[u] + 0.35 * s_ppg[u] + 0.20 * s_form[u] + 0.10 * s_all[u])
    meta = ids.get(u, {}).get(year, {})
    rows.append([t["conf"], meta.get("team") or meta.get("handle") or proc["latest_name"].get(u, u), meta.get("handle") or proc["latest_name"].get(u, ""), round(score, 1),
                 dict(record=f"{t['w']}-{t['l']}" + (f"-{t['t']}" if t["t"] else ""), ppg=round(ppg[u], 1), form=round(form[u], 1), allPlay=round(100 * s_all[u]))])
rows.sort(key=lambda r: (-r[3], -r[4]["ppg"]))
rows = [[i + 1, *r] for i, r in enumerate(rows)]
OUT.write_text(json.dumps(dict(edition=f"Week {last_week} Edition · {time.strftime('%b %d, %Y')}",
    note="Computed from results through week %d: win percentage, points per game, last-three-week scoring form, and all-play record. Updates automatically after every scored week." % last_week,
    week=last_week, rows=rows), ensure_ascii=False), encoding="utf-8")
print(f"power rankings week {last_week}: #1 {rows[0][2]} ({rows[0][1]}) {rows[0][4]}")
