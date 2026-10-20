/** Audio-reactive ring drawn behind the avatar: spectrum spokes + level arc. */
export class Ring {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.w = canvas.width;
    this.h = canvas.height;
    this.rot = 0;
    this.pulse = 0;
    this.lastLevel = 0;
  }

  draw(dt, audio) {
    const ctx = this.ctx;
    const cx = this.w / 2;
    const cy = this.h / 2;
    const r = 132;
    const level = audio?.level ?? 0;
    this.rot = (this.rot + dt * (0.18 + level * 0.9)) % (Math.PI * 2);

    // onset pulse
    if (level - this.lastLevel > 0.22) this.pulse = 1;
    this.lastLevel = level;
    this.pulse = Math.max(0, this.pulse - dt * 1.8);

    ctx.clearRect(0, 0, this.w, this.h);

    // soft inner glow driven by loudness
    const glow = ctx.createRadialGradient(cx, cy, 20, cx, cy, r + 20 + level * 30);
    glow.addColorStop(0, `rgba(232, 200, 138, ${0.10 + level * 0.22})`);
    glow.addColorStop(1, "rgba(232, 200, 138, 0)");
    ctx.fillStyle = glow;
    ctx.fillRect(0, 0, this.w, this.h);

    // base rings
    ctx.strokeStyle = "rgba(232, 200, 138, 0.22)";
    ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.arc(cx, cy, r + 16, 0, Math.PI * 2); ctx.stroke();
    ctx.beginPath(); ctx.arc(cx, cy, r - 26, 0, Math.PI * 2); ctx.stroke();

    // spectrum spokes
    const bands = audio?.bands || [];
    const n = bands.length || 12;
    for (let i = 0; i < n; i++) {
      const v = Math.max(0, Math.min(1, bands[i] ?? 0));
      const ang = (i / n) * Math.PI * 2 + this.rot;
      const len = 10 + v * 56;
      const cos = Math.cos(ang), sin = Math.sin(ang);
      ctx.strokeStyle = `rgba(232, 200, 138, ${0.25 + v * 0.65})`;
      ctx.lineWidth = 4;
      ctx.lineCap = "round";
      ctx.beginPath();
      ctx.moveTo(cx + cos * (r + 4), cy + sin * (r + 4));
      ctx.lineTo(cx + cos * (r + 4 + len), cy + sin * (r + 4 + len));
      ctx.stroke();
    }

    // loudness arc
    ctx.strokeStyle = "rgba(240, 220, 170, 0.95)";
    ctx.lineWidth = 5;
    ctx.lineCap = "butt";
    ctx.beginPath();
    ctx.arc(cx, cy, r - 10, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * Math.min(1, level));
    ctx.stroke();

    // expanding shock ring on transients
    if (this.pulse > 0) {
      const p = 1 - this.pulse;
      ctx.strokeStyle = `rgba(255, 244, 214, ${this.pulse * 0.6})`;
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.arc(cx, cy, r + 20 + p * 60, 0, Math.PI * 2);
      ctx.stroke();
    }

    // rotating tick marks
    ctx.strokeStyle = "rgba(232, 200, 138, 0.35)";
    ctx.lineWidth = 2;
    for (let i = 0; i < 24; i++) {
      const ang = (i / 24) * Math.PI * 2 - this.rot * 0.6;
      const cos = Math.cos(ang), sin = Math.sin(ang);
      const inner = r + 74;
      ctx.beginPath();
      ctx.moveTo(cx + cos * inner, cy + sin * inner);
      ctx.lineTo(cx + cos * (inner + 8), cy + sin * (inner + 8));
      ctx.stroke();
    }
  }
}
