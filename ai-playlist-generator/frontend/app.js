/* ============================================================
   AI Playlist Generator — frontend logic
   ============================================================ */

const API_BASE = 'http://localhost:8000';

const GENRE_EMOJI = {
  'New Wave': '🌊', 'Synth-pop': '🎹', 'Pop Rock': '🎸', 'Rock': '🎸',
  'Hard Rock': '🤘', 'Alternative': '🎵', 'Grunge': '💀', 'Punk Rock': '⚡',
  'Pop Punk': '⚡', 'Pop': '✨', 'Dance': '🕺', 'Dance Pop': '🕺',
  'Dance Hall': '🌴', 'Hip-Hop': '🎤', 'R&B': '🎶', 'Soul Pop': '💜',
  'Country': '🤠', 'Country Pop': '🤠', 'Country Rap': '🤠', 'Indie Pop': '🌿',
  'Britpop': '🇬🇧', 'Latin Pop': '💃', 'Afrobeats': '🌍', 'Electropop': '⚡',
  'Pop Funk': '🕺', 'Synth': '🎹', 'Dancehall': '🌴',
};

function getGenreEmoji(genre) {
  for (const [key, emoji] of Object.entries(GENRE_EMOJI)) {
    if (genre.toLowerCase().includes(key.toLowerCase())) return emoji;
  }
  return '🎵';
}

// ---------------------------------------------------------------------------
// Main entry point
// ---------------------------------------------------------------------------
async function generatePlaylist() {
  const input = document.getElementById('queryInput');
  const btn   = document.getElementById('generateBtn');
  const query = input.value.trim();

  if (!query) {
    input.focus();
    input.style.borderColor = '#E22134';
    setTimeout(() => { input.style.borderColor = ''; }, 1500);
    return;
  }

  // reset UI
  resetWorkflowSteps();
  showResultsGrid();
  btn.disabled = true;
  btn.innerHTML = `<div class="spinner" style="width:16px;height:16px;border-width:2px;"></div> Generating…`;
  setWorkflowBadge('running', 'Running…');

  document.getElementById('trackList').innerHTML =
    `<div class="loading-tracks"><div class="spinner"></div><span>Generating your playlist…</span></div>`;
  document.getElementById('playlistName').textContent = 'Playlist';
  document.getElementById('playlistDesc').textContent = '';
  document.getElementById('trackCount').textContent = '';
  document.getElementById('logBody').innerHTML = '';
  document.getElementById('auditSection').style.display = 'none';

  try {
    const response = await fetch(`${API_BASE}/api/generate-playlist`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${response.status}`);
    }

    const data = await response.json();
    await animateWorkflow(data.workflow);
    renderPlaylist(data.playlist);
    renderAuditLog(data.audit_log);
    setWorkflowBadge('done', `Done in ${totalMs(data.workflow)}ms`);

  } catch (e) {
    showError(e.message);
    setWorkflowBadge('error', 'Error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<svg class="btn-icon" viewBox="0 0 24 24" fill="none">
      <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"
            stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    </svg> Generate`;
  }
}

// ---------------------------------------------------------------------------
// Workflow animation
// ---------------------------------------------------------------------------
async function animateWorkflow(steps) {
  for (const step of steps) {
    const el = document.getElementById(`step-${step.step}`);
    if (!el) continue;

    // mark running
    el.classList.add('running');
    el.querySelector('.step-status').textContent = 'running';

    // artificial delay so the user can see each step "fire"
    await sleep(280 + Math.random() * 120);

    // mark done
    el.classList.remove('running');
    el.classList.add('done');
    el.querySelector('.step-status').textContent = `✓ ${step.duration_ms}ms`;

    // inject output detail
    const outputEl = document.getElementById(`output-${step.step}`);
    if (outputEl) {
      outputEl.innerHTML = buildOutputTable(step.step, step.output);
      outputEl.classList.add('open');
    }

    await sleep(80);
  }
}

function buildOutputTable(stepNum, output) {
  const rows = [];

  const fmt = (v) => {
    if (v === null || v === undefined) return '—';
    if (Array.isArray(v)) {
      if (v.length === 0) return '<span style="color:var(--text-muted)">none</span>';
      return v.map(t => `<span class="output-tag">${t}</span>`).join('');
    }
    if (typeof v === 'object') return JSON.stringify(v);
    return String(v);
  };

  switch (stepNum) {
    case 1:
      if (output.theme)      rows.push(['Theme',       output.theme]);
      if (output.year_range) rows.push(['Years',        `${output.year_range.start} – ${output.year_range.end}`]);
      if (output.moods)      rows.push(['Moods',        output.moods]);
      if (output.genres?.length) rows.push(['Genres',  output.genres]);
      rows.push(['Target',   `${output.count} tracks${output.one_per_year ? ', one/year' : ''}`]);
      break;
    case 2:
      if (output.strategy)   rows.push(['Strategy',    output.strategy.replace(/_/g, ' ')]);
      if (output.tasks)      rows.push(['Tasks',        output.tasks]);
      break;
    case 3:
      rows.push(['Catalog',  `${output.catalog_size} songs`]);
      rows.push(['Matched',  `${output.songs_matched} songs`]);
      if (output.filters_applied?.length) rows.push(['Filters',  output.filters_applied]);
      break;
    case 4:
      rows.push(['Selected', `${output.songs_selected} tracks`]);
      rows.push(['Duration', output.total_duration]);
      if (output.strategy)   rows.push(['Strategy',    output.strategy.replace(/_/g, ' ')]);
      break;
    case 5:
      rows.push(['Playlist', output.playlist_name]);
      rows.push(['Tracks',   output.total_tracks]);
      rows.push(['Duration', output.total_duration]);
      break;
  }

  if (!rows.length) return '';
  return `<table class="output-table">${rows.map(([k, v]) =>
    `<tr><td>${k}</td><td>${Array.isArray(v) ? fmt(v) : fmt(v)}</td></tr>`
  ).join('')}</table>`;
}

// ---------------------------------------------------------------------------
// Playlist rendering
// ---------------------------------------------------------------------------
function renderPlaylist(playlist) {
  document.getElementById('playlistName').textContent = playlist.name;
  document.getElementById('playlistDesc').textContent = playlist.description;
  document.getElementById('trackCount').textContent =
    `${playlist.total_tracks} tracks · ${playlist.total_duration}`;

  const list = document.getElementById('trackList');
  if (!playlist.tracks || playlist.tracks.length === 0) {
    list.innerHTML = `<div class="loading-tracks" style="color:var(--text-muted)">No tracks found — try a different query.</div>`;
    return;
  }

  list.innerHTML = playlist.tracks.map((track, i) => `
    <div class="track-row" style="animation-delay:${i * 40}ms">
      <span class="track-num">${i + 1}</span>
      <div class="track-art">${getGenreEmoji(track.genre)}</div>
      <div class="track-info">
        <span class="track-title">${escHtml(track.title)}</span>
        <span class="track-artist">${escHtml(track.artist)}</span>
      </div>
      <span class="track-year">${track.year}</span>
      <span class="track-genre">${escHtml(track.genre)}</span>
      <div class="energy-bar-wrap" title="Energy: ${Math.round(track.energy * 100)}%">
        <span class="energy-label">${Math.round(track.energy * 100)}%</span>
        <div class="energy-bar"><div class="energy-fill" style="width:${track.energy * 100}%"></div></div>
      </div>
      <span class="track-duration">${escHtml(track.duration)}</span>
      <button class="play-btn" title="Play (mock)" aria-label="Play ${escHtml(track.title)}">
        <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
          <polygon points="2,1 11,6 2,11"/>
        </svg>
      </button>
    </div>
  `).join('');
}

// ---------------------------------------------------------------------------
// Audit log
// ---------------------------------------------------------------------------
function renderAuditLog(entries) {
  const body = document.getElementById('logBody');
  body.innerHTML = entries.map((e, i) => {
    const ts = new Date(e.timestamp).toISOString().replace('T', ' ').replace('Z', '').slice(11, 23);
    return `<div class="log-entry" style="animation-delay:${i * 20}ms">
      <span class="log-ts">${ts}</span>
      <span class="log-level ${e.level}">${e.level}</span>
      <span class="log-service">${escHtml(e.service)}</span>
      <span class="log-msg">${escHtml(e.message)}</span>
    </div>`;
  }).join('');

  document.getElementById('auditSection').style.display = '';
  // auto-scroll to bottom
  setTimeout(() => { body.scrollTop = body.scrollHeight; }, 50);
}

// ---------------------------------------------------------------------------
// UI helpers
// ---------------------------------------------------------------------------
function showResultsGrid() {
  document.getElementById('resultsGrid').style.display = 'grid';
}

function resetWorkflowSteps() {
  [1, 2, 3, 4, 5].forEach(n => {
    const el = document.getElementById(`step-${n}`);
    el.classList.remove('running', 'done');
    el.querySelector('.step-status').textContent = 'pending';
    const out = document.getElementById(`output-${n}`);
    out.innerHTML = '';
    out.classList.remove('open');
  });
}

function setWorkflowBadge(state, text) {
  const badge = document.getElementById('workflowBadge');
  badge.textContent = text;
  badge.className = 'badge';
  if (state === 'done')    badge.classList.add('done');
  if (state === 'running') badge.classList.add('running');
}

function showError(msg) {
  const list = document.getElementById('trackList');
  list.innerHTML = `
    <div class="loading-tracks" style="color:#E22134">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
        <circle cx="12" cy="12" r="10" stroke="#E22134" stroke-width="2"/>
        <path d="M12 8v4M12 16h.01" stroke="#E22134" stroke-width="2" stroke-linecap="round"/>
      </svg>
      <span>Error: ${escHtml(msg)}</span>
      <span style="font-size:0.75rem;color:var(--text-muted)">Is the backend running? Try: uvicorn main:app --reload</span>
    </div>`;
}

function toggleLog() {
  const body = document.getElementById('logBody');
  const btn  = document.getElementById('toggleLogBtn');
  const collapsed = body.style.display === 'none';
  body.style.display = collapsed ? '' : 'none';
  btn.textContent = collapsed ? 'Hide' : 'Show';
}

function fillExample(btn) {
  document.getElementById('queryInput').value = btn.textContent.trim();
  document.getElementById('queryInput').focus();
}

function totalMs(workflow) {
  return workflow.reduce((s, w) => s + w.duration_ms, 0);
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// Allow Enter key to submit (Shift+Enter for newline)
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('queryInput').addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      generatePlaylist();
    }
  });
});
