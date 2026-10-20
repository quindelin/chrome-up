import { delta } from "./net.js";

const CARDINALS = [
  { deg: 0, label: "N" },
  { deg: 90, label: "E" },
  { deg: 180, label: "S" },
  { deg: 270, label: "W" },
];

const FONT = '"Skyrim HUD", "Barlow Condensed", "Futura", "Arial Narrow", sans-serif';
const CAP = 46;                  // width of each ornamental end cap

/** Skyrim compass: a thin dark band between two filigree caps, white
 *  cardinal letters, location icons, and the quest marker. */
export class Compass {
  constructor(canvas, markers = []) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.markers = markers;
    this.w = canvas.width;
    this.h = canvas.height;
    this.span = 180;             // degrees visible across the band
    this.heading = 0;
    this.objective = null;       // {name, bearing, distance, step, icon}
    this.top = 22;               // band geometry
    this.bandH = 34;
  }

  setHeading(deg) { this.heading = deg; }
  setObjective(obj) { this.objective = obj; }

  get inner() { return this.w - CAP * 2; }
  get ppd() { return this.inner / this.span; }

  xFor(bearing) {
    return this.w / 2 + delta(this.heading, bearing) * this.ppd;
  }

  /** fade toward the caps, like the vanilla band */
  _alpha(x) {
    const edge = Math.min(x - CAP, this.w - CAP - x);
    return Math.max(0, Math.min(1, edge / 90));
  }

  draw() {
    const ctx = this.ctx;
    const { w } = this;
    const top = this.top, bh = this.bandH, mid = top + bh / 2;
    ctx.clearRect(0, 0, w, this.h);

    // --- band
    const g = ctx.createLinearGradient(0, top, 0, top + bh);
    g.addColorStop(0, "rgba(0,0,0,0.28)");
    g.addColorStop(0.5, "rgba(0,0,0,0.5)");
    g.addColorStop(1, "rgba(0,0,0,0.28)");
    ctx.fillStyle = g;
    ctx.fillRect(CAP - 4, top, w - (CAP - 4) * 2, bh);
    ctx.strokeStyle = "rgba(230,230,230,0.55)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(CAP - 4, top + 0.5); ctx.lineTo(w - CAP + 4, top + 0.5);
    ctx.moveTo(CAP - 4, top + bh - 0.5); ctx.lineTo(w - CAP + 4, top + bh - 0.5);
    ctx.stroke();

    ctx.save();
    ctx.beginPath();
    ctx.rect(CAP, 0, w - CAP * 2, this.h);
    ctx.clip();

    // --- cardinal letters (no ticks in vanilla)
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.font = `500 28px ${FONT}`;
    ctx.shadowColor = "rgba(0,0,0,0.9)";
    ctx.shadowBlur = 4;
    for (const c of CARDINALS) {
      const x = this.xFor(c.deg);
      ctx.globalAlpha = this._alpha(x);
      ctx.fillStyle = "#f2f2f2";
      ctx.fillText(c.label, x, mid + 1);
    }

    // --- location markers, inside the band
    for (const m of this.markers) {
      const x = this.xFor(m.bearing);
      ctx.globalAlpha = this._alpha(x) * 0.9;
      this._icon(m.icon || "diamond", x, mid, 0.8);
    }
    ctx.globalAlpha = 1;
    ctx.restore();

    if (this.objective) this._objective(this.objective);
    this._caps();
  }

  /** the filigree end pieces: a spear tip with two hooked flourishes */
  _caps() {
    const ctx = this.ctx;
    const mid = this.top + this.bandH / 2;
    for (const side of [-1, 1]) {
      const x0 = side < 0 ? CAP : this.w - CAP;
      ctx.save();
      ctx.translate(x0, mid);
      ctx.scale(-side, 1);         // draw pointing outward
      ctx.shadowColor = "rgba(0,0,0,0.9)";
      ctx.shadowBlur = 3;
      const metal = ctx.createLinearGradient(0, -20, 0, 20);
      metal.addColorStop(0, "#d9d9d9");
      metal.addColorStop(0.5, "#8d8d8d");
      metal.addColorStop(1, "#cfcfcf");
      ctx.fillStyle = metal;
      ctx.strokeStyle = "#eeeeee";
      ctx.lineWidth = 1.4;
      // spear tip
      ctx.beginPath();
      ctx.moveTo(2, -this.bandH / 2);
      ctx.lineTo(10, -this.bandH / 2);
      ctx.lineTo(CAP - 4, 0);
      ctx.lineTo(10, this.bandH / 2);
      ctx.lineTo(2, this.bandH / 2);
      ctx.lineTo(16, 0);
      ctx.closePath();
      ctx.fill();
      // hooks curling back over the band edge
      ctx.beginPath();
      ctx.moveTo(8, -this.bandH / 2);
      ctx.bezierCurveTo(-4, -this.bandH / 2 - 10, -16, -this.bandH / 2 - 2, -10, -this.bandH / 2 + 4);
      ctx.moveTo(8, this.bandH / 2);
      ctx.bezierCurveTo(-4, this.bandH / 2 + 10, -16, this.bandH / 2 + 2, -10, this.bandH / 2 - 4);
      ctx.stroke();
      // inner bead
      ctx.beginPath();
      ctx.arc(22, 0, 2.6, 0, Math.PI * 2);
      ctx.fillStyle = "#f4f4f4";
      ctx.fill();
      ctx.restore();
    }
  }

  _objective(o) {
    const ctx = this.ctx;
    const { w } = this;
    const mid = this.top + this.bandH / 2;
    const rel = delta(this.heading, o.bearing);
    const half = this.span / 2;
    const off = Math.abs(rel) > half;
    // off the band: park at the edge, as Skyrim does
    const x = off ? (rel > 0 ? w - CAP - 12 : CAP + 12) : this.xFor(o.bearing);

    // quest marker: a down-pointing arrowhead with a notched top
    ctx.save();
    ctx.translate(x, mid - 2);
    ctx.shadowColor = "rgba(0,0,0,0.95)";
    ctx.shadowBlur = 4;
    ctx.fillStyle = "#f3e3b5";
    ctx.strokeStyle = "rgba(0,0,0,0.6)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(-9, -10);
    ctx.lineTo(0, -5);
    ctx.lineTo(9, -10);
    ctx.lineTo(0, 11);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
    ctx.restore();

    // distance under the band (IRL navigation needs it; vanilla has none)
    ctx.save();
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    ctx.font = `500 16px ${FONT}`;
    ctx.shadowColor = "rgba(0,0,0,0.9)";
    ctx.shadowBlur = 3;
    ctx.fillStyle = "rgba(242,242,242,0.85)";
    ctx.fillText(fmtDistance(o.distance), x, this.top + this.bandH + 3);
    ctx.restore();
  }

  _icon(kind, x, y, scale = 1) {
    const ctx = this.ctx;
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(scale, scale);
    ctx.strokeStyle = "rgba(240, 240, 240, 0.95)";
    ctx.fillStyle = "rgba(240, 240, 240, 0.9)";
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

export function fmtDuration(s) {
  const min = Math.max(1, Math.round((Number(s) || 0) / 60));
  if (min < 60) return `${min} min`;
  return `${Math.floor(min / 60)} h ${String(min % 60).padStart(2, "0")} min`;
}
