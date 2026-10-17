import { delta } from "./net.js";

const CARDINALS = [
  { deg: 0, label: "N" },
  { deg: 90, label: "E" },
  { deg: 180, label: "S" },
  { deg: 270, label: "W" },
];

/** Skyrim-style compass bar: cardinals, ticks, quest markers, live objective. */
export class Compass {
  constructor(canvas, markers = []) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.markers = markers;
    this.w = canvas.width;
    this.h = canvas.height;
    this.span = 220;             // degrees visible across the bar
    this.heading = 0;
    this.objective = null;       // {name, bearing, distance, step, icon}
  }

  setHeading(deg) { this.heading = deg; }
  setObjective(obj) { this.objective = obj; }

  get ppd() { return this.w / this.span; }

  xFor(bearing) {
    return this.w / 2 + delta(this.heading, bearing) * this.ppd;
  }

  draw() {
    const ctx = this.ctx;
    const { w, h } = this;
    ctx.clearRect(0, 0, w, h);

    ctx.fillStyle = "rgba(10, 9, 7, 0.42)";
    ctx.fillRect(0, 44, w, 48);

    // --- ticks every 15 degrees
    ctx.strokeStyle = "rgba(232, 200, 138, 0.75)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    for (let d = 0; d < 360; d += 15) {
      const x = this.xFor(d);
      if (x < -20 || x > w + 20) continue;
      const major = d % 45 === 0;
      ctx.moveTo(x, h - 30);
      ctx.lineTo(x, h - (major ? 12 : 22));
    }
    ctx.stroke();

    // --- cardinal letters
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.font = '700 30px "Cinzel", Georgia, serif';
    for (const c of CARDINALS) {
      const x = this.xFor(c.deg);
      if (x < -40 || x > w + 40) continue;
      const dist = Math.abs(delta(this.heading, c.deg));
      ctx.globalAlpha = Math.max(0, 1 - dist / (this.span * 0.62));
      ctx.fillStyle = "#f0dcae";
      ctx.fillText(c.label, x, h - 48);
    }
    ctx.globalAlpha = 1;

    // --- static quest markers
    for (const m of this.markers) {
      const x = this.xFor(m.bearing);
      if (x < -60 || x > w + 60) continue;
      const dist = Math.abs(delta(this.heading, m.bearing));
      ctx.globalAlpha = Math.max(0, 1 - dist / (this.span * 0.55));
      this._icon(m.icon || "diamond", x, 26, 0.75);
      ctx.font = '500 14px "Cinzel", Georgia, serif';
      ctx.fillStyle = "rgba(245, 232, 205, 0.85)";
      ctx.fillText(m.name, x, 44);
    }
    ctx.globalAlpha = 1;

    // --- live navigation objective
    if (this.objective) this._objective(this.objective);

    // --- centre player marker
    ctx.fillStyle = "#e8c88a";
    ctx.beginPath();
    ctx.moveTo(w / 2, 60);
    ctx.lineTo(w / 2 - 7, 48);
    ctx.lineTo(w / 2 + 7, 48);
    ctx.closePath();
    ctx.fill();
  }

  _objective(o) {
    const ctx = this.ctx;
    const { w } = this;
    const rel = delta(this.heading, o.bearing);
    const off = Math.abs(rel) > this.span / 2;
    const x = off ? (rel > 0 ? w - 42 : 42) : this.xFor(o.bearing);
    const pulse = 0.65 + 0.35 * Math.sin(performance.now() / 260);

    // quest marker
    ctx.save();
    ctx.translate(x, 24);
    ctx.scale(1.35, 1.35);
    ctx.shadowColor = `rgba(255, 226, 150, ${pulse})`;
    ctx.shadowBlur = 16;
    this._icon(o.icon || "diamond", 0, 0, 1);
    ctx.restore();

    // distance under the marker
    ctx.font = '700 15px "Cinzel", Georgia, serif';
    ctx.fillStyle = "#fff2d2";
    ctx.fillText(fmtDistance(o.distance), x, 46);

    // off-screen: big chevron at the edge
    if (off) {
      const dir = rel > 0 ? 1 : -1;
      ctx.save();
      ctx.translate(x, 24);
      ctx.fillStyle = `rgba(255, 236, 190, ${0.55 + pulse * 0.45})`;
      ctx.beginPath();
      ctx.moveTo(dir * 16, 0);
      ctx.lineTo(dir * 2, -13);
      ctx.lineTo(dir * 2, 13);
      ctx.closePath();
      ctx.fill();
      ctx.restore();
    }

    // "you are facing it" chevron under the compass centre
    if (Math.abs(rel) < 12) {
      ctx.save();
      ctx.translate(w / 2, 84);
      ctx.fillStyle = `rgba(255, 236, 190, ${pulse})`;
      ctx.beginPath();
      ctx.moveTo(0, 8);
      ctx.lineTo(-11, -6);
      ctx.lineTo(11, -6);
      ctx.closePath();
      ctx.fill();
      ctx.restore();
    }
  }

  _icon(kind, x, y, scale = 1) {
    const ctx = this.ctx;
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(scale, scale);
    ctx.strokeStyle = "rgba(232, 200, 138, 0.95)";
    ctx.fillStyle = "rgba(232, 200, 138, 0.9)";
    ctx.lineWidth = 2;
    if (kind === "home") {
      ctx.beginPath();
      ctx.moveTo(-9, -2); ctx.lineTo(0, -11); ctx.lineTo(9, -2);
      ctx.closePath(); ctx.fill();
      ctx.fillRect(-6, -2, 12, 11);
    } else if (kind === "door") {
      ctx.beginPath();
      ctx.moveTo(-7, 9); ctx.lineTo(-7, -2);
      ctx.quadraticCurveTo(-7, -11, 0, -11);
      ctx.quadraticCurveTo(7, -11, 7, -2);
      ctx.lineTo(7, 9);
      ctx.stroke();
    } else {
      ctx.beginPath();
      ctx.moveTo(0, -10); ctx.lineTo(9, 0); ctx.lineTo(0, 10); ctx.lineTo(-9, 0);
      ctx.closePath(); ctx.fill();
    }
    ctx.restore();
  }
}

export function fmtDistance(m) {
  const v = Number(m) || 0;
  if (v >= 1000) return `${(v / 1000).toFixed(1)} km`;
  if (v >= 100) return `${Math.round(v / 10) * 10} m`;
  return `${Math.round(v)} m`;
}
