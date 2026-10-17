/**
 * Optional Live2D model loader for the overlay's avatar panel.
 *
 * Set `avatar.engine: live2d` in config.yaml and drop a CC0 / CC-BY Live2D
 * model into `overlay/assets/live2d/` with a `manifest.json` like:
 *
 *   {
 *     "name": "my-anime-base",
 *     "moc3": "model.moc3",
 *     "textures": ["texture_00.png"],
 *     "sdk": "live2dcubismcore.min.js",
 *     "scale": 0.18,
 *     "offset": [0, 0]
 *   }
 *
 * The Live2D Cubism Core JS runtime (`live2dcubismcore.min.js`) is ~1 MB of
 * third-party code that we deliberately do NOT vendor — download it from
 * https://www.live2d.com/en/sdk/download/web/ and place it next to the
 * model. If it isn't present, we fall back to the procedural avatar so the
 * HUD never breaks.
 *
 * Licensing note: bring your own model. We ship none.
 */
export async function tryLoadLive2D(canvas, cfg) {
  const av = cfg?.avatar || {};
  if (av.engine !== "live2d") return null;
  try {
    const res = await fetch("assets/live2d/manifest.json");
    if (!res.ok) {
      console.warn("[hudstream] no manifest at overlay/assets/live2d/manifest.json");
      return null;
    }
    const man = await res.json();
    if (!window.Live2DCubismCore) {
      // Try to inject the SDK from the manifest path
      const sdk = man.sdk || "live2dcubismcore.min.js";
      const base = `assets/live2d/${sdk}`.replace(/\/+/g, "/");
      const ok = await new Promise((resolve) => {
        const s = document.createElement("script");
        s.src = base;
        s.onload = () => resolve(true);
        s.onerror = () => resolve(false);
        document.head.appendChild(s);
      });
      if (!ok || !window.Live2DCubismCore) {
        console.warn("[hudstream] Live2D Cubism Core SDK missing — falling back to procedural avatar");
        return null;
      }
    }
    const core = window.Live2DCubismCore;
    // Load .moc3 binary
    const moc = await _loadArrayBuffer(`assets/live2d/${man.moc3}`);
    const model = core.Moc.fromArrayBuffer(moc);
    if (!model) {
      console.warn("[hudstream] failed to parse .moc3");
      return null;
    }
    const textures = [];
    for (const t of man.textures || []) {
      textures.push(await _loadImage(`assets/live2d/${t}`));
    }
    return {
      kind: "live2d",
      name: man.name || "model",
      model,
      textures,
      manifest: man,
      canvas,
      ctx: canvas.getContext("2d"),
      scale: man.scale || 0.18,
      offset: man.offset || [0, 0],
    };
  } catch (e) {
    console.warn("[hudstream] Live2D load failed:", e);
    return null;
  }
}

function _loadArrayBuffer(url) {
  return fetch(url).then((r) => {
    if (!r.ok) throw new Error(`${url} -> ${r.status}`);
    return r.arrayBuffer();
  });
}

function _loadImage(url) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error(`texture ${url} failed`));
    img.src = url;
  });
}

/** Minimal draw path: renders flat textures unless a full Live2D renderer
 *  is present. Enough to confirm the model loaded; a real rig needs the
 *  Cubism Framework too. */
export function drawLive2D(handle, audio) {
  const { ctx, textures, canvas, scale, offset } = handle;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const openness = audio?.openness ?? 0;
  for (const img of textures) {
    const w = img.width * scale;
    const h = img.height * scale;
    ctx.drawImage(img, offset[0], offset[1], w, h);
  }
  // Simple mic-driven mouth overlay so even the flat fallback lip-syncs
  ctx.save();
  ctx.fillStyle = "#7c3444";
  ctx.globalAlpha = 0.85;
  const mw = 16 + (audio?.width ?? 0.5) * 10;
  const mh = 2 + openness * 18;
  ctx.beginPath();
  ctx.ellipse(canvas.width / 2, canvas.height * 0.62, mw, mh, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}
