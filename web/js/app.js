/* AI Security 90-Day Planner — Web SPA */

let CURRICULUM = [];
let pyodide = null;
let pyodideLoading = false;
let currentView = 'dashboard';
let currentTaskDay = null;
let showingSolution = false;

// ── Data Layer (localStorage) ─────────────────────────

const db = {
  _key(k) { return `planner_${k}`; },
  _get(k, def = null) {
    try { const v = localStorage.getItem(this._key(k)); return v !== null ? JSON.parse(v) : def; }
    catch { return def; }
  },
  _set(k, v) {
    try { localStorage.setItem(this._key(k), JSON.stringify(v)); } catch {}
  },

  getStartDate() {
    let d = this._get('start_date', null);
    if (!d) { d = new Date().toISOString().slice(0, 10); this._set('start_date', d); }
    return d;
  },

  getTodayDayNumber() {
    const start = new Date(this.getStartDate());
    const now = new Date(); now.setHours(0,0,0,0); start.setHours(0,0,0,0);
    const diff = Math.floor((now - start) / 86400000) + 1;
    return Math.max(0, Math.min(diff, 91));
  },

  getTask(day) {
    const item = CURRICULUM.find(c => c.day === day);
    if (!item) return null;
    return { ...item, status: this.getStatus(day) };
  },

  getStatus(day) { return this._get(`status_${day}`, 'pending'); },

  updateStatus(day, status) {
    this._set(`status_${day}`, status);
    if (status === 'completed') this._set(`completed_at_${day}`, new Date().toISOString());
  },

  getEffectiveStatus(day) {
    const s = this.getStatus(day);
    if (s === 'pending' && day < this.getTodayDayNumber()) return 'overdue';
    return s;
  },

  saveNote(day, text) { this._set(`note_${day}`, text); },
  getNote(day) { return this._get(`note_${day}`, ''); },

  getProgress() {
    const stats = { completed: 0, pending: 0, skipped: 0, postponed: 0, total: 90 };
    for (let d = 1; d <= 90; d++) {
      const s = this.getStatus(d);
      stats[s] = (stats[s] || 0) + 1;
    }
    return stats;
  },

  getStreak() {
    const today = this.getTodayDayNumber();
    let streak = 0;
    for (let d = Math.min(today, 90); d >= 1; d--) {
      if (this.getStatus(d) === 'completed') { streak++; }
      else { if (d === today) continue; break; }
    }
    return streak;
  },

  saveWeeklyReview(week, reflection, learnings) {
    this._set(`review_${week}`, { reflection, learnings, updated: new Date().toISOString() });
  },
  getWeeklyReview(week) { return this._get(`review_${week}`, { reflection: '', learnings: '' }); },

  exportJSON() {
    const data = {
      start_date: this.getStartDate(),
      progress: this.getProgress(),
      tasks: [],
      notes: [],
      reviews: []
    };
    for (let d = 1; d <= 90; d++) {
      data.tasks.push({ day: d, status: this.getStatus(d) });
      const n = this.getNote(d);
      if (n) data.notes.push({ day: d, text: n });
    }
    for (let w = 1; w <= 13; w++) {
      const r = this.getWeeklyReview(w);
      if (r.reflection || r.learnings) data.reviews.push({ week: w, ...r });
    }
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'planner_export.json';
    a.click();
    URL.revokeObjectURL(a.href);
  }
};

// ── Navigation ────────────────────────────────────────

function navigate(view, param) {
  currentView = view;
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.toggle('active', b.dataset.view === view));
  if (view === 'task' && param) currentTaskDay = param;
  location.hash = view === 'task' && currentTaskDay ? `task/${currentTaskDay}` : view;
  render();
  document.getElementById('sidebar').classList.remove('open');
}

function initNav() {
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => navigate(btn.dataset.view));
  });
  document.getElementById('mobile-menu-btn').addEventListener('click', () => {
    document.getElementById('sidebar').classList.toggle('open');
  });
  const hash = location.hash.slice(1);
  if (hash.startsWith('task/')) {
    currentTaskDay = parseInt(hash.split('/')[1]) || null;
    currentView = 'task';
  } else if (hash) {
    currentView = hash;
  }
}

function updateFooter() {
  const day = db.getTodayDayNumber();
  document.getElementById('sidebar-footer').textContent = `Day ${Math.min(Math.max(day, 1), 90)} / 90`;
}

// ── Render Router ─────────────────────────────────────

function render() {
  const el = document.getElementById('content');
  updateFooter();
  switch (currentView) {
    case 'dashboard': renderDashboard(el); break;
    case 'task': renderTask(el); break;
    case 'calendar': renderCalendar(el); break;
    case 'review': renderReview(el); break;
    case 'notes': renderNotes(el); break;
    case 'settings': renderSettings(el); break;
    default: renderDashboard(el);
  }
}

// ── Dashboard ─────────────────────────────────────────

function renderDashboard(el) {
  const stats = db.getProgress();
  const streak = db.getStreak();
  const pct = Math.round(stats.completed / 90 * 100);
  const today = db.getTodayDayNumber();
  const todayTask = db.getTask(Math.min(Math.max(today, 1), 90));
  const dayLabel = today >= 1 && today <= 90
    ? `Day ${today} / 90  ·  ${todayTask?.phase_name || ''}`
    : today > 90 ? 'Program completed!' : 'Program starts on first visit';

  const phases = [
    [1, 'Security & Engineering Foundations', 1, 20],
    [2, 'AI Engineering & LLM Agents', 21, 40],
    [3, 'AI Security & Red Teaming', 41, 60],
    [4, 'Portfolio Research Project', 61, 80],
    [5, 'Research & Internship Prep', 81, 90]
  ];

  let phaseBars = phases.map(([num, name, start, end]) => {
    const total = end - start + 1;
    let comp = 0;
    for (let d = start; d <= end; d++) if (db.getStatus(d) === 'completed') comp++;
    const w = total > 0 ? (comp / total * 100) : 0;
    return `<div class="phase-bar">
      <span class="phase-name">Phase ${num}: ${name}</span>
      <div class="progress-bar"><div class="progress-fill" style="width:${w}%"></div></div>
      <span class="phase-count">${comp}/${total}</span>
    </div>`;
  }).join('');

  el.innerHTML = `
    <div class="flex-between mb-20">
      <h2 class="page-title">Dashboard</h2>
      <span class="secondary">${dayLabel}</span>
    </div>
    <div class="card mb-16">
      <div class="flex-between mb-8">
        <span class="card-title">Overall Progress</span>
        <span style="color:var(--accent-blue);font-size:18px;font-weight:700">${pct}%</span>
      </div>
      <div class="progress-bar" style="height:18px">
        <div class="progress-fill" style="width:${pct}%"></div>
        <div class="progress-text">${stats.completed}/90</div>
      </div>
    </div>
    <div class="stats-row">
      <div class="stat-card"><div class="stat-label">Completed</div><div class="stat-value" style="color:var(--status-completed)">${stats.completed}</div></div>
      <div class="stat-card"><div class="stat-label">Pending</div><div class="stat-value" style="color:var(--status-pending)">${stats.pending}</div></div>
      <div class="stat-card"><div class="stat-label">Postponed</div><div class="stat-value" style="color:var(--status-postponed)">${stats.postponed}</div></div>
      <div class="stat-card"><div class="stat-label">Skipped</div><div class="stat-value" style="color:var(--status-skipped)">${stats.skipped}</div></div>
      <div class="stat-card"><div class="stat-label">Streak</div><div class="stat-value" style="color:var(--accent-purple)">${streak}</div></div>
    </div>
    <div class="card">
      <div class="card-title">Phase Progress</div>
      ${phaseBars}
    </div>
  `;
}

// ── Task View ─────────────────────────────────────────

function renderTask(el) {
  if (!currentTaskDay) currentTaskDay = Math.min(Math.max(db.getTodayDayNumber(), 1), 90);
  const day = currentTaskDay;
  const task = db.getTask(day);
  if (!task) { el.innerHTML = '<p>No task data.</p>'; return; }

  const status = db.getEffectiveStatus(day);
  const statusColors = { completed: 'var(--status-completed)', pending: 'var(--status-pending)', overdue: 'var(--status-overdue)', skipped: 'var(--status-skipped)', postponed: 'var(--status-postponed)' };
  const phaseLabels = { 1: 'FOUNDATIONS', 2: 'AI/LLM', 3: 'RED TEAM', 4: 'PROJECT', 5: 'CAREER' };

  const concepts = (task.concepts || []).join('  •  ');
  const resources = (task.resources || []).map(r =>
    typeof r === 'object' ? `<a class="resource-link" href="${esc(r.url)}" target="_blank" rel="noopener">${esc(r.title)}</a>` : `<a class="resource-link" href="${esc(r)}" target="_blank" rel="noopener">${esc(r)}</a>`
  ).join('') || '<span class="muted">No resources</span>';

  const note = db.getNote(day);
  const starterCode = task.starter_code || '';
  const hasSolution = !!task.solution_code;

  showingSolution = false;

  el.innerHTML = `
    <div class="task-nav">
      <button class="btn" id="prev-day" ${day <= 1 ? 'disabled' : ''}>‹ Previous</button>
      <button class="btn btn-primary" id="go-today">Go to Today</button>
      <button class="btn" id="next-day" ${day >= 90 ? 'disabled' : ''}>Next ›</button>
    </div>
    <h2 class="page-title">Day ${day} / 90</h2>
    <div class="phase-label">PHASE ${task.phase}: ${task.phase_name}</div>

    <div class="card">
      <div class="task-topic">${esc(task.topic)}</div>
      ${concepts ? `<div class="concepts-list">Key concepts: ${esc(concepts)}</div>` : ''}
      <div class="mt-8" style="color:var(--accent-cyan);font-weight:600">Exercise</div>
      <p class="secondary mt-8">${esc(task.exercise)}</p>
      ${task.deliverable ? `<p class="mt-8" style="color:var(--accent-blue)">Deliverable: ${esc(task.deliverable)}</p>` : ''}
      ${task.reflection_prompt ? `<p class="mt-8 muted" style="font-style:italic">Reflect: ${esc(task.reflection_prompt)}</p>` : ''}
      <div class="mt-12">
        <span class="badge">${phaseLabels[task.phase] || ''}</span>
        <span class="badge-duration">~${task.estimated_minutes || 60} min</span>
      </div>
    </div>

    <div class="card">
      <div class="card-title">Status</div>
      <div class="status-display" style="color:${statusColors[status] || 'inherit'}">Status: ${status.toUpperCase()}</div>
      <div class="btn-group">
        <button class="btn btn-success" data-status="completed">Mark Complete</button>
        <button class="btn btn-warning" data-status="skipped">Skip</button>
        <button class="btn btn-danger" data-status="postponed">Postpone</button>
        <button class="btn" data-status="pending">Reset</button>
      </div>
    </div>

    <div class="card">
      <div class="card-title">Resources</div>
      ${resources}
    </div>

    <div class="card">
      <div class="code-header">
        <span class="card-title">Code Runner</span>
        <button class="btn btn-success" id="run-code">▶ Run</button>
        <button class="btn" id="reset-code">Reset Code</button>
        ${hasSolution ? '<button class="btn" id="toggle-solution">Show Solution</button>' : ''}
        <button class="btn" id="clear-output">Clear Output</button>
      </div>
      <textarea class="code-editor" id="code-editor" spellcheck="false">${esc(starterCode)}</textarea>
      <div class="muted mt-8 mb-8">Output:</div>
      <pre class="code-output" id="code-output"></pre>
    </div>

    <div class="card">
      <div class="card-title">Notes</div>
      <textarea id="task-notes" rows="5" placeholder="Write your notes here...">${esc(note)}</textarea>
      <div class="text-right mt-8">
        <button class="btn btn-primary" id="save-notes">Save Notes</button>
      </div>
    </div>
  `;

  // Tab key in code editor
  const editor = document.getElementById('code-editor');
  editor.addEventListener('keydown', e => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const s = editor.selectionStart, end = editor.selectionEnd;
      editor.value = editor.value.substring(0, s) + '    ' + editor.value.substring(end);
      editor.selectionStart = editor.selectionEnd = s + 4;
    }
  });

  document.getElementById('prev-day').addEventListener('click', () => { currentTaskDay = Math.max(1, day - 1); navigate('task', currentTaskDay); });
  document.getElementById('next-day').addEventListener('click', () => { currentTaskDay = Math.min(90, day + 1); navigate('task', currentTaskDay); });
  document.getElementById('go-today').addEventListener('click', () => { currentTaskDay = Math.min(Math.max(db.getTodayDayNumber(), 1), 90); navigate('task', currentTaskDay); });

  el.querySelectorAll('[data-status]').forEach(btn => {
    btn.addEventListener('click', () => { db.updateStatus(day, btn.dataset.status); renderTask(el); });
  });

  document.getElementById('save-notes').addEventListener('click', () => {
    db.saveNote(day, document.getElementById('task-notes').value);
    showToast('Notes saved');
  });

  document.getElementById('run-code').addEventListener('click', () => runCode());
  document.getElementById('reset-code').addEventListener('click', () => {
    document.getElementById('code-editor').value = starterCode;
    showingSolution = false;
    const solBtn = document.getElementById('toggle-solution');
    if (solBtn) solBtn.textContent = 'Show Solution';
  });
  document.getElementById('clear-output').addEventListener('click', () => { document.getElementById('code-output').textContent = ''; });

  const solBtn = document.getElementById('toggle-solution');
  if (solBtn) {
    solBtn.addEventListener('click', () => {
      if (showingSolution) {
        document.getElementById('code-editor').value = starterCode;
        solBtn.textContent = 'Show Solution';
        showingSolution = false;
      } else {
        document.getElementById('code-editor').value = task.solution_code;
        solBtn.textContent = 'Hide Solution';
        showingSolution = true;
      }
    });
  }
}

// ── Pyodide Code Runner ───────────────────────────────

async function runCode() {
  const btn = document.getElementById('run-code');
  const output = document.getElementById('code-output');
  const code = document.getElementById('code-editor').value.trim();
  if (!code) { output.textContent = 'No code to run.'; return; }

  btn.disabled = true;
  btn.textContent = 'Loading Python...';
  output.textContent = 'Initializing...';

  try {
    if (!pyodide) {
      if (!pyodideLoading) {
        pyodideLoading = true;
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js';
        document.head.appendChild(script);
        await new Promise((resolve, reject) => { script.onload = resolve; script.onerror = reject; });
        pyodide = await loadPyodide();
      } else {
        while (!pyodide) await new Promise(r => setTimeout(r, 200));
      }
    }

    btn.textContent = 'Running...';
    output.textContent = '';

    pyodide.setStdout({ batched: msg => { output.textContent += msg + '\n'; } });
    pyodide.setStderr({ batched: msg => { output.textContent += msg + '\n'; } });

    const runPromise = pyodide.runPythonAsync(code);
    const timeout = new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout: 15s limit')), 15000));
    await Promise.race([runPromise, timeout]);

    if (!output.textContent.trim()) output.textContent = '(No output)';
  } catch (err) {
    output.textContent += '\nError: ' + err.message;
  } finally {
    btn.disabled = false;
    btn.textContent = '▶ Run';
  }
}

// ── Calendar ──────────────────────────────────────────

function renderCalendar(el) {
  const startDate = new Date(db.getStartDate());
  const todayNum = db.getTodayDayNumber();

  const legendItems = [
    ['Today', 'var(--accent-blue)'], ['Completed', 'var(--status-completed)'],
    ['Pending', 'var(--status-pending)'], ['Postponed', 'var(--status-postponed)'],
    ['Skipped', 'var(--status-skipped)'], ['Overdue', 'var(--status-overdue)']
  ];
  const legend = legendItems.map(([name, color]) =>
    `<span class="legend-item"><span class="legend-dot" style="background:${color}"></span>${name}</span>`
  ).join('');

  // Group days by calendar month
  const months = {};
  for (let d = 1; d <= 90; d++) {
    const dt = new Date(startDate);
    dt.setDate(dt.getDate() + d - 1);
    const key = `${dt.getFullYear()}-${String(dt.getMonth()+1).padStart(2,'0')}`;
    if (!months[key]) months[key] = [];
    const status = db.getEffectiveStatus(d);
    months[key].push({ day: d, date: new Date(dt), status, isToday: d === todayNum });
  }

  let monthsHTML = '';
  const monthNames = ['January','February','March','April','May','June','July','August','September','October','November','December'];

  for (const [key, days] of Object.entries(months)) {
    const [y, m] = key.split('-').map(Number);
    const title = `${monthNames[m-1]} ${y}`;
    const headers = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'].map(h => `<div class="cal-header">${h}</div>`).join('');

    let cells = '';
    const firstDow = (days[0].date.getDay() + 6) % 7;
    for (let i = 0; i < firstDow; i++) cells += '<div class="cal-cell empty"></div>';

    for (const d of days) {
      const cls = d.isToday ? 'is-today' : `status-${d.status}`;
      cells += `<div class="cal-cell ${cls}" data-day="${d.day}">${d.day}</div>`;
      const nextDow = (d.date.getDay() + 6) % 7;
      if (nextDow === 6 && d !== days[days.length - 1]) {} // row break handled by grid
    }

    monthsHTML += `<div class="card month-section"><div class="month-title">${title}</div><div class="calendar-grid">${headers}${cells}</div></div>`;
  }

  el.innerHTML = `
    <h2 class="page-title">Calendar</h2>
    <div class="calendar-legend">${legend}</div>
    ${monthsHTML}
  `;

  el.querySelectorAll('.cal-cell[data-day]').forEach(cell => {
    cell.addEventListener('click', () => {
      currentTaskDay = parseInt(cell.dataset.day);
      navigate('task', currentTaskDay);
    });
  });
}

// ── Weekly Review ─────────────────────────────────────

function renderReview(el) {
  let weekOptions = '';
  for (let w = 1; w <= 13; w++) {
    const s = (w-1)*7+1, e = Math.min(w*7, 90);
    weekOptions += `<option value="${w}">Week ${w} (Day ${s}-${e})</option>`;
  }

  el.innerHTML = `
    <h2 class="page-title">Weekly Review</h2>
    <div class="mb-16">
      <label>Select Week: </label>
      <select id="week-select" style="width:auto;display:inline-block;min-width:200px">${weekOptions}</select>
    </div>
    <div id="review-content"></div>
  `;

  const sel = document.getElementById('week-select');
  sel.addEventListener('change', () => renderWeekContent(parseInt(sel.value)));
  renderWeekContent(1);
}

function renderWeekContent(week) {
  const container = document.getElementById('review-content');
  const start = (week-1)*7+1, end = Math.min(week*7, 90);
  const todayNum = db.getTodayDayNumber();

  let completed = 0, skipped = 0, postponed = 0, pending = 0;
  let taskLines = '';
  for (let d = start; d <= end; d++) {
    const task = db.getTask(d);
    if (!task) continue;
    let status = db.getEffectiveStatus(d);
    if (status === 'completed') completed++;
    else if (status === 'skipped') skipped++;
    else if (status === 'postponed') postponed++;
    else pending++;

    const icons = { completed: '[Done]', skipped: '[Skip]', postponed: '[Later]', overdue: '[!]', pending: '[ ]' };
    const cls = { completed: 'done', overdue: 'overdue', skipped: 'skip' };
    taskLines += `<div class="${cls[status] || ''}"><span>${icons[status] || '[ ]'}</span> Day ${d}: ${esc(task.topic)}</div>`;
  }

  const total = end - start + 1;
  const review = db.getWeeklyReview(week);
  const pct = total > 0 ? Math.round(completed / total * 100) : 0;

  container.innerHTML = `
    <div class="card">
      <div class="card-title">Week Summary</div>
      <div class="progress-bar mb-8" style="height:14px"><div class="progress-fill" style="width:${pct}%"></div></div>
      <div class="secondary mb-12">${completed}/${total} completed${skipped ? ` | ${skipped} skipped` : ''}${postponed ? ` | ${postponed} postponed` : ''}${pending ? ` | ${pending} pending` : ''}</div>
      <div class="week-task-list">${taskLines}</div>
    </div>
    <div class="card">
      <div class="card-title">Reflection</div>
      <p class="muted mb-8">What went well? What was challenging? What would you do differently?</p>
      <textarea id="review-reflection" rows="5" placeholder="Write your weekly reflection...">${esc(review.reflection)}</textarea>
    </div>
    <div class="card">
      <div class="card-title">Key Learnings</div>
      <p class="muted mb-8">List the most important things you learned this week:</p>
      <textarea id="review-learnings" rows="4" placeholder="- Learning 1\n- Learning 2\n- ...">${esc(review.learnings)}</textarea>
    </div>
    <button class="btn btn-primary" id="save-review" style="min-height:40px;width:100%">Save Weekly Review</button>
  `;

  document.getElementById('save-review').addEventListener('click', () => {
    db.saveWeeklyReview(week, document.getElementById('review-reflection').value, document.getElementById('review-learnings').value);
    showToast('Weekly review saved');
  });
}

// ── Notes ─────────────────────────────────────────────

function renderNotes(el) {
  el.innerHTML = `
    <h2 class="page-title">Notes</h2>
    <input type="text" id="notes-search" placeholder="Search notes..." class="mb-16">
    <div class="notes-layout">
      <div class="note-list" id="note-list"></div>
      <div class="card" id="note-editor">
        <div class="card-title" id="note-editor-title">Select a day to view notes</div>
        <textarea id="note-text" rows="12" placeholder="Write your notes here..." disabled></textarea>
        <div class="text-right mt-8">
          <button class="btn btn-primary" id="save-note" disabled>Save Notes</button>
        </div>
      </div>
    </div>
  `;

  let selectedDay = null;
  const listEl = document.getElementById('note-list');
  const search = document.getElementById('notes-search');

  function populateList(filter = '') {
    listEl.innerHTML = '';
    const lf = filter.toLowerCase();
    for (let d = 1; d <= 90; d++) {
      const task = CURRICULUM.find(c => c.day === d);
      const topic = task ? task.topic : `Day ${d}`;
      const note = db.getNote(d);
      const hasNote = note && note.trim();

      if (filter && !topic.toLowerCase().includes(lf) && !(note || '').toLowerCase().includes(lf)) continue;

      const div = document.createElement('div');
      div.className = `note-item${!hasNote ? ' dimmed' : ''}${d === selectedDay ? ' active' : ''}`;
      div.innerHTML = `${hasNote ? '<span class="has-note">[Note]</span> ' : ''}Day ${d}: ${esc(topic)}`;
      div.addEventListener('click', () => selectNote(d));
      listEl.appendChild(div);
    }
  }

  function selectNote(day) {
    selectedDay = day;
    const task = CURRICULUM.find(c => c.day === day);
    document.getElementById('note-editor-title').textContent = `Day ${day}: ${task ? task.topic : ''}`;
    const textarea = document.getElementById('note-text');
    textarea.value = db.getNote(day);
    textarea.disabled = false;
    document.getElementById('save-note').disabled = false;
    populateList(search.value);
  }

  document.getElementById('save-note').addEventListener('click', () => {
    if (selectedDay) {
      db.saveNote(selectedDay, document.getElementById('note-text').value);
      populateList(search.value);
      showToast('Note saved');
    }
  });

  search.addEventListener('input', () => populateList(search.value));
  populateList();
}

// ── Settings ──────────────────────────────────────────

function renderSettings(el) {
  const stats = db.getProgress();
  el.innerHTML = `
    <h2 class="page-title">Settings</h2>
    <div class="card">
      <div class="card-title">Data Management</div>
      <div class="btn-group mb-12">
        <button class="btn" id="export-json">Export as JSON</button>
        <button class="btn btn-danger" id="reset-data">Reset All Data</button>
      </div>
      <p class="muted">Export saves all tasks, notes, and reviews as a JSON file. Reset clears all progress.</p>
    </div>
    <div class="card">
      <div class="card-title">About</div>
      <p>AI Security 90-Day Learning Planner</p>
      <p class="secondary mt-8">Start date: ${db.getStartDate()}</p>
      <p class="secondary mt-8">Total tasks: ${stats.total} | Completed: ${stats.completed}</p>
      <p class="muted mt-12">
        Phases: Foundations → AI/LLM → Red Teaming → Portfolio → Career Prep<br>
        Data stored in browser localStorage
      </p>
    </div>
  `;

  document.getElementById('export-json').addEventListener('click', () => db.exportJSON());
  document.getElementById('reset-data').addEventListener('click', () => {
    if (confirm('Reset ALL progress, notes, and reviews? This cannot be undone.')) {
      const keys = [];
      for (let i = 0; i < localStorage.length; i++) {
        const k = localStorage.key(i);
        if (k.startsWith('planner_')) keys.push(k);
      }
      keys.forEach(k => localStorage.removeItem(k));
      showToast('All data reset');
      render();
    }
  });
}

// ── Helpers ───────────────────────────────────────────

function esc(s) {
  if (!s) return '';
  const d = document.createElement('div');
  d.textContent = String(s);
  return d.innerHTML;
}

function showToast(msg) {
  let toast = document.getElementById('toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'toast';
    toast.style.cssText = 'position:fixed;bottom:24px;right:24px;background:var(--status-completed);color:#fff;padding:12px 24px;border-radius:8px;font-weight:600;z-index:999;opacity:0;transition:opacity 0.3s;pointer-events:none;';
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.style.opacity = '1';
  setTimeout(() => { toast.style.opacity = '0'; }, 2000);
}

// ── Init ──────────────────────────────────────────────

async function init() {
  try {
    const res = await fetch('js/curriculum.json');
    CURRICULUM = await res.json();
  } catch (e) {
    document.getElementById('content').innerHTML = '<p style="padding:40px;color:var(--status-overdue)">Failed to load curriculum data. Make sure curriculum.json is in js/ folder.</p>';
    return;
  }
  db.getStartDate();
  initNav();
  render();
}

init();
