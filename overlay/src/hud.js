const ORDER = ["speech", "speechcraft", "rizz", "agility", "sneak", "exploration",
               "bard", "strength", "combat", "intelligence", "enchanting"];

/** Bottom-left vitals + skill list, centre toasts and level-up banner. */
export class Hud {
  constructor() {
    this.levelNum = document.getElementById("levelnum");
    this.levelup = document.getElementById("levelup");
    this.toasts = document.getElementById("toasts");
    this.skillsEl = document.getElementById("skills");
    this.vitals = {};
    for (const el of document.querySelectorAll(".vital")) {
      this.vitals[el.dataset.vital] = el.querySelector(".fill");
    }
    this.rows = new Map();
  }

  update(payload) {
    const v = payload.vitals || {};
    for (const key of ["health", "magicka", "stamina"]) {
      const fill = this.vitals[key];
      if (fill) fill.style.width = `${Math.max(0, Math.min(100, v[key] ?? 0))}%`;
    }

    if (this.levelNum && payload.player_level !== undefined) {
      this.levelNum.textContent = payload.player_level;
    }

    this._ensureSkills(payload.skills || {});
    for (const [key, row] of this.rows) {
      const s = payload.skills?.[key];
      if (!s) continue;
      row.lvl.textContent = s.level;
      row.xp.style.width = `${Math.round((s.xp || 0) * 100)}%`;
      row.el.classList.toggle("active", !!s.active);
      row.el.classList.toggle("flash", (s.flash || 0) > 0.12);
    }
  }

  _ensureSkills(skills) {
    if (this.rows.size) return;
    const keys = ORDER.filter((k) => skills[k]);
    for (const key of keys.length ? keys : Object.keys(skills)) {
      const s = skills[key];
      const el = document.createElement("div");
      el.className = "skill";
      el.innerHTML =
        `<span class="name">${s.name || key}</span>` +
        `<span class="lvl">1</span>` +
        `<div class="xpbar"><div class="xpfill"></div></div>`;
      this.skillsEl.appendChild(el);
      this.rows.set(key, {
        el,
        lvl: el.querySelector(".lvl"),
        xp: el.querySelector(".xpfill"),
      });
    }
  }

  handleEvents(events = []) {
    for (const ev of events) {
      if (ev.type === "skill_level") {
        this.toast(`<span class="icon">&#9650;</span>${ev.text}`);
      } else if (ev.type === "shout") {
        this.banner(`Thu'um: ${ev.text}`);
      } else if (ev.type === "discovery") {
        this.toast(`<span class="icon">&#9737;</span>${ev.text}`);
      } else if (ev.type === "level" || ev.type === "arrival") {
        this.banner(ev.text);
      }
    }
  }

  toast(html) {
    const el = document.createElement("div");
    el.className = "toast";
    el.innerHTML = html;
    this.toasts.appendChild(el);
    setTimeout(() => el.remove(), 4400);
  }

  banner(text) {
    this.levelup.textContent = text;
    this.levelup.classList.remove("hidden");
    // restart the animation
    this.levelup.style.animation = "none";
    void this.levelup.offsetWidth;
    this.levelup.style.animation = "";
    clearTimeout(this._bannerT);
    this._bannerT = setTimeout(() => this.levelup.classList.add("hidden"), 4000);
  }
}
