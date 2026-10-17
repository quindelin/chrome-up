/**
 * Avatar theme presets for the procedural canvas vtuber. These are original
 * recolorings of the HUD's built-in anime base — NOT copies of any specific
 * licensed character. If you want a real Kirito / Eren / etc. model, load a
 * CC0 / CC-BY Live2D model into `overlay/assets/live2d/` (see README) or run
 * VTube Studio locally and bring your own licensed model.
 *
 * Naming is intentionally generic ("dark_swordsman", "green_scout") so
 * nobody mistakes this for an asset rip of any particular character.
 */
export const PRESETS = {
  default: {
    label: "Default (purple)",
    skin: "#f7d9c4", skinShade: "#e8bda2",
    hair: "#8f5aa8", hairLight: "#a86fc4",
    eye: "#5fb7e0", eyeDark: "#2b4a6b",
    cloth: "#2b3350", clothLight: "#3c4870",
    line: "#5a4030",
  },
  dark_swordsman: {
    // black-haired, blue-eyed, dark-cloaked protagonist vibe
    label: "Dark Swordsman",
    skin: "#f3d3bd", skinShade: "#e1b39a",
    hair: "#1a1a22", hairLight: "#3a3a48",
    eye: "#3b6fb6", eyeDark: "#1a3559",
    cloth: "#10131c", clothLight: "#262b3a",
    line: "#0c0c12",
  },
  green_scout: {
    // brown-haired, green-eyed, forest-jacketed scout vibe
    label: "Green Scout",
    skin: "#f5d4b3", skinShade: "#dfb190",
    hair: "#6a4a2a", hairLight: "#8c6438",
    eye: "#5e8a3a", eyeDark: "#2f4a18",
    cloth: "#3c4a26", clothLight: "#5b6b3c",
    line: "#3a2a18",
  },
  silver_knight: {
    // silver-haired, red-eyed, white-cloaked antihero vibe
    label: "Silver Knight",
    skin: "#f0d2bc", skinShade: "#dfb39b",
    hair: "#d6d8e0", hairLight: "#f4f5fa",
    eye: "#c0434a", eyeDark: "#5a1a1f",
    cloth: "#dadde6", clothLight: "#eef0f6",
    line: "#2a2a32",
  },
  blonde_prince: {
    label: "Blonde Prince",
    skin: "#f4d2b6", skinShade: "#e0b292",
    hair: "#e9c267", hairLight: "#f8e29a",
    eye: "#3aa37a", eyeDark: "#1a4a30",
    cloth: "#2a3a4a", clothLight: "#3c4f64",
    line: "#4a3a18",
  },
  hacker: {
    // dark terminal aesthetic, neon highlight
    label: "Hacker",
    skin: "#e8c8a8", skinShade: "#cfa880",
    hair: "#0d0d12", hairLight: "#1d1d28",
    eye: "#3affb6", eyeDark: "#0a3a26",
    cloth: "#0f1a18", clothLight: "#1c2c2a",
    line: "#0a0a0a",
  },
};

export const PRESET_KEYS = Object.keys(PRESETS);

export function resolve(name) {
  return PRESETS[name] || PRESETS.default;
}
