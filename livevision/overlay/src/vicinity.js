/**
 * vicinity.js — OBS panel that mirrors what the glasses are showing.
 *
 * Read-only. This panel has no input, no button and no write path: it renders
 * the same view model the phone pushes to the Meta Ray-Ban Display over DAT,
 * so the stream audience sees exactly what the wearer sees.
 *
 *   <div id="vicinity" data-relay="http://127.0.0.1:8901"></div>
 *
 * Prefers SSE (/vicinity/stream) and falls back to polling (/vicinity/feed)
 * when the relay is an older build or the connection drops. If the phone stops
 * pushing (stale), the panel hides itself rather than leaving dead chat on
 * screen.
 */

const POLL_MS = 2500;

export class VicinityFeed {
  constructor(el, relayUrl = null) {
    this.el = el;
    if (!this.el) return;
    this.relay = relayUrl || this.el.dataset.relay || "http://127.0.0.1:8901";
    this.maxLines = Number(this.el.dataset.maxLines || 5);
    this.hideStale = this.el.dataset.hideStale !== "false";
    this.es = null;
    this.timer = null;
  }

  start() {
    if (!this.el) return;
    this.el.classList.remove("hidden");
    this._sse();
    this._poll(); // also acts as the SSE fallback: SSE overwrites when it lands
  }

  stop() {
    if (this.es) this.es.close();
    if (this.timer) clearInterval(this.timer);
  }

  _sse() {
    try {
      this.es = new EventSource(`${this.relay}/vicinity/stream`);
      this.es.addEventListener("vicinity", (evt) => {
        try {
          this._render(JSON.parse(evt.data));
        } catch { /* ignore malformed frame */ }
      });
    } catch { /* no SSE in this build — polling covers it */ }
  }

  _poll() {
    this.tick();
    this.timer = setInterval(() => this.tick(), POLL_MS);
  }

  async tick() {
    try {
      const res = await fetch(`${this.relay}/vicinity/feed`, { cache: "no-store" });
      if (!res.ok) throw new Error(res.status);
      this._render(await res.json());
    } catch {
      this._gone();
    }
  }

  _gone() {
    if (this.hideStale) this.el.classList.add("hidden");
  }

  _render(vm) {
    if (!vm || typeof vm !== "object") return;
    // Phone stopped pushing (or never started): don't leave stale chat on air.
    if (this.hideStale && vm.relay && vm.relay.stale) {
      this._gone();
      return;
    }
    this.el.classList.remove("hidden");

    const lines = (vm.lines || []).slice(-this.maxLines);
    this.el.innerHTML = `
      <div class="vc-head">
        <span class="vc-channel">${esc(vm.channel || "Vicinity")}</span>
        ${vm.nearby ? `<span class="vc-nearby">${esc(vm.nearby)} nearby</span>` : ""}
      </div>
      <div class="vc-lines">
        ${lines.map(lineHtml).join("")}
      </div>
      <div class="vc-foot">${esc(vm.footer || "")}</div>
    `;
  }
}

function lineHtml(l) {
  const photo = l.photo
    ? `<img class="vc-photo" src="${esc(l.photo)}" alt="" />`
    : "";
  return `
    <div class="vc-line${l.mine ? " vc-mine" : ""}">
      <div class="vc-meta">
        <span class="vc-author">${esc(l.author || "Someone")}</span>
        <span class="vc-time">${esc(l.time || "")}</span>
      </div>
      <div class="vc-text">${esc(l.text || "")}${photo}</div>
    </div>
  `;
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}
