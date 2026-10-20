import { fmtDistance } from "./compass.js";

const ORDER = ["speech", "speechcraft", "rizz", "agility", "sneak",
               "exploration", "bard", "strength", "combat", "intelligence", "enchanting"];

/** Gesture-opened Skyrim menu: Skills / Stats / Objectives. */
export class Menu {
  constructor(root) {
    this.root = root;
    this.tab = -1;
    this.lastRender = 0;
    root.innerHTML = `
      <div class="menu-frame">
        <div class="menu-head"><span id="menu-title">Skills</span></div>
        <div class="menu-tabs" id="menu-tabs"></div>
        <div class="menu-body" id="menu-body"></div>
        <div class="menu-foot">tap / pinch = close &nbsp;·&nbsp; swipe = change tab &nbsp;·&nbsp; rotate = scroll</div>
      </div>`;
    this.titleEl = root.querySelector("#menu-title");
    this.tabsEl = root.querySelector("#menu-tabs");
    this.bodyEl = root.querySelector("#menu-body");
  }

  update(payload, ui) {
    this.root.classList.toggle("hidden", !ui.open);
    if (!ui.open) return;
    this.titleEl.textContent = ui.tabs[ui.tab] || "Skills";
    this.tabsEl.innerHTML = ui.tabs
      .map((t, i) => `<span class="menu-tab${i === ui.tab ? " active" : ""}">${t}</span>`)
      .join("");

    const now = performance.now();
    if (ui.tab === this.tab && now - this.lastRender < 220) return;
    this.tab = ui.tab;
    this.lastRender = now;

    const name = (ui.tabs[ui.tab] || "").toLowerCase();
    if (name === "stats") this.bodyEl.innerHTML = this._stats(payload);
    else if (name === "objectives") this.bodyEl.innerHTML = this._objectives(payload);
    else this.bodyEl.innerHTML = this._skills(payload);
  }

  _skills(p) {
    const keys = ORDER.filter((k) => p.skills?.[k]);
    const rows = keys.map((k) => {
      const s = p.skills[k];
      return `<div class="menu-row${s.active ? " active" : ""}">
        <span class="mr-name">${s.name}</span>
        <span class="mr-lvl">${s.level}</span>
        <span class="mr-bar"><i style="width:${Math.round((s.xp || 0) * 100)}%"></i></span>
        <span class="mr-total">${s.total} xp</span>
      </div>`;
    }).join("");
    return `<div class="menu-level">Level ${p.player_level ?? 1}</div>${rows}`;
  }

  _stats(p) {
    const v = p.vitals || {};
    const bar = (label, value, cls) => `
      <div class="menu-stat">
        <span class="mr-name">${label}</span>
        <span class="mr-bar ${cls}"><i style="width:${Math.round(value)}%"></i></span>
        <span class="mr-total">${Math.round(value)}</span>
      </div>`;
    const vis = p.vision || {};
    const aud = p.audio || {};
    const head = p.heading || {};
    const desk = p.desktop || {};
    const shout = p.shout || {};
    const focus = p.focus || {};
    const focusKind = focus.kind || vis.focus || "other";
    const focusConf = Math.round((focus.confidence || 0) * 100);
    const focusSrc = focus.features?.source || "—";
    const focusFeats = focus.features || {};
    const imu = p.imu || {};
    const imuF = imu.features || {};
    return `
      <div class="menu-level">Level ${p.player_level ?? 1}</div>
      ${bar("Health", v.health ?? 0, "h")}
      ${bar("Magicka", v.magicka ?? 0, "m")}
      ${bar("Stamina", v.stamina ?? 0, "s")}
      <div class="menu-meta">
        <div><b>Activity</b> ${vis.activity || "idle"}${vis.cadence ? ` · ${vis.cadence} Hz` : ""}</div>
        <div><b>Looking at</b> ${focusKind === "other" ? "—" : focusKind} <span class="dim">· ${focusConf}% via ${focusSrc}</span></div>
        <div><b>Frontmost</b> ${desk.app || "—"} <span class="dim">${desk.app ? `· ${desk.kind}` : ""}</span></div>
        <div><b>Phone IMU</b> ${imu.activity || "idle"} <span class="dim">· ${imu.cadence || 0} Hz · ${imu.fresh ? `fresh (${imu.age_s ?? 0}s)` : "stale"}</span></div>
        <div><b>Facing</b> ${Math.round(head.deg ?? 0)}° <span class="dim">(${head.source})</span></div>
        <div><b>Audio</b> ${aud.source || "—"} <span class="dim">${aud.speaking ? "speaking" : "quiet"}</span></div>
        <div><b>Video</b> ${vis.source || "—"} <span class="dim">${vis.fps || 0} fps · ${vis.people || 0} seen</span></div>
        <div><b>Thu'um</b> ${shout.ready ? "ready · " + (shout.last || "—") : Math.round(shout.cooldown || 0) + "s left"}</div>
        <div><b>Discovered</b> ${p.discovery?.count ?? 0} places</div>
      </div>
      ${focusFeats.text_rows ? `<div class="menu-step dim">text rows ${focusFeats.text_rows} · bright ${Math.round(focusFeats.mean_brightness || 0)} · sat ${Math.round(focusFeats.mean_saturation || 0)} · syntax ${(focusFeats.syntax_ratio || 0).toFixed(4)}</div>` : ""}
      ${imuF.az_var != null ? `<div class="menu-step dim">az var ${imuF.az_var} · gyro mean ${imuF.gyro_mean} · lin mean ${imuF.lin_mean}</div>` : ""}
      ${p.attributes?.enabled ? `<div class="menu-warn">face attributes: opt-in active</div>` : ""}`;
  }

  _objectives(p) {
    const nav = p.nav || {};
    const obj = nav.active ? nav.objective : null;
    const head = obj
      ? `<div class="menu-row active">
           <span class="mr-name">${obj.name}</span>
           <span class="mr-lvl">${fmtDistance(obj.distance)}</span>
           <span class="mr-bar"><i style="width:100%"></i></span>
           <span class="mr-total">${Math.round(obj.bearing)}°</span>
         </div>
         <div class="menu-step">${obj.step || "Head for the objective"}</div>`
      : `<div class="menu-empty">No active quest.</div>
         <div class="menu-step dim">Set one on the control panel, or paste a maps link.</div>`;
    const markers = (p.__markers || [])
      .map((m) => `<div class="menu-row"><span class="mr-name">${m.name}</span>
        <span class="mr-lvl">${Math.round(m.bearing)}°</span></div>`).join("");
    return `${head}<div class="menu-sub">Pinned markers</div>${markers ||
      '<div class="menu-step dim">none configured</div>'}`;
  }
}
