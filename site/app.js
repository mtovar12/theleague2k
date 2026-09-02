(function () {
  "use strict";

  const D = window.LEAGUE_DATA;
  const PLAYERS = window.PLAYERS || {};
  const $ = (id) => document.getElementById(id);
  const esc = (value) => String(value ?? "").replace(/[&<>'"]/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", "\"": "&quot;"
  })[char]);
  const formatNumber = (value, digits = 1) => value == null ? "—" : Number(value).toLocaleString("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits
  });
  const initials = (name) => {
    const parts = String(name || "?").match(/[A-Za-z0-9]+/g) || ["?"];
    return (parts.length > 1 ? parts[0][0] + parts[parts.length - 1][0] : parts[0].slice(0, 2)).toUpperCase();
  };

  if (!D) {
    document.body.innerHTML = '<main class="fatal-state">The League 2K data could not be loaded.</main>';
    return;
  }

  const people = D.people || {};
  const person = (id) => people[id] || null;
  const displayName = (id, fallback = "—") => person(id)?.name || fallback;
  const personIdForHandle = (handle) => D.handleToPerson?.[String(handle || "").toLowerCase()] || null;
  const personIdForUser = (userId) => D.userToPerson?.[String(userId)] || null;

  function teamOwnerLabel(team, personId, fallback = "") {
    const owner = displayName(personId, fallback);
    if (!team) return owner || "—";
    if (!owner || String(team).trim().toLowerCase() === String(owner).trim().toLowerCase()) return team;
    return `${team} · ${owner}`;
  }

  function trophyMarkup(personId) {
    if (!personId || personId !== D.currentChampion) return "";
    return '<span class="trophy" role="img" aria-label="Current champion" tabindex="0" data-tip="Current champion"><svg viewBox="0 0 24 24" width="12" height="12" aria-hidden="true"><path fill="currentColor" d="M7 2h10v2h3v3a5 5 0 0 1-4.6 4.98A6 6 0 0 1 13 15.9V18h3v2H8v-2h3v-2.1a6 6 0 0 1-2.4-3.92A5 5 0 0 1 4 7V4h3V2zm-1 4v1a3 3 0 0 0 2 2.83V6H6zm12 0h-2v3.83A3 3 0 0 0 18 7V6z"/></svg></span>';
  }

  function ownerMention(personId, label, options = {}) {
    const owner = person(personId);
    const primary = label || owner?.name || "—";
    const secondary = options.secondary || "";
    const className = ["owner-mention", options.className || ""].filter(Boolean).join(" ");
    const imageName = owner?.current?.team || owner?.name || primary;
    const image = owner?.current?.avatar || "";
    const primaryTag = options.primaryTag === "h1" ? "h1" : "span";
    const content = `${avatarMarkup(imageName, image, options.avatarClass || "owner-mention-avatar")}<span class="owner-mention-copy"><${primaryTag} class="owner-mention-primary">${options.withTrophy === false ? "" : trophyMarkup(personId)}${esc(primary)}</${primaryTag}>${secondary ? `<span class="owner-mention-secondary">${esc(secondary)}</span>` : ""}</span>`;
    if (!personId || options.link === false) {
      const wrapperTag = primaryTag === "h1" ? "div" : "span";
      return `<${wrapperTag} class="${esc(className)}">${content}</${wrapperTag}>`;
    }
    return `<a class="${esc(className)}" href="owner.html?id=${encodeURIComponent(personId)}">${content}</a>`;
  }

  function ownerLink(personId, label, className = "", withTrophy = true) {
    return ownerMention(personId, label, { className, withTrophy });
  }

  function seasonLogo(year, personId) {
    if (!personId) return "";
    const pools = [];
    const sleeper = D.sleeperSeasons?.[String(year)];
    if (sleeper) pools.push(...(sleeper.AFC || []), ...(sleeper.NFC || []));
    const mfl = D.mflSeasons?.[String(year)];
    if (mfl) pools.push(...(mfl.AFC || []), ...(mfl.NFC || []));
    pools.push(...(D.earlySeasons?.[String(year)] || []));
    const row = pools.find((item) => item.personId === personId);
    return row ? (row.avatar || row.logo || "") : "";
  }

  function podiumMarkup(year) {
    const champion = D.champions.find((item) => String(item.year) === String(year));
    if (!champion || !champion.winners?.length) return "";
    if (champion.type !== "league") {
      return `<div class="podium podium-split">${champion.winners.map((w) => `<div class="podium-slot"><span class="podium-label">${esc(w.conference)} champion</span><div class="podium-identity">${avatarMarkup(w.team || w.name, seasonLogo(year, w.personId), "podium-logo")}<div><strong>${esc(w.team || w.name)}</strong>${w.personId ? `<small>${ownerLink(w.personId, w.name)}</small>` : ""}</div></div></div>`).join("")}</div>`;
    }
    if (String(year) === "2014") {
      const founder = champion.winners[0];
      const founderPerson = person(founder.personId) || {};
      let image = seasonLogo(year, founder.personId) || founderPerson.avatar || founderPerson.image || founderPerson.logo || "";
      if (!image) {
        for (const y of ["2025", "2024", "2023", "2022", "2021", "2020", "2019", "2018", "2017"]) {
          image = seasonLogo(y, founder.personId);
          if (image) break;
        }
      }
      return `<div class="podium podium-founding">
        <span class="founding-kicker">The Founding Championship</span>
        <h3 class="founding-title">Where it all started</h3>
        <div class="founding-identity">${avatarMarkup(founder.name, image, "podium-logo")}<div><strong>${ownerLink(founder.personId, founder.name)}</strong><small>Inaugural champion · 2014</small></div></div>
        <p class="founding-lede">Ten teams. One league. One title before there was an AFC or an NFC — the season every other season descends from. The platform that hosted it is long gone; the result is permanent.</p>
        <div class="founding-facts"><span>Format<b>10-team ESPN league</b></span><span>Conferences<b>None yet</b></span><span>Championships since<b>11</b></span></div>
      </div>`;
    }
    const w = champion.winners[0];
    const r = champion.runner;
    const tag = (item) => item?.conference ? `<em>(${esc(item.conference)} winner)</em>` : "";
    return `<div class="podium">
      <div class="podium-slot champion">
        <span class="podium-label">Champion</span>
        <div class="podium-identity">${avatarMarkup(w.team || w.name, seasonLogo(year, w.personId), "podium-logo")}<div><strong>${esc(w.team || w.name)} ${tag(w)}</strong>${w.personId ? `<small>${ownerLink(w.personId, w.name)}</small>` : ""}</div></div>
      </div>
      ${r ? `<div class="podium-slot runner">
        <span class="podium-label">Runner-up</span>
        <div class="podium-identity">${avatarMarkup(r.team || r.name, seasonLogo(year, r.personId), "podium-logo")}<div><strong>${esc(r.team || r.name)} ${tag(r)}</strong>${r.personId ? `<small>${ownerLink(r.personId, r.name)}</small>` : ""}</div></div>
      </div>` : ""}
      ${champion.score ? `<span class="podium-score">${esc(champion.score)}</span>` : ""}
    </div>`;
  }

  function safeImage(raw) {
    if (!raw) return "";
    const source = String(raw).trim();
    if (/^(assets\/|\.\/assets\/)/.test(source)) return source.replace(/^\.\//, "");
    const candidate = /^https:\/\//i.test(source)
      ? source
      : `https://sleepercdn.com/avatars/thumbs/${encodeURIComponent(source)}`;
    try {
      const url = new URL(candidate);
      return url.protocol === "https:" ? url.href : "";
    } catch (error) {
      return "";
    }
  }

  function avatarMarkup(name, image, className = "team-avatar") {
    const source = safeImage(image);
    return source
      ? `<img class="${esc(className)}" src="${esc(source)}" alt="" data-name="${esc(name || "?")}" loading="lazy">`
      : `<span class="${esc(className)} avatar-placeholder" aria-hidden="true">${esc(initials(name))}</span>`;
  }

  function repairImages(container = document) {
    container.querySelectorAll("img.team-avatar, img.owner-avatar, img.owner-mention-avatar, img.season-logo, img.season-game-logo, img.podium-logo, img.player-photo").forEach((image) => {
      const repair = () => {
        const fallback = document.createElement("span");
        fallback.className = `${image.className} avatar-placeholder`;
        fallback.setAttribute("aria-hidden", "true");
        fallback.textContent = initials(image.dataset.name || image.alt || "?");
        image.replaceWith(fallback);
      };
      if (image.complete && image.naturalWidth === 0) repair();
      else if (!image.dataset.repairBound) {
        image.dataset.repairBound = "true";
        image.addEventListener("error", repair, { once: true });
      }
    });
  }

  function identityMarkup(team, personId, handle, image, size = "small") {
    const owner = displayName(personId, handle || "");
    const same = !owner || String(team).trim().toLowerCase() === owner.trim().toLowerCase();
    return `<span class="identity ${esc(size)}">
      ${avatarMarkup(team || owner, image, "team-avatar")}
      ${ownerMention(personId, team || owner || "—", { secondary: same ? "" : owner, className: "identity-owner" })}
    </span>`;
  }

  function recordText(row) {
    if (row.wins == null || row.losses == null) return "—";
    const ties = row.ties ? `–${row.ties}` : "";
    return `${row.wins}–${row.losses}${ties}`;
  }

  function table(headers, rows, className = "") {
    return `<div class="table-wrap"><table${className ? ` class="${esc(className)}"` : ""}><thead><tr>${headers.map((heading) => `<th>${esc(heading)}</th>`).join("")}</tr></thead><tbody>${rows.map((row) => `<tr>${row.map((cell) => `<td>${cell}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
  }

  function getJSON(url) {
    return fetch(url).then((response) => {
      if (!response.ok) throw new Error(`Request failed: ${response.status}`);
      return response.json();
    });
  }

  const nflStatePromise = ($("current-week") || $("transactions"))
    ? getJSON("https://api.sleeper.app/v1/state/nfl")
    : Promise.resolve({});
  const leagueContext = {};

  function getLeagueContext(conference) {
    if (leagueContext[conference]) return leagueContext[conference];
    const leagueId = D.leagueIds[conference];
    leagueContext[conference] = Promise.all([
      getJSON(`https://api.sleeper.app/v1/league/${leagueId}/users`),
      getJSON(`https://api.sleeper.app/v1/league/${leagueId}/rosters`)
    ]).then(([users, rosters]) => {
      const userMap = {};
      users.forEach((user) => {
        const metadata = user.metadata || {};
        userMap[String(user.user_id)] = {
          userId: String(user.user_id),
          team: String(metadata.team_name || user.display_name || "Unnamed team").trim(),
          handle: String(user.display_name || "").trim(),
          avatar: metadata.avatar || user.avatar || "",
          personId: personIdForUser(user.user_id) || personIdForHandle(user.display_name)
        };
      });
      const rosterMap = {};
      const rosterByPerson = {};
      rosters.forEach((roster) => {
        const user = userMap[String(roster.owner_id)] || {
          team: "Unclaimed team", handle: "", avatar: "", personId: null, userId: String(roster.owner_id || "")
        };
        const merged = { ...roster, owner: user, conference };
        rosterMap[String(roster.roster_id)] = merged;
        if (user.personId) rosterByPerson[user.personId] = merged;
      });
      return { conference, leagueId, users, rosters, userMap, rosterMap, rosterByPerson };
    });
    return leagueContext[conference];
  }

  function playerInfo(playerId) {
    const info = PLAYERS[String(playerId)] || [String(playerId), "", ""];
    const id = String(playerId);
    const position = info[1] || (/^[A-Z]{2,4}$/.test(id) ? "DEF" : "—");
    return { id, sid: id, name: info[0], position, pos: position, team: info[2] || (position === "DEF" ? id : "FA") };
  }

  function normalizedPosition(value) {
    const raw = String(value || "—").toUpperCase();
    return raw === "DEFENSE" || raw === "D/ST" ? "DEF" : raw === "PK" ? "K" : raw;
  }

  function playerPhotoUrl(player) {
    const sid = String(player?.sid || player?.id || "").trim();
    if (!sid) return "";
    const position = normalizedPosition(player?.pos || player?.position);
    if (position === "DEF") return `https://sleepercdn.com/images/team_logos/nfl/${encodeURIComponent(sid.toLowerCase())}.png`;
    return safeImage(player?.photo) || `https://sleepercdn.com/content/nfl/players/thumb/${encodeURIComponent(sid)}.jpg`;
  }

  function playerPhotoMarkup(player, className = "player-photo") {
    const name = player?.name || player?.player || player?.sid || "Player";
    const position = normalizedPosition(player?.pos || player?.position);
    const source = playerPhotoUrl(player);
    const classes = [className, position === "DEF" ? "defense-photo" : ""].filter(Boolean).join(" ");
    return source
      ? `<img class="${esc(classes)}" src="${esc(source)}" alt="" data-name="${esc(name)}" loading="lazy">`
      : `<span class="${esc(classes)} avatar-placeholder" aria-hidden="true">${esc(initials(name))}</span>`;
  }

  function renderPlayerList(ids, title) {
    return `<div class="roster-group"><h4>${esc(title)}</h4><div>${ids.length ? ids.map((id) => {
      const player = playerInfo(id);
      return `<span class="player-line">${playerPhotoMarkup(player)}<i>${esc(normalizedPosition(player.position))}</i><strong>${esc(player.name)}</strong><small>${esc(player.team)}</small></span>`;
    }).join("") : '<p class="empty-state">—</p>'}</div></div>`;
  }

  async function loadRoster(personId, conference, detail) {
    detail.innerHTML = '<div class="skeleton stack"><span></span><span></span></div>';
    try {
      const context = await getLeagueContext(conference);
      const roster = context.rosterByPerson[personId];
      if (!roster) {
        detail.innerHTML = '<p class="empty-state">Current roster is not available.</p>';
        return;
      }
      const allPlayers = roster.players || [];
      const starterSet = new Set(roster.starters || []);
      const starters = (roster.starters || []).filter(Boolean);
      const bench = allPlayers.filter((id) => !starterSet.has(id));
      detail.innerHTML = `<div class="roster-grid">${renderPlayerList(starters, "Starters")}${renderPlayerList(bench, "Bench")}</div>`;
      repairImages(detail);
    } catch (error) {
      detail.innerHTML = '<p class="error-state">Roster data is unavailable right now.</p>';
    }
  }

  function renderPowerRankings() {
    const board = $("pr-table");
    if (!board || !D.powerRankings) return;
    if ($("pr-note")) $("pr-note").textContent = `${D.powerRankings.edition} — ${D.powerRankings.note}`;
    const controls = Array.from(document.querySelectorAll("[data-power-filter]"));
    let filter = "ALL";

    function draw() {
      const source = D.powerRankings.rows.filter((row) => filter === "ALL" || row[1] === filter);
      const max = Math.max(...source.map((row) => Number(row[4]) || 0), 1);
      board.innerHTML = source.map((row, index) => {
        const [, conference, team, manager, score] = row;
        const personId = personIdForHandle(manager);
        const owner = person(personId);
        const avatar = owner?.current?.avatar || "";
        const ownerName = displayName(personId, manager);
        const width = Math.max(8, Math.round(Number(score) / max * 100));
        return `<article class="power-row" data-person="${esc(personId || "")}" data-conference="${esc(conference)}">
          <div class="power-row-main">
            <button class="power-toggle" type="button" aria-expanded="false" aria-label="Open ${esc(team)} roster"><span class="rank-number">${index + 1}</span><i aria-hidden="true">+</i></button>
            <span class="confchip ${conference.toLowerCase()}">${esc(conference)}</span>
            ${ownerLink(personId, `${team} · ${ownerName}`, "power-identity")}
            <span class="power-score">${esc(score)}</span>
            <span class="power-meter" aria-hidden="true"><i class="${conference.toLowerCase()}" style="--power:${width}%"></i></span>
          </div>
          <div class="roster-detail" hidden><p class="roster-prompt">Open to load the live roster.</p></div>
        </article>`;
      }).join("");

      board.querySelectorAll(".power-row").forEach((row) => {
        const toggle = row.querySelector(".power-toggle");
        const detail = row.querySelector(".roster-detail");
        const open = () => {
          const willOpen = detail.hidden;
          board.querySelectorAll(".roster-detail:not([hidden])").forEach((openDetail) => {
            if (openDetail !== detail) {
              openDetail.hidden = true;
              openDetail.closest(".power-row").querySelector(".power-toggle").setAttribute("aria-expanded", "false");
            }
          });
          detail.hidden = !willOpen;
          toggle.setAttribute("aria-expanded", String(willOpen));
          if (willOpen && !detail.dataset.loaded) {
            detail.dataset.loaded = "true";
            loadRoster(row.dataset.person, row.dataset.conference, detail);
          }
        };
        toggle.addEventListener("click", open);
        row.addEventListener("click", (event) => {
          if (event.target.closest("a, button") || !detail.hidden) return;
          open();
        });
      });
      repairImages(board);
    }

    controls.forEach((button) => button.addEventListener("click", () => {
      filter = button.dataset.powerFilter;
      controls.forEach((item) => {
        const active = item === button;
        item.classList.toggle("is-active", active);
        item.setAttribute("aria-pressed", String(active));
      });
      draw();
    }));
    draw();
  }

  async function renderMasthead() {
    if (!$("current-week")) return;
    $("current-season").textContent = D.currentSeason || "2026";
    try {
      const state = await nflStatePromise;
      const week = Math.max(1, Number(state.display_week || state.week || 1));
      $("current-week").textContent = week;
      $("live-label").textContent = state.season_type === "pre" ? "Preseason" : "Live";
    } catch (error) {
      $("current-week").textContent = "—";
      $("live-label").textContent = "Season";
    }
  }

  async function renderStandings(conference, elementId) {
    const element = $(elementId);
    if (!element) return;
    try {
      const context = await getLeagueContext(conference);
      const rows = Object.values(context.rosterMap).map((roster) => {
        const settings = roster.settings || {};
        return {
          owner: roster.owner,
          wins: Number(settings.wins || 0),
          losses: Number(settings.losses || 0),
          points: Number(settings.fpts || 0) + Number(settings.fpts_decimal || 0) / 100
        };
      }).sort((a, b) => b.wins - a.wins || a.losses - b.losses || b.points - a.points);
      element.innerHTML = rows.map((row, index) => `<div class="standing-row" style="--delay:${Math.min(index * 30, 300)}ms">
        <span class="standing-rank">${index + 1}</span>
        ${ownerLink(row.owner.personId, `${row.owner.team}${row.owner.personId ? ` · ${displayName(row.owner.personId, row.owner.handle)}` : row.owner.handle ? ` · ${row.owner.handle}` : ""}`, "standing-owner")}
        <strong>${row.wins}–${row.losses}</strong><span>${formatNumber(row.points, 1)}</span>
      </div>`).join("");
      repairImages(element);
    } catch (error) {
      element.innerHTML = '<p class="error-state">Live standings are unavailable right now.</p>';
    } finally {
      element.setAttribute("aria-busy", "false");
    }
  }

  async function renderMatchups(conference, elementId) {
    const element = $(elementId);
    if (!element) return;
    try {
      const [context, state] = await Promise.all([getLeagueContext(conference), nflStatePromise]);
      const week = Math.max(1, Math.min(18, Number(state.display_week || state.week || 1)));
      if ($("matchup-week")) $("matchup-week").textContent = `Week ${week}`;
      const matchups = await getJSON(`https://api.sleeper.app/v1/league/${context.leagueId}/matchups/${week}`);
      const grouped = {};
      (matchups || []).forEach((matchup) => {
        if (matchup.matchup_id == null) return;
        (grouped[matchup.matchup_id] ||= []).push(matchup);
      });
      const pairs = Object.values(grouped).filter((pair) => pair.length === 2);
      if (!pairs.length) {
        element.innerHTML = '<p class="empty-state">The Week 1 slate will appear when the schedule is set.</p>';
        return;
      }
      element.innerHTML = pairs.map((pair, index) => {
        const [left, right] = pair;
        const leftRoster = context.rosterMap[String(left.roster_id)]?.owner || {};
        const rightRoster = context.rosterMap[String(right.roster_id)]?.owner || {};
        const leftPoints = Number(left.points || 0);
        const rightPoints = Number(right.points || 0);
        const started = leftPoints > 0 || rightPoints > 0;
        return `<article class="matchup-game" style="--delay:${index * 40}ms">
          <div class="matchup-team ${started && leftPoints > rightPoints ? "winner" : ""}"><span>${ownerLink(leftRoster.personId, `${leftRoster.team || "—"}${leftRoster.personId ? ` · ${displayName(leftRoster.personId, leftRoster.handle)}` : ""}`)}</span><strong>${started ? leftPoints.toFixed(1) : "—"}</strong></div>
          <span class="matchup-vs">VS</span>
          <div class="matchup-team right ${started && rightPoints > leftPoints ? "winner" : ""}"><span>${ownerLink(rightRoster.personId, `${rightRoster.team || "—"}${rightRoster.personId ? ` · ${displayName(rightRoster.personId, rightRoster.handle)}` : ""}`)}</span><strong>${started ? rightPoints.toFixed(1) : "—"}</strong></div>
        </article>`;
      }).join("");
      repairImages(element);
    } catch (error) {
      element.innerHTML = '<p class="error-state">Live matchups are unavailable right now.</p>';
    } finally {
      element.setAttribute("aria-busy", "false");
    }
  }

  function transactionPlayers(players) {
    return players.map((playerId) => {
      const player = playerInfo(playerId);
      return `<span class="transaction-player">${playerPhotoMarkup(player, "player-photo player-photo-compact")}<b>${esc(player.name)}</b></span>`;
    }).join("");
  }

  async function renderTransactions() {
    const element = $("transactions");
    if (!element) return;
    try {
      const state = await nflStatePromise;
      const week = Math.max(1, Math.min(18, Number(state.display_week || state.week || 1)));
      const weeks = week > 1 ? [week, week - 1] : [week];
      const contexts = await Promise.all([getLeagueContext("AFC"), getLeagueContext("NFC")]);
      const requests = contexts.flatMap((context) => weeks.map((targetWeek) =>
        getJSON(`https://api.sleeper.app/v1/league/${context.leagueId}/transactions/${targetWeek}`)
          .then((transactions) => ({ context, targetWeek, transactions }))
      ));
      const settled = await Promise.allSettled(requests);
      const moves = settled.flatMap((result) => result.status === "fulfilled"
        ? (result.value.transactions || []).map((transaction) => ({ ...transaction, _context: result.value.context, _week: result.value.targetWeek }))
        : []
      ).sort((a, b) => Number(b.created || 0) - Number(a.created || 0)).slice(0, 14);
      if (!moves.length) {
        element.innerHTML = '<p class="empty-state">No moves this week.</p>';
        return;
      }
      element.innerHTML = moves.map((move) => {
        const context = move._context;
        const rosterIds = move.roster_ids || [];
        const primary = context.rosterMap[String(rosterIds[0])]?.owner || {};
        const adds = Object.keys(move.adds || {});
        const drops = Object.keys(move.drops || {});
        const type = String(move.type || "move").replace("free_agent", "free agent");
        let heading = ownerLink(primary.personId, teamOwnerLabel(primary.team, primary.personId, primary.handle || "League move"));
        let detail = "";
        if (move.type === "trade") {
          const teams = rosterIds.map((id) => context.rosterMap[String(id)]?.owner).filter(Boolean);
          heading = teams.map((team) => ownerLink(team.personId, teamOwnerLabel(team.team, team.personId, team.handle))).join(' <span aria-hidden="true">↔</span> ');
          detail = transactionPlayers([...adds, ...drops].filter((id, index, all) => all.indexOf(id) === index));
        } else {
          detail = `${adds.length ? `<b>Add</b>${transactionPlayers(adds)}` : ""}${drops.length ? `<b>Drop</b>${transactionPlayers(drops)}` : ""}`;
        }
        const bid = move.settings?.waiver_bid;
        return `<article class="transaction"><header><span class="confchip ${context.conference.toLowerCase()}">${context.conference}</span><strong>${heading}</strong><small>W${move._week}</small></header><p>${detail || "—"}</p><footer><span>${esc(type)}</span>${bid != null ? `<strong>$${esc(bid)} FAAB</strong>` : ""}</footer></article>`;
      }).join("");
    } catch (error) {
      element.innerHTML = '<p class="error-state">Transactions are unavailable right now.</p>';
    } finally {
      element.setAttribute("aria-busy", "false");
    }
  }

  function wireTabs(groupId) {
    const group = $(groupId);
    if (!group) return;
    const buttons = Array.from(group.querySelectorAll("button[data-panel-target]"));
    buttons.forEach((button) => button.addEventListener("click", () => {
      buttons.forEach((item) => {
        const active = item === button;
        item.classList.toggle("is-active", active);
        item.setAttribute("aria-pressed", String(active));
        const panel = $(item.dataset.panelTarget);
        if (panel) panel.hidden = !active;
      });
    }));
  }

  function renderTimeline() {
    const element = $("timeline");
    if (!element) return;
    element.innerHTML = D.eras.map((era) => `<article class="era"><strong>${esc(era.years)}</strong><span>${esc(era.platform)}</span><p>${esc(era.note)}</p></article>`).join("");
  }

  function championPerson(item) {
    if (!item) return "—";
    if (!item.personId) return esc(item.team || "—");
    const label = item.team ? `${item.name} — ${item.team}` : item.name;
    return ownerLink(item.personId, label);
  }

  function renderChampions() {
    const wall = $("champ-list");
    if (!wall) return;
    wall.innerHTML = D.champions.slice().reverse().map((champion) => {
      const conference = champion.type === "conference";
      const winners = conference
        ? champion.winners.map((winner) => `<div class="crown-row ${winner.conference.toLowerCase()}"><span class="confchip ${winner.conference.toLowerCase()}">${esc(winner.conference)}</span><strong>${championPerson(winner)}</strong></div>`).join("")
        : `<h3>${championPerson(champion.winners[0])}</h3>`;
      const result = !conference && champion.runner
        ? `<p>Def. ${championPerson(champion.runner)}${champion.score ? ` · ${esc(champion.score)}` : ""}</p>`
        : "";
      return `<article class="champion-card ${conference ? "conference-crowns" : "league-crown"}"><div class="champion-year">${esc(champion.year)}</div><div class="champion-body"><span class="champion-label">${conference ? "Conference champions" : "League champion"}</span>${winners}${result}<small>${esc(champion.note)}</small></div></article>`;
    }).join("");
  }

  const aliasToPerson = {};
  Object.values(people).forEach((owner) => {
    [owner.name, owner.handle].filter(Boolean).forEach((alias) => { aliasToPerson[alias.toLowerCase()] = owner.id; });
  });
  const aliasPattern = Object.keys(aliasToPerson)
    .sort((a, b) => b.length - a.length)
    .map((alias) => alias.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  const aliasRegex = aliasPattern.length ? new RegExp(`(${aliasPattern.join("|")})`, "gi") : null;

  function linkifyText(text) {
    if (!aliasRegex) return esc(text);
    return String(text).split(aliasRegex).map((part) => {
      const personId = aliasToPerson[part.toLowerCase()];
      return personId ? ownerLink(personId, part) : esc(part);
    }).join("");
  }

  function renderRecords() {
    const cards = $("record-cards");
    if (!cards) return;
    cards.innerHTML = D.records.map((record) => `<article class="record-card"><span>League file</span><h3>${linkifyText(record.title)}</h3><p>${linkifyText(record.body)}</p></article>`).join("");
  }

  function renderMarks() {
    if (!$("marks-top") || !D.marks) return;
    const scoreRows = (rows) => rows.map((row) => [
      `<strong>${Number(row.score).toFixed(2)}</strong>`,
      ownerLink(row.personId, teamOwnerLabel(row.team, row.personId)),
      `${esc(row.year)} · W${esc(row.week)} · ${esc(row.platform)}`
    ]);
    $("marks-top").innerHTML = table(["Score", "Team · Owner", "When"], scoreRows(D.marks.top));
    $("marks-low").innerHTML = table(["Score", "Team · Owner", "When"], scoreRows(D.marks.low));
    $("marks-blow").innerHTML = table(["Winner", "Loser", "When", "Margin"], D.marks.blowouts.map((row) => [
      `${ownerLink(row.winnerPersonId, teamOwnerLabel(row.winner, row.winnerPersonId))} <strong>${Number(row.winnerScore).toFixed(1)}</strong>`,
      `${ownerLink(row.loserPersonId, teamOwnerLabel(row.loser, row.loserPersonId))} ${Number(row.loserScore).toFixed(1)}`,
      `${esc(row.year)} · W${esc(row.week)}`,
      `<strong>+${Number(row.margin).toFixed(1)}</strong>`
    ]));
    const top = D.marks.top[0];
    if (top) {
      $("mark-record-score").textContent = Number(top.score).toFixed(2);
      $("mark-record-team").innerHTML = ownerLink(top.personId, teamOwnerLabel(top.team, top.personId));
      $("mark-record-detail").textContent = `${top.year} · Week ${top.week} · ${top.platform}`;
    }
  }

  function seasonChampion(year) {
    const champion = D.champions.find((item) => String(item.year) === String(year));
    if (!champion) return "—";
    return champion.winners.map(championPerson).join(" · ");
  }

  function archiveRows(rows, imageKey) {
    return rows.map((row, index) => [
      esc(row.rank || row.conferenceRank || index + 1),
      identityMarkup(row.team, row.personId, row.handle, row[imageKey] || row.logo),
      esc(recordText(row)),
      row.pf == null ? "—" : formatNumber(row.pf, 1),
      row.pa == null ? "—" : formatNumber(row.pa, 1),
      `<span class="finish ${row.champion ? "champion" : ""}">${esc(row.finish || "—")}</span>`
    ]);
  }

  function renderSeasons() {
    const stack = $("season-list");
    if (!stack) return;
    const seasons = [];
    ["2025", "2024", "2023", "2022"].forEach((year) => {
      const data = D.sleeperSeasons[year];
      if (!data) return;
      seasons.push({ year, platform: "Sleeper", champion: seasonChampion(year), body: `<div class="season-columns"><div><h4 class="afc-text">AFC standings</h4>${table(["#", "Team · Owner", "Record", "PF", "PA", "Finish"], archiveRows(data.AFC, "avatar"))}</div><div><h4 class="nfc-text">NFC standings</h4>${table(["#", "Team · Owner", "Record", "PF", "PA", "Finish"], archiveRows(data.NFC, "avatar"))}</div></div>` });
    });
    ["2021", "2020", "2019", "2018", "2017"].forEach((year) => {
      const data = D.mflSeasons[year];
      if (!data) return;
      seasons.push({ year, platform: "MyFantasyLeague", champion: seasonChampion(year), body: `<div class="season-columns"><div><h4 class="afc-text">AFC standings</h4>${table(["#", "Team · Owner", "Record", "PF", "PA", "Finish"], archiveRows(data.AFC, "logo"))}</div><div><h4 class="nfc-text">NFC standings</h4>${table(["#", "Team · Owner", "Record", "PF", "PA", "Finish"], archiveRows(data.NFC, "logo"))}</div></div>` });
    });
    ["2016", "2015", "2014"].forEach((year) => {
      const rows = (D.earlySeasons[year] || []).slice().sort((a, b) => (b.wins ?? -1) - (a.wins ?? -1) || displayName(a.personId).localeCompare(displayName(b.personId)));
      const facts = D.recon?.[`y${year}`]?.facts || [];
      seasons.push({ year, platform: year === "2015" ? "RT Sports" : "ESPN", champion: seasonChampion(year), body: `${String(year) === "2014" ? "" : table(["Team · Owner", "Conf.", "Record", "Finish"], rows.map((row) => [identityMarkup(row.team, row.personId, "", row.logo), esc(row.conference || "—"), esc(recordText(row)), `<span class="finish ${row.champion ? "champion" : ""}">${esc(row.finish || "—")}</span>`]))}${facts.length ? `<ul class="fact-list">${facts.map((fact) => `<li>${linkifyText(fact)}</li>`).join("")}</ul>` : ""}` });
    });
    stack.innerHTML = seasons.map((season, index) => `<article class="season-card-wrap"><details class="season-card${String(season.year) === "2014" ? " season-card-founding" : ""}"${index === 0 ? " open" : ""}><summary><strong>${esc(season.year)}</strong><span>${esc(season.platform)}</span><div><small>Champion</small><p>${season.champion}</p></div><i aria-hidden="true">+</i></summary><div class="season-body">${podiumMarkup(season.year)}${season.body}</div></details><a class="season-card-link" href="season.html?year=${encodeURIComponent(season.year)}">Week by week →</a></article>`).join("");
    repairImages(stack);
    // Deep link: archive.html#2014 opens that season and scrolls to it.
    const hashYear = (location.hash || "").replace("#", "");
    if (/^20\d\d$/.test(hashYear)) {
      const target = [...stack.querySelectorAll("details.season-card")].find((card) => (card.querySelector("summary")?.textContent || "").includes(hashYear));
      if (target) {
        stack.querySelectorAll("details.season-card").forEach((card) => { card.open = card === target; });
        requestAnimationFrame(() => target.scrollIntoView({ block: "start" }));
      }
    }
  }

  function renderOwnerGrid() {
    const list = $("owner-grid");
    if (!list) return;
    const search = $("owner-search");
    const sortButtons = Array.from(document.querySelectorAll("[data-owner-sort]"));
    const activeToggle = $("owner-active-only");
    let sortMode = "winpct";
    let activeOnly = false;
    const isActive = (owner) => owner.current?.year === String(D.currentSeason);
    const played = (owner) => owner.seasons.filter((season) => season.wins != null && (season.wins + season.losses) > 0).length;

    function draw() {
      const query = search.value.trim().toLowerCase();
      const owners = Object.values(people).filter((owner) => {
        if (activeOnly && !isActive(owner)) return false;
        const haystack = [owner.name, owner.handle, ...owner.seasons.map((season) => season.team)].join(" ").toLowerCase();
        return !query || haystack.includes(query);
      });
      const games = (owner) => owner.summary.wins + owner.summary.losses + (owner.summary.ties || 0);
      const qualified = (owner) => games(owner) >= 26; // roughly two full seasons
      const byWinPct = (a, b) => (Number(qualified(b)) - Number(qualified(a))) || (b.summary.winPct - a.summary.winPct) || (b.summary.wins - a.summary.wins) || a.name.localeCompare(b.name);
      owners.sort((a, b) => {
        if (sortMode === "az") return a.name.localeCompare(b.name);
        if (sortMode === "titles") return (b.summary.titles - a.summary.titles) || (b.summary.conferenceTitles - a.summary.conferenceTitles) || byWinPct(a, b);
        if (sortMode === "wins") return (b.summary.wins - a.summary.wins) || byWinPct(a, b);
        return byWinPct(a, b);
      });
      const header = `<div class="owner-row owner-row-head" role="row"><span>#</span><span>Owner</span><span class="col-conf">Conf.</span><span class="col-seasons">Seasons</span><span>Record</span><span>Win %</span><span class="col-pf">PF</span><span>Titles</span></div>`;
      list.innerHTML = owners.length ? header + owners.map((owner, index) => {
        const current = owner.current || {};
        const active = isActive(owner);
        const s = owner.summary;
        const pct = (s.wins + s.losses) ? `${(s.winPct * 100).toFixed(1)}%` : "—";
        const titleMark = s.titles ? `<strong>${s.titles}</strong>` : `<span class="muted">0</span>`;
        return `<a class="owner-row ${active ? "" : "is-alumni"}" role="row" href="owner.html?id=${encodeURIComponent(owner.id)}">
          <span class="owner-rank">${index + 1}</span>
          ${ownerMention(owner.id, owner.name, { link: false, secondary: active ? (current.team || owner.handle || "") : (owner.handle || "Alumni"), className: "owner-identity", avatarClass: "owner-avatar" })}
          <span class="col-conf">${active && current.conference ? `<span class="confchip ${current.conference.toLowerCase()}">${esc(current.conference)}</span>` : `<span class="confchip alumni">Alumni</span>`}</span>
          <span class="col-seasons">${played(owner)}</span>
          <span class="owner-record">${s.wins}–${s.losses}${s.ties ? `–${s.ties}` : ""}</span>
          <span class="owner-pct">${pct}${qualified(owner) ? "" : '<small class="unranked">under 2 seasons</small>'}</span>
          <span class="col-pf">${s.pf ? formatNumber(s.pf, 0) : "—"}</span>
          <span class="owner-titles">${titleMark}${s.conferenceTitles ? `<small>${s.conferenceTitles} conf.</small>` : ""}</span>
          <span class="owner-row-chevron" aria-hidden="true">›</span>
        </a>`;
      }).join("") : '<p class="empty-state owner-empty">No owners match this view.</p>';
      repairImages(list);
    }
    search.addEventListener("input", draw);
    sortButtons.forEach((button) => button.addEventListener("click", () => {
      sortMode = button.dataset.ownerSort;
      sortButtons.forEach((item) => { const on = item === button; item.classList.toggle("is-active", on); item.setAttribute("aria-pressed", String(on)); });
      draw();
    }));
    if (activeToggle) activeToggle.addEventListener("click", () => {
      activeOnly = !activeOnly;
      activeToggle.classList.toggle("is-active", activeOnly);
      activeToggle.setAttribute("aria-pressed", String(activeOnly));
      draw();
    });
    draw();
  }

  function renderPlayers() {
    const rankingsRoot = $("player-rankings");
    if (!rankingsRoot) return;
    const headlinesRoot = $("player-headlines");
    const search = $("player-search");
    const scopeButtons = Array.from(document.querySelectorAll("[data-player-scope]"));
    const boardButtons = Array.from(document.querySelectorAll("[data-player-board]"));
    const glossary = $("player-glossary");
    let board = "points";
    let scope = "skill";
    let playerData = null;

    const boardMeta = {
      points: {
        label: "Starter points",
        value: (player) => Number(player.pts || 0),
        format: (player) => formatNumber(player.pts, 1),
        support: (player) => [`${player.starts} starts`, `${player.weeks} roster weeks`],
        glossary: "Points = fantasy points scored while in a starting lineup, 2017–2025."
      },
      winShares: {
        label: "Win share",
        value: (player) => Number(player.winShare || 0),
        format: (player) => formatNumber(player.winShare, 3),
        support: (player) => [`${player.winsContributed} winning weeks`, `${formatNumber(player.pts, 1)} starter pts`],
        glossary: "Win share = share of a winning team’s points that week, summed."
      },
      playoffRosters: {
        label: "Playoff weeks",
        value: (player) => Number(player.playoffWeeks || 0),
        format: (player) => String(player.playoffWeeks || 0),
        support: (player) => [`${player.owners} owners`, `${formatNumber(player.pts, 1)} starter pts`],
        glossary: "Playoff weeks = roster appearances in weeks 14+."
      },
      mostOwners: {
        label: "Distinct owners",
        value: (player) => Number(player.owners || 0),
        format: (player) => String(player.owners || 0),
        support: (player) => [`${player.weeks} roster weeks`, `${player.tx?.total || 0} transactions`],
        glossary: "Owners = distinct owners from 2017–2025."
      },
      mostTransactions: {
        label: "Transactions",
        value: (player) => Number(player.tx?.total || 0),
        format: (player) => String(player.tx?.total || 0),
        support: (player) => [`${player.tx?.adds || 0} adds · ${player.tx?.drops || 0} drops`, `${player.tx?.waivers || 0} waivers · ${player.tx?.trades || 0} trades`],
        glossary: "Transactions = recorded adds, drops, waiver claims, and trades, summed."
      },
      mostWeeks: {
        label: "Roster weeks",
        value: (player) => Number(player.weeks || 0),
        format: (player) => String(player.weeks || 0),
        support: (player) => [`${player.starts} starts`, `${player.owners} owners`],
        glossary: "Most weeks = total weekly roster appearances from 2017–2025."
      }
    };

    const isSkillPlayer = (player) => !["K", "DEF"].includes(normalizedPosition(player?.pos));
    const seasonsSpan = (player) => {
      const years = (player.seasons || []).map(String).sort();
      if (!years.length) return "—";
      return years.length === 1 ? years[0] : `${years[0]}–${years[years.length - 1]}`;
    };

    function ownerTrailMarkup(player) {
      const best = player.best || {};
      const bestOwner = best.ownerId ? person(best.ownerId) : null;
      const owners = (player.ownerIds || []).map((ownerId) => {
        const owner = person(ownerId);
        if (!owner) return "";
        return ownerMention(owner.id, owner.name, { secondary: owner.current?.team || owner.handle || "—", className: "player-trail-owner", avatarClass: "team-avatar" });
      }).filter(Boolean).join("");
      return `<div class="player-detail-grid">
        <section><span class="player-detail-label">Who owned him</span><div class="player-owner-trail">${owners || '<span class="player-detail-empty">No ownership stops recorded</span>'}</div></section>
        <section class="player-best-week"><span class="player-detail-label">Best week</span><strong>${best.pts == null ? "—" : `${seasonScore(best.pts)} pts`}</strong><small>${best.year ? `${esc(best.year)} · Week ${esc(best.week)}` : "No starter week"}</small>${bestOwner ? ownerMention(bestOwner.id, bestOwner.name, { secondary: bestOwner.current?.team || bestOwner.handle || "—", className: "player-best-owner", avatarClass: "team-avatar" }) : ""}</section>
        <section class="player-career-span"><span class="player-detail-label">Seasons</span><strong>${esc(seasonsSpan(player))}</strong><small>${(player.seasons || []).length} season${(player.seasons || []).length === 1 ? "" : "s"} represented</small></section>
        <section class="player-transaction-breakdown"><span class="player-detail-label">Transaction breakdown</span><div><span><b>${player.tx?.adds || 0}</b>Adds</span><span><b>${player.tx?.drops || 0}</b>Drops</span><span><b>${player.tx?.waivers || 0}</b>Waivers</span><span><b>${player.tx?.trades || 0}</b>Trades</span></div></section>
      </div>`;
    }

    function headlineCard(player, label, metric, note, boardName) {
      if (!player) return "";
      return `<button class="player-headline-card" type="button" data-headline-board="${esc(boardName)}">${playerPhotoMarkup(player, "player-photo player-headline-photo")}<span class="player-headline-copy"><span>${esc(label)}</span><strong class="player-headline-name">${esc(player.name)}</strong><span class="player-headline-stat"><b>${esc(metric)}</b>${esc(note)}</span><small>${esc(normalizedPosition(player.pos))} · ${esc(seasonsSpan(player))}</small></span></button>`;
    }

    function drawHeadlines() {
      const players = playerData.players || {};
      const lists = playerData.lists || {};
      const points = players[lists.points?.[0]];
      const owners = players[lists.mostOwnersSkill?.[0]];
      const playoffs = players[lists.playoffRosters?.[0]];
      const shares = players[lists.winShares?.[0]];
      headlinesRoot.innerHTML = [
        headlineCard(points, "Most starter points", formatNumber(points?.pts, 1), " points", "points"),
        headlineCard(owners, "Most owners", String(owners?.owners || 0), " different teams", "mostOwners"),
        headlineCard(playoffs, "Most playoff weeks", String(playoffs?.playoffWeeks || 0), " roster appearances", "playoffRosters"),
        headlineCard(shares, "Top win share", formatNumber(shares?.winShare, 3), " summed share", "winShares")
      ].join("");
      headlinesRoot.setAttribute("aria-busy", "false");
      repairImages(headlinesRoot);
    }

    function boardKeys() {
      const query = search.value.trim().toLowerCase();
      const meta = boardMeta[board];
      if (query) {
        return Object.values(playerData.players || {})
          .filter((player) => (scope === "all" || isSkillPlayer(player)) && `${player.name} ${normalizedPosition(player.pos)}`.toLowerCase().includes(query))
          .sort((a, b) => meta.value(b) - meta.value(a) || a.name.localeCompare(b.name))
          .map((player) => player.key);
      }
      const listName = scope === "skill" && board === "mostOwners" ? "mostOwnersSkill"
        : scope === "skill" && board === "mostTransactions" ? "mostTransactionsSkill"
          : board;
      return (playerData.lists?.[listName] || []).filter((key) => scope === "all" || isSkillPlayer(playerData.players?.[key]));
    }

    function drawBoard() {
      const meta = boardMeta[board];
      const keys = boardKeys();
      glossary.textContent = meta.glossary;
      rankingsRoot.innerHTML = keys.length ? keys.map((key, index) => {
        const player = playerData.players[key];
        const detailId = `player-detail-${index}`;
        const support = meta.support(player);
        return `<article class="player-ranking" data-player-key="${esc(key)}">
          <button class="player-ranking-toggle" type="button" aria-expanded="false" aria-controls="${detailId}">
            <span class="player-ranking-number">${index + 1}</span>
            ${playerPhotoMarkup(player, "player-photo player-ranking-photo")}
            <span class="player-ranking-name"><span class="position-badge pos-${esc(normalizedPosition(player.pos).toLowerCase())}">${esc(normalizedPosition(player.pos))}</span><strong>${esc(player.name)}</strong><small>${support.map(esc).join(" · ")}</small></span>
            <span class="player-ranking-metric"><strong>${esc(meta.format(player))}</strong><small>${esc(meta.label)}</small></span>
            <i aria-hidden="true">+</i>
          </button>
          <div class="player-ranking-detail" id="${detailId}" hidden>${ownerTrailMarkup(player)}</div>
        </article>`;
      }).join("") : '<p class="history-empty">No players match this view.</p>';
      rankingsRoot.setAttribute("aria-busy", "false");
      repairImages(rankingsRoot);
    }

    function selectBoard(nextBoard) {
      board = nextBoard;
      boardButtons.forEach((button) => {
        const active = button.dataset.playerBoard === board;
        button.classList.toggle("is-active", active);
        button.setAttribute("aria-selected", String(active));
        button.tabIndex = active ? 0 : -1;
      });
      drawBoard();
    }

    boardButtons.forEach((button, index) => {
      button.addEventListener("click", () => selectBoard(button.dataset.playerBoard));
      button.addEventListener("keydown", (event) => {
        if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
        event.preventDefault();
        const next = event.key === "Home" ? 0 : event.key === "End" ? boardButtons.length - 1 : (index + (event.key === "ArrowRight" ? 1 : -1) + boardButtons.length) % boardButtons.length;
        boardButtons[next].click();
        boardButtons[next].focus();
      });
    });
    scopeButtons.forEach((button) => button.addEventListener("click", () => {
      scope = button.dataset.playerScope;
      scopeButtons.forEach((item) => {
        const active = item === button;
        item.classList.toggle("is-active", active);
        item.setAttribute("aria-pressed", String(active));
      });
      drawBoard();
    }));
    search.addEventListener("input", drawBoard);
    headlinesRoot.addEventListener("click", (event) => {
      const card = event.target.closest("[data-headline-board]");
      if (!card) return;
      selectBoard(card.dataset.headlineBoard);
      $("player-board-title")?.scrollIntoView({ block: "start" });
    });
    rankingsRoot.addEventListener("click", (event) => {
      const button = event.target.closest(".player-ranking-toggle");
      if (!button) return;
      const detail = $(button.getAttribute("aria-controls"));
      const willOpen = detail.hidden;
      rankingsRoot.querySelectorAll(".player-ranking-detail:not([hidden])").forEach((openDetail) => {
        openDetail.hidden = true;
        openDetail.closest(".player-ranking")?.querySelector(".player-ranking-toggle")?.setAttribute("aria-expanded", "false");
      });
      detail.hidden = !willOpen;
      button.setAttribute("aria-expanded", String(willOpen));
    });

    getJSON("players/index.json").then((loaded) => {
      if (!loaded?.players || !loaded?.lists) throw new Error("Invalid player index");
      playerData = loaded;
      drawHeadlines();
      drawBoard();
    }).catch(() => {
      headlinesRoot.innerHTML = '<p class="history-empty">Player highlights are unavailable right now.</p>';
      rankingsRoot.innerHTML = '<p class="history-empty">Player boards are unavailable right now.</p>';
      headlinesRoot.setAttribute("aria-busy", "false");
      rankingsRoot.setAttribute("aria-busy", "false");
    });
  }

  const ownerBestWeekCache = new Map();

  function ownerPlayerKey(player) {
    return player?.key || `${String(player?.name || player?.player || "").trim().toLowerCase()}|${normalizedPosition(player?.pos)}`;
  }

  function loadOwnerSeasonBest(personId, year) {
    const cacheKey = `${personId}:${year}`;
    if (ownerBestWeekCache.has(cacheKey)) return ownerBestWeekCache.get(cacheKey);
    const request = getJSON(`seasons/${encodeURIComponent(year)}.json`).then((season) => {
      const best = new Map();
      const inspectTeam = (team, week) => {
        if (team?.personId !== personId) return;
        (team.lineup || []).filter((player) => player.starter).forEach((player) => {
          const key = ownerPlayerKey(player);
          const points = Number(player.pts || 0);
          if (!best.has(key) || points > best.get(key).pts) best.set(key, { pts: points, year: String(year), week: Number(week) });
        });
      };
      (season.weeks || []).forEach((week) => {
        (week.matchups || []).forEach((matchup) => {
          inspectTeam(matchup.home, week.week);
          inspectTeam(matchup.away, week.week);
        });
        (week.scores || []).forEach((team) => inspectTeam(team, week.week));
      });
      return best;
    }).catch(() => new Map());
    ownerBestWeekCache.set(cacheKey, request);
    return request;
  }

  function setupOwnerHistory(history, owner) {
    const root = $("owner-history-content");
    if (!root || history.personId !== owner.id) return;
    const years = (history.seasons || []).map(String);
    const draftYears = Object.keys(history.drafts || {}).sort((a, b) => Number(b) - Number(a));
    const positions = ["QB", "RB", "WR", "TE", "K", "DEF"];
    let year = "ALL";
    let playerSearch = "";
    let playerPosition = "ALL";
    let sortKey = "pts";
    let sortDirection = "desc";
    let draftYear = draftYears[0] || "";
    let selectedBest = null;

    root.innerHTML = `<div class="history-controls">
      <label class="history-season-picker" for="history-season"><span>History season</span><select id="history-season"><option value="ALL">All-time</option>${years.map((item) => `<option value="${esc(item)}">${esc(item)}</option>`).join("")}</select></label>
      <nav class="history-anchor-nav" aria-label="Team history sections"><a href="#hall-of-fame">Hall of Fame</a><a href="#most-rostered">Most Rostered</a><a href="#top-scorers">Top Scorers</a><a href="#draft-history">Draft History</a></nav>
    </div>
    <div class="owner-signature" id="owner-signature" aria-live="polite"></div>
    <section class="history-section" id="hall-of-fame" aria-labelledby="hall-of-fame-title"><header><div><p class="section-kicker">The inner circle</p><h3 id="hall-of-fame-title">Hall of Fame</h3></div><span class="panel-status" id="hof-context">All-time</span></header><div class="hall-grid" id="owner-hof"></div></section>
    <section class="history-section" id="most-rostered" aria-labelledby="most-rostered-title"><header><div><p class="section-kicker">Loyalty ledger</p><h3 id="most-rostered-title">Most Rostered</h3></div><span class="panel-status" id="rostered-context">All-time</span></header><div class="loyalty-list" id="owner-loyalty"></div></section>
    <section class="history-section" id="top-scorers" aria-labelledby="top-scorers-title"><header><div><p class="section-kicker">Every contributor</p><h3 id="top-scorers-title">Top Scorers</h3></div><span class="panel-status" id="scorers-count"></span></header>
      <div class="scorer-tools"><label class="search-field"><span>Search players</span><input id="player-history-search" type="search" placeholder="Player name" autocomplete="off"></label><div class="position-filters" id="player-position-filter" role="group" aria-label="Filter players by position"><button class="is-active" type="button" data-player-position="ALL" aria-pressed="true">All</button>${positions.map((position) => `<button type="button" data-player-position="${position}" aria-pressed="false">${position}</button>`).join("")}</div></div>
      <div class="history-table" id="owner-scorers"></div>
    </section>
    <section class="history-section" id="draft-history" aria-labelledby="draft-history-title"><header><div><p class="section-kicker">Draft room</p><h3 id="draft-history-title">Draft History</h3></div><span class="panel-status">Pick by pick</span></header><div class="draft-year-tabs" id="owner-draft-tabs" role="tablist" aria-label="Draft year"></div><div id="owner-drafts"></div></section>`;

    const historySeason = $("history-season");
    const hofRoot = $("owner-hof");
    const loyaltyRoot = $("owner-loyalty");
    const scorersRoot = $("owner-scorers");
    const draftTabs = $("owner-draft-tabs");
    const draftsRoot = $("owner-drafts");

    function viewPlayers() {
      return (history.players || []).map((player) => {
        if (year === "ALL") return { ...player, pos: normalizedPosition(player.pos), best: player.best || null };
        const stats = player.seasons?.[year];
        if (!stats) return null;
        return {
          ...player,
          pos: normalizedPosition(player.pos),
          pts: Number(stats.pts || 0),
          starts: Number(stats.starts || 0),
          weeks: Number(stats.weeks || 0),
          best: selectedBest?.get(ownerPlayerKey(player)) || (String(player.best?.year) === year ? player.best : null)
        };
      }).filter(Boolean);
    }

    function seasonsSpan(player) {
      const playerYears = Object.keys(player.seasons || {}).filter((item) => year === "ALL" || item === year).sort();
      if (!playerYears.length) return "—";
      return playerYears.length === 1 ? playerYears[0] : `${playerYears[0]}–${playerYears[playerYears.length - 1]}`;
    }

    function drawSignature(players) {
      const drafts = Object.entries(history.drafts || {}).filter(([draftSeason]) => year === "ALL" || draftSeason === year);
      const draftCounts = new Map();
      drafts.forEach(([, draft]) => {
        const seen = new Set();
        (draft.picks || []).forEach((pick) => {
          const key = String(pick.player || "").trim().toLowerCase();
          if (!key || seen.has(key)) return;
          seen.add(key);
          const current = draftCounts.get(key) || { name: pick.player, pos: pick.pos, sid: pick.sid, photo: pick.photo, count: 0 };
          current.count += 1;
          draftCounts.set(key, current);
        });
      });
      const drafted = [...draftCounts.values()].sort((a, b) => b.count - a.count || a.name.localeCompare(b.name))[0];
      const byPosition = new Map();
      players.forEach((player) => byPosition.set(player.pos, (byPosition.get(player.pos) || 0) + Number(player.pts || 0)));
      const totalPoints = [...byPosition.values()].reduce((sum, value) => sum + value, 0);
      const favorite = [...byPosition.entries()].sort((a, b) => b[1] - a[1])[0];
      const loyal = players.slice().sort((a, b) => Number(b.weeks || 0) - Number(a.weeks || 0) || a.name.localeCompare(b.name))[0];
      $("owner-signature").innerHTML = `<article>${drafted ? playerPhotoMarkup(drafted, "player-photo signature-photo") : '<span class="signature-photo avatar-placeholder" aria-hidden="true">—</span>'}<div><small>${year === "ALL" ? "Most drafted" : "Draft name"}</small><strong>${esc(drafted?.name || "—")}</strong><span>${drafted ? `${drafted.count} draft${drafted.count === 1 ? "" : "s"}` : "No picks"}</span></div></article>
        <article><span class="signature-position">${esc(favorite?.[0] || "—")}</span><div><small>Scoring DNA</small><strong>${esc(favorite?.[0] || "—")}</strong><span>${favorite && totalPoints ? `${Math.round(favorite[1] / totalPoints * 100)}% of starter points` : "No starter points"}</span></div></article>
        <article>${loyal ? playerPhotoMarkup(loyal, "player-photo signature-photo") : '<span class="signature-photo avatar-placeholder" aria-hidden="true">—</span>'}<div><small>Longest tenure</small><strong>${esc(loyal?.name || "—")}</strong><span>${loyal ? `${loyal.weeks} weeks · ${seasonsSpan(loyal)}` : "No roster weeks"}</span></div></article>`;
      repairImages($("owner-signature"));
    }

    function drawHall(players) {
      const rows = players.filter((player) => Number(player.pts || 0) > 0).sort((a, b) => Number(b.pts || 0) - Number(a.pts || 0) || Number(b.starts || 0) - Number(a.starts || 0)).slice(0, 12);
      $("hof-context").textContent = year === "ALL" ? "All-time" : year;
      hofRoot.innerHTML = rows.length ? rows.map((player, index) => `<article class="hall-card${index < 3 ? " is-featured" : ""}"><span class="hall-rank">${index + 1}</span>${playerPhotoMarkup(player, "player-photo hall-photo")}<div><span class="position-badge pos-${esc(player.pos.toLowerCase())}">${esc(player.pos)}</span><h4>${esc(player.name)}</h4><p><strong>${formatNumber(player.pts, 1)}</strong> pts · ${player.starts} starts</p><small>${player.best ? `Best ${seasonScore(player.best.pts)} · ${esc(player.best.year)} W${esc(player.best.week)}` : "Season high —"}</small></div></article>`).join("") : '<p class="history-empty">No starter points in this season.</p>';
      repairImages(hofRoot);
    }

    function drawLoyalty(players) {
      const rows = players.filter((player) => Number(player.weeks || 0) > 0).sort((a, b) => Number(b.weeks || 0) - Number(a.weeks || 0) || Number(b.starts || 0) - Number(a.starts || 0)).slice(0, 12);
      $("rostered-context").textContent = year === "ALL" ? "All-time" : year;
      loyaltyRoot.innerHTML = rows.length ? rows.map((player, index) => `<article><span class="loyalty-rank">${index + 1}</span>${playerPhotoMarkup(player, "player-photo loyalty-photo")}<div><span>${esc(player.pos)}</span><strong>${esc(player.name)}</strong><small>${player.weeks} weeks · ${esc(seasonsSpan(player))}</small></div></article>`).join("") : '<p class="history-empty">No roster weeks in this season.</p>';
      repairImages(loyaltyRoot);
    }

    function drawScorers(players) {
      const query = playerSearch.trim().toLowerCase();
      const rows = players.filter((player) => (playerPosition === "ALL" || player.pos === playerPosition) && (!query || player.name.toLowerCase().includes(query)));
      const valueFor = (player, key) => key === "pps" ? (player.starts ? Number(player.pts || 0) / player.starts : 0) : Number(player[key] || 0);
      rows.sort((a, b) => {
        const direction = sortDirection === "asc" ? 1 : -1;
        return (valueFor(a, sortKey) - valueFor(b, sortKey)) * direction || a.name.localeCompare(b.name);
      });
      $("scorers-count").textContent = `${rows.length} player${rows.length === 1 ? "" : "s"}`;
      const heading = (label, key) => `<th aria-sort="${sortKey === key ? (sortDirection === "asc" ? "ascending" : "descending") : "none"}"><button type="button" data-history-sort="${key}">${label}<span aria-hidden="true">${sortKey === key ? (sortDirection === "asc" ? "↑" : "↓") : "↕"}</span></button></th>`;
      scorersRoot.innerHTML = rows.length ? `<div class="table-wrap"><table><thead><tr><th>Player</th>${heading("Points", "pts")}${heading("Starts", "starts")}${heading("Pts / start", "pps")}${heading("Weeks", "weeks")}</tr></thead><tbody>${rows.map((player) => `<tr><td><span class="scorer-player">${playerPhotoMarkup(player)}<span><strong>${esc(player.name)}</strong><small>${esc(player.pos)}</small></span></span></td><td><strong>${formatNumber(player.pts, 1)}</strong></td><td>${player.starts}</td><td>${player.starts ? formatNumber(player.pts / player.starts, 1) : "—"}</td><td>${player.weeks}</td></tr>`).join("")}</tbody></table></div>` : '<p class="history-empty">No players match this view.</p>';
      repairImages(scorersRoot);
    }

    function drawDraftTabs() {
      draftTabs.innerHTML = draftYears.map((item) => `<button type="button" role="tab" data-draft-year="${esc(item)}" aria-selected="${String(item === draftYear)}" tabindex="${item === draftYear ? "0" : "-1"}" class="${item === draftYear ? "is-active" : ""}">${esc(item)}</button>`).join("");
    }

    function draftPickMarkup(pick, format) {
      const price = format === "auction" && pick.price != null ? `<b class="price-badge">$${esc(pick.price)}</b>` : "";
      return `<article class="owner-draft-pick">${playerPhotoMarkup({ name: pick.player, pos: pick.pos, sid: pick.sid, photo: pick.photo }, "player-photo draft-history-photo")}<div><span>${format === "auction" ? `Pick ${esc(pick.pick || "—")}` : `Round ${esc(pick.round || "—")}${pick.pick ? ` · Pick ${esc(pick.pick)}` : ""}`}</span><strong>${esc(pick.player || "—")}</strong><small>${esc(normalizedPosition(pick.pos))}</small></div>${price}</article>`;
    }

    function drawDraft() {
      drawDraftTabs();
      const draft = history.drafts?.[draftYear];
      if (!draft) {
        draftsRoot.innerHTML = '<p class="history-empty">No draft picks for this season.</p>';
        return;
      }
      const auction = draft.format === "auction";
      const picks = (draft.picks || []).slice().sort((a, b) => auction ? Number(b.price || 0) - Number(a.price || 0) || Number(a.pick || 0) - Number(b.pick || 0) : Number(a.round || 0) - Number(b.round || 0) || Number(a.pick || 0) - Number(b.pick || 0));
      const biggest = auction ? picks[0] : null;
      draftsRoot.innerHTML = `<div class="owner-draft-heading"><div><span class="platform-chip">${esc(draft.platform)}</span>${draft.conference ? `<span class="confchip ${String(draft.conference).toLowerCase()}">${esc(draft.conference)}</span>` : ""}</div><strong>${auction ? "Auction board" : "Snake draft"}</strong></div>
        ${biggest ? `<aside class="biggest-buy"><div><span>Biggest buy · ${esc(draftYear)}</span><strong>$${esc(biggest.price)}</strong></div>${playerPhotoMarkup({ name: biggest.player, pos: biggest.pos, sid: biggest.sid, photo: biggest.photo }, "player-photo biggest-buy-photo")}<p><b>${esc(biggest.player)}</b><small>${esc(normalizedPosition(biggest.pos))}</small></p></aside>` : ""}
        <div class="owner-draft-list ${auction ? "is-auction" : "is-snake"}">${picks.length ? picks.map((pick) => draftPickMarkup(pick, draft.format)).join("") : '<p class="history-empty">No draft picks for this season.</p>'}</div>`;
      repairImages(draftsRoot);
    }

    function drawPlayers() {
      const players = viewPlayers();
      drawSignature(players);
      drawHall(players);
      drawLoyalty(players);
      drawScorers(players);
    }

    async function selectYear(nextYear) {
      year = nextYear;
      selectedBest = null;
      if (year !== "ALL" && history.drafts?.[year]) draftYear = year;
      drawPlayers();
      drawDraft();
      if (year !== "ALL") {
        const targetYear = year;
        const best = await loadOwnerSeasonBest(owner.id, targetYear);
        if (year !== targetYear) return;
        selectedBest = best;
        drawHall(viewPlayers());
      }
    }

    historySeason.addEventListener("change", () => selectYear(historySeason.value));
    $("player-history-search").addEventListener("input", (event) => {
      playerSearch = event.target.value;
      drawScorers(viewPlayers());
    });
    $("player-position-filter").addEventListener("click", (event) => {
      const button = event.target.closest("[data-player-position]");
      if (!button) return;
      playerPosition = button.dataset.playerPosition;
      $("player-position-filter").querySelectorAll("[data-player-position]").forEach((item) => {
        const active = item === button;
        item.classList.toggle("is-active", active);
        item.setAttribute("aria-pressed", String(active));
      });
      drawScorers(viewPlayers());
    });
    scorersRoot.addEventListener("click", (event) => {
      const button = event.target.closest("[data-history-sort]");
      if (!button) return;
      const nextKey = button.dataset.historySort;
      if (sortKey === nextKey) sortDirection = sortDirection === "desc" ? "asc" : "desc";
      else {
        sortKey = nextKey;
        sortDirection = "desc";
      }
      drawScorers(viewPlayers());
    });
    draftTabs.addEventListener("click", (event) => {
      const button = event.target.closest("[data-draft-year]");
      if (!button) return;
      draftYear = button.dataset.draftYear;
      drawDraft();
    });
    draftTabs.addEventListener("keydown", (event) => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
      const buttons = Array.from(draftTabs.querySelectorAll("[data-draft-year]"));
      const current = buttons.indexOf(event.target.closest("[data-draft-year]"));
      if (current < 0) return;
      event.preventDefault();
      const next = event.key === "Home" ? 0 : event.key === "End" ? buttons.length - 1 : (current + (event.key === "ArrowRight" ? 1 : -1) + buttons.length) % buttons.length;
      buttons[next].click();
      draftTabs.querySelector(`[data-draft-year="${draftYear}"]`)?.focus();
    });

    drawPlayers();
    drawDraft();
    root.dataset.loaded = "true";
    const anchor = (location.hash || "").slice(1);
    if (["team-history", "hall-of-fame", "most-rostered", "top-scorers", "draft-history"].includes(anchor)) requestAnimationFrame(() => document.getElementById(anchor)?.scrollIntoView({ block: "start" }));
  }

  function queueOwnerHistory(personId, owner) {
    const shell = $("team-history");
    const root = $("owner-history-content");
    if (!shell || !root) return;
    let started = false;
    const start = () => {
      if (started) return;
      started = true;
      root.setAttribute("aria-busy", "true");
      getJSON(`owners/${encodeURIComponent(personId)}.json`).then((history) => setupOwnerHistory(history, owner)).catch(() => {
        root.innerHTML = '<div class="history-load-error"><strong>Team history is unavailable right now.</strong><button type="button" data-history-retry>Try again</button></div>';
        root.querySelector("[data-history-retry]")?.addEventListener("click", () => {
          started = false;
          root.innerHTML = '<div class="skeleton history-skeleton"><span></span><span></span><span></span></div>';
          start();
        });
      }).finally(() => root.setAttribute("aria-busy", "false"));
    };
    const requested = ["#team-history", "#hall-of-fame", "#most-rostered", "#top-scorers", "#draft-history"].includes(location.hash);
    if (requested) start();
    else if ("IntersectionObserver" in window) {
      const observer = new IntersectionObserver((entries) => {
        if (!entries.some((entry) => entry.isIntersecting)) return;
        observer.disconnect();
        start();
      }, { rootMargin: "900px 0px" });
      observer.observe(shell);
    } else if ("requestIdleCallback" in window) window.requestIdleCallback(start, { timeout: 1600 });
    else window.setTimeout(start, 250);
  }

  function renderOwnerProfile() {
    const root = $("owner-profile");
    if (!root) return;
    const personId = new URLSearchParams(window.location.search).get("id");
    const owner = person(personId);
    if (!owner) {
      root.innerHTML = '<div class="not-found"><p class="section-kicker">Owner profile</p><h1>Owner not found</h1><a class="button-link" href="owners.html">View all owners</a></div>';
      return;
    }
    document.title = `${owner.name} | The League 2K`;
    const current = owner.current || {};
    const summary = owner.summary;
    const years = [...new Set(owner.seasons.map((season) => season.year))];
    root.innerHTML = `<header class="profile-header">
      <div><p class="section-kicker profile-kicker">Owner career</p><div class="profile-identity">${ownerMention(owner.id, owner.name, { link: false, secondary: current.team || owner.handle || "—", className: "profile-owner-mention", avatarClass: "owner-avatar profile-avatar", primaryTag: "h1" })}<div class="profile-chips">${current.conference ? `<span class="confchip ${current.conference.toLowerCase()}">${esc(current.conference)}</span>` : ""}${owner.handle && owner.handle !== owner.name ? `<span class="handle-chip">@${esc(owner.handle)}</span>` : ""}</div></div></div>
      <a class="back-link" href="owners.html">All owners →</a>
    </header>
    <div class="summary-grid">
      <article><small>Overall record</small><strong>${summary.wins}–${summary.losses}${summary.ties ? `–${summary.ties}` : ""}</strong></article>
      <article><small>Win percentage</small><strong>${(summary.winPct * 100).toFixed(1)}%</strong></article>
      <article><small>Total PF</small><strong>${formatNumber(summary.pf, 1)}</strong></article>
      <article class="gold-stat"><small>League titles</small><strong>${summary.titles}</strong></article>
      <article><small>Conference titles</small><strong>${summary.conferenceTitles}</strong></article>
      <article><small>Playoff appearances</small><strong>${summary.playoffAppearances}</strong></article>
      <article><small>Best season</small><strong>${summary.bestSeason ? `${esc(summary.bestSeason.year)} · ${esc(summary.bestSeason.record)}` : "—"}</strong></article>
    </div>
    <section class="profile-section" aria-labelledby="career-seasons"><div class="profile-section-heading"><div><p class="section-kicker">Career log</p><h2 id="career-seasons">Season by season</h2></div><div class="season-filters"><label>Year<select id="owner-year"><option value="ALL">All years</option>${years.map((year) => `<option value="${esc(year)}">${esc(year)}</option>`).join("")}</select></label><div class="segmented" id="era-filter" role="group" aria-label="Filter career seasons"><button class="is-active" type="button" data-era-filter="ALL" aria-pressed="true">All eras</button><button type="button" data-era-filter="Sleeper" aria-pressed="false">Sleeper</button><button type="button" data-era-filter="MFL" aria-pressed="false">MFL</button><button type="button" data-era-filter="Early" aria-pressed="false">Early</button></div></div></div><div class="career-table" id="career-table"></div></section>
    <section class="profile-section team-history-shell" id="team-history" aria-labelledby="team-history-title"><div class="profile-section-heading"><div><p class="section-kicker">Lineup era · 2017 onward</p><h2 id="team-history-title">Team History</h2><p class="section-intro">The players, draft choices, scoring fingerprints, and long-term favorites that define this roster.</p></div><span class="panel-status">Starter points · roster weeks</span></div><div id="owner-history-content" aria-busy="true"><div class="skeleton history-skeleton"><span></span><span></span><span></span></div></div></section>
    <section class="profile-section" aria-labelledby="h2h-title"><div class="profile-section-heading"><div><p class="section-kicker">Head to head</p><h2 id="h2h-title">Every opponent</h2></div><span class="panel-status">Regular season · playoffs</span></div><div class="h2h-highlights" id="owner-h2h-highlights"></div><div class="h2h-list" id="owner-h2h"></div><button class="toggle-chip h2h-toggle" type="button" id="owner-h2h-toggle" aria-expanded="false" hidden>Show all opponents</button></section>`;

    let eraFilter = "ALL";
    const yearSelect = $("owner-year");
    const eraButtons = Array.from(document.querySelectorAll("[data-era-filter]"));
    function drawCareer() {
      const rows = owner.seasons.filter((season) => (yearSelect.value === "ALL" || season.year === yearSelect.value) && (eraFilter === "ALL" || season.era === eraFilter));
      $("career-table").innerHTML = table(["Year", "Platform", "Team", "Conf.", "Record", "PF", "PA", "Finish", "Season"], rows.map((season) => [
        `<strong>${esc(season.year)}</strong>`, `<span class="platform-chip">${esc(season.platform)}</span>`, identityMarkup(season.team, personId, owner.handle, season.logo), esc(season.conference || "—"), esc(recordText(season)), season.pf == null ? "—" : formatNumber(season.pf, 1), season.pa == null ? "—" : formatNumber(season.pa, 1), `<span class="finish ${season.champion ? "champion" : ""}">${esc(season.finish || "—")}</span>`, `<a class="season-row-link" href="season.html?year=${encodeURIComponent(season.year)}">View season →</a>`
      ]));
      repairImages($("career-table"));
    }
    yearSelect.addEventListener("change", drawCareer);
    eraButtons.forEach((button) => button.addEventListener("click", () => {
      eraFilter = button.dataset.eraFilter;
      eraButtons.forEach((item) => {
        const active = item === button;
        item.classList.toggle("is-active", active);
        item.setAttribute("aria-pressed", String(active));
      });
      drawCareer();
    }));
    drawCareer();

    const opponents = Object.entries(owner.h2h).map(([opponentId, stats]) => ({ owner: person(opponentId), stats })).filter((item) => item.owner).sort((a, b) => b.stats.games - a.stats.games || b.stats.playoffWins + b.stats.playoffLosses - a.stats.playoffWins - a.stats.playoffLosses || a.owner.name.localeCompare(b.owner.name));
    const hasMeeting = ({ stats }) => Number(stats.games || 0) + Number(stats.playoffWins || 0) + Number(stats.playoffLosses || 0) > 0;
    const activeOpponents = opponents.filter(hasMeeting);
    const zeroOpponents = opponents.filter((item) => !hasMeeting(item));
    const totalWins = ({ stats }) => Number(stats.wins || 0) + Number(stats.playoffWins || 0);
    const totalLosses = ({ stats }) => Number(stats.losses || 0) + Number(stats.playoffLosses || 0);
    const nemesis = activeOpponents.slice().sort((a, b) => totalLosses(b) - totalLosses(a) || totalWins(a) - totalWins(b) || a.owner.name.localeCompare(b.owner.name))[0];
    const favorite = activeOpponents.slice().sort((a, b) => totalWins(b) - totalWins(a) || totalLosses(a) - totalLosses(b) || a.owner.name.localeCompare(b.owner.name))[0];
    const rivalryHighlight = (label, item, value, singular, plural) => item ? `<article><span>${esc(label)}</span>${ownerMention(item.owner.id, item.owner.name, { secondary: item.owner.current?.team || item.owner.handle || "—", className: "h2h-highlight-owner", avatarClass: "team-avatar" })}<strong>${value(item)} ${value(item) === 1 ? singular : plural}</strong></article>` : "";
    $("owner-h2h-highlights").innerHTML = `${rivalryHighlight("Nemesis", nemesis, totalLosses, "loss", "losses")}${rivalryHighlight("Favorite victim", favorite, totalWins, "win", "wins")}`;
    const opponentRow = ({ owner: opponent, stats }) => `<div class="h2h-row">${ownerMention(opponent.id, opponent.name, { secondary: opponent.current?.team || opponent.handle || "—", className: "h2h-owner", avatarClass: "team-avatar" })}<b>${stats.games ? `${stats.wins}–${stats.losses}${stats.ties ? `–${stats.ties}` : ""}` : "—"}</b><em>${stats.games ? `${stats.games} meeting${stats.games === 1 ? "" : "s"}` : "No meetings"}${stats.playoffWins + stats.playoffLosses ? ` · Playoffs ${stats.playoffWins}–${stats.playoffLosses}` : ""}</em></div>`;
    const h2hRoot = $("owner-h2h");
    const h2hToggle = $("owner-h2h-toggle");
    let showAllOpponents = false;
    const drawOpponents = () => {
      h2hRoot.innerHTML = [...activeOpponents, ...(showAllOpponents ? zeroOpponents : [])].map(opponentRow).join("");
      h2hToggle.textContent = showAllOpponents ? "Hide zero-meeting opponents" : `Show all opponents (${zeroOpponents.length})`;
      h2hToggle.setAttribute("aria-expanded", String(showAllOpponents));
      repairImages(h2hRoot);
    };
    if (zeroOpponents.length) {
      h2hToggle.hidden = false;
      h2hToggle.addEventListener("click", () => {
        showAllOpponents = !showAllOpponents;
        drawOpponents();
      });
    }
    drawOpponents();
    repairImages(root);
    queueOwnerHistory(personId, owner);
  }

  function renderRivalries() {
    const output = $("riv-out");
    if (!output) return;
    const conference = $("riv-conf");
    const left = $("riv-a");
    const right = $("riv-b");

    function drawPickerPreview(select, targetId) {
      const target = $(targetId);
      if (!target) return;
      const selected = person(select.value);
      target.innerHTML = selected ? ownerMention(selected.id, selected.name, { secondary: selected.current?.team || selected.handle || "—", link: false, className: "picker-owner-mention" }) : "";
      repairImages(target);
    }

    function candidates() {
      if (conference.value === "ALL") return Object.values(people).filter((owner) => Object.values(owner.h2h).some((stats) => stats.games || stats.playoffWins || stats.playoffLosses));
      return (D.currentPeople[conference.value] || []).map(person).filter(Boolean);
    }

    function fill() {
      const owners = candidates().sort((a, b) => a.name.localeCompare(b.name));
      const previousLeft = left.value;
      const previousRight = right.value;
      const options = owners.map((owner) => `<option value="${esc(owner.id)}">${esc(owner.name)}${owner.current?.team && owner.current.team !== owner.name ? ` — ${esc(owner.current.team)}` : ""}</option>`).join("");
      const placeholder = '<option value="">Choose an owner…</option>';
      left.innerHTML = placeholder + options;
      right.innerHTML = placeholder + options;
      left.value = owners.some((owner) => owner.id === previousLeft) ? previousLeft : "";
      right.value = owners.some((owner) => owner.id === previousRight && owner.id !== left.value) ? previousRight : "";
      draw();
    }

    function draw() {
      const leftId = left.value;
      const rightId = right.value;
      drawPickerPreview(left, "riv-a-preview");
      drawPickerPreview(right, "riv-b-preview");
      if (!leftId || !rightId || leftId === rightId) {
        output.innerHTML = '<p class="empty-state">Pick two owners to open the tale of the tape.</p>';
        return;
      }
      const leftOwner = person(leftId);
      const rightOwner = person(rightId);
      const stats = leftOwner.h2h[rightId] || { wins: 0, losses: 0, ties: 0, games: 0, pf: 0, pa: 0 };
      const games = D.rivalry.games.filter((game) => (game.a === leftId && game.b === rightId) || (game.a === rightId && game.b === leftId));
      const playoffs = D.rivalry.playoffs.filter((game) => (game.a === leftId && game.b === rightId) || (game.a === rightId && game.b === leftId));
      const averageLeft = stats.games ? (stats.pf / stats.games).toFixed(1) : "—";
      const averageRight = stats.games ? (stats.pa / stats.games).toFixed(1) : "—";
      output.innerHTML = `<div class="tale-of-tape"><div class="fighter">${ownerMention(leftId, teamOwnerLabel(leftOwner.current?.team, leftId), { className: "fighter-owner", avatarClass: "owner-avatar" })}<span>${stats.wins} wins · ${averageLeft} avg</span></div><div class="series-score"><strong>${stats.wins}</strong><small>Series</small><strong>${stats.losses}</strong></div><div class="fighter right">${ownerMention(rightId, teamOwnerLabel(rightOwner.current?.team, rightId), { className: "fighter-owner", avatarClass: "owner-avatar" })}<span>${stats.losses} wins · ${averageRight} avg</span></div></div>
        ${playoffs.length ? `<div class="playoff-strip">${playoffs.map((game) => {
          const leftScore = game.a === leftId ? game.scoreA : game.scoreB;
          const rightScore = game.a === leftId ? game.scoreB : game.scoreA;
          return `<div><span>${esc(game.year)} · ${esc(game.round)}</span><strong>${leftScore > rightScore ? ownerLink(leftId, leftOwner.name) : ownerLink(rightId, rightOwner.name)} won</strong></div>`;
        }).join("")}</div>` : ""}
        ${games.length ? `<div class="meeting-list">${games.map((game) => {
          const leftScore = game.a === leftId ? game.scoreA : game.scoreB;
          const rightScore = game.a === leftId ? game.scoreB : game.scoreA;
          return `<div class="meeting-row"><span>${esc(game.year)} · W${esc(game.week)}<small>${esc(game.platform)}</small></span><strong class="${leftScore > rightScore ? "winner" : ""}">${Number(leftScore).toFixed(1)}</strong><i>–</i><strong class="${rightScore > leftScore ? "winner" : ""}">${Number(rightScore).toFixed(1)}</strong></div>`;
        }).join("")}</div>` : '<p class="empty-state">No regular-season meetings.</p>'}`;
      repairImages(output);
    }
    conference.addEventListener("change", fill);
    left.addEventListener("change", draw);
    right.addEventListener("change", draw);
    fill();
  }

  const seasonCache = new Map();
  const seasonYears = (Array.isArray(D.seasonYears) && D.seasonYears.length ? D.seasonYears : Array.from({ length: 9 }, (_, index) => 2025 - index)).map(String);

  function seasonScore(value) {
    const number = Number(value);
    return Number.isFinite(number) ? number.toLocaleString("en-US", {
      minimumFractionDigits: 1,
      maximumFractionDigits: 2
    }) : "—";
  }

  function seasonTeamLogo(data, personId, teamName) {
    for (const week of data.weeks || []) {
      for (const matchup of week.matchups || []) {
        for (const team of [matchup.home, matchup.away]) {
          if ((personId && team?.personId === personId) || (!personId && teamName && team?.team === teamName)) {
            if (team.logo) return team.logo;
          }
        }
      }
    }
    return seasonLogo(data.year, personId);
  }

  function seasonTeamText(team, className = "") {
    const teamName = team?.team || displayName(team?.personId, "Team");
    const ownerName = team?.personId ? displayName(team.personId, "") : "";
    const same = ownerName && teamName.trim().toLowerCase() === ownerName.trim().toLowerCase();
    return ownerMention(team?.personId, teamName, { secondary: ownerName && !same ? ownerName : "", className, withTrophy: false });
  }

  function seasonSummaryMarkup(matchups) {
    const teams = matchups.flatMap((matchup) => [matchup.home, matchup.away]).filter(Boolean);
    if (!matchups.length || !teams.length) {
      return `<article><small>Top score</small><strong>—</strong><span>No matchups this week</span></article>
        <article><small>Closest game</small><strong>—</strong><span>No result</span></article>
        <article><small>Biggest blowout</small><strong>—</strong><span>No result</span></article>
        <article><small>League average</small><strong>—</strong><span>No scores</span></article>`;
    }
    const top = teams.reduce((best, team) => Number(team.score) > Number(best.score) ? team : best);
    const margins = matchups.map((matchup) => ({ matchup, margin: Math.abs(Number(matchup.home?.score || 0) - Number(matchup.away?.score || 0)) }));
    const closest = margins.reduce((best, row) => row.margin < best.margin ? row : best);
    const blowout = margins.reduce((best, row) => row.margin > best.margin ? row : best);
    const average = teams.reduce((total, team) => total + Number(team.score || 0), 0) / teams.length;
    const pairing = ({ matchup }) => `${ownerLink(matchup.home?.personId, matchup.home?.team || "Team", "", false)} <i aria-hidden="true">vs</i> ${ownerLink(matchup.away?.personId, matchup.away?.team || "Team", "", false)}`;
    return `<article><small>Top score</small><strong>${seasonScore(top.score)}</strong>${seasonTeamText(top)}</article>
      <article><small>Closest game</small><strong>${seasonScore(closest.margin)}</strong><span>${pairing(closest)}</span></article>
      <article><small>Biggest blowout</small><strong>${seasonScore(blowout.margin)}</strong><span>${pairing(blowout)}</span></article>
      <article><small>League average</small><strong>${seasonScore(average)}</strong><span>${teams.length} team scores</span></article>`;
  }

  function seasonPlayerMarkup(player, showNflTeam = true) {
    const position = normalizedPosition(player?.pos);
    return `<div class="season-player${showNflTeam ? "" : " no-nfl-team"}">${playerPhotoMarkup(player)}<span class="position-badge pos-${esc(position.toLowerCase())}">${esc(position)}</span><strong title="${esc(player?.name || "—")}">${esc(player?.name || "—")}</strong>${showNflTeam ? `<small>${esc(player?.nfl || "FA")}</small>` : ""}<b>${seasonScore(player?.pts)}</b></div>`;
  }

  function seasonLineupMarkup(team, side, showNflTeam = true) {
    const lineup = Array.isArray(team?.lineup) ? team.lineup : [];
    const starters = lineup.filter((player) => player.starter);
    const bench = lineup.filter((player) => !player.starter);
    const starterTotal = starters.reduce((total, player) => total + Number(player.pts || 0), 0);
    return `<div class="season-lineup ${esc(side)}">
      <header>${avatarMarkup(team?.team, team?.logo, "team-avatar")}${seasonTeamText(team, "lineup-team-name")}</header>
      <div class="lineup-label"><span>Starters</span><strong>${seasonScore(starterTotal)} pts</strong></div>
      <div class="season-player-list">${starters.length ? starters.map((player) => seasonPlayerMarkup(player, showNflTeam)).join("") : '<p class="lineup-empty">No starter data</p>'}</div>
      <details class="lineup-bench"><summary>Bench <span>${bench.length}</span></summary><div class="season-player-list">${bench.length ? bench.map((player) => seasonPlayerMarkup(player, showNflTeam)).join("") : '<p class="lineup-empty">No bench data</p>'}</div></details>
    </div>`;
  }

  function seasonMatchupMarkup(matchup, gameIndex, expanded, showNflTeam = true) {
    const homeScore = Number(matchup.home?.score || 0);
    const awayScore = Number(matchup.away?.score || 0);
    const conference = String(matchup.conference || "Interconference");
    const conferenceClass = conference.toLowerCase() === "afc" ? "afc" : conference.toLowerCase() === "nfc" ? "nfc" : "interconference";
    const team = (entry, side, winner) => `<div class="season-game-team ${esc(side)}${winner ? " winner" : ""}">
      ${avatarMarkup(entry?.team, entry?.logo, "team-avatar season-game-logo")}
      ${seasonTeamText(entry, "season-game-identity")}
      <strong class="season-game-score">${seasonScore(entry?.score)}</strong>
    </div>`;
    return `<article class="season-game${expanded ? " is-expanded" : ""}" data-game-index="${gameIndex}">
      <div class="season-game-head">
        <span class="confchip ${esc(conferenceClass)}">${esc(conference)}</span>
        <span>Game ${gameIndex + 1}</span>
      </div>
      <div class="season-game-faceoff">
        ${team(matchup.home, "home", homeScore > awayScore)}
        <span class="season-game-vs" aria-hidden="true">VS</span>
        ${team(matchup.away, "away", awayScore > homeScore)}
      </div>
      <button class="season-game-toggle" type="button" aria-expanded="${String(expanded)}" aria-controls="season-lineups-${gameIndex}"><span>${expanded ? "Hide" : "View"} lineups</span><i aria-hidden="true">+</i></button>
      <div class="season-lineups" id="season-lineups-${gameIndex}"${expanded ? "" : " hidden"}>${expanded ? `${seasonLineupMarkup(matchup.home, "home", showNflTeam)}${seasonLineupMarkup(matchup.away, "away", showNflTeam)}` : ""}</div>
    </article>`;
  }

  function draftPlayerMap(data) {
    const playersByName = new Map();
    const add = (name, position, sid = "", photo = "") => {
      const key = String(name || "").trim().toLowerCase();
      if (!key) return;
      const current = playersByName.get(key) || {};
      playersByName.set(key, {
        name,
        pos: normalizedPosition(position || current.pos || ""),
        sid: String(sid || current.sid || ""),
        photo: photo || current.photo || ""
      });
    };
    Object.entries(PLAYERS).forEach(([sid, row]) => add(row?.[0], row?.[1], sid));
    (data.weeks || []).forEach((week) => (week.matchups || []).forEach((matchup) => [matchup.home, matchup.away].forEach((team) => (team?.lineup || []).forEach((player) => add(player.name, player.pos, player.sid, player.photo)))));
    return playersByName;
  }

  function draftPlayer(name, playersByName) {
    const key = String(name || "").trim().toLowerCase();
    const found = playersByName.get(key);
    if (found) return found;
    const pos = /d\/st|defense/i.test(name) ? "DEF" : /kicker/i.test(name) ? "K" : "";
    return { name, pos, sid: pos === "DEF" ? String(name).split(/\s/)[0] : "", photo: "" };
  }

  function draftBoardMarkup(board, data, boardIndex, playersByName) {
    const columns = board.columns || [];
    const rounds = Math.max(0, ...columns.map((column) => column.picks?.length || 0));
    const boardName = String(board.name || `Board ${boardIndex + 1}`).replace(/^board\s*/i, "Board ");
    const header = columns.map((column) => {
      const logo = seasonTeamLogo(data, column.personId, column.team);
      return `<th scope="col">${avatarMarkup(column.team, logo, "team-avatar")}${seasonTeamText({ team: column.team, personId: column.personId }, "draft-team-name")}</th>`;
    }).join("");
    const rows = Array.from({ length: rounds }, (_, roundIndex) => {
      const round = roundIndex + 1;
      const picks = columns.map((column, columnIndex) => {
        const playerName = column.picks?.[roundIndex] || "—";
        const player = draftPlayer(playerName, playersByName);
        const position = normalizedPosition(player.pos);
        const group = ["QB", "RB", "WR", "TE", "K", "DEF"].includes(position) ? position.toLowerCase() : "other";
        const overall = round % 2 ? roundIndex * columns.length + columnIndex + 1 : roundIndex * columns.length + (columns.length - columnIndex);
        return `<td><div class="draft-pick pos-${esc(group)}"><small>${overall}</small>${playerPhotoMarkup(player, "player-photo draft-player-photo")}<strong title="${esc(playerName)}">${esc(playerName)}</strong>${position && position !== "—" ? `<span>${esc(position)}</span>` : ""}</div></td>`;
      }).join("");
      return `<tr><th class="draft-round" scope="row"><span>Round</span><strong>${round}</strong></th>${picks}</tr>`;
    }).join("");
    return `<section class="draft-board-section"><header><p class="section-kicker">${esc(boardName)}</p><h2>${esc(data.year)} draft board</h2></header><div class="draft-board-scroll"><table class="draft-board"><caption class="sr-only">${esc(boardName)}, ${esc(data.year)} snake draft</caption><thead><tr><th class="draft-corner" scope="col">Rd.</th>${header}</tr></thead><tbody>${rows}</tbody></table></div></section>`;
  }

  function renderSeasonExplorer() {
    const yearSelect = $("season-year");
    if (!yearSelect) return;
    const title = $("season-title");
    const platform = $("season-platform");
    const championRoot = $("season-champion");
    const loading = $("season-loading");
    const errorRoot = $("season-error");
    const content = $("season-content");
    const weekStrip = $("season-week-strip");
    const summaryRoot = $("season-summary");
    const matchupsRoot = $("season-matchups");
    const weekPanel = $("season-week-panel");
    const draftPanel = $("season-draft-panel");
    const viewButtons = Array.from(document.querySelectorAll("[data-season-view]"));
    const filterButtons = Array.from(document.querySelectorAll("[data-season-filter]"));
    const initial = new URLSearchParams(window.location.search);
    const requestedYear = initial.get("year");
    let year = /^\d{4}$/.test(requestedYear || "") ? requestedYear : seasonYears[0];
    let week = Math.max(1, Number(initial.get("week")) || 1);
    let game = /^\d+$/.test(initial.get("game") || "") ? Number(initial.get("game")) : null;
    let filter = "ALL";
    let view = initial.get("view") === "draft" ? "draft" : "schedule";
    let data = null;
    let loadToken = 0;

    const pickerYears = seasonYears.includes(year) ? seasonYears : [year, ...seasonYears];
    yearSelect.innerHTML = pickerYears.map((item) => `<option value="${item}">${item}</option>`).join("");
    yearSelect.value = year;

    function replaceUrl() {
      const url = new URL(window.location.href);
      url.searchParams.set("year", year);
      url.searchParams.set("week", String(week));
      if (game == null) url.searchParams.delete("game");
      else url.searchParams.set("game", String(game));
      if (view === "draft") url.searchParams.set("view", "draft");
      else url.searchParams.delete("view");
      window.history.replaceState({}, "", url);
    }

    function getSeason(targetYear) {
      if (!seasonCache.has(targetYear)) {
        const request = getJSON(`seasons/${encodeURIComponent(targetYear)}.json`).catch((error) => {
          seasonCache.delete(targetYear);
          throw error;
        });
        seasonCache.set(targetYear, request);
      }
      return seasonCache.get(targetYear);
    }

    function renderChampion() {
      const champion = D.champions.find((item) => String(item.year) === String(data.year));
      if (!champion?.winners?.length) {
        championRoot.innerHTML = '<div><small>Season champion</small><strong>—</strong></div>';
        return;
      }
      championRoot.innerHTML = `<div><small>${champion.type === "league" ? "Season champion" : "Conference champions"}</small>${champion.winners.map((winner) => identityMarkup(winner.team || winner.name, winner.personId, winner.name, seasonTeamLogo(data, winner.personId, winner.team), "season-champion-identity")).join("")}</div>`;
      repairImages(championRoot);
    }

    function setView(nextView, update = true) {
      view = nextView;
      viewButtons.forEach((button) => {
        const active = button.dataset.seasonView === view;
        button.classList.toggle("is-active", active);
        button.setAttribute("aria-selected", String(active));
        button.tabIndex = active ? 0 : -1;
      });
      weekPanel.hidden = view !== "schedule";
      draftPanel.hidden = view !== "draft";
      if (view === "draft" && data) renderDraft();
      if (update) replaceUrl();
    }

    function renderWeekStrip() {
      const weeks = data.weeks || [];
      weekStrip.innerHTML = weeks.map((item) => {
        const active = Number(item.week) === Number(week);
        return `<button id="season-week-${esc(item.week)}" type="button" role="tab" data-season-week="${esc(item.week)}" aria-selected="${String(active)}" aria-controls="season-matchups" tabindex="${active ? "0" : "-1"}" class="${active ? "is-active" : ""}"><span>W</span>${esc(item.week)}</button>`;
      }).join("");
    }

    function selectedWeekMatchups() {
      const selected = (data.weeks || []).find((item) => Number(item.week) === Number(week));
      return (selected?.matchups || []).map((matchup, index) => ({ matchup, index }));
    }

    function seasonScoreboardMarkup(scores) {
      const rows = scores.filter((team) => filter === "ALL" || team.conference === filter).slice().sort((a, b) => Number(b.score || 0) - Number(a.score || 0));
      if (!rows.length) {
        return { summary: seasonSummaryMarkup([]), list: `<div class="season-empty"><strong>Week ${esc(week)}</strong><p>No scores are available for this view.</p></div>` };
      }
      const top = rows[0];
      const average = rows.reduce((total, team) => total + Number(team.score || 0), 0) / rows.length;
      const averageLabel = filter === "ALL" ? "League average" : `${filter} average`;
      const showNflTeam = data.platform !== "Sleeper";
      const summary = `<article><small>Top score</small><strong>${seasonScore(top.score)}</strong>${seasonTeamText(top)}</article>
        <article><small>Teams scoring</small><strong>${rows.length}</strong><span>weekly scoreboard</span></article>
        <article><small>Lowest score</small><strong>${seasonScore(rows[rows.length - 1].score)}</strong>${seasonTeamText(rows[rows.length - 1])}</article>
        <article><small>${esc(averageLabel)}</small><strong>${seasonScore(average)}</strong><span>${rows.length} team scores</span></article>`;
      const list = rows.map((team, index) => {
        const starters = (team.lineup || []).filter((player) => player.starter);
        return `<details class="season-score-row ${esc((team.conference || "").toLowerCase())}">
          <summary>
            <span class="season-score-rank">${index + 1}</span>
            ${avatarMarkup(team.team, team.logo, "season-game-logo")}
            ${seasonTeamText(team, "season-game-identity")}
            <span class="confchip ${esc((team.conference || "").toLowerCase())}">${esc(team.conference || "")}</span>
            <strong class="season-score-points">${seasonScore(team.score)}</strong>
          </summary>
          <div class="season-score-lineup">${starters.map((player) => `<span class="player-line${showNflTeam ? "" : " no-nfl-team"}">${playerPhotoMarkup(player)}<i>${esc(normalizedPosition(player.pos))}</i><strong>${esc(player.name)}</strong>${showNflTeam ? `<small>${esc(player.nfl)}</small>` : ""}<b>${seasonScore(player.pts)}</b></span>`).join("")}</div>
        </details>`;
      }).join("");
      return { summary, list: `<div class="season-scoreboard"><p class="season-scoreboard-note">Scores only — matchups weren't recorded for this week.</p>${list}</div>` };
    }

    function renderWeek() {
      renderWeekStrip();
      const allRows = selectedWeekMatchups();
      const selected = (data.weeks || []).find((item) => Number(item.week) === Number(week));
      if (!allRows.length && selected?.scores?.length) {
        const board = seasonScoreboardMarkup(selected.scores);
        summaryRoot.innerHTML = board.summary;
        matchupsRoot.innerHTML = board.list;
        repairImages(matchupsRoot);
        replaceUrl();
        return;
      }
      const rows = allRows.filter(({ matchup }) => filter === "ALL" || matchup.conference === filter);
      if (game != null && !rows.some((row) => row.index === game)) game = null;
      summaryRoot.innerHTML = seasonSummaryMarkup(rows.map((row) => row.matchup));
      matchupsRoot.innerHTML = rows.length
        ? rows.map(({ matchup, index }) => seasonMatchupMarkup(matchup, index, game === index, data.platform !== "Sleeper")).join("")
        : `<div class="season-empty"><strong>Week ${esc(week)}</strong><p>No matchups are available for this view.</p></div>`;
      repairImages(matchupsRoot);
      replaceUrl();
    }

    function renderDraft() {
      if (!data.drafts) {
        draftPanel.innerHTML = '<p class="draft-unavailable">Draft board not yet loaded</p>';
        return;
      }
      const playersByName = draftPlayerMap(data);
      draftPanel.innerHTML = `<div class="draft-intro"><p class="section-kicker">Draft night</p><h2>Built pick by pick</h2><p>${esc(data.drafts.format)}</p></div>${data.drafts.boards.map((board, index) => draftBoardMarkup(board, data, index, playersByName)).join("")}`;
      repairImages(draftPanel);
    }

    function toggleGame(nextGame, returnFocus = false) {
      game = game === nextGame ? null : nextGame;
      renderWeek();
      if (returnFocus) matchupsRoot.querySelector(`[data-game-index="${nextGame}"] .season-game-toggle`)?.focus();
    }

    async function loadSeason() {
      const token = ++loadToken;
      data = null;
      game = null;
      title.textContent = year;
      platform.textContent = "Loading";
      championRoot.innerHTML = '<div class="skeleton stack"><span></span></div>';
      loading.hidden = false;
      content.hidden = true;
      errorRoot.hidden = true;
      yearSelect.value = year;
      try {
        if (!seasonYears.includes(year)) {
          const unsupported = new Error("Season is outside the explorer range");
          unsupported.code = "UNSUPPORTED_SEASON";
          throw unsupported;
        }
        const loaded = await getSeason(year);
        if (token !== loadToken) return;
        if (!loaded || String(loaded.year) !== year || !Array.isArray(loaded.weeks)) throw new Error("Invalid season file");
        data = loaded;
        const requestedWeek = Math.max(1, Number(new URLSearchParams(window.location.search).get("week")) || 1);
        week = data.weeks.some((item) => Number(item.week) === requestedWeek) ? requestedWeek : Number(data.weeks[0]?.week || 1);
        const requestedGame = new URLSearchParams(window.location.search).get("game");
        game = /^\d+$/.test(requestedGame || "") ? Number(requestedGame) : null;
        platform.textContent = data.platform || "Season";
        document.title = `${year} Season Explorer | The League 2K`;
        renderChampion();
        renderWeek();
        renderDraft();
        loading.hidden = true;
        content.hidden = false;
        setView(view, false);
        replaceUrl();
        if (game != null) requestAnimationFrame(() => matchupsRoot.querySelector(`[data-game-index="${game}"]`)?.scrollIntoView({ block: "nearest" }));
      } catch (error) {
        if (token !== loadToken) return;
        const unsupported = error.code === "UNSUPPORTED_SEASON";
        platform.textContent = unsupported ? "Archive only" : "Unavailable";
        championRoot.innerHTML = '<div><small>Season champion</small><strong>—</strong></div>';
        loading.hidden = true;
        content.hidden = true;
        errorRoot.hidden = false;
        errorRoot.innerHTML = unsupported
          ? `<strong>${esc(year)} week-by-week scores are unavailable.</strong><p>The Season Explorer covers 2017 through 2025. The season archive still has standings and the championship result.</p><div><a href="archive.html">Season archive →</a></div>`
          : `<strong>${esc(year)} could not be loaded.</strong><p>Check the connection and try again, or return to the season archive.</p><div><button type="button" data-season-retry>Try again</button><a href="archive.html">Season archive →</a></div>`;
        replaceUrl();
      }
    }

    yearSelect.addEventListener("change", () => {
      year = yearSelect.value;
      week = 1;
      game = null;
      view = "schedule";
      replaceUrl();
      loadSeason();
    });
    weekStrip.addEventListener("click", (event) => {
      const button = event.target.closest("[data-season-week]");
      if (!button) return;
      week = Number(button.dataset.seasonWeek);
      game = null;
      renderWeek();
      weekStrip.querySelector(`[data-season-week="${week}"]`)?.scrollIntoView({ block: "nearest", inline: "center" });
    });
    weekStrip.addEventListener("keydown", (event) => {
      const buttons = Array.from(weekStrip.querySelectorAll("[data-season-week]"));
      const current = buttons.indexOf(event.target.closest("[data-season-week]"));
      if (current < 0 || !["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
      event.preventDefault();
      const next = event.key === "Home" ? 0 : event.key === "End" ? buttons.length - 1 : (current + (event.key === "ArrowRight" ? 1 : -1) + buttons.length) % buttons.length;
      buttons[next].click();
      weekStrip.querySelector(`[data-season-week="${week}"]`)?.focus();
    });
    filterButtons.forEach((button) => button.addEventListener("click", () => {
      filter = button.dataset.seasonFilter;
      game = null;
      filterButtons.forEach((item) => {
        const active = item === button;
        item.classList.toggle("is-active", active);
        item.setAttribute("aria-pressed", String(active));
      });
      renderWeek();
    }));
    viewButtons.forEach((button, index) => {
      button.addEventListener("click", () => setView(button.dataset.seasonView));
      button.addEventListener("keydown", (event) => {
        if (!["ArrowLeft", "ArrowRight"].includes(event.key)) return;
        event.preventDefault();
        const next = (index + (event.key === "ArrowRight" ? 1 : -1) + viewButtons.length) % viewButtons.length;
        viewButtons[next].click();
        viewButtons[next].focus();
      });
    });
    matchupsRoot.addEventListener("click", (event) => {
      if (event.target.closest("a, .lineup-bench, .season-player")) return;
      const card = event.target.closest("[data-game-index]");
      if (card) toggleGame(Number(card.dataset.gameIndex), Boolean(event.target.closest(".season-game-toggle")));
    });
    errorRoot.addEventListener("click", (event) => {
      if (event.target.closest("[data-season-retry]")) loadSeason();
    });

    replaceUrl();
    loadSeason();
  }

  renderPowerRankings();
  renderMasthead();
  renderTimeline();
  renderChampions();
  renderRecords();
  renderMarks();
  renderSeasons();
  renderOwnerGrid();
  renderPlayers();
  renderOwnerProfile();
  renderRivalries();
  renderSeasonExplorer();
  wireTabs("standing-tabs");
  wireTabs("matchup-tabs");

  if ($("live-afc")) {
    renderStandings("AFC", "live-afc");
    renderStandings("NFC", "live-nfc");
    renderMatchups("AFC", "matchups-afc");
    renderMatchups("NFC", "matchups-nfc");
    renderTransactions();
  }
  if ($("founders")) $("founders").innerHTML = linkifyText(D.founding.join(", "));
})();
