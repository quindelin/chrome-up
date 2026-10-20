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
import { loadSfx } from "./sfx.js";

const cfg = await fetchConfig();
loadSfx();

const compass = new Compass(document.getElementById("compass"), cfg.markers || []);
const hud = new Hud();
const ring = new Ring(document.getElementById("ring"));
const avatarCanvas = document.getElementById("avatar");
const avatar = new Avatar(avatarCanvas, resolveTheme(cfg.avatar?.theme || "default"));
const live2d = await tryLoadLive2D(avatarCanvas, cfg);
if (live2d) console.log("[hudstream] Live2D model loaded:", live2d.name);
// 3D VRM avatar (default). Falls back to Live2D / the 2D avatar if it can't load.
const avatar3dCanvas = document.getElementById("avatar3d");
// imported lazily: if the 3D module fails to load (bad build, no WebGL
// support at all), the rest of the HUD must still come up
let avatar3d = null;
if (!live2d) {
  try {
    const { tryLoadAvatar3D } = await import("./avatar3d.js");
    avatar3d = await tryLoadAvatar3D(avatar3dCanvas, cfg);
  } catch (err) {
    console.warn("[hudstream] 3D avatar unavailable, using 2D:", err?.message || err);
  }
}
if (avatar3d) {
  avatar3dCanvas.classList.remove("hidden");
  avatarCanvas.classList.add("hidden");
  document.getElementById("ring").classList.add("hidden");
  document.getElementById("avatar-wrap").classList.add("is-3d", cfg.avatar?.layout === "bust" ? "bust" : "full");
  window.__avatar3d = avatar3d;            // console: __avatar3d.debug = {activity: "running"}
}
const menu = new Menu(document.getElementById("menu"));
const privacy = new PrivacyBadge(document.getElementById("privacy"));
privacy.start();
new VicinityFeed(document.getElementById("vicinity")).start();
const statusEl = document.getElementById("status");
const objectiveEl = document.getElementById("objective");
const thuumName = document.getElementById("thuum-name");
const thuumFill = document.getElementById("thuum-fill");

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
  avatar3d?.react(payload.events);
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
    if (avatar3d) avatar3d.update(dt, audioForDraw, latest.vision, latest.skills, latest.head);
    else ring.draw(dt, audioForDraw);
    if (avatar3d) { /* the 3D rig draws itself */ }
    else if (live2d) drawLive2D(live2d, audioForDraw);
    else avatar.draw(dt, audioForDraw, latest.vision, latest.skills);
    menu.update(latest, latest.ui || { open: false, tab: 0, tabs: [] });

    // Thu'um meter
    const sh = latest.shout || {};
    if (thuumName) thuumName.textContent = sh.last || "Fus Ro Dah";
    if (thuumFill) {
      const ratio = sh.cooldown_max > 0 ? 1 - (sh.cooldown / sh.cooldown_max) : 1;
      thuumFill.style.width = `${Math.max(0, Math.min(1, ratio)) * 100}%`;
      // like the vanilla shout meter: only on screen while recharging
      thuumFill.closest("#thuum")?.classList.toggle("ready", ratio >= 1);
    }
  } else {
    compass.draw();
  }
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
