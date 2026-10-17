/**
 * Procedural VTube-style avatar rendered on canvas.
 * Mouth is driven by the server viseme estimate, body bob/sway by mic level,
 * blush by "rizz" activity and a sweat drop while "agility" is grinding.
 */
export const THEME = {
  skin: "#f7d9c4",
  skinShade: "#e8bda2",
  hair: "#8f5aa8",
  hairLight: "#a86fc4",
  eye: "#5fb7e0",
  eyeDark: "#2b4a6b",
  cloth: "#2b3350",
  clothLight: "#3c4870",
  line: "#5a4030",
};

export class Avatar {
  constructor(canvas, theme = THEME) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.theme = { ...THEME, ...theme };
    this.t = 0;
    this.blink = 0;       // 0 = open, 1 = fully closed
    this.nextBlink = 2.5;
    this.bob = 0;
  }

  draw(dt, audio, vision, skills = {}) {
    const ctx = this.ctx;
    const th = this.theme;
    const cx = 150;
    const cy = 140;
    const level = audio?.level ?? 0;
    const openness = audio?.openness ?? 0;

    this.t += dt;
    // blink scheduling
    this.nextBlink -= dt;
    if (this.nextBlink <= 0) { this.nextBlink = 2.2 + Math.random() * 3.6; this.blink = 1; }
    this.blink = Math.max(0, this.blink - dt * 7);

    // motion: bob with voice, sway gently, lean when running
    const targetBob = -level * 7 + (vision?.running ? Math.sin(this.t * 9) * 5 : 0);
    this.bob += (targetBob - this.bob) * Math.min(1, dt * 8);
    const sway = Math.sin(this.t * 1.3) * 3 + (vision?.running ? Math.sin(this.t * 9) * 4 : 0);

    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    ctx.save();
    ctx.translate(sway, this.bob);

    this._torso(cx, cy);
    this._neck(cx, cy);
    this._backHair(cx, cy);
    this._head(cx, cy);
    this._sideHair(cx, cy);
    this._bangHair(cx, cy);
    this._ahoge(cx, cy, level);
    this._eyes(cx, cy, skills);
    this._nose(cx, cy);
    this._mouth(cx, cy + 52, openness, audio?.width ?? 0.5, audio?.viseme ?? "closed");
    this._blush(cx, cy, skills);
    if (skills?.agility?.active) this._sweat(cx, cy);
    if (vision?.running) this._speedLines(cx, cy);
    if (vision?.focus) this._glasses(cx, cy, vision.focus);

    ctx.restore();
  }

  // ------------------------------------------------------------- body
  _torso(cx, cy) {
    const ctx = this.ctx, th = this.theme;
    ctx.fillStyle = th.cloth;
    ctx.beginPath();
    ctx.moveTo(cx - 96, 380);
    ctx.quadraticCurveTo(cx - 86, 286, cx - 40, 258);
    ctx.lineTo(cx + 40, 258);
    ctx.quadraticCurveTo(cx + 86, 286, cx + 96, 380);
    ctx.closePath();
    ctx.fill();

    // collar
    ctx.fillStyle = th.clothLight;
    ctx.beginPath();
    ctx.moveTo(cx - 40, 258);
    ctx.lineTo(cx, 300);
    ctx.lineTo(cx + 40, 258);
    ctx.closePath();
    ctx.fill();
    ctx.strokeStyle = "rgba(232,200,138,0.5)";
    ctx.lineWidth = 2;
    ctx.stroke();
  }

  _neck(cx, cy) {
    const ctx = this.ctx, th = this.theme;
    ctx.fillStyle = th.skinShade;
    ctx.beginPath();
    ctx.moveTo(cx - 20, cy + 62);
    ctx.lineTo(cx + 20, cy + 62);
    ctx.lineTo(cx + 22, cy + 104);
    ctx.lineTo(cx - 22, cy + 104);
    ctx.closePath();
    ctx.fill();
  }

  _backHair(cx, cy) {
    const ctx = this.ctx, th = this.theme;
    ctx.fillStyle = th.hair;
    ctx.beginPath();
    ctx.ellipse(cx, cy + 10, 88, 104, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(cx - 84, cy + 40);
    ctx.quadraticCurveTo(cx - 96, cy + 150, cx - 70, cy + 178);
    ctx.quadraticCurveTo(cx - 58, cy + 120, cx - 58, cy + 60);
    ctx.closePath();
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(cx + 84, cy + 40);
    ctx.quadraticCurveTo(cx + 96, cy + 150, cx + 70, cy + 178);
    ctx.quadraticCurveTo(cx + 58, cy + 120, cx + 58, cy + 60);
    ctx.closePath();
    ctx.fill();
  }

  _head(cx, cy) {
    const ctx = this.ctx, th = this.theme;
    ctx.fillStyle = th.skin;
    ctx.beginPath();
    ctx.moveTo(cx - 62, cy - 8);
    ctx.bezierCurveTo(cx - 62, cy - 82, cx + 62, cy - 82, cx + 62, cy - 8);
    ctx.bezierCurveTo(cx + 62, cy + 44, cx + 28, cy + 76, cx, cy + 80);
    ctx.bezierCurveTo(cx - 28, cy + 76, cx - 62, cy + 44, cx - 62, cy - 8);
    ctx.closePath();
    ctx.fill();

    // ears
    ctx.beginPath();
    ctx.ellipse(cx - 62, cy + 12, 9, 15, -0.2, 0, Math.PI * 2);
    ctx.ellipse(cx + 62, cy + 12, 9, 15, 0.2, 0, Math.PI * 2);
    ctx.fill();
  }

  _sideHair(cx, cy) {
    const ctx = this.ctx, th = this.theme;
    ctx.fillStyle = th.hair;
    for (const s of [-1, 1]) {
      ctx.beginPath();
      ctx.moveTo(cx + s * 56, cy - 30);
      ctx.quadraticCurveTo(cx + s * 84, cy + 30, cx + s * 62, cy + 116);
      ctx.quadraticCurveTo(cx + s * 52, cy + 60, cx + s * 42, cy + 6);
      ctx.closePath();
      ctx.fill();
    }
  }

  _bangHair(cx, cy) {
    const ctx = this.ctx, th = this.theme;
    ctx.fillStyle = th.hair;
    ctx.beginPath();
    ctx.moveTo(cx - 66, cy + 8);
    ctx.bezierCurveTo(cx - 74, cy - 92, cx + 74, cy - 92, cx + 66, cy + 8);
    ctx.bezierCurveTo(cx + 46, cy - 34, cx + 26, cy - 8, cx + 8, cy - 22);
    ctx.bezierCurveTo(cx - 4, cy - 4, cx - 30, cy - 30, cx - 52, cy + 2);
    ctx.bezierCurveTo(cx - 58, cy + 6, cx - 62, cy + 8, cx - 66, cy + 8);
    ctx.closePath();
    ctx.fill();

    ctx.fillStyle = th.hairLight;
    ctx.globalAlpha = 0.45;
    ctx.beginPath();
    ctx.moveTo(cx - 48, cy - 44);
    ctx.bezierCurveTo(cx - 10, cy - 78, cx + 30, cy - 74, cx + 52, cy - 40);
    ctx.bezierCurveTo(cx + 20, cy - 60, cx - 16, cy - 60, cx - 48, cy - 44);
    ctx.closePath();
    ctx.fill();
    ctx.globalAlpha = 1;
  }

  _ahoge(cx, cy, level) {
    const ctx = this.ctx, th = this.theme;
    const wob = Math.sin(this.t * 4) * (4 + level * 10);
    ctx.strokeStyle = th.hair;
    ctx.lineWidth = 7;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(cx + 6, cy - 78);
    ctx.quadraticCurveTo(cx + 26 + wob, cy - 116, cx + 4 + wob * 0.5, cy - 134);
    ctx.stroke();
  }

  // ------------------------------------------------------------- face
  _eyes(cx, cy, skills) {
    const ctx = this.ctx, th = this.theme;
    const open = 1 - this.blink;
    const sparkle = skills?.rizz?.active ? 1 : 0;
    for (const s of [-1, 1]) {
      const ex = cx + s * 32;
      const ey = cy + 16;
      const ry = Math.max(1.5, 24 * open);

      // whites
      ctx.fillStyle = "#fffaf4";
      ctx.beginPath();
      ctx.ellipse(ex, ey, 21, ry, 0, 0, Math.PI * 2);
      ctx.fill();

      if (open > 0.25) {
        // iris
        const g = ctx.createRadialGradient(ex, ey + 2, 2, ex, ey, 16);
        g.addColorStop(0, th.eye);
        g.addColorStop(1, th.eyeDark);
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.ellipse(ex, ey + 2, 14, Math.min(15, ry * 0.8), 0, 0, Math.PI * 2);
        ctx.fill();
        // pupil + highlights
        ctx.fillStyle = "#1a1a22";
        ctx.beginPath();
        ctx.ellipse(ex, ey + 3, 6, Math.min(7, ry * 0.45), 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = "rgba(255,255,255,0.9)";
        ctx.beginPath();
        ctx.ellipse(ex - 5, ey - 5, 4, Math.min(5, ry * 0.3), 0, 0, Math.PI * 2);
        ctx.fill();
        if (sparkle) {
          ctx.fillStyle = "rgba(255,240,200,0.85)";
          ctx.beginPath();
          ctx.ellipse(ex + 6, ey + 7, 3, Math.min(4, ry * 0.25), 0, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      // upper lash line
      ctx.strokeStyle = th.line;
      ctx.lineWidth = 4.5;
      ctx.lineCap = "round";
      ctx.beginPath();
      if (open > 0.25) {
        ctx.moveTo(ex - 22, ey - 4);
        ctx.quadraticCurveTo(ex, ey - ry - 6, ex + 22, ey - 3);
      } else {
        ctx.moveTo(ex - 20, ey);
        ctx.lineTo(ex + 20, ey);
      }
      ctx.stroke();

      // brow
      ctx.strokeStyle = th.hair;
      ctx.lineWidth = 4;
      ctx.beginPath();
      ctx.moveTo(ex - 20, ey - 26 - (1 - open) * 4);
      ctx.quadraticCurveTo(ex, ey - 36 - (1 - open) * 4, ex + 20, ey - 28 - (1 - open) * 4);
      ctx.stroke();
    }
  }

  _nose(cx, cy) {
    const ctx = this.ctx, th = this.theme;
    ctx.strokeStyle = th.skinShade;
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.moveTo(cx - 3, cy + 34);
    ctx.lineTo(cx + 4, cy + 38);
    ctx.stroke();
  }

  _mouth(cx, cy, openness, width, viseme) {
    const ctx = this.ctx;
    const w = 22 + width * 16;
    const h = 2 + openness * 32;

    if (viseme === "closed" || h < 4) {
      ctx.strokeStyle = "#a4606a";
      ctx.lineWidth = 3;
      ctx.lineCap = "round";
      ctx.beginPath();
      ctx.moveTo(cx - w * 0.28, cy);
      ctx.quadraticCurveTo(cx, cy + 5, cx + w * 0.28, cy);
      ctx.stroke();
      return;
    }

    let rx = w / 2;
    let ry = h / 2;
    switch (viseme) {
      case "A": rx = w * 0.50; ry = h * 0.62; break;
      case "O": rx = w * 0.34; ry = h * 0.60; break;
      case "U": rx = w * 0.26; ry = h * 0.52; break;
      case "E": rx = w * 0.56; ry = h * 0.40; break;
      case "I": rx = w * 0.58; ry = Math.min(ry, 7); break;
      default: rx = w * 0.42; ry = h * 0.45;
    }

    ctx.fillStyle = "#7c3444";
    ctx.beginPath();
    ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2);
    ctx.fill();

    if (ry > 6) {
      ctx.fillStyle = "#cf7480";
      ctx.beginPath();
      ctx.ellipse(cx, cy + ry * 0.42, rx * 0.62, ry * 0.45, 0, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.strokeStyle = "rgba(90,52,48,0.55)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2);
    ctx.stroke();
  }

  _blush(cx, cy, skills) {
    const amount = skills?.rizz?.active ? 0.5 : (skills?.speechcraft?.active ? 0.22 : 0);
    if (amount <= 0) return;
    const ctx = this.ctx;
    ctx.fillStyle = `rgba(240, 120, 130, ${amount})`;
    for (const s of [-1, 1]) {
      ctx.beginPath();
      ctx.ellipse(cx + s * 46, cy + 40, 17, 9, 0, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  _glasses(cx, cy, focus) {
    const ctx = this.ctx, th = this.theme;
    const isCode = focus === "coding";
    const lens = isCode ? "rgba(0,0,0,0.55)" : "rgba(255,255,255,0.18)";
    const rim = isCode ? "#0a0a0a" : "#3a2a1a";
    ctx.strokeStyle = rim;
    ctx.fillStyle = lens;
    ctx.lineWidth = 3;
    ctx.lineCap = "round";
    for (const s of [-1, 1]) {
      ctx.beginPath();
      ctx.ellipse(cx + s * 32, cy + 16, 22, 20, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
    }
    ctx.beginPath();
    ctx.moveTo(cx - 10, cy + 16);
    ctx.lineTo(cx + 10, cy + 16);
    ctx.stroke();
    // small reflection on the right lens for code mode
    if (isCode) {
      ctx.fillStyle = "rgba(120, 200, 255, 0.85)";
      for (const s of [-1, 1]) {
        ctx.beginPath();
        ctx.moveTo(cx + s * 30, cy + 4);
        ctx.lineTo(cx + s * 38, cy + 4);
        ctx.lineTo(cx + s * 30, cy + 26);
        ctx.lineTo(cx + s * 22, cy + 26);
        ctx.closePath();
        ctx.fill();
      }
    }
  }

  _sweat(cx, cy) {
    const ctx = this.ctx;
    const y = cy - 40 + ((this.t * 60) % 40);
    ctx.fillStyle = "rgba(150, 210, 240, 0.85)";
    ctx.beginPath();
    ctx.moveTo(cx + 74, y);
    ctx.quadraticCurveTo(cx + 84, y + 12, cx + 74, y + 18);
    ctx.quadraticCurveTo(cx + 64, y + 12, cx + 74, y);
    ctx.fill();
  }

  _speedLines(cx, cy) {
    const ctx = this.ctx;
    ctx.strokeStyle = "rgba(255,255,255,0.28)";
    ctx.lineWidth = 3;
    for (let i = 0; i < 5; i++) {
      const y = cy - 60 + i * 42 + ((this.t * 300) % 42);
      const len = 60 + (i % 2) * 40;
      ctx.beginPath();
      ctx.moveTo(cx - 120, y);
      ctx.lineTo(cx - 120 + len, y);
      ctx.stroke();
    }
  }
}
