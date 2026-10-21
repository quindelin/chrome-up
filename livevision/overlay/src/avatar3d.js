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
 *   body   -> payload.body (server/body.py): sits when the phone in your
 *             pocket says your thigh is horizontal, reaches its hands to
 *             where the glasses camera sees yours (two-bone arm IK), and
 *             turns its wrists with the Apple Watch / Neural Band, and throws
 *             a punch on the matching arm each time the Watch / band feels
 *             one (body.punches), holding a guard while they keep coming
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
// boxing guard, measured on the rig: upper arm forward (+x) and in toward the
// chest (+z on the left, -z on the right), forearm folded up: wrists at chin
// height, ~12 cm either side of centre, ~23 cm in front
const GUARD_UP = 0.7, GUARD_FOLD = 2.2, GUARD_IN = 0.3;

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
  rig.addSeat(THREE);
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
    this.punch = { left: null, right: null };  // {t, kind, strength} on the avatar's arm
    this.punchSeen = -1;                   // highest body.punches id played (-1: not synced yet)
    this.punchE = { left: 0, right: 0 };   // 0 guard .. 1 full extension, this frame
    this.phase = 0;
    this.headW = 0;                        // how much the real head drives ours
    this.headPose = { yaw: 0, pitch: 0, roll: 0 };
    this.debug = null;                     // {activity, cadence, head, body} to test without sensors
    this.sit = 0;                          // 0 standing .. 1 sitting
    this.handW = { left: 0, right: 0 };    // how much a tracked hand drives each arm
    this.handTarget = { left: null, right: null };
    this.armW = { left: 0, right: 0 };     // how much a wrist-tracked arm direction drives it
    this.armDir = { left: null, right: null };
    this.wristW = { left: 0, right: 0 };
    this.wristPose = { left: { yaw: 0, pitch: 0, roll: 0 }, right: { yaw: 0, pitch: 0, roll: 0 } };
    this._v = [new THREE.Vector3(), new THREE.Vector3(), new THREE.Vector3(), new THREE.Vector3()];
    this._q = [new THREE.Quaternion(), new THREE.Quaternion(), new THREE.Quaternion()];

    const h = vrm.humanoid;
    this.bone = (name) => h.getNormalizedBoneNode(name);
    this.restShoulder = Object.fromEntries(["left", "right"].map((s) => [s, this.bone(s + "Shoulder")?.rotation.clone()]));
    this._restPose();
    this._measure();
    this._frame();
  }

  /** arms down and slightly forward instead of the T-pose; every frame's
   *  motion is added on top of these */
  _restPose() {
    this.rest = {
      leftUpperArm: [0.12, 0, 1.22], rightUpperArm: [0.12, 0, -1.22],
      leftLowerArm: [0, 0.42, 0.1], rightLowerArm: [0, -0.42, -0.1],
      leftHand: [0, 0, 0.1], rightHand: [0, 0, -0.1],
    };
    for (const name of Object.keys(this.rest)) this._pose(name, 0, 0, 0);
  }

  /** lengths taken from the model itself, so any VRM sits and reaches right */
  _measure() {
    this.vrm.scene.updateMatrixWorld(true);
    const at = (n) => { const b = this.bone(n); return b ? b.getWorldPosition(new THREE.Vector3()) : null; };
    const sh = at("leftUpperArm"), el = at("leftLowerArm"), wr = at("leftHand");
    this.armLen = sh && el && wr ? sh.distanceTo(el) + el.distanceTo(wr) : null;
    const hip = at("hips"), knee = at("leftLowerLeg"), ankle = at("leftFoot");
    this.legs = hip && knee && ankle ? {
      hipY: hip.y, shin: knee.distanceTo(ankle), ankleY: ankle.y, thigh: hip.distanceTo(knee),
    } : null;
  }

  /** a plain seat that fades in when you sit, so the avatar isn't sitting on air */
  addSeat(T) {
    if (!this.legs) return;
    const top = this.legs.shin + this.legs.ankleY;          // seat height = knee height
    const geo = new T.BoxGeometry(0.46, top, 0.42);
    const mat = new T.MeshStandardMaterial({ color: 0x4a3a2a, roughness: 0.9, transparent: true, opacity: 0 });
    this.seat = new T.Mesh(geo, mat);
    this.seat.position.set(0, top / 2, -this.legs.thigh * 0.45);
    this.seat.visible = false;
    this.scene.add(this.seat);
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

  /** Tracked hands pull the arms to them (two-bone IK); wrists turn the hands.
   *  Mirror (default): your right hand drives the avatar's left, on screen-right,
   *  like a webcam; head-relative +x (your right) maps to world +x. */
  _arms(dt, bodyIn) {
    const head = this.bone("head");
    if (!head) return;
    const flip = this.mirror ? 1 : -1;
    const ease = Math.min(1, dt * 6);
    for (const side of ["left", "right"]) {
      const theirs = this.mirror ? (side === "left" ? "right" : "left") : side;
      const h = bodyIn?.hands?.[theirs];
      const fresh = !!(h && h.fresh);
      this.handW[side] += ((fresh ? 1 : 0) - this.handW[side]) * ease;
      if (fresh) {
        head.getWorldPosition(this._v[0]);
        const t = new THREE.Vector3(this._v[0].x + flip * h.x, this._v[0].y + h.y, this._v[0].z + h.z);
        this.handTarget[side] = this.handTarget[side] ? this.handTarget[side].lerp(t, ease) : t;
      }
      if (this.handW[side] > 0.01 && this.handTarget[side]) this._ikArm(side, this.handTarget[side], this.handW[side]);

      // the wrist sensors say where the arm points (server/arms.py, body
      // frame: x = your right, y = up, z = forward): reach along it, unless
      // the camera sees the hand itself (that's a real position)
      const arm = bodyIn?.arms?.[theirs];
      const af = !!(arm && arm.fresh && Array.isArray(arm.dir));
      this.armW[side] += ((af && !fresh ? 1 : 0) - this.armW[side]) * ease;
      if (af) {
        const d = new THREE.Vector3(flip * arm.dir[0], arm.dir[1], arm.dir[2]).normalize();
        this.armDir[side] = this.armDir[side] ? this.armDir[side].lerp(d, Math.min(1, dt * 12)).normalize() : d;
      }
      if (this.armW[side] > 0.01 && this.armDir[side]) {
        this.vrm.scene.updateMatrixWorld(true);
        const S = this.bone(side + "UpperArm").getWorldPosition(new THREE.Vector3());
        const E = this.bone(side + "LowerArm").getWorldPosition(new THREE.Vector3());
        const Hh = this.bone(side + "Hand").getWorldPosition(new THREE.Vector3());
        const reach = (S.distanceTo(E) + E.distanceTo(Hh)) * 0.93;   // a soft elbow
        this._ikArm(side, S.clone().add(this.armDir[side].clone().multiplyScalar(reach)), this.armW[side]);
      }

      // a punch wins over the camera's hand for its ~0.3 s
      const pe = this.punchE[side];
      if (pe > 0.001 && this.punch[side] && this.armW[side] < 0.5) {
        this.vrm.scene.updateMatrixWorld(true);
        const H0 = this.bone(side + "Hand").getWorldPosition(new THREE.Vector3());
        const { target, pole } = this._punchTarget(side, H0, pe);
        this._ikArm(side, target, Math.min(1, pe * 4), pole);
      }

      const w = bodyIn?.wrists?.[theirs];
      const wf = !!(w && w.fresh);
      this.wristW[side] += ((wf ? 1 : 0) - this.wristW[side]) * ease;
      if (wf) for (const k of ["yaw", "pitch", "roll"]) {
        this.wristPose[side][k] += ((Number(w[k]) || 0) - this.wristPose[side][k]) * ease;
      }
      // rest + offset every frame (nothing else resets the hand bones, so
      // adding to the current rotation would spin the hand)
      const r = THREE.MathUtils.degToRad, k = this.wristW[side], wp = this.wristPose[side];
      const clamp = (v, m) => Math.max(-m, Math.min(m, v));
      // only the forearm twist (rotation about the Watch's x axis, which
      // runs along the forearm: HeadPose calls it pitch). The other two axes
      // are mostly the whole arm moving, and as hand bends they left the hand
      // sitting crooked
      this._pose(side + "Hand", r(clamp(wp.pitch, 60)) * k, 0, 0);
    }
  }

  /** New punches from body.punches, each id once. The first payload only
   *  syncs (no replaying what happened before the page loaded); a smaller id
   *  than we've seen means the server restarted. */
  _takePunches(bodyIn) {
    const list = Array.isArray(bodyIn?.punches) ? bodyIn.punches : null;
    if (!list) return;
    const top = list.reduce((m, p) => Math.max(m, Number(p.id) || 0), 0);
    if (this.punchSeen < 0 || (list.length && top < this.punchSeen)) { this.punchSeen = top; return; }
    for (const p of list) {
      if (!(p.id > this.punchSeen) || !(p.side === "left" || p.side === "right")) continue;
      this.punchSeen = p.id;
      if ((Number(p.age) || 0) > 0.5) continue;             // too late to look in sync
      // mirror: the wearer's right drives the avatar's left, like the hands
      const side = this.mirror ? (p.side === "left" ? "right" : "left") : p.side;
      this.punch[side] = { t: this.t, kind: p.kind || "straight",
                           strength: Math.max(0, Math.min(1, Number(p.strength) || 0.7)) };
    }
  }

  /** 0 at guard .. 1 at full reach: a fast ease-out (~120 ms, quicker when
   *  harder) and a ~200 ms smooth recovery */
  _punchEnvelope(side) {
    const p = this.punch[side];
    if (!p) return 0;
    const ext = 0.12 * (1.15 - 0.3 * p.strength), rec = 0.2;
    const t = this.t - p.t;
    if (t >= ext + rec) { this.punch[side] = null; return 0; }
    if (t < ext) { const u = t / ext; return 1 - (1 - u) * (1 - u); }
    const u = (t - ext) / rec;
    return 1 - u * u * (3 - 2 * u);
  }

  /** The fist's path from the guard (H0, world) to the punch's end point,
   *  for the avatar's `side` arm. Straight: forward to the centre line at chin
   *  height; hook: swings out and round to the front of the chin, elbow out;
   *  uppercut: dips, then drives up under the chin. */
  _punchTarget(side, H0, e) {
    const p = this.punch[side];
    const S = this.bone(side + "UpperArm").getWorldPosition(new THREE.Vector3());
    const out = S.x >= 0 ? 1 : -1;
    const L = this.armLen || 0.47;
    const chinY = (this.bone("head")?.getWorldPosition(this._v[3]).y ?? S.y + 0.14) - 0.04;
    const reach = 0.8 + 0.2 * p.strength;                  // harder = further
    let end, bulge, pole;
    if (p.kind === "hook") {
      end = new THREE.Vector3(out * 0.02, chinY - 0.06, S.z + 0.6 * L);
      bulge = new THREE.Vector3(out * 0.18, 0.02, -0.03);
      pole = new THREE.Vector3(out, -0.15, -0.3);           // elbow up and out
    } else if (p.kind === "uppercut") {
      end = new THREE.Vector3(-out * 0.03, chinY + 0.03, S.z + 0.5 * L);
      bulge = new THREE.Vector3(0, -0.14, 0.02);
      pole = new THREE.Vector3(0.25 * out, -1, 0.1);        // elbow under the fist
    } else {
      end = S.clone().addScaledVector(new THREE.Vector3(-out * 0.22, (chinY - S.y) / L, 1).normalize(), 0.97 * L);
      bulge = new THREE.Vector3();
      pole = null;
    }
    end.sub(H0).multiplyScalar(reach).add(H0);
    return { target: H0.clone().lerp(end, e).addScaledVector(bulge, Math.sin(Math.PI * e)), pole };
  }

  /** Close the hands into fists by k (0..1). Measured on the rig: +z curls
   *  the left fingers toward the palm, -z the right ones. */
  _fists(k) {
    for (const [side, sg] of [["left", 1], ["right", -1]]) {
      for (const f of ["Index", "Middle", "Ring", "Little"]) {
        for (const [j, a] of [["Proximal", 1.4], ["Intermediate", 1.5], ["Distal", 1.0]]) {
          const b = this.bone(side + f + j);
          if (b) b.rotation.set(0, 0, sg * a * k);
        }
      }
      for (const [j, a] of [["Metacarpal", 0.3], ["Proximal", 0.5], ["Distal", 0.6]]) {
        const b = this.bone(side + "Thumb" + j);
        if (b) b.rotation.set(0, 0, sg * a * k);
      }
    }
  }

  /** Analytic two-bone IK: upper arm + forearm reach `target` (world), elbow
   *  bent toward a pole that points down, back and out, the way elbows go.
   *  Works on whatever rest orientation the model's bones have: each bone is
   *  turned by the world-space rotation that points it at the next joint. */
  _ikArm(side, target, weight, poleDir = null) {
    const up = this.bone(side + "UpperArm"), lo = this.bone(side + "LowerArm"), hand = this.bone(side + "Hand");
    if (!up || !lo || !hand) return;
    this.vrm.scene.updateMatrixWorld(true);
    const S = up.getWorldPosition(new THREE.Vector3());
    const E = lo.getWorldPosition(new THREE.Vector3());
    const H = hand.getWorldPosition(new THREE.Vector3());
    const L1 = S.distanceTo(E), L2 = E.distanceTo(H);
    const d = target.clone().sub(S);
    const dist = Math.min(Math.max(d.length(), Math.abs(L1 - L2) + 0.01), (L1 + L2) * 0.999);
    const dir = d.normalize();
    const out = S.x >= 0 ? 1 : -1;                           // this arm's side of the body
    const pole = poleDir ? poleDir.clone() : new THREE.Vector3(0.35 * out, -1, -0.45);
    const perp = pole.sub(dir.clone().multiplyScalar(pole.dot(dir))).normalize();
    const a = (L1 * L1 - L2 * L2 + dist * dist) / (2 * dist);
    const hgt = Math.sqrt(Math.max(0, L1 * L1 - a * a));
    const elbow = S.clone().add(dir.clone().multiplyScalar(a)).add(perp.multiplyScalar(hgt));
    const goal = S.clone().add(dir.clone().multiplyScalar(dist));
    this._aim(up, lo, elbow, weight);
    this.vrm.scene.updateMatrixWorld(true);
    this._aim(lo, hand, goal, weight);
  }

  /** turn `bone` so its child moves toward `targetWorld`, blended by weight */
  _aim(bone, child, targetWorld, weight) {
    const p = bone.getWorldPosition(new THREE.Vector3());
    const cur = child.getWorldPosition(new THREE.Vector3()).sub(p).normalize();
    const want = targetWorld.clone().sub(p).normalize();
    const delta = new THREE.Quaternion().setFromUnitVectors(cur, want);
    const world = bone.getWorldQuaternion(new THREE.Quaternion());
    const parent = bone.parent.getWorldQuaternion(new THREE.Quaternion());
    const local = parent.invert().multiply(delta.multiply(world));
    bone.quaternion.slerp(local, weight);
  }

  /** debug.body shorthand: {posture, hands: {right: {x,y,z}}, wrists: {left: {yaw,..}}} */
  _debugBody(b) {
    const hands = {}, wrists = {};
    for (const s of ["left", "right"]) {
      if (b.hands?.[s]) hands[s] = { ...b.hands[s], fresh: true };
      if (b.wrists?.[s]) wrists[s] = { ...b.wrists[s], fresh: true };
    }
    const arms = {};
    for (const s of ["left", "right"]) if (b.arms?.[s]) arms[s] = { ...b.arms[s], fresh: true };
    return { posture: b.posture || "standing", hands, wrists, arms, punches: b.punches, punching: b.punching };
  }

  /** one leg forward while the other is back; the knee folds on the way through */
  _legs(g, ph, pc) {
    const swing = (0.42 + 0.25 * Math.max(0, (g - 0.55) / 0.45)) * g;
    const set = (name, x, z = 0, y = 0) => { const bn = this.bone(name); if (bn) bn.rotation.set(x, y, z); };
    // stance: legs a little apart (measured: -z swings the left leg out, +z the right),
    // feet turned out a touch and kept flat; narrower while striding
    const wide = 0.075 * (1 - 0.6 * g);
    // sitting: thighs forward to horizontal, knees fold the shins back down
    // (measured: +x on an upper leg swings it forward, -x on a lower leg folds it)
    const sit = this.sit * 1.5;
    set("leftUpperLeg", -ph * swing + sit, -wide);
    set("rightUpperLeg", ph * swing + sit, wide);
    // measured on the rig: +x on the lower leg kicks the foot forward
    // (hyperextension); a real knee folds the foot back, so negative
    set("leftLowerLeg", -Math.max(0, -pc) * 1.1 * g - sit);
    set("rightLowerLeg", -Math.max(0, pc) * 1.1 * g - sit);
    set("leftFoot", ph * 0.2 * g, wide, 0.12);
    set("rightFoot", -ph * 0.2 * g, -wide, -0.12);
  }

  update(dt, audio, vision, skills = {}, headIn = null, bodyIn = null) {
    this.t += dt;
    if (this.debug) {           // window.__avatar3d.debug = {activity, cadence, head, body}
      vision = { ...(vision || {}), activity: this.debug.activity ?? vision?.activity,
                 cadence: this.debug.cadence ?? vision?.cadence };
      if (this.debug.head) headIn = { fresh: true, ...this.debug.head };
      if (this.debug.body) bodyIn = this._debugBody(this.debug.body);
    }
    // sitting wins over walking: the phone knows your thigh is horizontal
    const sitting = bodyIn?.posture === "sitting";
    this.sit += ((sitting ? 1 : 0) - this.sit) * Math.min(1, dt * 3);
    if (sitting) vision = { ...(vision || {}), activity: "idle" };
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
    // ---- punches: envelopes first, the torso twists into them below
    this._takePunches(bodyIn);
    // a tracked arm shows the punch itself; the canned one is for untracked arms
    for (const s of ["left", "right"]) this.punchE[s] = this.armW[s] > 0.5 ? 0 : this._punchEnvelope(s);
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
    // a real head turn is carried down the spine: neck + head take most of
    // it, the chest and spine the rest (head-only turns looked like a bobble
    // on a statue). Shares add up to 1, so the face still points where yours does
    this.bodyYaw = yaw * w;
    if (chest) {
      chest.rotation.y = this.bodyYaw * 0.18;
      chest.rotation.x += pitch * 0.12 * w;                     // look down: shoulders round a touch
    }
    if (neck) neck.rotation.y = Math.sin(this.t * 0.45) * 0.06 * (1 - w) + yaw * 0.3 * w;
    if (head) {
      // nod on loud syllables, small tilt that wanders while you talk
      const idleX = -talk * 0.12 + Math.sin(this.t * 6.5) * talk * 0.05 + Math.sin(this.t * 0.9) * 0.02;
      head.rotation.x = idleX * (1 - w) + (pitch + idleX * 0.3) * w;
      head.rotation.z = (Math.sin(this.t * 0.55) * 0.04 + Math.sin(this.t * 2.1) * talk * 0.05) * (1 - w) + roll * w;
      head.rotation.y = Math.sin(this.t * 0.33) * 0.05 * (1 - w) + yaw * 0.4 * w;
    }

    // ---- locomotion: gait paced by your real step cadence
    const act = vision?.activity || (running ? "running" : vision?.moving ? "walking" : "idle");
    const gaitTarget = act === "running" ? 1 : act === "walking" ? 0.55 : 0;
    this.gait += (gaitTarget - this.gait) * Math.min(1, dt * 3);
    // guard pose only on an explicit "boxing" label: punches alone used to
    // raise it, and the avatar sat in its guard whenever a wrist twitched
    const boxing = act === "boxing";
    this.box += ((boxing ? 1 : 0) - this.box) * Math.min(1, dt * 4);
    const cad = Number(vision?.cadence) > 0.5 ? Number(vision.cadence) : act === "running" ? 2.8 : 1.8;
    this.phase += dt * Math.PI * cad * (this.gait > 0.02 ? 1 : 0);   // 2 steps = 1 cycle
    const g = this.gait, ph = Math.sin(this.phase), pc = Math.cos(this.phase);
    const run = Math.max(0, (g - 0.55) / 0.45);                 // 0 walking .. 1 running
    this._legs(g, ph, pc);
    // Offsets measured on the rig (camera at +z): +x swings an upper arm
    // forward; the elbow folds the forearm up with -y on the left, +y on the
    // right. Guard (GUARD_*): fists by the chin.
    // Punches are IK on top of this (_arms), timed by the Watch / band.
    const b = this.box;
    this._pose("leftUpperArm",  ph * 0.45 * g * (1 - b) + b * GUARD_UP, 0, b * GUARD_IN);
    this._pose("rightUpperArm", -ph * 0.45 * g * (1 - b) + b * GUARD_UP, 0, -b * GUARD_IN);
    this._pose("leftLowerArm",  0, -(1.0 * run * (1 - b) + b * GUARD_FOLD), 0);
    this._pose("rightLowerArm", 0, 1.0 * run * (1 - b) + b * GUARD_FOLD, 0);
    // twist into the punch: measured, +y on the spine or a shoulder takes the
    // avatar's left (+x) shoulder back, so -out drives the punching one forward
    let twist = 0;
    for (const s of ["left", "right"]) {
      const pe = this.punchE[s], p = this.punch[s];
      const out = s === "left" ? 1 : -1;
      const k = p ? (p.kind === "hook" ? 0.34 : p.kind === "uppercut" ? 0.16 : 0.26) * (0.6 + 0.4 * p.strength) : 0;
      twist += -out * k * pe;
      const sh = this.bone(s + "Shoulder"), r0 = this.restShoulder[s];
      if (sh && r0) sh.rotation.set(r0.x, r0.y - out * 0.22 * pe * (p ? 0.6 + 0.4 * p.strength : 0), r0.z);
    }
    this._fists(0.28 + 0.72 * b);                               // relaxed curl at rest, a fist on guard
    if (spine) {
      spine.rotation.y = ph * 0.1 * g + twist + (this.bodyYaw || 0) * 0.12;
      spine.rotation.x += 0.14 * run + 0.08 * b;                // lean in to run or fight
    }
    const hips = this.bone("hips");
    if (hips) {
      hips.rotation.y = -ph * 0.08 * g;
      // standing still: a slow weight shift side to side, the spine leaning
      // back against it, so the idle body isn't frozen
      const still = (1 - g) * (1 - this.sit);
      hips.rotation.z = Math.sin(this.t * 0.42) * 0.025 * still;
      if (spine) spine.rotation.z -= Math.sin(this.t * 0.42) * 0.02 * still;
    }
    this.vrm.scene.position.y = Math.abs(Math.sin(this.t * 4.5)) * talk * 0.006
      + Math.abs(ph) * (0.012 + 0.03 * run) * g;
    if (this.legs) {
      // hips come down until the shins stand on the floor: hip height becomes
      // knee height (shin + ankle) once the thighs are horizontal
      const drop = Math.max(0, this.legs.hipY - (this.legs.shin + this.legs.ankleY));
      this.vrm.scene.position.y -= drop * this.sit;
      if (this.sit > 0.01) {
        // the thighs never sit perfectly level, so measure where the feet
        // landed and lift the body until they're back on the floor
        this.vrm.scene.updateMatrixWorld(true);
        const lf = this.bone("leftFoot"), rf = this.bone("rightFoot");
        if (lf && rf) {
          const y = Math.min(lf.getWorldPosition(this._v[1]).y, rf.getWorldPosition(this._v[2]).y);
          this.vrm.scene.position.y += (this.legs.ankleY - y) * this.sit;
        }
      }
      if (spine) spine.rotation.x -= 0.06 * this.sit;          // lean back a touch
    }
    if (this.seat) {
      this.seat.material.opacity = Math.min(1, this.sit * 1.4);
      this.seat.visible = this.sit > 0.03;
    }
    this._arms(dt, bodyIn);

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
