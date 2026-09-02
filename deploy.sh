#!/usr/bin/env bash
# Refresh Sleeper data, rebuild all site data and pages, commit, and push.
# GitHub Actions (.github/workflows/update.yml) runs the same steps on a schedule, so this is only for manual pushes.
# Usage: ./deploy.sh "message"
set -euo pipefail
cd "$(dirname "$0")"
python3 sleeper_refresh.py
python3 season_data_build.py >/dev/null
python3 owner_data_build.py >/dev/null
python3 players_data_build.py >/dev/null
python3 power_build.py
python3 site_data_build.py >/dev/null
python3 site_build.py >/dev/null
git add -A
git -c user.name="Mark Tovar" -c user.email="mtovar12@gmail.com" commit -q -m "${1:-Update site $(date +%Y-%m-%d)}" || echo "nothing to commit"
git push -u origin main
echo "Live at https://mtovar12.github.io/theleague2k/ (the Actions run redeploys Pages in ~2 minutes)"
