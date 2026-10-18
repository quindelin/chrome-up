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

  const rig = new Rig(vrm, camera, renderer, scene, av);
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

    const h = vrm.humanoid;
    this.bone = (name) => h.getNormalizedBoneNode(name);
    this._restPose();
    this._frame();
  }

  /** arms down and slightly forward instead of the T-pose */
  _restPose() {
    const set = (name, x, y, z) => { const b = this.bone(name); if (b) b.rotation.set(x, y, z); };
    set("leftUpperArm", 0.1, 0, 1.2);
    set("rightUpperArm", 0.1, 0, -1.2);
    set("leftLowerArm", 0, 0.3, 0.1);
    set("rightLowerArm", 0, -0.3, -0.1);
    set("leftHand", 0, 0, 0.1);
    set("rightHand", 0, 0, -0.1);
  }

  /** frame head and shoulders, whatever the model's height */
  _frame() {
    this.vrm.scene.updateMatrixWorld(true);
    const head = this.bone("head");
    const p = new THREE.Vector3();
    head.getWorldPosition(p);
    this.headY = p.y;
    this.camera.position.set(0, p.y - 0.02, 2.05);
    this.camera.lookAt(0, p.y - 0.2, 0);
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

  update(dt, audio, vision, skills = {}) {
    this.t += dt;
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
    if (neck) neck.rotation.y = Math.sin(this.t * 0.45) * 0.06;
    if (head) {
      // nod on loud syllables, small tilt that wanders while you talk
      head.rotation.x = -talk * 0.12 + Math.sin(this.t * 6.5) * talk * 0.05 + Math.sin(this.t * 0.9) * 0.02;
      head.rotation.z = Math.sin(this.t * 0.55) * 0.04 + Math.sin(this.t * 2.1) * talk * 0.05;
      head.rotation.y = Math.sin(this.t * 0.33) * 0.05;
    }
    this.vrm.scene.position.y = Math.abs(Math.sin(this.t * 4.5)) * talk * 0.006
      + (running ? Math.abs(Math.sin(this.t * 9)) * 0.02 : 0);

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
