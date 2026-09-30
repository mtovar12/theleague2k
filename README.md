# The League 2K — league hub

Static site (GitHub Pages) for a 24-team, two-conference fantasy football league running since 2014.

- `site/` — the published pages. Live scores, standings, transactions and rosters come straight from the Sleeper API in the browser.
- `data/history/` — the league dataset: Sleeper seasons (2022–), MyFantasyLeague seasons (2017–2021), identities, drafts, transactions, champions.
- `sleeper_refresh.py` pulls the current season from Sleeper; `season_data_build.py`, `owner_data_build.py`, `players_data_build.py`, `power_build.py`, `site_data_build.py` and `site_build.py` rebuild every data file and page.
- `./deploy.sh "message"` runs that pipeline, commits and pushes; GitHub Pages redeploys from `main`. A scheduled GitHub Actions workflow to run it after each game window is drafted but not yet installed.
