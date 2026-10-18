"""Caption file writers: SRT (sidecar / upload) and ASS (animated burn-in).

Three burn-in styles, set via `render.caption_style.mode`:

  karaoke (default) : the whole line is on screen, and the active word fills in
                      colour as it is spoken (ASS \\kf sweep). Smooth, no flicker.
  pop               : one event per word — the active word highlights and pops
                      in scale, exactly like CapCut / TikTok auto-captions.
  line              : plain static line (no animation).

All three need word-level timestamps; without them we silently fall back to
`line`.
"""
from __future__ import annotations

from pathlib import Path
from typing import List

from .util import ass_time, ensure_dir, srt_time


def _esc(text: str) -> str:
    """Escape ASS-reserved characters inside dialogue text."""
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def write_srt(lines: List[dict], path: Path) -> Path:
    ensure_dir(path.parent)
    out = []
    for i, line in enumerate(lines, start=1):
        out.append(f"{i}\n{srt_time(line['t0'])} --> {srt_time(line['t1'])}\n{line['text']}\n")
    path.write_text("\n".join(out), encoding="utf-8")
    return path


# --------------------------------------------------------------------------- styling
def _style_line(style: dict) -> str:
    size = int(style.get("size", 64))
    font = style.get("font", "Arial")
    primary = style.get("primary", "&H00FFFFFF")        # the "active"/sung colour
    secondary = style.get("secondary", "&H00E8E8E8")    # the not-yet-sung colour
    outline = style.get("outline", "&H00000000")
    back = style.get("back", "&H80000000")
    margin_v = int(style.get("margin_v", 260))
    return (
        f"Style: Cap,{font},{size},{primary},{secondary},{outline},{back},"
        "1,0,0,0,100,100,0,0,1,6,2,2,30,30,"f"{margin_v},1"
    )


def _header(style: dict) -> str:
    playres_x = int(style.get("playres_x", 1080))
    playres_y = int(style.get("playres_y", 1920))
    return (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        f"PlayResX: {playres_x}\n"
        f"PlayResY: {playres_y}\n"
        "WrapStyle: 2\n"
        "ScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"{_style_line(style)}\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )


def _hold(line: dict, min_seconds: float = 0.4) -> tuple[float, float]:
    start = float(line["t0"])
    end = float(line["t1"])
    if end - start < min_seconds:
        end = start + min_seconds
    return start, end


# --------------------------------------------------------------------------- modes
def _event_karaoke(line: dict, style: dict) -> str:
    words = line.get("words") or []
    start, end = _hold(line)
    fade = int(style.get("fade_ms", 90))
    prefix = f"{{\\an2\\fad({fade},{fade})}}"
    if not words:
        return f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Cap,,0,0,0,,{prefix}{_esc(line['text'])}"

    parts = []
    cursor = start
    for i, w in enumerate(words):
        w0 = max(float(w["t0"]), cursor)
        w1 = max(float(w["t1"]), w0 + 0.05)
        cs = max(1, int(round((w1 - max(w0, start)) * 100)))
        text = w["text"]
        if i < len(words) - 1:
            text += " "
        parts.append(f"{{\\kf{cs}}}{_esc(text)}")
        cursor = w1
    # trailing gap: hold the finished line briefly before it disappears
    tail = max(0, end - cursor)
    if tail > 0:
        parts.append(f"{{\\kf{max(1, int(tail * 100))}}}")
    return f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Cap,,0,0,0,,{prefix}{''.join(parts)}"


def _event_pop(line: dict, style: dict) -> List[str]:
    """One dialogue per word: whole line shown, active word highlighted + popped."""
    words = line.get("words") or []
    start, end = _hold(line)
    if not words:
        return [f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Cap,,0,0,0,,"
                f"{{\\an2}}{_esc(line['text'])}"]

    active = style.get("active_inline", "&H00FFFF&")     # BGR: yellow
    inactive = style.get("inactive_inline", "&HFFFFFF&")  # BGR: white
    scale = int(style.get("pop_scale", 118))
    pop_ms = int(style.get("pop_ms", 90))

    events = []
    for i, w in enumerate(words):
        w0 = float(w["t0"])
        w1 = max(float(w["t1"]), w0 + 0.08)
        rendered = []
        for j, other in enumerate(words):
            text = other["text"] + ("" if j == len(words) - 1 else " ")
            colour = active if j == i else inactive
            rendered.append(f"{{\\c{colour}\\b1}}{_esc(text)}" if j == i
                            else f"{{\\c{colour}}}{_esc(text)}")
        body = "".join(rendered)
        transform = (f"{{\\an2\\fscx{scale}\\fscy{scale}\\t(0,{pop_ms},"
                     f"\\fscx100\\fscy100)}}{body}")
        events.append(f"Dialogue: 0,{ass_time(w0)},{ass_time(w1)},Cap,,0,0,0,,{transform}")

    # keep the completed line on screen a beat longer
    if end > words[-1]["t1"]:
        events.append(f"Dialogue: 0,{ass_time(float(words[-1]['t1']))},{ass_time(end)},"
                      f"Cap,,0,0,0,,{{\\an2}}{_esc(line['text'])}")
    return events


def _event_line(line: dict, style: dict) -> str:
    start, end = _hold(line)
    fade = int(style.get("fade_ms", 90))
    return (f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Cap,,0,0,0,,"
            f"{{\\an2\\fad({fade},{fade})}}{_esc(line['text'])}")


def write_ass(lines: List[dict], path: Path, style: dict) -> Path:
    """Animated burn-in captions. Falls back to static lines without word timings."""
    ensure_dir(path.parent)
    mode = str(style.get("mode", "karaoke")).lower()
    has_words = any(line.get("words") for line in lines)
    if not has_words:
        mode = "line"

    events: List[str] = []
    for line in lines:
        text = " ".join(str(line.get("text", "")).split())
        if not text:
            continue
        line = {**line, "text": text}
        if mode == "pop":
            events.extend(_event_pop(line, style))
        elif mode == "karaoke":
            events.append(_event_karaoke(line, style))
        else:
            events.append(_event_line(line, style))

    path.write_text(_header(style) + "\n".join(events) + "\n", encoding="utf-8")
    return path


def write_captions(lines: List[dict], out_dir: Path, style: dict,
                   stem: str = "captions") -> dict:
    """Write both sidecar SRT and burn-in ASS. Returns {'srt': path, 'ass': path}.

    Pass the clip name as `stem`: clips share one directory, and a shared
    captions.srt meant every clip's sidecar was overwritten by the next one.
    """
    out_dir = ensure_dir(out_dir)
    return {
        "srt": write_srt(lines, out_dir / f"{stem}.srt"),
        "ass": write_ass(lines, out_dir / f"{stem}.ass", style),
    }
