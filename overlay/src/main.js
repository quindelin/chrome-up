import { Net, fetchConfig, delta, lerp } from "./net.js";
import { Compass, fmtDistance } from "./compass.js";
import { Hud } from "./hud.js";
import { Ring } from "./ring.js";
import { Avatar } from "./avatar.js";
import { Menu } from "./menu.js";
import { resolve as resolveTheme } from "./themes.js";
import { tryLoadLive2D, drawLive2D } from "./live2d.js";
import { PrivacyBadge } from "./privacy.js";
import { VicinityFeed } from "./vicinity.js";

const cfg = await fetchConfig();

const compass = new Compass(document.getElementById("compass"), cfg.markers || []);
const hud = new Hud();
const ring = new Ring(document.getElementById("ring"));
const avatarCanvas = document.getElementById("avatar");
const avatar = new Avatar(avatarCanvas, resolveTheme(cfg.avatar?.theme || "default"));
const live2d = await tryLoadLive2D(avatarCanvas, cfg);
if (live2d) console.log("[hudstream] Live2D model loaded:", live2d.name);
const menu = new Menu(document.getElementById("menu"));
const privacy = new PrivacyBadge(document.getElementById("privacy"));
privacy.start();
new VicinityFeed(document.getElementById("vicinity")).start();
const statusEl = document.getElementById("status");
const stateText = document.getElementById("statetext");
const objectiveEl = document.getElementById("objective");
const thuumName = document.getElementById("thuum-name");
const thuumFill = document.getElementById("thuum-fill");
const stealthEl = document.getElementById("stealth");

let latest = null;

const net = new Net();
net.onStatus((ok) => {
  if (!ok) {
    statusEl.textContent = "Reconnecting to HUDstream…";
    statusEl.classList.remove("hidden");
  } else {
    statusEl.classList.add("hidden");
  }
});
net.on((payload) => {
  latest = payload;
  payload.__markers = cfg.markers || [];
  hud.update(payload);
  hud.handleEvents(payload.events);
});
net.connect();

const smooth = { level: 0, openness: 0, heading: 0, width: 0.5 };
let viseme = "closed";
let lastT = performance.now();

function frame(now) {
  const dt = Math.min(0.1, (now - lastT) / 1000);
  lastT = now;

  if (latest) {
    const a = latest.audio || {};
    smooth.level = lerp(smooth.level, a.level || 0, Math.min(1, dt * 14));
    smooth.openness = lerp(smooth.openness, a.openness || 0, Math.min(1, dt * 16));
    smooth.width = lerp(smooth.width, a.width ?? 0.5, Math.min(1, dt * 8));
    smooth.heading = smooth.heading + delta(smooth.heading, latest.heading?.deg || 0) * Math.min(1, dt * 6);
    viseme = a.viseme || "closed";

    // navigation objective on the compass + text line
    const nav = latest.nav || {};
    const obj = nav.active ? nav.objective : null;
    compass.setObjective(obj);
    if (obj) {
      objectiveEl.innerHTML =
        `${obj.step || obj.name}<span class="dist">${fmtDistance(obj.distance)}</span>`;
      objectiveEl.classList.remove("hidden");
    } else if (nav.status) {
      objectiveEl.textContent = nav.status;
      objectiveEl.classList.remove("hidden");
    } else {
      objectiveEl.classList.add("hidden");
    }

    compass.setHeading(smooth.heading);
    compass.draw();

    const audioForDraw = {
      level: smooth.level,
      openness: smooth.openness,
      width: smooth.width,
      viseme,
      bands: a.bands || [],
    };
    ring.draw(dt, audioForDraw);
    if (live2d) drawLive2D(live2d, audioForDraw);
    else avatar.draw(dt, audioForDraw, latest.vision, latest.skills);
    stateText.textContent = describe(latest);
    menu.update(latest, latest.ui || { open: false, tab: 0, tabs: [] });

    // Thu'um meter + stealth eye
    const sh = latest.shout || {};
    if (thuumName) thuumName.textContent = sh.last || "Fus Ro Dah";
    if (thuumFill) {
      const ratio = sh.cooldown_max > 0 ? 1 - (sh.cooldown / sh.cooldown_max) : 1;
      thuumFill.style.width = `${Math.max(0, Math.min(1, ratio)) * 100}%`;
    }
    if (stealthEl) stealthEl.classList.toggle("hidden", !(latest.skills?.sneak?.active));
  } else {
    compass.draw();
  }
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);

function describe(p) {
  const v = p.vision || {};
  const a = p.audio || {};
  if (v.focus === "coding") return "coding";
  if (v.focus === "reading") return "reading";
  const act = v.activity;
  if (act && act !== "idle") return act;
  if (a.speaking && (v.people || 0) >= 3) return "crowd speech";
  if (a.speaking && (v.people || 0) === 1) return "1-on-1";
  if (a.speaking) return "speaking";
  if (v.moving) return "moving";
  return "idle";
}
