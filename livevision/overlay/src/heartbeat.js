// Heart rate (Apple Watch -> phone -> payload.body.heart_rate) above the
// Magicka bar: a heart that beats at the measured rate, the bpm, and a short
// ECG strip of the recent beats.
//
// OBS renders this page in software, so nothing here runs per frame: one
// timer per beat triggers a short lub-dub (Web Animations, transform only)
// and redraws the small trace canvas once.

const STRIP_S = 5;           // seconds of beats on the trace
const EASE = 0.35;           // per beat, how far the pulse moves toward a new bpm

export class Heartbeat {
  constructor(el, opts = {}) {
    this.el = el;
    this.heart = el.querySelector(".hb-heart");
    this.num = el.querySelector(".hb-num");
    this.canvas = el.querySelector(".hb-trace canvas");
    this.ctx = this.canvas.getContext("2d");
    this.highBpm = opts.high_bpm ?? 150;
    this.target = null;      // last measured bpm
    this.bpm = null;         // eased rate the heart actually beats at
    this.beats = [];         // performance.now() of recent beats
    this.timer = 0;
    if (opts.enabled === false) el.classList.add("hidden");
    this.enabled = opts.enabled !== false;
  }

  update(body) {
    if (!this.enabled) return;
    const hr = body?.heart_rate;
    const known = typeof hr === "number" && hr > 0;
    this.el.classList.toggle("unknown", !known);
    if (!known) {
      if (this.target !== null) this._stop();
      return;
    }
    if (hr !== this.target) {
      this.num.textContent = Math.round(hr);
      this.el.classList.toggle("high", hr > this.highBpm);
    }
    const starting = this.target === null;
    this.target = hr;
    if (starting) {
      this.bpm = hr;
      this._beat();
    }
  }

  _stop() {
    clearTimeout(this.timer);
    this.target = this.bpm = null;
    this.beats = [];
  }

  _beat() {
    if (this.target === null) return;
    this.bpm += (this.target - this.bpm) * EASE;
    const interval = 60000 / this.bpm;
    const now = performance.now();
    this.beats.push(now);
    while (this.beats.length && now - this.beats[0] > STRIP_S * 1000 + 500) this.beats.shift();

    // lub-dub: a strong first beat, a softer second one, then rest
    const dur = Math.min(460, interval * 0.7);
    this.heart.animate([
      { transform: "scale(1)", offset: 0 },
      { transform: "scale(1.2)", offset: 0.14 },
      { transform: "scale(0.98)", offset: 0.32 },
      { transform: "scale(1.1)", offset: 0.46 },
      { transform: "scale(1)", offset: 1 },
    ], { duration: dur, easing: "ease-out" });

    this._draw(now);
    this.timer = setTimeout(() => this._beat(), interval);
  }

  // PQRST complex, x in px from the R peak, y from -1..1 (up = positive)
  static _ecg(x) {
    const g = (c, w, a) => a * Math.exp(-((x - c) ** 2) / (2 * w * w));
    return g(-11, 2.2, 0.16) + g(-2.2, 0.9, -0.22) + g(0, 1.1, 1) +
           g(2.4, 1.0, -0.38) + g(11, 3.0, 0.3);
  }

  _draw(now) {
    const { ctx, canvas } = this;
    const w = canvas.width, h = canvas.height;
    const mid = h * 0.62, amp = h * 0.5;
    const pxPerMs = (w - 16) / (STRIP_S * 1000);
    const peaks = this.beats.map((t) => w - 16 - (now - t) * pxPerMs);
    const high = this.el.classList.contains("high");
    ctx.clearRect(0, 0, w, h);
    ctx.lineJoin = "round";
    ctx.lineWidth = 1.6;
    // older beats dim, the newest one bright
    for (const bright of [false, true]) {
      ctx.beginPath();
      ctx.strokeStyle = bright ? (high ? "#ff8a7a" : "#f4f4f4")
                               : (high ? "rgba(255,138,122,0.5)" : "rgba(236,236,236,0.45)");
      const from = bright ? peaks[peaks.length - 1] - 16 : 0;
      const to = bright ? w : peaks[peaks.length - 1] - 16;
      for (let x = Math.max(0, from); x <= to; x += 1) {
        let y = 0;
        for (const p of peaks) if (Math.abs(x - p) < 22) y += Heartbeat._ecg(x - p);
        const py = mid - y * amp;
        if (x === Math.max(0, from)) ctx.moveTo(x, py); else ctx.lineTo(x, py);
      }
      ctx.stroke();
    }
  }
}
