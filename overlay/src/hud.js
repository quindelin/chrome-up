import { play } from "./sfx.js";

const ORDER = ["speech", "speechcraft", "rizz", "agility", "sneak", "exploration",
               "bard", "strength", "combat", "intelligence", "enchanting"];

// glasses battery below this blinks, like a low Skyrim bar
const LOW_AT = 20;

/** Vitals, skill-increase + level meter, discovery title. No top-left
 *  notification stack: it only repeated the skill-ups shown under the compass. */
export class Hud {
  constructor() {
    this.levelNum = document.getElementById("levelnum");
    this.levelup = document.getElementById("levelup");
    this.skillsEl = document.getElementById("skills");
    this.skillup = document.getElementById("skillup");
    this.suText = this.skillup.querySelector(".su-text");
    this.suLvl = document.getElementById("su-lvlnum");
    this.suFill = document.getElementById("su-fill");
    this.discover = document.getElementById("discover");
    this.dcName = this.discover.querySelector(".dc-name");
    this.vitals = {};
    for (const el of document.querySelectorAll(".vital")) {
      this.vitals[el.dataset.vital] = { el, fill: el.querySelector(".fill") };
    }
    this.rows = new Map();
    this.playerLevel = 1;
    this.levelProgress = 0;
    this._timers = {};
    if (new URLSearchParams(location.search).get("skills") === "1") {
      document.body.classList.add("show-skills");
    }
  }

  update(payload) {
    // magicka = the glasses' battery (phone relays DAT's DeviceState)
    const bar = this.vitals.magicka;
    const g = payload.glasses || {};
    const known = typeof g.battery === "number" && g.fresh !== false;
    if (bar) {
      bar.el.classList.toggle("unknown", !known);
      if (known) {
        const val = Math.max(0, Math.min(100, g.battery));
        bar.fill.style.width = `${val}%`;
        bar.el.classList.toggle("charging", g.charging === true);
        bar.el.classList.toggle("low", val < LOW_AT && g.charging !== true);
      }
    }

    if (payload.player_level !== undefined) {
      this.playerLevel = payload.player_level;
      if (this.levelNum) this.levelNum.textContent = payload.player_level;
    }
    if (payload.level_progress !== undefined) this.levelProgress = payload.level_progress;

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
    // A level-up outranks the skill increase that caused it in the same frame.
    const levelEv = events.find((e) => e.type === "level");
    for (const ev of events) {
      if (ev.type === "skill_level") {
        if (!levelEv) this.skillIncrease(ev);
      } else if (ev.type === "level") {
        this.levelUp(ev);
      } else if (ev.type === "discovery") {
        this.discovered(ev.place || String(ev.text || "").replace(/^Discovered:\s*/i, ""));
      }
    }
  }

  /** "Speech increased to 26" under the compass, with the level meter. */
  skillIncrease(ev) {
    // a level-up owns the slot under the compass until it fades
    if (!this.levelup.classList.contains("hidden")) { play("skillup"); return; }
    this.suText.textContent = ev.text;
    this.suLvl.textContent = this.playerLevel;
    this._show(this.skillup, 4500);
    // the meter animates from where it was to where it is now
    this.suFill.style.transition = "none";
    this.suFill.style.width = `${Math.max(0, this.levelProgress - 0.1) * 100}%`;
    void this.suFill.offsetWidth;
    this.suFill.style.transition = "";
    this.suFill.style.width = `${this.levelProgress * 100}%`;
    play("skillup");
  }

  levelUp(ev) {
    this.skillup.classList.add("hidden");
    this.levelup.textContent = ev.text || `You are now level ${ev.level}`;
    this._show(this.levelup, 5000);
    play("levelup");
  }

  discovered(place) {
    if (!place) return;
    this.dcName.textContent = place;
    this._show(this.discover, 5500);
    play("discover");
  }

  _show(el, ms) {
    el.classList.remove("hidden");
    el.style.animation = "none";        // restart the fade
    void el.offsetWidth;
    el.style.animation = "";
    clearTimeout(this._timers[el.id]);
    this._timers[el.id] = setTimeout(() => el.classList.add("hidden"), ms);
  }

  // kept for callers that still use the old name
  banner(text) { this.levelUp({ text }); }
}
