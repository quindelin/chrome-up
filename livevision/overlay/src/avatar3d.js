/**
 * 3D VTuber avatar: a VRM model (VRoid / VSeeFace format) rendered with
 * three.js + three-vrm, driven like a normal VTuber rig from your voice.
 *
 *   voice  -> vowel lip-sync (あ い う え お) from the server's viseme + openness
 *   idle   -> breathing, blinking, slow sway, eyes drifting
 *   talk   -> head nods and tilts with loudness, a little body bounce
 *   events -> joy on a level-up / skill-up, angry face on a shout,
 *             relaxed smile while "rizz" is active, bob while running
 *   physics-> hair and clothes spring bones (vrm.update)
 *   motion -> full body: walk / run cycle paced by your step cadence, a
 *             boxing guard, and the head follows yours when orientation
 *             arrives (payload.head: glasses Motion quaternion via the server)
 *
 * Layout: config `avatar.layout` full (default: head to toe, sized for the
 * side bar beside the portrait glasses feed) | bust (shoulders up).
 *
 * Model: overlay/assets/avatar/<file>.vrm, chosen by config `avatar.model`
 * (default fumiriya.vrm, VRoid's CC0 sample "Sakurada Fumiriya").
 * If WebGL or the model is unavailable this returns null and the caller
 * falls back to the 2D avatar, so the HUD never breaks.
 */
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { VRMLoaderPlugin, VRMUtils } from "../vendor/three-vrm.module.min.js";

// server viseme -> VRM expression, with how open that vowel is
const VISEME = {
  A: ["aa", 1.0], I: ["ih", 0.7], U: ["ou", 0.8], E: ["ee", 0.8], O: ["oh", 1.0], e: ["ee", 0.45],
};
const VOWELS = ["aa", "ih", "ou", "ee", "oh"];

export async function tryLoadAvatar3D(canvas, cfg) {
  const av = cfg?.avatar || {};
  if ((av.engine || "vrm") !== "vrm") return null;
  const file = av.model || "fumiriya.vrm";
  const layout = av.layout === "bust" ? "bust" : "full";
  if (layout === "full") {
    // drawn at render_scale and stretched by CSS: a 620x900 WebGL canvas in
    // software GL (no GPU on the VPS) costs more CPU than OBS can spare
    const k = Math.max(0.4, Math.min(1, Number(av.render_scale) || 0.75));
    canvas.width = Math.round(620 * k);
    canvas.height = Math.round(860 * k);
  }

  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({
      canvas, alpha: true, antialias: true, premultipliedAlpha: true,
      // we render at 30 fps; keep the last frame so OBS never captures a cleared canvas
      preserveDrawingBuffer: true, powerPreference: "low-power",
    });
  } catch (err) {
    console.warn("[hudstream] WebGL unavailable, using 2D avatar:", err?.message || err);
    return null;
  }
  renderer.setPixelRatio(1);
  renderer.setSize(canvas.width, canvas.height, false);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.setClearColor(0x000000, 0);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(20, canvas.width / canvas.height, 0.1, 20);
  const key = new THREE.DirectionalLight(0xffffff, Math.PI * 0.9);
  key.position.set(0.6, 1.4, 1.6);
  const rim = new THREE.DirectionalLight(0xbfd4ff, Math.PI * 0.45);
  rim.position.set(-1.2, 1.6, -1.0);
  scene.add(key, rim, new THREE.AmbientLight(0xffffff, 0.55));

  const loader = new GLTFLoader();
  loader.register((parser) => new VRMLoaderPlugin(parser));
  let gltf;
  try {
    gltf = await loader.loadAsync(new URL(`../assets/avatar/${file}`, import.meta.url).href);
  } catch (err) {
    console.warn(`[hudstream] could not load assets/avatar/${file}, using 2D avatar:`, err?.message || err);
    renderer.dispose();
    return null;
  }
  const vrm = gltf.userData.vrm;
  VRMUtils.removeUnnecessaryVertices(gltf.scene);
  VRMUtils.combineSkeletons?.(gltf.scene);
  VRMUtils.rotateVRM0(vrm);              // VRM 0.x faces -Z; turn it to the camera
  vrm.scene.traverse((o) => { o.frustumCulled = false; });
  scene.add(vrm.scene);

  const rig = new Rig(vrm, camera, renderer, scene, { ...av, layout });
  console.log("[hudstream] 3D avatar loaded:", vrm.meta?.name || vrm.meta?.title || file);
  return rig;
}

class Rig {
  constructor(vrm, camera, renderer, scene, opts) {
    this.vrm = vrm;
    this.camera = camera;
    this.renderer = renderer;
    this.scene = scene;
    this.t = 0;
    this.weights = Object.fromEntries(VOWELS.map((v) => [v, 0]));
    this.blink = 0;
    this.nextBlink = 2 + Math.random() * 3;
    this.mood = { name: null, until: 0 };
    this.level = 0;
    this.lookX = 0;
    this.lookY = 0;
    this.nextLook = 1.5;
    this.fps = Number(opts.fps) || 30;     // OBS composites at 30
    this.acc = 0;
    this.layout = opts.layout;
    this.mirror = opts.mirror !== false;   // like a webcam: you turn left, it turns screen-left
    this.gait = 0;                         // 0 idle .. 0.55 walk .. 1 run
    this.box = 0;                          // boxing guard weight
    this.phase = 0;
    this.headW = 0;                        // how much the real head drives ours
    this.headPose = { yaw: 0, pitch: 0, roll: 0 };
    this.debug = null;                     // {activity, cadence, head} to test without sensors

    const h = vrm.humanoid;
    this.bone = (name) => h.getNormalizedBoneNode(name);
    this._restPose();
    this._frame();
  }

  /** arms down and slightly forward instead of the T-pose; every frame's
   *  motion is added on top of these */
  _restPose() {
    this.rest = {
      leftUpperArm: [0.1, 0, 1.2], rightUpperArm: [0.1, 0, -1.2],
      leftLowerArm: [0, 0.3, 0.1], rightLowerArm: [0, -0.3, -0.1],
      leftHand: [0, 0, 0.1], rightHand: [0, 0, -0.1],
    };
    for (const name of Object.keys(this.rest)) this._pose(name, 0, 0, 0);
  }

  /** rest pose + offset */
  _pose(name, x, y, z) {
    const b = this.bone(name);
    if (!b) return;
    const r = this.rest?.[name] || [0, 0, 0];
    b.rotation.set(r[0] + x, r[1] + y, r[2] + z);
  }

  /** bust shot cut halfway through the shoulders, whatever the model's
   *  proportions: top of the hair down to the shoulder joints */
  _frame() {
    if (this.layout === "full") return this._frameFull();
    this.vrm.scene.updateMatrixWorld(true);
    const p = new THREE.Vector3();
    this.bone("head").getWorldPosition(p);
    this.headY = p.y;
    const top = p.y + 0.24;                       // head bone sits at the jaw; hair above
    const arm = this.bone("leftUpperArm") || this.bone("leftShoulder");
    const bottom = arm ? arm.getWorldPosition(new THREE.Vector3()).y : p.y - 0.22;
    const half = (top - bottom) / 2;
    const dist = half / Math.tan(THREE.MathUtils.degToRad(this.camera.fov / 2));
    const mid = (top + bottom) / 2;
    this.camera.position.set(0, mid + 0.02, dist);
    this.camera.lookAt(0, mid, 0);
  }

  /** head to toe with a little air, centred */
  _frameFull() {
    this.vrm.scene.updateMatrixWorld(true);
    const v = new THREE.Vector3();
    this.bone("head").getWorldPosition(v);
    this.headY = v.y;
    const top = v.y + 0.3;
    const foot = this.bone("leftToes") || this.bone("leftFoot");
    const bottom = (foot ? foot.getWorldPosition(new THREE.Vector3()).y : 0) - 0.12;
    const half = (top - bottom) / 2;
    const dist = half / Math.tan(THREE.MathUtils.degToRad(this.camera.fov / 2));
    const mid = (top + bottom) / 2;
    this.camera.position.set(0, mid + 0.1, dist);
    this.camera.lookAt(0, mid, 0);
  }

  /** one-shot facial reactions driven by HUD events */
  react(events = []) {
    for (const ev of events) {
      if (ev.type === "level") this._mood("happy", 3.5);
      else if (ev.type === "skill_level") this._mood("happy", 1.6);
      else if (ev.type === "shout") this._mood("angry", 1.4);
      else if (ev.type === "discovery") this._mood("surprised", 2.0);
    }
  }

  _mood(name, seconds) {
    this.mood = { name, until: this.t + seconds };
  }

  /** one leg forward while the other is back; the knee folds on the way through */
  _legs(g, ph, pc) {
    const swing = (0.42 + 0.25 * Math.max(0, (g - 0.55) / 0.45)) * g;
    const set = (name, x) => { const bn = this.bone(name); if (bn) bn.rotation.set(x, 0, 0); };
    set("leftUpperLeg", -ph * swing);
    set("rightUpperLeg", ph * swing);
    // measured on the rig: +x on the lower leg kicks the foot forward
    // (hyperextension); a real knee folds the foot back, so negative
    set("leftLowerLeg", -Math.max(0, -pc) * 1.1 * g);
    set("rightLowerLeg", -Math.max(0, pc) * 1.1 * g);
    set("leftFoot", ph * 0.2 * g);
    set("rightFoot", -ph * 0.2 * g);
  }

  update(dt, audio, vision, skills = {}, headIn = null) {
    this.t += dt;
    if (this.debug) {           // window.__avatar3d.debug = {activity, cadence, head}
      vision = { ...(vision || {}), activity: this.debug.activity ?? vision?.activity,
                 cadence: this.debug.cadence ?? vision?.cadence };
      if (this.debug.head) headIn = { fresh: true, ...this.debug.head };
    }
    const em = this.vrm.expressionManager;
    const level = audio?.level ?? 0;
    this.level += (level - this.level) * Math.min(1, dt * 10);

    // ---- lip-sync: ease toward the current vowel, everything else to 0
    const vis = VISEME[audio?.viseme];
    const open = Math.min(1, (audio?.openness ?? 0) * 1.35);
    for (const v of VOWELS) {
      const target = vis && vis[0] === v ? open * vis[1] : 0;
      const rate = target > this.weights[v] ? 22 : 14;     // open fast, close a bit slower
      this.weights[v] += (target - this.weights[v]) * Math.min(1, dt * rate);
      em?.setValue(v, this.weights[v]);
    }

    // ---- mood / expression
    const ambient = skills?.rizz?.active ? "relaxed" : null;
    const moodName = this.t < this.mood.until ? this.mood.name : ambient;
    for (const m of ["happy", "angry", "surprised", "relaxed", "sad"]) {
      const cur = em?.getValue(m) ?? 0;
      const target = m === moodName ? (m === "relaxed" ? 0.6 : 1) : 0;
      em?.setValue(m, cur + (target - cur) * Math.min(1, dt * 6));
    }

    // ---- blink (suppressed while smiling: VRoid's joy already closes the eyes)
    this.nextBlink -= dt;
    if (this.nextBlink <= 0) {
      this.blink = 1;
      this.nextBlink = 2.2 + Math.random() * 3.8;
      if (Math.random() < 0.15) this.nextBlink = 0.25;    // occasional double blink
    }
    this.blink = Math.max(0, this.blink - dt * 8);
    const blinkW = moodName === "happy" ? 0 : Math.sin(Math.min(1, this.blink) * Math.PI);
    em?.setValue("blink", blinkW);

    // ---- body: breathing, idle sway, talking nods, running bob
    const running = !!vision?.running;
    const breathe = Math.sin(this.t * 1.9) * 0.012;
    const talk = this.level;
    const spine = this.bone("spine");
    const chest = this.bone("chest") || this.bone("upperChest");
    const neck = this.bone("neck");
    const head = this.bone("head");
    if (spine) {
      spine.rotation.x = breathe + (running ? Math.sin(this.t * 9) * 0.03 : 0);
      spine.rotation.z = Math.sin(this.t * 0.7) * 0.02;
    }
    if (chest) chest.rotation.x = breathe * 0.8;
    // ---- your head drives ours when orientation is arriving, else idle motion
    const hp = headIn && headIn.fresh ? headIn : null;
    this.headW += ((hp ? 1 : 0) - this.headW) * Math.min(1, dt * 4);
    if (hp) {
      const clamp = (v, m) => Math.max(-m, Math.min(m, Number(v) || 0));
      const ease = Math.min(1, dt * 10);
      const target = { yaw: clamp(hp.yaw, 70), pitch: clamp(hp.pitch, 40), roll: clamp(hp.roll, 30) };
      for (const k of ["yaw", "pitch", "roll"]) this.headPose[k] += (target[k] - this.headPose[k]) * ease;
    }
    const rad = THREE.MathUtils.degToRad;
    const w = this.headW, flip = this.mirror ? -1 : 1;
    const yaw = rad(this.headPose.yaw) * flip, pitch = rad(this.headPose.pitch), roll = rad(this.headPose.roll) * flip;
    if (neck) neck.rotation.y = Math.sin(this.t * 0.45) * 0.06 * (1 - w) + yaw * 0.4 * w;
    if (head) {
      // nod on loud syllables, small tilt that wanders while you talk
      const idleX = -talk * 0.12 + Math.sin(this.t * 6.5) * talk * 0.05 + Math.sin(this.t * 0.9) * 0.02;
      head.rotation.x = idleX * (1 - w) + (pitch + idleX * 0.3) * w;
      head.rotation.z = (Math.sin(this.t * 0.55) * 0.04 + Math.sin(this.t * 2.1) * talk * 0.05) * (1 - w) + roll * w;
      head.rotation.y = Math.sin(this.t * 0.33) * 0.05 * (1 - w) + yaw * 0.6 * w;
    }

    // ---- locomotion: gait paced by your real step cadence
    const act = vision?.activity || (running ? "running" : vision?.moving ? "walking" : "idle");
    const gaitTarget = act === "running" ? 1 : act === "walking" ? 0.55 : 0;
    this.gait += (gaitTarget - this.gait) * Math.min(1, dt * 3);
    this.box += ((act === "boxing" ? 1 : 0) - this.box) * Math.min(1, dt * 4);
    const cad = Number(vision?.cadence) > 0.5 ? Number(vision.cadence) : act === "running" ? 2.8 : 1.8;
    this.phase += dt * Math.PI * cad * (this.gait > 0.02 || this.box > 0.02 ? 1 : 0);   // 2 steps = 1 cycle
    const g = this.gait, ph = Math.sin(this.phase), pc = Math.cos(this.phase);
    const run = Math.max(0, (g - 0.55) / 0.45);                 // 0 walking .. 1 running
    this._legs(g, ph, pc);
    // Offsets measured on the rig (camera at +z): +x swings an upper arm
    // forward; the elbow folds the forearm up with -y on the left, +y on the
    // right. Guard = upper +0.5, forearm 1.9: fists in front of the chin.
    const b = this.box;
    const jab = Math.max(0, Math.sin(this.phase * 2));          // one punch per step
    const jabL = b * (ph > 0 ? jab : 0), jabR = b * (ph < 0 ? jab : 0);
    this._pose("leftUpperArm",  ph * 0.45 * g + b * 0.5 + jabL * 0.7, 0, 0);
    this._pose("rightUpperArm", -ph * 0.45 * g + b * 0.5 + jabR * 0.7, 0, 0);
    this._pose("leftLowerArm",  0, -(1.0 * run * (1 - b) + b * 1.9 * (1 - 0.85 * jabL / Math.max(b, 1e-3))), 0);
    this._pose("rightLowerArm", 0, 1.0 * run * (1 - b) + b * 1.9 * (1 - 0.85 * jabR / Math.max(b, 1e-3)), 0);
    if (spine) {
      spine.rotation.y = ph * 0.1 * g + Math.sin(this.phase * 2) * 0.12 * b;
      spine.rotation.x += 0.14 * run + 0.08 * b;                // lean in to run or fight
    }
    const hips = this.bone("hips");
    if (hips) hips.rotation.y = -ph * 0.08 * g;
    this.vrm.scene.position.y = Math.abs(Math.sin(this.t * 4.5)) * talk * 0.006
      + Math.abs(ph) * (0.012 + 0.03 * run) * g;

    // ---- eyes wander a little, as people's do
    this.nextLook -= dt;
    if (this.nextLook <= 0) {
      this.nextLook = 1.2 + Math.random() * 2.8;
      this.lookX = (Math.random() - 0.5) * 0.25;
      this.lookY = (Math.random() - 0.5) * 0.12;
    }
    if (this.vrm.lookAt) {
      this.vrm.lookAt.yaw += (this.lookX * 20 - this.vrm.lookAt.yaw) * Math.min(1, dt * 5);
      this.vrm.lookAt.pitch += (this.lookY * 20 - this.vrm.lookAt.pitch) * Math.min(1, dt * 5);
    }

    // ---- render at the stream's frame rate, not the display's
    this.acc += dt;
    if (this.acc < 1 / this.fps) return;
    this.vrm.update(this.acc);           // expressions, look-at, spring bones
    this.acc = 0;
    this.renderer.render(this.scene, this.camera);
  }
}
