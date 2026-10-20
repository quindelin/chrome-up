"""Fallback caption renderer: pre-renders animated captions as PNG frames.

Why: a lot of ffmpeg builds (including Homebrew's) ship **without** libass, so
the `subtitles` filter does not exist. This module renders the same animated
captions with Pillow and overlays them as an RGBA image sequence — which only
needs ffmpeg's always-available `overlay` filter.

Output is a directory of PNGs (one per caption frame, ~12 fps) plus the band
geometry, ready to be wired into a filter_complex.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import List, Optional, Tuple

from .util import ensure_dir

try:
    from PIL import Image, ImageDraw, ImageFont  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    Image = ImageDraw = ImageFont = None  # type: ignore


def available() -> bool:
    return Image is not None


# --------------------------------------------------------------------------- colours
def ass_colour_to_rgb(value: str, default: Tuple[int, int, int] = (255, 255, 255)) -> Tuple[int, int, int]:
    """'&H00FFFFFF' (AABBGGRR) or '&H00FFFF&' (BBGGRR) -> (R, G, B)."""
    s = str(value or "").strip().upper().lstrip("&").lstrip("H").rstrip("&")
    try:
        if len(s) >= 8:  # AABBGGRR
            return (int(s[6:8], 16), int(s[4:6], 16), int(s[2:4], 16))
        if len(s) == 6:  # BBGGRR
            return (int(s[4:6], 16), int(s[2:4], 16), int(s[0:2], 16))
    except ValueError:
        pass
    return default


# --------------------------------------------------------------------------- font
_FONT_DIRS = (
    "/System/Library/Fonts/Supplemental",
    "/System/Library/Fonts",
    "/Library/Fonts",
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/truetype/freefont",
    "/usr/share/fonts",
)


def resolve_font(name: str, size: int):
    """Load a TrueType font by name, or the best available default."""
    if ImageFont is None:
        return None
    candidates: List[Path] = []
    p = Path(name).expanduser()
    if p.exists():
        candidates.append(p)
    else:
        for directory in _FONT_DIRS:
            d = Path(directory)
            if not d.exists():
                continue
            for ext in (f"{name}.ttf", f"{name}.ttc", f"{name}.otf",
                        f"{name.title()}.ttf", f"{name}-Bold.ttf", f"{name} Bold.ttf"):
                candidates.append(d / ext)
    for candidate in candidates:
        if candidate.exists():
            try:
                return ImageFont.truetype(str(candidate), size=size)
            except Exception:
                continue
    try:
        return ImageFont.truetype(size=size)  # Pillow >= 10.1 default scalable font
    except Exception:
        try:
            return ImageFont.load_default()
        except Exception:
            return None


# --------------------------------------------------------------------------- states
def caption_states(lines: List[dict], max_gap: float = 0.7) -> List[dict]:
    """Flatten caption lines into timed 'states'.

    A state is one frame of the animation: the words on screen plus which word
    is currently active (spoken). Gaps longer than `max_gap` get no caption.
    """
    states: List[dict] = []
    for line in lines:
        words = line.get("words") or []
        t0 = float(line["t0"])
        t1 = float(line["t1"])
        if t1 - t0 < 0.4:
            t1 = t0 + 0.4
        if not words:
            states.append({"t0": t0, "t1": t1, "words": [{"text": line["text"]}],
                           "active": 0})
            continue
        for i, w in enumerate(words):
            start = max(t0, float(w["t0"]))
            end = float(w["t1"])
            if i + 1 < len(words):
                end = max(end, min(float(words[i + 1]["t0"]), t1))
            end = min(max(end, start + 0.08), max(t1, start + 0.08))
            states.append({"t0": start, "t1": end,
                           "words": [{"text": x["text"]} for x in words],
                           "active": i})
        if t1 > states[-1]["t1"]:
            states[-1]["t1"] = min(t1, states[-1]["t1"] + max_gap)
    states.sort(key=lambda s: s["t0"])
    return states


def state_at(states: List[dict], t: float, max_gap: float = 0.7) -> Optional[int]:
    best = None
    for i, s in enumerate(states):
        if s["t0"] - 0.001 <= t <= s["t1"] + 0.001:
            best = i
        elif t > s["t1"] and best is None and t - s["t1"] <= max_gap and i + 1 < len(states):
            if states[i + 1]["t0"] >= t:
                best = i
    return best


# --------------------------------------------------------------------------- render
def measure_line(font, words: List[str], spacing: int) -> List[int]:
    widths = []
    for w in words:
        box = font.getbbox(w) if hasattr(font, "getbbox") else font.getsize(w)
        widths.append(box[2] - box[0])
    return widths


def render_caption_sequence(states: List[dict], duration: float, out_dir: Path,
                            style: dict, width: int,
                            fps: int = 12) -> dict:
    """Write an RGBA PNG sequence. Returns {frames_dir, pattern, fps, band_height}."""
    if not available():
        raise RuntimeError("Pillow is not installed (pip install Pillow)")

    size = int(style.get("size", 64))
    font = resolve_font(str(style.get("font", "Arial")), size)
    if font is None:
        raise RuntimeError("no usable font for caption rendering")
    active_rgb = ass_colour_to_rgb(style.get("active_inline", "&H00FFFF&"), (255, 255, 0))
    inactive_rgb = ass_colour_to_rgb(style.get("inactive_inline", "&HFFFFFF&"), (255, 255, 255))
    outline_rgb = ass_colour_to_rgb(style.get("outline", "&H00000000"), (0, 0, 0))
    stroke = int(style.get("stroke", 5))
    pad_x, pad_y = int(size * 0.5), int(size * 0.35)
    line_gap = int(size * 0.18)

    # word boxes (measured once; the active word may be scaled up)
    spacing = " "
    gap_w = font.getbbox(spacing)[2] - font.getbbox(spacing)[0] if hasattr(font, "getbbox") else size // 3
    boxes = {}
    for state in states:
        for w in state["words"]:
            if w["text"] not in boxes:
                b = font.getbbox(w["text"]) if hasattr(font, "getbbox") else font.getsize(w["text"])
                boxes[w["text"]] = (b[2] - b[0], b[3] - b[1])

    def layout(words: List[dict]) -> List[List[str]]:
        rows: List[List[str]] = [[]]
        used = 0
        for w in words:
            ww = boxes[w["text"]][0]
            add = ww + (gap_w if rows[-1] else 0)
            if used + add > width - 2 * pad_x and rows[-1]:
                rows.append([w["text"]])
                used = ww
            else:
                rows[-1].append(w["text"])
                used += add
        return rows

    max_rows = 1
    for state in states:
        max_rows = max(max_rows, len(layout(state["words"])))
    line_h = size + line_gap
    band_h = int(max_rows * line_h + 2 * pad_y)

    frames_dir = ensure_dir(out_dir)
    for stale in frames_dir.glob("cap_*.png"):
        try:
            stale.unlink()
        except Exception:
            pass

    cache: dict = {}
    n_frames = max(1, int(round(duration * fps)))
    for idx in range(n_frames):
        t = idx / float(fps)
        si = state_at(states, t)
        if si is None:
            key = "blank"
        else:
            state = states[si]
            key = f"{si}"
        if key not in cache:
            img = Image.new("RGBA", (width, band_h), (0, 0, 0, 0))
            if si is not None:
                draw = ImageDraw.Draw(img)
                state = states[si]
                rows = layout(state["words"])
                total_h = len(rows) * line_h - line_gap
                y = (band_h - total_h) // 2
                flat = 0
                for r, row in enumerate(rows):
                    widths = [boxes[w][0] for w in row]
                    total_w = sum(widths) + gap_w * (len(row) - 1)
                    x = max(pad_x, (width - total_w) // 2)
                    for w in row:
                        is_active = flat == state["active"]
                        colour = active_rgb if is_active else inactive_rgb
                        draw.text((x, y + r * line_h), w, font=font, fill=colour,
                                  stroke_width=stroke, stroke_fill=outline_rgb)
                        x += boxes[w][0] + gap_w
                        flat += 1
            path = frames_dir / f"cap_{key}.png"
            img.save(path, "PNG")
            cache[key] = path
        src = cache[key]
        dst = frames_dir / f"cap_seq_{idx:06d}.png"
        if src != dst:
            shutil.copyfile(src, dst)

    # remove the per-state originals so image2 only sees the sequence
    for key, path in cache.items():
        try:
            path.unlink()
        except Exception:
            pass

    return {"frames_dir": frames_dir, "pattern": str(frames_dir / "cap_seq_%06d.png"),
            "fps": fps, "band_height": band_h, "frames": n_frames}


def needs_ffmpeg_ass(ffmpeg_has_ass: bool, mode: str) -> bool:
    """Choose the burn strategy: ass when available, else pre-rendered images."""
    if mode == "ass":
        return True
    if mode == "images":
        return False
    return ffmpeg_has_ass
