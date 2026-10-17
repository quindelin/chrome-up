/* Per-course progress for the phone.

   Two panels, both data-only:
     Progress         - one row per course (lessons, words, minutes, streak)
                        plus a level-by-level breakdown of the active one
     Words learned    - every item you have passed the gate on, for whichever
                        course you pick, with search + level filter

   Self-contained on purpose: it needs nothing from app.js and no native
   code. The course switcher itself lives in app.js; this file only reads. */

(function () {
  const params = new URLSearchParams(location.search);
  const CLIENT = params.get('client_id') || 'default';

  const el = (id) => document.getElementById(id);
  const progressBox = () => el('progressPanel');
  const wordsBox = () => el('wordsPanel');

  let active = 'zh';
  let courses = [];
  let summaries = {};      // course id -> /api/progress payload
  let speechLang = {};
  let wordsCourse = null;  // which course's word list is on screen
  const filter = { kind: 'word', band: null, q: '' };

  /* ---------- server ---------- */
  async function getJSON(path) {
    const res = await fetch(path);
    if (!res.ok) throw new Error(path.replace(/\?.*/, '') + ' ' + res.status);
    return res.json();
  }

  const withClient = (path) =>
    path + (path.includes('?') ? '&' : '?') + 'client_id=' + encodeURIComponent(CLIENT);

  /* ---------- helpers ---------- */
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, (c) =>
      ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])
    );
  }

  function speak(text, lang) {
    if (!text || !window.speechSynthesis) return;
    const u = new SpeechSynthesisUtterance(text);
    u.lang = lang || speechLang[wordsCourse || active] || 'zh-CN';
    u.rate = 0.85;
    speechSynthesis.cancel();
    speechSynthesis.speak(u);
    if (navigator.vibrate) { try { navigator.vibrate(12); } catch (_) {} }
  }

  function bar(done, total) {
    const pct = total ? Math.min(100, Math.round((100 * done) / total)) : 0;
    return (
      `<div class="pbar"><div class="fill" style="width:${pct}%"></div>` +
      `<span class="plabel">${done} / ${total}</span></div>`
    );
  }

  /* ---------- progress: every course at a glance ---------- */
  function renderProgress() {
    const box = progressBox();
    if (!box) return;
    const ready = courses.filter((c) => c.ready);
    if (!ready.length) {
      box.innerHTML = `<div class="empty">No course is loaded yet.</div>`;
      return;
    }

    const rows = ready
      .map((c) => {
        const p = summaries[c.id] || {};
        return (
          `<div class="crow ${c.id === active ? 'on' : ''}">` +
          `<span class="cn">${esc(c.native)}</span>` +
          `<span class="cs">${p.lessons_done || 0}/${p.lessons_total || c.lessons} lessons</span>` +
          `<span class="cs">${p.words_learned || 0} words</span>` +
          `<span class="cs">${p.minutes || 0} min</span>` +
          `<span class="cs">${p.streak_days || 0}d streak</span>` +
          `</div>`
        );
      })
      .join('');

    const p = summaries[active] || {};
    const stat = (v, label) => `<div class="stat"><b>${v}</b><span>${label}</span></div>`;
    box.innerHTML =
      `<div class="crows">${rows}</div>` +
      `<div class="stats">` +
      stat(`${p.lessons_done || 0}<span class="of">/${p.lessons_total || 0}</span>`, 'lessons') +
      stat(`${p.words_learned || 0}<span class="of">/${p.words_total || 0}</span>`, 'words') +
      stat(p.phrases_learned || 0, 'lines') +
      stat(p.review_due || 0, 'due') +
      stat(p.streak_days || 0, 'day streak') +
      stat(p.minutes || 0, 'min speaking') +
      `</div>` +
      bar(p.lessons_done || 0, p.lessons_total || 0) +
      `<div class="bands">` +
      (p.bands || [])
        .map(
          (b) =>
            `<div class="band"><span class="code">${esc(b.code)}</span>` +
            `<span class="bt">${b.lessons_done}/${b.lessons_total} lessons · ` +
            `${b.words_learned}/${b.words_total} words</span></div>`
        )
        .join('') +
      `</div>` +
      (p.recent && p.recent.length
        ? `<div class="recent">Latest: ` +
          p.recent
            .slice(0, 6)
            .map(
              (r) =>
                `<button class="w" data-say="${esc(r.text)}">${esc(r.text)}</button>`
            )
            .join(' ') +
          `</div>`
        : '');

    box.querySelectorAll('[data-say]').forEach((n) =>
      n.addEventListener('click', () => speak(n.dataset.say, speechLang[active]))
    );
  }

  /* ---------- words learned ---------- */
  function renderWords(w) {
    const box = wordsBox();
    if (!box) return;
    const id = wordsCourse || active;
    const p = summaries[id] || {};
    const bands = p.bands || [];
    const langName = (courses.find((c) => c.id === id) || {}).native || id;

    box.innerHTML =
      `<div class="wtools">` +
      `<select id="wcourse">` +
      courses
        .filter((c) => c.ready)
        .map(
          (c) =>
            `<option value="${c.id}" ${c.id === id ? 'selected' : ''}>${esc(c.native)}</option>`
        )
        .join('') +
      `</select>` +
      `<input type="search" id="wq" placeholder="Search ${esc(langName)} / reading / English" value="${esc(filter.q)}" />` +
      `</div>` +
      `<div class="wtools">` +
      `<select id="wband"><option value="">all levels</option>` +
      bands
        .map(
          (b) =>
            `<option value="${b.band}" ${filter.band === b.band ? 'selected' : ''}>${esc(b.code)}</option>`
        )
        .join('') +
      `</select>` +
      `<select id="wkind">` +
      [['word', 'words only'], ['phrase', 'lines only'], ['', 'words + lines']]
        .map(
          ([v, t]) =>
            `<option value="${v}" ${filter.kind === v ? 'selected' : ''}>${t}</option>`
        )
        .join('') +
      `</select>` +
      `<span class="wcount">${w.total} learned</span>` +
      `</div>` +
      `<div class="wlist">` +
      (w.items.length
        ? w.items
            .map(
              (i) =>
                `<div class="wrow" data-say="${esc(i.text)}">` +
                `<span class="wt">${esc(i.text)}</span>` +
                `<span class="wr">${esc(i.reading || '')}</span>` +
                `<span class="we">${esc(i.en || '')}</span>` +
                `<span class="wm">${i.passes || 1}× · ${esc(i.last_day || '')}</span></div>`
            )
            .join('')
        : `<div class="empty">Nothing yet — pass a line and it lands here.</div>`) +
      `</div>`;

    el('wcourse').addEventListener('change', (e) => {
      wordsCourse = e.target.value;
      filter.band = null;
      loadWords();
    });
    const q = el('wq');
    let timer = null;
    q.addEventListener('input', () => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        filter.q = q.value;
        loadWords();
      }, 220);
    });
    el('wband').addEventListener('change', (e) => {
      filter.band = e.target.value === '' ? null : Number(e.target.value);
      loadWords();
    });
    el('wkind').addEventListener('change', (e) => {
      filter.kind = e.target.value;
      loadWords();
    });
    box.querySelectorAll('[data-say]').forEach((n) =>
      n.addEventListener('click', () => speak(n.dataset.say, speechLang[id]))
    );
  }

  async function loadWords() {
    const id = wordsCourse || active;
    const args = ['course=' + encodeURIComponent(id)];
    if (filter.kind) args.push('kind=' + encodeURIComponent(filter.kind));
    if (filter.band !== null && filter.band !== undefined) args.push('band=' + filter.band);
    if (filter.q) args.push('q=' + encodeURIComponent(filter.q));
    args.push('limit=200');
    try {
      renderWords(await getJSON(withClient('/api/progress/words?' + args.join('&'))));
    } catch (err) {
      const box = wordsBox();
      if (box) box.innerHTML = `<div class="empty">${esc(err.message)}</div>`;
    }
  }

  /* ---------- refresh ---------- */
  async function refresh() {
    try {
      const list = await getJSON(withClient('/api/courses'));
      courses = list.courses || [];
      active = list.active || active;
      if (!wordsCourse) wordsCourse = active;
      courses.forEach((c) => {
        if (c.speech_lang) speechLang[c.id] = c.speech_lang;
      });
      for (const c of courses) {
        if (!c.ready) continue;
        try {
          summaries[c.id] = await getJSON(withClient('/api/progress?course=' + c.id));
        } catch (_) { /* one broken course must not blank the screen */ }
      }
      renderProgress();
      await loadWords();
    } catch (err) {
      const box = progressBox();
      if (box) box.innerHTML = `<div class="empty">${esc(err.message)}</div>`;
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    if (!progressBox() && !wordsBox()) return;
    refresh();
    setInterval(refresh, 20000);      // the lesson moves; keep the numbers honest
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) refresh();
    });
    window.addEventListener('lingualens:refresh', refresh);
  });

  window.LinguaLensProgress = { refresh, speak };
})();
