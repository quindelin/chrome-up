/* LinguaLens client - shared by the glasses display and the phone companion.
   Language-agnostic: the server tells us which course is loaded and what
   BCP-47 tag to speak / dictate with, so this file works for Mandarin and for
   Japanese without branching.

   Glasses web apps get no microphone, so the phone page is the one that
   records; both stay in sync over a websocket.

   Haptic / input model (Meta Ray-Ban Display):
     Neural Band swipe or temple swipe  -> ArrowUp / ArrowDown / ArrowLeft
     tap (thumb-index pinch)            -> Enter
     swipe back / long press            -> Escape
   Every meaningful action fires a haptic through the native bridge if the
   wrapper injected one, with navigator.vibrate as a fallback. */

const params = new URLSearchParams(location.search);
const CLIENT = params.get('client_id') || 'default';
const IS_PHONE = document.body.dataset.page === 'phone';
// The glasses Web App runtime exposes one TTS voice, en-US, and ignores
// `lang` (webapps/build/text-to-speech), so it would read 你好 / こんにちは
// with an English voice. Model audio therefore comes from the phone page, or
// from the native wrapper's WebView (which plays through the glasses
// speakers over Bluetooth). On the glasses the page only shows.
const AUDIO_HOST = IS_PHONE || !!window.LinguaLensHaptics;
// ?view=stream: the copy OBS shows on stream. Read-only (never advances the
// lesson, never speaks) and drawn as a translucent panel instead of black.
const STREAM_VIEW = params.get('view') === 'stream';
// <html> is black too, so both get the class
if (STREAM_VIEW) { document.documentElement.classList.add('stream'); document.body.classList.add('stream'); }

let state = null;
let course = null;
let showEnglish = false;
let showNotes = false;
let spokenKey = '';
let ws = null;

const el = (id) => document.getElementById(id);

/* ---------- haptics ---------- */
function haptic(kind = 'tick') {
  // native DAT wrapper injects this bridge; otherwise try the vibration API
  const bridge = window.LinguaLensHaptics;
  if (bridge && typeof bridge.play === 'function') {
    try { bridge.play(kind); return; } catch (_) { /* fall through */ }
  }
  const patterns = { tick: 12, select: 28, back: 18, pass: [20, 40, 20], fail: [60, 30, 60] };
  if (navigator.vibrate) {
    try { navigator.vibrate(patterns[kind] || 15); } catch (_) { /* ignore */ }
  }
  try {
    window.parent && window.parent.postMessage({ type: 'haptic', kind }, '*');
  } catch (_) { /* ignore */ }
}

/* ---------- language helpers ---------- */
function lang() { return (state && state.language) || 'zh'; }
function speechLang() { return (state && state.speech_lang) || (lang() === 'ja' ? 'ja-JP' : 'zh-CN'); }
function langPrefix() { return speechLang().split('-')[0].toLowerCase(); }

// 声调 for Mandarin, アクセント for Japanese - the suprasegmental score label
function toneLabel() { return lang() === 'ja' ? 'アクセント' : '声调'; }
function youSaidLabel() { return lang() === 'ja' ? 'あなたは' : '你说'; }

// Reading, literacy and listening used to be Japanese-only, so their on-screen
// labels were Japanese strings written straight into render(). Now Mandarin has
// passages, 汉字 and an audio-only step too, and '読む' above a Chinese
// sentence is simply wrong - so the labels follow the language.
const STEP_LABELS = {
  ja: { read: '読む', literacy: '漢字', hearing: '聞く', writing: '要約' },
  zh: { read: '读', literacy: '汉字', hearing: '听', writing: '缩写' },
  es: { read: 'Leer', literacy: 'Letras', hearing: 'Escuchar', writing: 'Resumen' },
};
// a course's meta.py may declare its own labels (state.config.step_labels)
function stepLabels() {
  const own = (state && state.config && state.config.step_labels) || {};
  return Object.assign({}, STEP_LABELS[lang()] || STEP_LABELS.zh, own);
}
function readingLabel() { return stepLabels().read; }
function literacyLabel() { return stepLabels().literacy; }
function hearingLabel() { return stepLabels().hearing; }
function writingLabel() { return stepLabels().writing; }
function vocabLabel() {
  return (state && state.config && state.config.vocab_label) || ({ ja: '単語', es: 'Vocabulario' }[lang()] || '词汇');
}

/* ---------- server calls ---------- */
async function api(path, body) {
  const opts = { method: 'POST' };
  if (body instanceof FormData) {
    opts.body = body;
  } else {
    opts.headers = { 'Content-Type': 'application/x-www-form-urlencoded' };
    opts.body = new URLSearchParams(body || {}).toString();
  }
  const res = await fetch(path, opts);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

/* ---------- websocket ---------- */
function connect() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  ws = new WebSocket(`${proto}://${location.host}/ws?client_id=${encodeURIComponent(CLIENT)}`);
  ws.onmessage = (e) => {
    const prev = state && state.last_score;
    state = JSON.parse(e.data);
    if (state.last_score && state.last_score !== prev) {
      haptic(state.last_score.passed ? 'pass' : 'fail');
    }
    render();
    mirrorToGlasses();
    // the ladder belongs to one course: load it on the first message and
    // reload it whenever the learner switches (loadCourse no-ops otherwise)
    loadCourse().then(() => { if (menu.open) renderMenu(); render(); });
  };
  ws.onclose = () => setTimeout(connect, 1500);
}

// Native display mode (Android wrapper + DAT mwdat-display): the wrapper
// redraws the current line itself, because a DAT display session hides the
// Web App. A no-op everywhere else.
function mirrorToGlasses() {
  const g = window.LinguaLensGlasses;
  if (!g || !state) return;
  try {
    // The server decides the card for every step kind (engine.glasses_card):
    // a recall shows its English cue, never a bare "…".
    if (g.showCard && state.glasses) {
      // `playing` labels the Start / Stop button drawn on the glasses
      g.showCard(JSON.stringify(Object.assign({}, state.glasses, { playing: recording })));
      // (the Android wrapper's native glasses-mic take sets its own label)
      return;
    }
    const s = state.step;
    if (!s) return;
    const hidden = s.kind === 'hear';
    g.showLine(hidden ? '' : s.text || s.prompt_en || '',
               hidden || s.show_reading === false ? '' : s.reading || '', s.en || s.prompt_en || '');
  } catch (_) { /* wrapper not ready */ }
}

// The Redo / Start / Skip buttons drawn on the glasses (Android wrapper,
// GlassesBridge) call back in here: the same actions as the phone controls.
window.glassesCommand = (cmd) => {
  const s = state && state.step;
  if (cmd === 'repeat') {
    if (s && s.kind === 'hear') playHidden(s);
    else if (s && s.text) speak(s.text, 0.6);
  } else if (cmd === 'playPause') {
    toggleRecord();
  } else if (cmd === 'next') {
    maybeAdvance();
  }
};

/* ---------- text to speech (native model audio) ---------- */
// A course that only ever plays one voice is teaching you to understand one
// voice. Real listening means several: different pitches, different
// timbres, different habits of phrasing. Most platforms ship three or four
// voices per language and this used to take whichever matched first and
// never let go of it, so the learner met exactly one speaker for a year.
let modelVoices = [];
let modelVoiceLang = '';
let voiceCursor = 0;

function pickVoices() {
  const want = langPrefix();
  if (modelVoices.length && modelVoiceLang === want) return modelVoices;
  const all = window.speechSynthesis ? speechSynthesis.getVoices() : [];
  const matched = all.filter((v) => (v.lang || '').toLowerCase().startsWith(want));
  // A "remote"/network voice is usually the good one, but it is also the
  // one that stalls; keep them, they are still a distinct speaker.
  modelVoices = matched;
  modelVoiceLang = want;
  voiceCursor = 0;
  return modelVoices;
}

// One voice per line, round-robin. Deterministic rather than random, so
// that repeating a line does not reroll the speaker mid-drill and make the
// learner think they misheard.
function pickVoice() {
  const voices = pickVoices();
  if (!voices.length) return null;
  const v = voices[voiceCursor % voices.length];
  voiceCursor += 1;
  return v;
}
if (window.speechSynthesis) speechSynthesis.onvoiceschanged = pickVoices;

// Rate comes from config: the model line no longer drops to 0.9 by reflex.
// Slowing everything down teaches you to understand slowed speech, which is
// not a thing anyone will say to you.
function rateFor(kind, fallback) {
  const r = (state && state.config && state.config.listening_rate) || {};
  if (kind === 'natural') return r.natural ?? r.listen ?? fallback;
  if (kind === 'listen') return r.listen ?? fallback;
  if (kind === 'slow') return r.slow ?? fallback;
  if (kind === 'drill') return r.drill ?? fallback;
  return r.model ?? fallback;
}

function speak(text, rate = 0.9, opts = {}) {
  if (!text || !window.speechSynthesis) return null;
  const u = new SpeechSynthesisUtterance(text);
  u.lang = speechLang();
  u.rate = rate;
  const v = opts.voice !== undefined ? opts.voice : pickVoice();
  if (v) u.voice = v;
  // A second speaker is not only a different voice: nudging the pitch is
  // what stops three synth voices from sounding like one synth voice with a
  // cold. Kept small so it never sounds like a cartoon.
  const vary = !(state && state.config && state.config.listening_vary_pitch === false);
  if (vary && v) u.pitch = 0.85 + ((voiceCursor * 7) % 5) * 0.07;
  speechSynthesis.cancel();
  speechSynthesis.speak(u);
  return u;
}

// A blind step is a whole passage or a whole dialogue, played part by part.
// Each part names its speaker (audio_voices), and each speaker keeps one
// voice for the whole step, so a dialogue is two people, not one. Below the
// natural bands the narrator is always the same familiar voice at the
// listening rate; from them (s.natural) the voices rotate from step to step
// and nothing is slowed down.
function playHidden(s, done) {
  const parts = (s.audio_parts && s.audio_parts.length) ? s.audio_parts : [s.audio_text || s.text];
  const who = s.audio_voices || [];
  const voices = pickVoices();
  const rotate = !(state && state.config && state.config.listening_rotate_voices === false);
  const base = s.natural && rotate ? voiceCursor++ : 0;
  const rate = s.natural ? rateFor('natural', 1.1) : rateFor('listen', 1.0);
  let i = 0;
  const next = () => {
    if (i >= parts.length) { if (done) done(); return; }
    const v = voices.length ? voices[(base + (who[i] || 0)) % voices.length] : undefined;
    const u = speak(parts[i], rate, { voice: v });
    i += 1;
    if (!u) { if (done) done(); return; }
    u.onend = () => setTimeout(next, s.natural ? 150 : 400);
  };
  next();
}

/* ---------- menu (levels -> units -> lessons) ---------- */
const menu = { open: false, path: [], index: 0 };

let courseLangLoaded = '';

async function loadCourse(force) {
  const lang = (state && state.active) || '';
  if (!force && lang && lang === courseLangLoaded && course) return;
  const res = await fetch('/api/course' + (lang ? `?course=${encodeURIComponent(lang)}` : ''));
  const data = await res.json();
  if (!data || !data.levels) return;   // course not ready: keep the old ladder
  course = data;
  courseLangLoaded = lang;
  spokenKey = '';
  if (IS_PHONE) buildLessonPicker();
}

async function switchCourse(lang) {
  haptic('select');
  try {
    await api('/api/course/select', { client_id: CLIENT, course: lang });
    await loadCourse(true);
  } catch (err) {
    if (el('message')) el('message').textContent = 'Course switch failed: ' + err.message;
  }
}

function renderCourses() {
  const box = el('courseBtns');
  if (!box || !state || !state.courses) return;
  box.innerHTML = state.courses
    .map(
      (c) =>
        `<button class="ghost ${c.active ? '' : ''}" data-course="${c.id}"` +
        `${c.ready ? '' : ' disabled'} style="${c.active ? 'border-color:var(--accent);color:var(--accent)' : ''}">` +
        `${c.native || c.id}${c.ready ? '' : ' (…)'}</button>`
    )
    .join('');
  box.querySelectorAll('button[data-course]').forEach((b) => {
    b.addEventListener('click', () => switchCourse(b.dataset.course));
  });
  const active = state.courses.find((c) => c.active) || {};
  const stats = el('courseStats');
  if (stats) {
    stats.textContent = active.ready
      ? `${active.name} · ${active.lessons_done || 0}/${active.lessons} lessons · `
        + `${active.words_learned || 0} words · ${active.minutes || 0} min · `
        + `${active.streak_days || 0}-day streak · ${active.review_due || 0} due`
      : active.error || '';
  }
  const badge = el('course');
  if (badge) badge.textContent = (state.native || state.language_name || '').toString();
}

function menuRows() {
  if (!menu.path.length) {
    const rows = [
      { label: 'Continue', sub: state && state.lesson ? `L${state.lesson.id} · ${state.lesson.title}` : 'L1', act: 'continue' },
      { label: 'Review', sub: `${(state && state.review_due) || 0} lines due`, act: 'review' },
      { label: 'Switch course', sub: state ? `${state.native} · ${state.language_name}` : '', act: 'courses' },
    ];
    (course ? course.levels : []).forEach((lv) => {
      rows.push({ label: lv.code, sub: `${lv.title} · ${lv.lesson_count} lessons`, act: 'level', id: lv.id });
    });
    return rows;
  }
  const at = menu.path[menu.path.length - 1];
  if (at.type === 'courses') {
    return (state && state.courses ? state.courses : []).map((c) => ({
      label: `${c.native || ''} · ${c.name}`,
      sub: c.ready
        ? `${c.lessons} lessons · ${c.vocab} words${c.active ? ' · studying now' : ''}`
        : c.error || 'not ready',
      act: 'course',
      id: c.id,
      ready: c.ready,
    }));
  }
  if (at.type === 'level') {
    const lv = course.levels.find((l) => l.id === at.id);
    const rows = lv.units.map((u) => ({ label: u.title, sub: `${u.lessons.length} lessons`, act: 'unit', id: u.id }));
    if (lv.vocab_topics && lv.vocab_topics.length) {
      rows.push({
        label: `${vocabLabel()} Vocabulary`,
        sub: `${lv.vocab_count} words · ${lv.vocab_topics.length} topics`,
        act: 'vocab',
        id: lv.id,
      });
    }
    return rows;
  }
  if (at.type === 'vocab') {
    const lv = course.levels.find((l) => l.id === at.id);
    return (lv.vocab_topics || []).map((t) => ({
      label: `${t.title_native} · ${t.title}`,
      sub: `${t.count} words`,
      act: 'topic',
      id: t.id,
    }));
  }
  if (at.type === 'unit') {
    for (const lv of course.levels) {
      const u = lv.units.find((x) => x.id === at.id);
      if (u) {
        return u.lessons.map((l) => ({
          label: `L${l.id} ${l.title}`,
          sub: l.goal,
          act: 'lesson',
          id: l.id,
        }));
      }
    }
  }
  return [];
}

function renderMenu() {
  const box = el('menu');
  if (!box) return;
  if (!menu.open || !course) {
    box.classList.add('hidden');
    return;
  }
  box.classList.remove('hidden');
  const rows = menuRows();
  menu.index = Math.max(0, Math.min(menu.index, rows.length - 1));
  const crumb = menu.path.length
    ? menu.path.map((p) => p.title).join('  ›  ')
    : 'LinguaLens';
  box.innerHTML =
    `<div class="crumb">${crumb}</div>` +
    `<div class="list">` +
    rows
      .map(
        (r, i) =>
          `<div class="item ${i === menu.index ? 'sel' : ''}"><span class="t">${r.label}</span>` +
          `<span class="s">${r.sub || ''}</span></div>`
      )
      .join('') +
    `</div>` +
    `<div class="keyhint">↑↓ move · ⏎ open · esc back</div>`;
}

function menuMove(delta) {
  const rows = menuRows();
  if (!rows.length) return;
  menu.index = (menu.index + delta + rows.length) % rows.length;
  haptic('tick');
  renderMenu();
}

async function menuSelect() {
  const rows = menuRows();
  const row = rows[menu.index];
  if (!row) return;
  haptic('select');
  if (row.act === 'continue') {
    menu.open = false;
    navReset();
    renderMenu();
    render();
    return;
  }
  if (row.act === 'review') {
    await api('/api/review/start', { client_id: CLIENT, limit: 20 });
    menu.open = false;
    navReset();
    renderMenu();
    return;
  }
  if (row.act === 'courses') {
    navPush();
    menu.path.push({ type: 'courses', title: 'Course' });
    menu.index = 0;
    renderMenu();
    return;
  }
  if (row.act === 'course') {
    if (!row.ready) { haptic('fail'); return; }
    await switchCourse(row.id);
    menu.open = false;
    navReset();
    menu.path = [];
    menu.index = 0;
    renderMenu();
    return;
  }
  if (row.act === 'level') {
    const lv = course.levels.find((l) => l.id === row.id);
    navPush();
    menu.path.push({ type: 'level', id: lv.id, title: lv.code });
    menu.index = 0;
    renderMenu();
    return;
  }
  if (row.act === 'vocab') {
    const lv = course.levels.find((l) => l.id === row.id);
    navPush();
    menu.path.push({ type: 'vocab', id: lv.id, title: `${lv.code} ${vocabLabel()}` });
    menu.index = 0;
    renderMenu();
    return;
  }
  if (row.act === 'topic') {
    await api('/api/vocab/start', { client_id: CLIENT, topic_id: row.id });
    menu.open = false;
    navReset();
    menu.path = [];
    menu.index = 0;
    renderMenu();
    return;
  }
  if (row.act === 'unit') {
    for (const lv of course.levels) {
      const u = lv.units.find((x) => x.id === row.id);
      if (u) {
        navPush();
    menu.path.push({ type: 'unit', id: u.id, title: u.title });
        menu.index = 0;
        renderMenu();
        return;
      }
    }
    return;
  }
  if (row.act === 'lesson') {
    await api('/api/lesson/start', { client_id: CLIENT, lesson_id: row.id });
    menu.open = false;
    navReset();
    menu.path = [];
    menu.index = 0;
    renderMenu();
    return;
  }
}

function menuBack() {
  if (!menu.open) return;
  haptic('back');
  if (menu.path.length) {
    menu.path.pop();
    menu.index = 0;
  } else {
    menu.open = false;
  }
  renderMenu();
}

function toggleMenu() {
  menu.open = !menu.open;
  menu.index = 0;
  if (menu.open) { menu.path = []; navPush(); } else navReset();
  haptic(menu.open ? 'select' : 'back');
  renderMenu();
  render();
}

/* ---------- main rendering ---------- */
/* ---------- Back ----------------------------------------------------------- */
// On the glasses Back is not a keypress. The shell calls history.back() when
// there is an entry to go back to, and otherwise opens the system menu (a
// second Back there exits the app) - webapps/build "Back navigation". So
// every overlay we open (menu, each menu level, the grammar page) pushes one
// entry, and popstate is what closes it. Escape still works for desktop and
// phone testing by going through the same history. The shell keeps at most
// five entries including the root, hence the cap.
let navDepth = 0;
let draining = false;

function navPush() {
  if (navDepth >= 4) return;
  history.pushState({ ll: navDepth + 1 }, '');
  navDepth += 1;
}

// An overlay closed by a selection, not by Back: drop the entries it owned so
// the next Back is not swallowed by a stale one.
function navReset() {
  if (!navDepth) return;
  const n = navDepth;
  navDepth = 0;
  draining = true;
  history.go(-n);
}

function goBack() {
  if (navDepth) history.back();
  else if (grammarPage) closeGrammar();
  else if (menu.open) menuBack();
}

window.addEventListener('popstate', () => {
  if (draining) { draining = false; return; }
  navDepth = Math.max(0, navDepth - 1);
  if (grammarPage) closeGrammar();
  else if (menu.open) menuBack();
});

/* ---------- the grammar page ------------------------------------------- */
// One page per lesson, stating the point, the formula, and two examples.
// Reachable from anywhere with a press, because a rule is worth looking up
// at the moment it confuses you, not on a schedule.
let grammarPage = null;
let grammarIdx = 0;

function openGrammar() {
  if (grammarPage) {
    grammarIdx = (grammarIdx + 1) % Math.max(1, grammarPage.length);
    render();
    return;
  }
  const rows = (state && state.grammar) || [];
  if (!rows.length) { haptic('fail'); return; }
  grammarPage = rows;
  grammarIdx = 0;
  navPush();
  render();
}

function closeGrammar() {
  grammarPage = null;
  grammarIdx = 0;
  render();
}

function renderGrammarPage() {
  const rows = grammarPage || [];
  const row = rows[grammarIdx] || {};
  el('role').textContent = '文法';
  el('role').className = 'role them';
  el('target').textContent = row.point || '';
  el('target').className = 'target short';
  el('reading').textContent = row.formula || '';
  el('en').textContent = row.en || '';
  el('en').classList.remove('hidden');
  const ex = (row.examples || [])[0];
  el('cue').textContent = ex ? `${ex[0]}  —  ${ex[2]}` : '';
  el('note').textContent = row.contrast || row.watch || `${grammarIdx + 1} / ${rows.length}`;
  const box = el('sample');
  if (box) box.classList.add('hidden');
  el('scorebox').innerHTML = '';
  if (IS_PHONE) el('mic').disabled = true;
}

function render() {
  if (!state) return;
  if (grammarPage) { renderGrammarPage(); return; }
  const s = state.step;
  const kind = s ? s.kind : 'done';

  const code = state.level ? state.level.code : '';
  el('lesson').textContent = state.topic
    ? `${vocabLabel()} · ${state.topic.title_native} ${state.topic.title}`
    : state.lesson
    ? `${code} · L${state.lesson.id} ${state.lesson.title}`
    : '—';
  el('progress').textContent = `${state.position.index + (s ? 1 : 0)}/${state.position.total}`;
  const badge = el('provider');
  if (badge) {
    badge.textContent = state.provider === 'iflytek' ? `iflytek · ${toneLabel()}` : state.provider;
    badge.className = 'badge ' + (state.provider === 'mock' ? 'mock' : 'live');
  }
  const locale = el('locale');
  if (locale) locale.textContent = state.speech_lang || '';
  const thinkTitle = el('thinktitle');
  if (thinkTitle) {
    thinkTitle.textContent = `Think in ${state.language_name || 'the language'}`;
  }
  renderCourses();

  const role = el('role');
  const reading = el('reading');
  const target = el('target');
  const english = el('en');
  const cue = el('cue');
  const note = el('note');
  const wait = el('wait');
  const sample = el('sample');

  cue.textContent = '';
  note.textContent = '';
  wait.textContent = '';
  reading.textContent = '';
  target.textContent = '';
  target.className = 'target';
  english.textContent = '';
  if (sample) {
    sample.textContent = '';
    sample.classList.add('hidden');
  }

  if (!s) {
    role.textContent = 'done';
    role.className = 'role pass';
    target.textContent = lang() === 'ja' ? 'コース完了' : '课程完成';
    english.textContent = 'Course complete.';
    renderScore();
    return;
  }

  if (kind === 'info') {
    // round 0 info steps are the scene; the numbered ones open a recall round
    const isScene = !s.round;
    role.textContent = isScene ? 'scene' : 'recall';
    role.className = 'role ' + (isScene ? 'scene' : 'recall');
    cue.textContent = s.en;
    // a scene is a whole sentence, so it gets a smaller, wrapping face
    cue.className = isScene ? 'cue scene' : 'cue';
    if (s.wait_seconds > 0) startCountdown(s.wait_seconds, wait);
    else maybeAdvance();
    renderScore();
    return;
  }

  // free response: the model asks, you answer. Nothing is scripted.
  // A role-play turn (`converse`) is the same shape: the other speaker's
  // line on screen, your reply graded - it just comes back with a new line.
  if (kind === 'answer' || kind === 'converse') {
    const talk = kind === 'converse';
    role.textContent = talk ? 'talk' : 'answer';
    role.className = 'role answer';
    target.textContent = s.text || '';
    const qlen = (s.text || '').length;
    target.className = 'target ' + (qlen <= 9 ? 'short' : 'long');
    reading.textContent = s.show_reading === false ? '' : s.reading || '';
    english.textContent = s.en || '';
    english.classList.remove('hidden');
    cue.textContent = talk
      ? `Reply as yourself · turn ${(s.turn || 0) + 1} of ${s.turns || 1}`
      : 'Answer in the language';
    if (s.show_sample && s.sample && s.sample.text && sample) {
      sample.classList.remove('hidden');
      sample.innerHTML =
        `<span class="lbl">${talk ? 'one reply' : 'one answer'}</span>` +
        `<span class="rd">${s.sample.reading || ''}</span>` +
        `<span class="tg">${s.sample.text}</span>`;
    }
    renderScore();
    if (IS_PHONE) {
      renderLog();
      el('mic').disabled = recording;
      el('message').textContent = state.message || '';
    }
    maybeSpeak();
    return;
  }

  // A 缩写: say the passage back, shorter. Shown like a question, but the
  // cue says what is being graded - keeping the point, not the wording -
  // because the instinct is to repeat the passage instead.
  if (kind === 'write') {
    role.textContent = writingLabel();
    role.className = 'role answer';
    target.textContent = s.text || '';
    target.className = 'target long';
    reading.textContent = s.show_reading === false ? '' : s.reading || '';
    english.textContent = s.en || '';
    english.classList.remove('hidden');
    cue.textContent = 'Say it back shorter - keep the point, not the words';
    if (s.show_sample && s.sample && s.sample.text && sample) {
      sample.classList.remove('hidden');
      sample.innerHTML =
        '<span class="lbl">one summary</span>' +
        `<span class="rd">${s.sample.reading || ''}</span>` +
        `<span class="tg">${s.sample.text}</span>`;
    }
    renderScore();
    if (IS_PHONE) {
      renderLog();
      el('mic').disabled = recording;
      el('message').textContent = state.message || '';
    }
    maybeSpeak();
    return;
  }

  // --- literacy: kana and kanji ------------------------------------------
  // Neither is speech-gated. You look at あ and ア together, or at 日 with
  // its two readings kept apart, and press on. They are taught, not drilled:
  // what makes them stick is meeting them in the lines that follow.
  if (kind === 'kana') {
    role.textContent = 'かな';
    role.className = 'role them';
    target.textContent = s.text || '';
    target.className = 'target short';
    reading.textContent = s.reading || '';
    english.textContent = '';
    english.classList.add('hidden');
    cue.textContent = s.alt ? `${s.alt_label || 'カタカナ'}　${s.alt}` : '';
    note.textContent = showNotes ? s.note || '' : '';
    renderScore();
    if (IS_PHONE) { el('mic').disabled = true; el('message').textContent = state.message || ''; }
    return;
  }

  if (kind === 'kanji') {
    role.textContent = '漢字';
    role.className = 'role them';
    target.textContent = s.text || '';
    target.className = 'target short';
    const on = s.reading && s.reading !== '—' ? `音 ${s.reading}` : '';
    const kun = s.kun && s.kun !== '—' ? `　訓 ${s.kun}` : '';
    reading.textContent = on + kun;
    english.textContent = s.en || '';
    english.classList.remove('hidden');
    cue.textContent = s.note || '';
    note.textContent = '';
    renderScore();
    if (IS_PHONE) { el('mic').disabled = true; el('message').textContent = state.message || ''; }
    return;
  }

  // Mandarin's counterpart to the kanji step. A character is shown with its
  // 部首 and its 部件, because 妈 is 女 + 马 and noticing that is the whole
  // difference between memorising a drawing and learning a system. Not
  // speech-gated: you look at it, you do not recite it.
  if (kind === 'hanzi') {
    role.textContent = literacyLabel();
    role.className = 'role them';
    target.textContent = s.text || '';
    target.className = 'target short';
    reading.textContent = s.reading || '';
    english.textContent = s.en || '';
    english.classList.remove('hidden');
    // 部首 first: it is the half that carries the meaning, and it is the
    // heading you would look the character up under.
    const rad = s.radical ? `${s.alt_label || '部首'} ${s.radical}` : '';
    cue.textContent = [rad, s.components || ''].filter(Boolean).join('　·　');
    note.textContent = s.note || '';
    renderScore();
    if (IS_PHONE) { el('mic').disabled = true; el('message').textContent = state.message || ''; }
    return;
  }

  // --- reading ------------------------------------------------------------
  // A passage, one sentence at a time, read aloud. The English stays folded
  // away: reading is not translating, and having the translation on screen
  // turns it into translation.
  if (kind === 'read') {
    role.textContent = readingLabel();
    role.className = 'role you';
    target.textContent = s.text || '';
    target.className = 'target long';
    reading.textContent = s.show_reading === false ? '' : s.reading || '';
    english.textContent = s.en || '';
    english.classList.toggle('hidden', !showEnglish);
    cue.textContent = s.chunk_total ? `${s.chunk_index} / ${s.chunk_total}` : '';
    note.textContent = s.passage_title || '';
    renderScore();
    if (IS_PHONE) {
      renderLog();
      el('mic').disabled = recording;
      el('message').textContent = state.message || '';
    }
    return;
  }

  // --- listening ----------------------------------------------------------
  // The only step with a blank screen. Everything else in a lesson is printed
  // while it is spoken, so nothing else is actually listening practice; here
  // the line plays and the question after it can only be answered from what
  // was heard. `audio_text` is deliberately not `text` - see maybeSpeak.
  if (kind === 'hear') {
    role.textContent = hearingLabel();
    role.className = 'role them';
    target.textContent = '';
    target.className = 'target short';
    reading.textContent = '';
    english.textContent = s.en || '';
    english.classList.remove('hidden');
    // everything the step says is hidden by hide_text, so the instruction
    // itself has to be visible: 只听，不看 is all the learner should see
    cue.textContent = s.note || '只听，不看';
    note.textContent = '';
    renderScore();
    if (IS_PHONE) { el('mic').disabled = true; el('message').textContent = state.message || ''; }
    maybeSpeak();
    return;
  }

  role.textContent = kind === 'listen' ? 'listen' : kind === 'recall' ? 'recall' : 'speak';
  role.className = 'role ' + (kind === 'listen' ? 'them' : kind === 'recall' ? 'recall' : 'you');

  if (kind === 'recall' && !s.show_target) {
    // Anticipation: hold the English back for a few seconds, so the first
    // thing you try is retrieval from memory rather than reading a gloss.
    // The cue then arrives as a rescue for a blank, not as the prompt.
    const akey = `${state.position.index}:${s.text}`;
    if (s.wait_seconds > 0 && anticipationKey !== akey) {
      startAnticipation(akey, s.wait_seconds);
    }
    if (s.wait_seconds > 0 && anticipationLeft > 0) {
      cue.textContent = '';
      wait.textContent = `${anticipationLeft}s`;
    } else {
      cue.textContent = s.prompt_en || s.en;
    }
    english.textContent = 'Say it in the language.';
  } else {
    // the reading line fades out as you climb the ladder
    reading.textContent = s.show_reading === false ? '' : s.reading || '';
    target.textContent = s.text || '';
    const len = (s.text || '').length;
    target.className = 'target ' + (len <= 4 ? 'short' : len > 9 ? 'long' : '');
    english.textContent = s.en || '';
  }

  english.classList.toggle('hidden', !showEnglish && kind !== 'recall');
  // at the top bands the scene is not printed; it is still one press away
  note.textContent = showNotes ? s.note || state.scene || '' : '';

  renderScore();
  if (IS_PHONE) {
    renderLog();
    el('mic').disabled = !(kind === 'speak' || kind === 'recall' || kind === 'answer' || kind === 'read') || recording;
    el('message').textContent = state.message || '';
  }
  maybeSpeak();
}

function renderScore() {
  const box = el('scorebox');
  const sc = state.last_score;
  if (!sc) {
    box.innerHTML = '';
    return;
  }
  const ok = sc.passed;
  const tone = sc.tone >= 0 ? ` · ${toneLabel()} ${Math.round(sc.tone)}` : '';
  const worst = (sc.syllables || []).length
    ? sc.syllables.reduce((a, b) => (b.tone >= 0 && b.tone < (a.tone >= 0 ? a.tone : 999) ? b : a))
    : null;
  box.innerHTML =
    `<div class="score"><div class="value ${ok ? 'ok' : 'bad'}">${Math.round(sc.pron || 0)}</div>` +
    `<div class="label">${ok ? 'passed' : 'not yet'} · ${state.attempts} attempt${state.attempts === 1 ? '' : 's'}${tone}</div></div>` +
    `<div class="bars">${['accuracy', 'fluency', 'completeness']
      .map((k) => `<div class="${(sc[k] || 0) >= 70 ? 'on' : ''}" title="${k} ${Math.round(sc[k] || 0)}"></div>`)
      .join('')}</div>` +
    (worst && worst.tone >= 0 && worst.tone < 70
      ? `<div class="tonebad">${toneLabel()}: ${worst.word} ${Math.round(worst.tone)}</div>`
      : '') +
    (sc.recognized && state.step && ['answer', 'converse'].includes(state.step.kind)
      ? `<div class="heard">${youSaidLabel()} ${sc.recognized}</div>`
      : '') +
    (sc.reasons && sc.reasons.length
      ? `<div class="reasons">${sc.reasons.slice(0, 2).join(' · ')}</div>`
      : '');
}

function renderLog() {
  const log = el('log');
  if (!log) return;
  log.innerHTML = (state.history || [])
    .slice()
    .reverse()
    .map(
      (h) =>
        `<div>${h.passed ? '✔' : '✘'} ${h.text} — ${Math.round(h.score)} (try ${h.attempt})</div>`
    )
    .join('');
}

/* ---------- pacing ---------- */
let countdownTimer = null;

/* The anticipation gap. `startCountdown` here would advance the step when it
   expires, which is the opposite of what we want: a recall step has to wait
   for the learner to speak. This one only counts, then re-renders so the
   English cue appears. */
let anticipationKey = '';
let anticipationLeft = 0;
let anticipationTimer = null;
function startAnticipation(key, seconds) {
  clearInterval(anticipationTimer);
  anticipationKey = key;
  anticipationLeft = Math.ceil(seconds);
  anticipationTimer = setInterval(() => {
    anticipationLeft -= 1;
    if (anticipationLeft <= 0) clearInterval(anticipationTimer);
    render();
  }, 1000);
}

function startCountdown(seconds, node) {
  clearInterval(countdownTimer);
  let left = Math.ceil(seconds);
  node.textContent = `${left}s`;
  countdownTimer = setInterval(() => {
    left -= 1;
    node.textContent = left > 0 ? `${left}s` : '';
    if (left <= 0) {
      clearInterval(countdownTimer);
      maybeAdvance();
    }
  }, 1000);
}

async function maybeAdvance() {
  if (STREAM_VIEW) return;
  const s = state.step;
  // Steps you do not speak move on by themselves or on a press. The server
  // refuses to skip anything gated, so asking is always safe here.
  if (!s || !['listen', 'info', 'kana', 'kanji', 'hanzi', 'hear'].includes(s.kind)) return;
  await api('/api/next', { client_id: CLIENT, at: state.position.index });
}

function maybeSpeak() {
  const s = state.step;
  if (!s || !AUDIO_HOST) return;
  const key = `${state.position.index}:${s.kind}:${s.text}:${state.attempts}`;
  if (key === spokenKey) return;
  spokenKey = key;

  if (s.kind === 'listen') {
    // the model line, at something close to how it would actually be said
    const u = speak(s.text, rateFor('listen', 0.9));
    if (!u) return maybeAdvance();
    u.onend = () => setTimeout(maybeAdvance, 350);
    return;
  }
  if (s.kind === 'hear') {
    // The one step with nothing on the screen. The words live in audio_text /
    // audio_parts because the client has to be able to play something it
    // must not show - if they were in `text` they would be on the glasses a
    // frame later.
    playHidden(s, () => setTimeout(maybeAdvance, 350));
    return;
  }
  if (s.kind === 'converse') {
    // the other speaker: a voice that is not the narrator's, and at the top
    // bands at the speed they would actually talk
    const voices = pickVoices();
    const v = voices.length ? voices[1 % voices.length] : undefined;
    const rate = state.attempts > 0 ? rateFor('slow', 0.6)
      : s.natural ? rateFor('natural', 1.1) : rateFor('model', 0.9);
    speak(s.text, rate, { voice: v });
    return;
  }
  if (s.kind === 'answer') {
    // ask the question out loud, slower if you have already missed it once
    speak(s.text, state.attempts > 0 ? rateFor('slow', 0.6) : rateFor('model', 0.9));
    return;
  }
  if (s.kind === 'speak' || s.kind === 'recall') {
    if (state.attempts > 0) {
      speak(s.text, state.slow_replay ? rateFor('slow', 0.55) : rateFor('drill', 0.8));
    }
  }
}

/* ---------- recording (phone only) ---------- */
let stream = null;
let recorder = null;
let chunks = [];
let recording = false;
let stopTimer = null;

/* dictation: the phone listens too, so free response can be graded without a
   cloud ASR key. Chrome/Edge only - everything else falls back to the server. */
let recog = null;
let heardText = '';
let dictating = false;

function startDictation() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) return;
  heardText = '';
  try {
    recog = new SR();
    recog.lang = speechLang();
    recog.continuous = true;
    recog.interimResults = true;
    recog.onresult = (e) => {
      for (let i = e.resultIndex; i < e.results.length; i++) {
        if (e.results[i].isFinal) heardText += e.results[i][0].transcript;
      }
    };
    recog.onerror = () => {};
    recog.onend = () => {};
    recog.start();
    dictating = true;
  } catch (err) {
    recog = null;
    dictating = false;
  }
}

function stopDictation() {
  if (recog) {
    try { recog.stop(); } catch (err) {}
    recog = null;
  }
}

async function toggleRecord() {
  if (recording) return stopRecording();
  // Reaching for the mic means you are not stuck, so drop the anticipation
  // gap rather than let the English land halfway through your sentence.
  if (anticipationTimer) {
    clearInterval(anticipationTimer);
    anticipationTimer = null;
    anticipationLeft = 0;
    render();
  }
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true },
    });
  } catch (err) {
    el('message').textContent = 'Microphone blocked: ' + err.message;
    return;
  }
  const mime = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4'].find(
    (m) => window.MediaRecorder && MediaRecorder.isTypeSupported(m)
  );
  recorder = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
  chunks = [];
  recorder.ondataavailable = (e) => e.data && chunks.push(e.data);
  recorder.onstop = sendAttempt;
  recorder.start();
  startDictation();
  recording = true;
  mirrorToGlasses();
  el('mic').textContent = 'Stop & grade';
  el('mic').disabled = false;
  haptic('select');
  stopTimer = setTimeout(stopRecording, 12000);
}

function stopRecording() {
  clearTimeout(stopTimer);
  stopDictation();
  if (recorder && recording) {
    recording = false;
    recorder.stop();
    mirrorToGlasses();
  }
  if (stream) stream.getTracks().forEach((t) => t.stop());
  if (el('mic')) {
    el('mic').textContent = 'Hold to speak';
    el('mic').disabled = true;
  }
}

async function sendAttempt() {
  const blob = new Blob(chunks, { type: recorder.mimeType || 'audio/webm' });
  if (!blob.size) return;
  // let the last dictation result land before we grade
  if (dictating) await new Promise((r) => setTimeout(r, 400));
  const wav = await toWav16k(blob);
  const fd = new FormData();
  fd.append('file', new Blob([wav], { type: 'audio/wav' }), 'attempt.wav');
  fd.append('encoding', 'wav');
  fd.append('client_id', CLIENT);
  if (heardText) fd.append('recognized', heardText.trim());
  el('message').textContent = 'Grading…';
  try {
    const res = await api('/api/attempt', fd);
    if (res.reasons && res.reasons.length) el('reason').textContent = res.reasons.join(' · ');
  } catch (err) {
    el('message').textContent = 'Grading failed: ' + err.message;
  }
}

/* decode -> resample to 16 kHz mono -> 16-bit PCM WAV (what the scorers want) */
async function toWav16k(blob) {
  const Ctx = window.AudioContext || window.webkitAudioContext;
  const ctx = new Ctx();
  const buf = await ctx.decodeAudioData(await blob.arrayBuffer());
  const src = buf.getChannelData(0);
  const target = 16000;
  const ratio = buf.sampleRate / target;
  const outLen = Math.max(1, Math.floor(src.length / ratio));
  const out = new Float32Array(outLen);
  for (let i = 0; i < outLen; i++) {
    const p = i * ratio;
    const i0 = Math.floor(p);
    const i1 = Math.min(src.length - 1, i0 + 1);
    const f = p - i0;
    out[i] = src[i0] * (1 - f) + src[i1] * f;
  }
  const view = new DataView(new ArrayBuffer(44 + out.length * 2));
  const str = (o, s) => { for (let i = 0; i < s.length; i++) view.setUint8(o + i, s.charCodeAt(i)); };
  str(0, 'RIFF'); view.setUint32(4, 36 + out.length * 2, true); str(8, 'WAVE');
  str(12, 'fmt '); view.setUint32(16, 16, true); view.setUint16(20, 1, true);
  view.setUint16(22, 1, true); view.setUint32(24, target, true);
  view.setUint32(28, target * 2, true); view.setUint16(32, 2, true); view.setUint16(34, 16, true);
  str(36, 'data'); view.setUint32(40, out.length * 2, true);
  let o = 44;
  for (let i = 0; i < out.length; i++, o += 2) {
    const s = Math.max(-1, Math.min(1, out[i]));
    view.setInt16(o, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }
  ctx.close();
  return view.buffer;
}

/* ---------- wiring ---------- */
function buildLessonPicker() {
  const sel = el('lessonSelect');
  if (!sel || !course) return;
  sel.innerHTML = course.levels
    .map(
      (lv) =>
        `<optgroup label="${lv.title}">` +
        lv.units
          .map((u) =>
            u.lessons.map((l) => `<option value="${l.id}">L${l.id} · ${l.title}</option>`).join('')
          )
          .join('') +
        `</optgroup>`
    )
    .join('');
  if (state) sel.value = String(state.progress.lesson_id);
}

function boot() {
  connect();
  loadCourse();
  if (STREAM_VIEW) return;      // display only: no keys, no clicks

  document.addEventListener('keydown', (e) => {
    if (menu.open) {
      if (e.key === 'ArrowUp') menuMove(-1);
      else if (e.key === 'ArrowDown') menuMove(1);
      else if (e.key === 'Enter') menuSelect();
      else if (e.key === 'Escape' || e.key === 'ArrowLeft') goBack();
      return;
    }
    if (e.key === 'ArrowUp') { showEnglish = !showEnglish; render(); }
    else if (e.key === 'ArrowDown') { showNotes = !showNotes; render(); }
    // the grammar page for this lesson: open it, then step through it
    else if (e.key === 'ArrowRight') { openGrammar(); }
    else if (e.key === 'Enter') {
      const s = state && state.step;
      // On a step you do not speak, the tap means "next" - pressing to hear
      // あ read aloud gets you nothing. Anywhere else the tap is a request
      // to hear the line again.
      if (s && ['kana', 'kanji', 'info'].includes(s.kind)) maybeAdvance();
      // nothing can be replayed from the glasses; a press moves past the line
      else if (!AUDIO_HOST) { if (s && ['listen', 'hear'].includes(s.kind)) maybeAdvance(); }
      else if (s && s.kind === 'hear') playHidden(s);
      else if (s && s.text) speak(s.text, 0.7);
    }
    else if (e.key === 'Escape') { if (grammarPage) goBack(); else toggleMenu(); }
    else if (e.key === 'ArrowLeft' && IS_PHONE) api('/api/think/exit', { client_id: CLIENT });
    // the glasses have no Escape key, so the menu opens with a left swipe
    else if (e.key === 'ArrowLeft') { if (grammarPage) goBack(); else toggleMenu(); }
  });

  // a tap on the stage also opens the menu (glasses have no pointer, phone does)
  const stage = el('stage');
  if (stage) stage.addEventListener('click', () => { if (!IS_PHONE) toggleMenu(); });

  if (!IS_PHONE) return;

  el('mic').addEventListener('click', toggleRecord);
  el('menuBtn').addEventListener('click', toggleMenu);
  el('reviewBtn').addEventListener('click', () => api('/api/review/start', { client_id: CLIENT, limit: 20 }));
  el('good').addEventListener('click', () => api('/api/attempt/sim', { client_id: CLIENT, quality: 'good' }));
  el('bad').addEventListener('click', () => api('/api/attempt/sim', { client_id: CLIENT, quality: 'bad' }));
  el('repeat').addEventListener('click', () => { const s = state && state.step; if (s && s.text) speak(s.text, 0.6); });

  el('thinkform').addEventListener('submit', async (e) => {
    e.preventDefault();
    const input = el('thought');
    const text = input.value.trim();
    if (!text) return;
    input.value = '';
    await api('/api/think', { client_id: CLIENT, text });
  });

  el('exitThink').addEventListener('click', () => api('/api/think/exit', { client_id: CLIENT }));

  const sel = el('lessonSelect');
  sel.addEventListener('change', () => api('/api/lesson/start', { client_id: CLIENT, lesson_id: sel.value }));
}

document.addEventListener('DOMContentLoaded', boot);
