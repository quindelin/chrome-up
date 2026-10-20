/**
 * Privacy badge — mirrors autoclip's face-blur switch into the overlay.
 *
 * An OBS browser source cannot read the pixels underneath it, so the blur
 * itself lives in autoclip (ffmpeg patches on rendered clips, and/or a
 * cropped+blurred patch scene on the live OBS output). What the overlay *can*
 * do is show the wearer (and the audience) that it is on, and how many faces
 * are covered.
 *
 * Two feeds, both cross-origin to the HUD server (autoclip sets CORS):
 *   GET {base}/api/autoclip/privacy          poll, every 5s (authoritative)
 *   GET {base}/api/autoclip/events           SSE, instant on a voice toggle
 *
 * Point `base` at your autoclip REST server:
 *   <div id="privacy" data-autoclip="http://127.0.0.1:8899">
 * or set window.AUTOCLIP_URL before this module loads.
 */
const DEFAULT_BASE = "http://127.0.0.1:8899";

export class PrivacyBadge {
  constructor(el) {
    this.el = el;
    this.textEl = el ? el.querySelector(".pv-text") : null;
    this.base = (el && el.dataset.autoclip) || window.AUTOCLIP_URL || DEFAULT_BASE;
    this.on = null;
    this.faces = 0;
    this.es = null;
  }

  start() {
    if (!this.el) return;
    this._poll();
    setInterval(() => this._poll(), 5000);
    this._stream();
  }

  async _poll() {
    try {
      const res = await fetch(`${this.base}/api/autoclip/privacy`);
      if (!res.ok) return;
      const s = await res.json();
      this._apply(s.enabled ? !!s.on : false, s.faces || 0, s.enabled);
    } catch (err) {
      /* autoclip not running — badge stays hidden */
    }
  }

  _stream() {
    if (typeof EventSource === "undefined") return;
    try {
      this.es = new EventSource(`${this.base}/api/autoclip/events`);
    } catch (err) {
      return;
    }
    this.es.onmessage = (evt) => {
      try {
        const ev = JSON.parse(evt.data);
        if (ev.type !== "privacy_status") return;
        const on = ev.value === "on" || !!(ev.extra && ev.extra.on);
        this._apply(on, (ev.extra && ev.extra.faces) || 0, true);
      } catch (err) { /* ignore malformed frame */ }
    };
  }

  _apply(on, faces, reachable) {
    this.on = on;
    this.faces = faces || 0;
    if (!this.el) return;
    if (on) {
      this.el.classList.remove("hidden");
      this.el.classList.toggle("pv-off", false);
      if (this.textEl) {
        this.textEl.textContent = this.faces > 0
          ? `faces blurred · ${this.faces}`
          : "faces blurred";
      }
    } else if (reachable) {
      // reachable but off: keep a dim "privacy off" chip only if you want it
      // visible — default is to hide the badge entirely.
      this.el.classList.add("hidden");
    } else {
      this.el.classList.add("hidden");
    }
  }
}
