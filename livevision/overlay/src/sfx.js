/* UI sounds for the HUD.

   The real Skyrim cues (sound descriptors UILevelUpSD and UISkillIncreaseSD)
   are Bethesda's audio, so they are not in this repo. Extract them from your
   own copy of the game and drop them in overlay/assets/sfx/ as
       levelup.(wav|ogg|mp3)     skillup.(wav|ogg|mp3)     discover.(wav|ogg|mp3)
   (see overlay/assets/sfx/README.md). That folder is gitignored.

   Whatever is missing falls back to a synthesized stand-in so the HUD is
   never silent. In OBS tick "Control audio via OBS" on the browser source to
   mix these into the stream. */

const BASE = new URL("../assets/sfx/", import.meta.url);
const EXTS = ["wav", "ogg", "mp3"];
const VOLUME = { levelup: 0.9, skillup: 0.7, discover: 0.8 };

const clips = {};
let ctx = null;

function audioCtx() {
  if (!ctx) {
    const Ctx = window.AudioContext || window.webkitAudioContext;
    if (!Ctx) return null;
    ctx = new Ctx();
  }
  if (ctx.state === "suspended") ctx.resume().catch(() => {});
  return ctx;
}

async function probe(name) {
  for (const ext of EXTS) {
    const url = new URL(`${name}.${ext}`, BASE).href;
    try {
      const res = await fetch(url, { method: "HEAD" });
      if (res.ok) return url;
    } catch (_) { /* try the next extension */ }
  }
  return null;
}

/** Look for the user-supplied files once at start-up. */
export async function loadSfx() {
  await Promise.all(Object.keys(VOLUME).map(async (name) => {
    const url = await probe(name);
    if (!url) return;
    const a = new Audio(url);
    a.preload = "auto";
    a.volume = VOLUME[name];
    clips[name] = a;
  }));
  const found = Object.keys(clips);
  console.log(`[hudstream] sfx: ${found.length ? found.join(", ") : "none found, using synth"}`);
}

export function play(name) {
  const clip = clips[name];
  if (clip) {
    clip.currentTime = 0;
    clip.play().catch(() => synth(name));
    return;
  }
  synth(name);
}

/* ---- synthesized stand-ins: a low drum hit under a slow minor-key swell */
function synth(name) {
  const ac = audioCtx();
  if (!ac) return;
  const t = ac.currentTime + 0.02;
  const out = ac.createGain();
  out.gain.value = VOLUME[name] ?? 0.7;
  out.connect(ac.destination);

  if (name === "levelup") {
    drum(ac, out, t, 55, 1.6);
    swell(ac, out, t + 0.05, [146.83, 220.0, 293.66, 349.23], 3.2, 0.10);   // D minor, open
    swell(ac, out, t + 0.9, [196.0, 293.66, 392.0], 2.6, 0.07);
  } else if (name === "skillup") {
    drum(ac, out, t, 70, 0.9);
    swell(ac, out, t + 0.03, [220.0, 329.63, 440.0], 1.8, 0.07);
  } else {
    drum(ac, out, t, 48, 2.0);
    swell(ac, out, t + 0.1, [110.0, 164.81, 220.0, 261.63], 3.8, 0.09);
  }
}

function drum(ac, out, t, freq, dur) {
  const o = ac.createOscillator();
  const g = ac.createGain();
  o.type = "sine";
  o.frequency.setValueAtTime(freq * 2.2, t);
  o.frequency.exponentialRampToValueAtTime(freq, t + 0.12);
  g.gain.setValueAtTime(0.0001, t);
  g.gain.exponentialRampToValueAtTime(0.9, t + 0.01);
  g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
  o.connect(g).connect(out);
  o.start(t);
  o.stop(t + dur + 0.05);
}

function swell(ac, out, t, freqs, dur, level) {
  const lp = ac.createBiquadFilter();
  lp.type = "lowpass";
  lp.frequency.setValueAtTime(600, t);
  lp.frequency.linearRampToValueAtTime(2400, t + dur * 0.4);
  lp.connect(out);
  for (const f of freqs) {
    for (const detune of [-6, 6]) {          // two voices per note: a soft choir
      const o = ac.createOscillator();
      const g = ac.createGain();
      o.type = "sawtooth";
      o.frequency.value = f;
      o.detune.value = detune;
      g.gain.setValueAtTime(0.0001, t);
      g.gain.linearRampToValueAtTime(level, t + dur * 0.35);
      g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
      o.connect(g).connect(lp);
      o.start(t);
      o.stop(t + dur + 0.05);
    }
  }
}
