#!/usr/bin/env python3
"""Generate every static page in ./site from one shared shell."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "site"

PAGES = [
    ("index.html", "Home", "The League 2K | League Home"),
    ("power.html", "Power", "Power Rankings | The League 2K"),
    ("owners.html", "Owners", "Owners | The League 2K"),
    ("players.html", "Players", "Player Hall of Fame | The League 2K"),
    ("champions.html", "Champions", "Champions | The League 2K"),
    ("records.html", "Records", "Record Book | The League 2K"),
    ("rivalries.html", "Rivalries", "Rivalries | The League 2K"),
    ("season.html", "Seasons", "Season Explorer | The League 2K"),
    ("archive.html", "Archive", "Season Archive | The League 2K"),
    ("owner.html", "", "Owner Career | The League 2K"),
]

HEAD = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="The League 2K — the live home, permanent record, and complete owner history for a two-conference fantasy football institution.">
  <meta name="theme-color" content="#080b10" media="(prefers-color-scheme: dark)">
  <meta name="theme-color" content="#f2f0ea" media="(prefers-color-scheme: light)">
  <title>{title}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="preconnect" href="https://sleepercdn.com">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bebas+Neue&amp;family=Manrope:wght@400;500;600;700;800&amp;display=swap">
  <link rel="stylesheet" href="styles.css">
</head>
<body data-page="{slug}">
  <a class="skip-link" href="#main">Skip to content</a>
  <div class="conference-rail" aria-hidden="true"><span></span><span></span></div>
  <header class="site-header">
    <div class="shell header-inner">
      <a class="brand" href="index.html" aria-label="The League 2K home">
        <span class="brand-mark" aria-hidden="true">2K</span>
        <span class="brand-copy"><strong>The League 2K</strong><small>Est. 2014 · AFC / NFC</small></span>
      </a>
      <nav class="primary-nav" aria-label="Primary navigation">
{nav}
      </nav>
    </div>
  </header>
  <main id="main">
"""

FOOT = """  </main>
  <footer class="site-footer">
    <div class="shell footer-grid">
      <div><span class="footer-mark">2K</span><p class="footer-title">The League 2K</p></div>
      <div><p>Live season data from Sleeper. History from MyFantasyLeague and league records dating to 2014.</p></div>
      <div><p class="footer-label">Permanent record</p><p>Two conferences. Every season. One place built for Sunday.</p></div>
    </div>
    <div class="shell footer-bottom"><span>Est. 2014</span><span>AFC red · NFC blue</span><span>Built for the group chat</span></div>
  </footer>
  <script src="players.js"></script>
  <script src="data.js"></script>
  <script src="app.js"></script>
</body>
</html>
"""

BODIES = {}

BODIES["index.html"] = """
    <section class="masthead-band" aria-labelledby="masthead-title">
      <div class="shell masthead-inner">
        <div><p class="section-kicker">Current league</p><h1 id="masthead-title">The League 2K</h1></div>
        <div class="masthead-meta">
          <span><small>Season</small><strong id="current-season">2026</strong></span>
          <span><small>Week</small><strong id="current-week">—</strong></span>
          <span class="live-signal"><i aria-hidden="true"></i><strong id="live-label">Live</strong></span>
        </div>
      </div>
    </section>

    <section class="section home-dashboard" aria-label="Current league dashboard">
      <div class="shell dashboard-grid">
        <div class="dashboard-main">
          <section class="product-section power-centerpiece" aria-labelledby="home-power-title">
            <div class="product-heading">
              <div><p class="section-kicker">Power rankings</p><h2 id="home-power-title">Who owns Sunday</h2><p id="pr-note" class="section-intro"></p></div>
              <div class="segmented" id="power-filter" role="group" aria-label="Filter power rankings">
                <button type="button" class="is-active" data-power-filter="ALL" aria-pressed="true">Combined</button>
                <button type="button" data-power-filter="AFC" aria-pressed="false">AFC</button>
                <button type="button" data-power-filter="NFC" aria-pressed="false">NFC</button>
              </div>
            </div>
            <div class="power-board" id="pr-table" aria-live="polite"></div>
          </section>

          <section class="product-section" aria-labelledby="matchups-title">
            <div class="product-heading compact-heading"><div><p class="section-kicker">This week</p><h2 id="matchups-title">Matchups</h2></div><span class="panel-status" id="matchup-week">Live scores</span></div>
            <div class="conference-tabs" id="matchup-tabs" role="group" aria-label="Matchup conference">
              <button class="is-active afc-tab" type="button" data-panel-target="matchups-afc" aria-pressed="true">AFC</button>
              <button class="nfc-tab" type="button" data-panel-target="matchups-nfc" aria-pressed="false">NFC</button>
            </div>
            <div id="matchups-afc" class="matchup-board live-panel" aria-busy="true"><div class="skeleton stack"><span></span><span></span><span></span></div></div>
            <div id="matchups-nfc" class="matchup-board live-panel" aria-busy="true" hidden><div class="skeleton stack"><span></span><span></span><span></span></div></div>
          </section>
        </div>

        <aside class="dashboard-rail">
          <section class="rail-panel" aria-labelledby="standings-title">
            <div class="rail-heading"><div><p class="section-kicker">League table</p><h2 id="standings-title">Standings</h2></div><span class="panel-status">W–L · PF</span></div>
            <div class="conference-tabs" id="standing-tabs" role="group" aria-label="Standings conference">
              <button class="is-active afc-tab" type="button" data-panel-target="live-afc" aria-pressed="true">AFC</button>
              <button class="nfc-tab" type="button" data-panel-target="live-nfc" aria-pressed="false">NFC</button>
            </div>
            <div id="live-afc" class="standings-list live-panel" aria-busy="true"><div class="skeleton rows"><span></span><span></span><span></span><span></span><span></span></div></div>
            <div id="live-nfc" class="standings-list live-panel" aria-busy="true" hidden><div class="skeleton rows"><span></span><span></span><span></span><span></span><span></span></div></div>
          </section>

          <section class="rail-panel transactions-panel" aria-labelledby="transactions-title">
            <div class="rail-heading"><div><p class="section-kicker">League wire</p><h2 id="transactions-title">Transactions</h2></div><span class="panel-status">Latest</span></div>
            <div id="transactions" class="transaction-list live-panel" aria-busy="true"><div class="skeleton stack"><span></span><span></span><span></span></div></div>
          </section>
        </aside>
      </div>
    </section>
"""

BODIES["power.html"] = """
    <section class="section page-top" aria-labelledby="power-title">
      <div class="shell">
        <div class="page-heading product-heading">
          <div><p class="section-kicker">Power rankings</p><h1 id="power-title">The full board</h1><p id="pr-note" class="section-intro"></p></div>
          <div class="segmented" id="power-filter" role="group" aria-label="Filter power rankings">
            <button type="button" class="is-active" data-power-filter="ALL" aria-pressed="true">Combined</button>
            <button type="button" data-power-filter="AFC" aria-pressed="false">AFC</button>
            <button type="button" data-power-filter="NFC" aria-pressed="false">NFC</button>
          </div>
        </div>
        <div class="power-board standalone-power" id="pr-table" aria-live="polite"></div>
      </div>
    </section>
"""

BODIES["owners.html"] = """
    <section class="section page-top" aria-labelledby="owners-title">
      <div class="shell">
        <div class="page-heading split-heading">
          <div><p class="section-kicker">League people</p><h1 id="owners-title">Owners</h1></div>
          <p class="section-intro">Every owner since 2014, ranked by career win percentage (two full seasons to qualify). Careers combine every era — ESPN, RT Sports, MyFantasyLeague, and Sleeper.</p>
        </div>
        <div class="owner-tools">
          <label class="search-field"><span>Find an owner</span><input id="owner-search" type="search" placeholder="Name, handle, or team" autocomplete="off"></label>
          <div class="owner-tool-group">
            <div class="segmented" id="owner-sort" role="group" aria-label="Sort owners"><button class="is-active" type="button" data-owner-sort="winpct" aria-pressed="true">Win %</button><button type="button" data-owner-sort="az" aria-pressed="false">A–Z</button><button type="button" data-owner-sort="titles" aria-pressed="false">Titles</button><button type="button" data-owner-sort="wins" aria-pressed="false">Wins</button></div>
            <button class="toggle-chip" type="button" id="owner-active-only" aria-pressed="false">Active owners only</button>
          </div>
        </div>
        <div class="owner-list" id="owner-grid" role="table" aria-label="Owner career records"></div>
      </div>
    </section>
"""

BODIES["owner.html"] = """
    <section class="section owner-page page-top" aria-live="polite">
      <div class="shell" id="owner-profile"><div class="profile-skeleton"><div class="skeleton-avatar"></div><div class="skeleton stack"><span></span><span></span><span></span></div></div></div>
    </section>
"""

BODIES["players.html"] = """
    <section class="players-hero page-top" aria-labelledby="players-title">
      <div class="shell">
        <div class="page-heading split-heading">
          <div><p class="section-kicker gold-kicker">League player Hall of Fame</p><h1 id="players-title">The names behind the numbers.</h1></div>
          <p class="section-intro">Every starter point, roster stop, playoff appearance, and transaction from the complete lineup era — 2017 through 2025.</p>
        </div>
        <div class="player-headline-grid" id="player-headlines" aria-busy="true"><div class="skeleton stack"><span></span><span></span><span></span></div></div>
      </div>
    </section>

    <section class="section player-records" aria-labelledby="player-board-title">
      <div class="shell">
        <div class="page-heading player-board-heading"><div><p class="section-kicker">All-time boards</p><h2 id="player-board-title">Twenty-five deep.</h2></div><p class="section-intro">Skill positions are the default view. Include kickers and defenses to see the full churn-heavy board.</p></div>
        <div class="player-board-tools">
          <label class="search-field"><span>Search every player</span><input id="player-search" type="search" placeholder="Name or position" autocomplete="off"></label>
          <div class="segmented player-scope-filter" id="player-scope-filter" role="group" aria-label="Choose player positions"><button class="is-active" type="button" data-player-scope="skill" aria-pressed="true">Skill positions</button><button type="button" data-player-scope="all" aria-pressed="false">Include K / DEF</button></div>
        </div>
        <div class="player-board-tabs" id="player-board-tabs" role="tablist" aria-label="Player leaderboard metric">
          <button class="is-active" type="button" role="tab" data-player-board="points" aria-selected="true">Points</button>
          <button type="button" role="tab" data-player-board="winShares" aria-selected="false">Win Shares</button>
          <button type="button" role="tab" data-player-board="playoffRosters" aria-selected="false">Playoff Rosters</button>
          <button type="button" role="tab" data-player-board="mostOwners" aria-selected="false">Most Owners</button>
          <button type="button" role="tab" data-player-board="mostTransactions" aria-selected="false">Most Transactions</button>
          <button type="button" role="tab" data-player-board="mostWeeks" aria-selected="false">Most Weeks</button>
        </div>
        <p class="player-glossary" id="player-glossary" aria-live="polite"></p>
        <div class="player-ranking-list" id="player-rankings" aria-live="polite" aria-busy="true"><div class="skeleton rows"><span></span><span></span><span></span><span></span></div></div>
      </div>
    </section>
"""

BODIES["champions.html"] = """
    <section class="trophy-hero" aria-labelledby="champions-title">
      <div class="shell trophy-grid">
        <div><p class="section-kicker gold-kicker">Trophy room</p><h1 id="champions-title">Built on Sundays.<br>Settled for good.</h1><p>Every league champion and conference crown since the founding season.</p></div>
        <aside class="trophy-plaque" aria-label="Twelve completed seasons"><span>Seasons in the books</span><strong>12</strong><small>2014 — 2025</small></aside>
      </div>
    </section>
    <section class="section champions-section" aria-labelledby="wall-title">
      <div class="shell"><div class="page-heading"><p class="section-kicker gold-kicker">The immortals</p><h2 id="wall-title">Wall of champions</h2></div><div class="champion-wall" id="champ-list"></div></div>
    </section>
"""

BODIES["records.html"] = """

    <section class="section marks-section" aria-labelledby="marks-title">
      <div class="shell"><div class="page-heading split-heading"><div><p class="section-kicker">All-time marks</p><h1 id="marks-title">The outer limits</h1></div><p class="section-intro">Every weekly score from the MFL and Sleeper eras.</p></div>
        <blockquote class="record-pullquote"><span>Highest week</span><strong id="mark-record-score">—</strong><p id="mark-record-team">—</p><small id="mark-record-detail">—</small></blockquote>
        <div class="marks-grid"><article class="table-panel"><header><p class="section-kicker">Scoring ceiling</p><h3>Highest single weeks</h3></header><div class="data-table" id="marks-top"></div></article><article class="table-panel"><header><p class="section-kicker">Scoring floor</p><h3>Lowest single weeks</h3></header><div class="data-table" id="marks-low"></div></article></div>
        <article class="table-panel blowout-panel"><header><p class="section-kicker">Runaway games</p><h3>Biggest blowouts</h3></header><div class="data-table" id="marks-blow"></div></article>
      </div>
    </section>
"""

BODIES["rivalries.html"] = """
    <section class="section rivalry-section page-top" aria-labelledby="rivalries-title">
      <div class="shell"><div class="page-heading centered-heading"><p class="section-kicker">Head to head</p><h1 id="rivalries-title">Settle the score</h1><p class="section-intro">Choose two owners for the complete cross-era series.</p></div>
        <div class="fight-picker"><label><span>Conference</span><select id="riv-conf"><option value="ALL">All</option><option value="AFC">AFC</option><option value="NFC">NFC</option></select></label><label><span>Red corner</span><span class="picker-owner-control"><select id="riv-a"></select><span class="picker-owner-preview" id="riv-a-preview" aria-live="polite"></span></span></label><span class="versus" aria-hidden="true">VS</span><label><span>Blue corner</span><span class="picker-owner-control"><select id="riv-b"></select><span class="picker-owner-preview" id="riv-b-preview" aria-live="polite"></span></span></label></div>
        <div id="riv-out" class="fight-card" aria-live="polite">Choose two owners.</div>
      </div>
    </section>
"""

BODIES["archive.html"] = """
    <section class="era-band page-top" aria-labelledby="era-title"><div class="shell"><div class="page-heading split-heading"><div><p class="section-kicker">League timeline</p><h1 id="era-title">Five platforms. One lineage.</h1></div><p class="section-intro">Looking for every score and lineup? <a class="text-link" href="season.html">Open the Season Explorer →</a></p></div><div class="timeline" id="timeline"></div></div></section>
    <section class="section archive-section" aria-labelledby="seasons-title"><div class="shell"><div class="page-heading"><p class="section-kicker">The archive</p><h2 id="seasons-title">Season by season</h2><p class="section-intro">Standings, teams, owners, and champions from every year.</p></div><div class="season-stack" id="season-list"></div></div></section>
"""

BODIES["season.html"] = """
    <section class="section season-explorer page-top" aria-labelledby="season-title">
      <div class="shell">
        <header class="season-hero">
          <div class="season-title-block">
            <p class="section-kicker">Season explorer</p>
            <div class="season-year-line"><h1 id="season-title">2025</h1><span class="platform-chip" id="season-platform">Loading</span></div>
            <label class="season-picker"><span>Choose season</span><select id="season-year" aria-label="Choose season"></select></label>
          </div>
          <div class="season-champion" id="season-champion" aria-live="polite"><div class="skeleton stack"><span></span></div></div>
          <a class="back-link" href="archive.html">Season archive →</a>
        </header>

        <div class="season-loading" id="season-loading" role="status" aria-live="polite">
          <span class="sr-only">Loading season</span>
          <div class="skeleton season-skeleton"><span></span><span></span><span></span><span></span></div>
        </div>
        <div class="season-load-error" id="season-error" role="alert" hidden></div>

        <div id="season-content" hidden>
          <div class="season-view-tabs" role="tablist" aria-label="Season view">
            <button class="is-active" id="schedule-tab" type="button" role="tab" aria-selected="true" aria-controls="season-week-panel" data-season-view="schedule">Week by week</button>
            <button id="draft-tab" type="button" role="tab" aria-selected="false" aria-controls="season-draft-panel" data-season-view="draft">Draft</button>
          </div>

          <section id="season-week-panel" role="tabpanel" aria-labelledby="schedule-tab">
            <div class="season-week-controls">
              <div class="week-strip-wrap"><p class="control-label">Week</p><div class="week-strip" id="season-week-strip" role="tablist" aria-label="Choose week"></div></div>
              <div class="segmented season-conference-filter" id="season-conference-filter" role="group" aria-label="Filter matchups by conference">
                <button class="is-active" type="button" data-season-filter="ALL" aria-pressed="true">Combined</button>
                <button type="button" data-season-filter="AFC" aria-pressed="false">AFC</button>
                <button type="button" data-season-filter="NFC" aria-pressed="false">NFC</button>
              </div>
            </div>
            <div class="weekly-summary" id="season-summary" aria-live="polite"></div>
            <div class="season-matchups" id="season-matchups" aria-live="polite"></div>
          </section>

          <section id="season-draft-panel" role="tabpanel" aria-labelledby="draft-tab" hidden></section>
        </div>
      </div>
    </section>
"""


def nav_for(current):
    active = "owners.html" if current == "owner.html" else current
    links = []
    for filename, label, _ in PAGES:
        if not label or filename == "owner.html":
            continue
        marker = ' aria-current="page"' if filename == active else ""
        links.append(f'        <a href="{filename}"{marker}>{label}</a>')
    return "\n".join(links)


OUT.mkdir(parents=True, exist_ok=True)
for filename, _, title in PAGES:
    html = HEAD.format(title=title, slug=filename.removesuffix(".html"), nav=nav_for(filename)) + BODIES[filename] + FOOT
    (OUT / filename).write_text(html, encoding="utf-8")
    print("wrote", filename)
