"""Clip rendering: cut -> reframe -> privacy blur -> captions -> loudness normalize.

Everything is ffmpeg. Output is a platform-ready MP4 (H.264 + AAC, faststart),
plus a sidecar .srt (for upload APIs) and a thumbnail .jpg.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Tuple

if TYPE_CHECKING:  # pragma: no cover - import cycle is type-only
    from .privacy import PrivacyManager

from . import caption_images
from .agents import ClipDecision
from .captions import write_captions
from .transcript import Transcript, caption_lines, ffmpeg_has_ass
from .util import clamp, ensure_dir, probe, require_ffmpeg, run


@dataclass
class Clip:
    path: Path
    start: float
    end: float
    duration: float
    decision: ClipDecision
    srt: Optional[Path] = None
    ass: Optional[Path] = None
    thumb: Optional[Path] = None
    captions_burned: bool = False
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "path": str(self.path),
            "start": round(self.start, 2),
            "end": round(self.end, 2),
            "duration": round(self.duration, 2),
            "captions_burned": self.captions_burned,
            "srt": str(self.srt) if self.srt else None,
            "ass": str(self.ass) if self.ass else None,
            "thumb": str(self.thumb) if self.thumb else None,
            "notes": self.notes,
            "decision": self.decision.to_dict(),
        }


def _escape_filter_path(path: Path) -> str:
    """ffmpeg filtergraph escaping for a filename argument."""
    s = str(path)
    s = s.replace("\\", "/")
    s = re.sub(r"(?<!\\)'", r"\\'", s)
    s = s.replace(":", r"\:")
    return s


def _even(v: float) -> int:
    return max(2, int(round(v / 2.0)) * 2)


def _box(hud: dict, key: str) -> Tuple[int, int, int, int]:
    x, y, w, h = (int(v) for v in hud[key])
    return x, y, _even(w), _even(h)


def _feather(name: str, w: int, h: int, fx: float, fy: float) -> str:
    """Chain tail that gives a `w`x`h` stream soft edges (alpha ramps over
    `fx` of the width and `fy` of the height), so a crop laid on a different
    blur doesn't show its rectangle. The ramp is drawn at 64x64 and scaled
    up, which keeps geq cheap."""
    ramp = (f"clip(min(X+0.5\\,W-X-0.5)/(W*{fx:g})\\,0\\,1)"
            f"*clip(min(Y+0.5\\,H-Y-0.5)/(H*{fy:g})\\,0\\,1)")
    return (f",format=yuva420p,split[{name}c][{name}m];"
            f"[{name}m]scale=64:64,format=gray,geq=lum=255*{ramp},"
            f"scale={w}:{h}:flags=bilinear[{name}a];[{name}c][{name}a]alphamerge")


def is_program_frame(in_w: int, in_h: int, hud: dict) -> bool:
    """Landscape input with the HUD base's shape: OBS's program, not the raw
    portrait glasses feed (which has no HUD to cut out)."""
    bw, bh = (int(v) for v in hud.get("base", [1920, 1080]))
    if in_w <= 0 or in_h <= 0:
        return False
    return abs(in_w / in_h - bw / bh) < 0.05


def resolve_layout(layout: str, in_w: int, in_h: int, hud: dict) -> str:
    """hud_stack only applies to the program; anything else gets the fallback."""
    if layout != "hud_stack" or is_program_frame(in_w, in_h, hud):
        return layout
    return str(hud.get("fallback", "crop"))


def hud_stack_graph(hud: dict, width: int, height: int) -> Tuple[str, int]:
    """One filtergraph (single in, single out) that cuts the HUD out of a
    program frame and stacks it into `width`x`height`:

        camera             (crop-to-fill everything above the band)
        compass            |
        heart rate         | avatar      (the bottom band)
        Magicka            |

    The whole HUD lives in the band: a compass strip on top would leave black
    corners (it is narrower than a 9:16 frame) and cost camera height. The
    band's backdrop is `band_background`: "blur" (the camera, cover-scaled,
    blurred and dimmed, matching OBS's blurred side bars) or "black".
    Returns (graph, band_height); captions go above the band. The graph is
    comma-chainable, so it drops into -vf, the privacy scan and
    privacy_filter_complex like the plain crop chain does.
    """
    bw, bh = (int(v) for v in hud.get("base", [1920, 1080]))
    kx, ky, kw, kh = _box(hud, "compass")
    cx, cy, cw, ch = _box(hud, "camera")
    ax, ay, aw, ah = _box(hud, "avatar")
    hx, hy, hw, hh = _box(hud, "heartbeat")
    mx, my, mw, mh = _box(hud, "magicka")

    band_h = _even(min(int(hud.get("bottom_height", 560)), height // 3))
    mid_h = height - band_h

    # camera: crop-to-fill the top, focus_y picks which slice survives
    src_h = min(ch, _even(cw * mid_h / width))
    src_w = min(cw, _even(src_h * width / mid_h))
    fy = clamp(float(hud.get("camera_focus_y", 0.5)), 0.0, 1.0)
    cam_x = cx + (cw - src_w) // 2
    cam_y = cy + int((ch - src_h) * fy)

    # bottom band: compass + vitals column on the left, avatar full height right
    pad = 20
    av_h = band_h - 2 * pad
    av_w = _even(av_h * aw / ah)
    vit_w = _even(min(float(hud.get("vitals_width", 600)), width - av_w - 4 * pad))
    gap = _even(int(hud.get("vitals_gap", 24)))
    k_h = _even(vit_w * kh / kw)
    hb_h = _even(vit_w * hh / hw)
    mg_h = _even(vit_w * mh / mw)
    col_h = k_h + gap + hb_h + mg_h
    if col_h > band_h:
        raise ValueError(f"hud_stack: compass + vitals need {col_h}px, band is {band_h}")
    vit_x = max(0, (width - av_w - 2 * pad - vit_w) // 2)
    vit_y = max(0, (band_h - col_h) // 2)
    # the compass is drawn over the camera: darken the camera inside its crop
    # so it reads as HUD, not a stray slice of sharp video
    dim = clamp(float(hud.get("compass_dim", 0.7)), 0.0, 1.0)
    dx0, dx1 = max(kx, cx), min(kx + kw, cx + cw)
    k_dim = (f",drawbox=x={dx0 - kx}:y=0:w={dx1 - dx0}:h={kh}:color=black@{dim:g}:t=fill"
             if dim > 0 and dx1 > dx0 else "")
    av_x = width - av_w - 2 * pad

    # band backdrop: the camera crop cover-scaled small, blurred, scaled back
    # up and dimmed (cheap next to a full-size gblur), or plain black. Both
    # come off the input (no color source) so the graph stays single-in/out.
    if str(hud.get("band_background", "blur")) == "blur":
        sw, sh = _even(width / 8), _even(band_h / 8)
        keep = clamp(float(hud.get("band_brightness", 0.55)), 0.0, 1.0)
        sigma = max(0.5, float(hud.get("band_blur", 4)))
        bg = (f"[hb]crop={cw}:{ch}:{cx}:{cy},"
              f"scale={sw}:{sh}:force_original_aspect_ratio=increase,crop={sw}:{sh},"
              f"gblur=sigma={sigma:g},scale={width}:{band_h}:flags=bicubic,"
              f"lutyuv=y=val*{keep:g}:u=128+(val-128)*0.8:v=128+(val-128)*0.8[hbg];")
        # the crops carry the program's own blur, which won't line up with
        # this one: feather their edges into it
        fk, fh, fm, fa = (_feather("fk", vit_w, k_h, 0.03, 0.2),
                          _feather("fh", vit_w, hb_h, 0.08, 0.15),
                          _feather("fm", vit_w, mg_h, 0.03, 0.15),
                          _feather("fa", av_w, av_h, 0.15, 0.03))
    else:
        bg = f"[hb]scale={width}:{band_h},drawbox=t=fill:color=black[hbg];"
        fk = fh = fm = fa = ""
    hb_y = vit_y + k_h + gap
    graph = (
        f"scale={bw}:{bh},setsar=1,split=6[hk][hc][ha][hh][hm][hb];"
        f"[hc]crop={src_w}:{src_h}:{cam_x}:{cam_y},scale={width}:{mid_h}[hmid];"
        f"{bg}"
        f"[hk]crop={kw}:{kh}:{kx}:{ky}{k_dim},scale={vit_w}:{k_h}{fk}[hkp];"
        f"[hh]crop={hw}:{hh}:{hx}:{hy},scale={vit_w}:{hb_h}{fh}[hhb];"
        f"[hm]crop={mw}:{mh}:{mx}:{my},scale={vit_w}:{mg_h}{fm}[hmg];"
        f"[ha]crop={aw}:{ah}:{ax}:{ay},scale={av_w}:{av_h}{fa}[hav];"
        f"[hbg][hkp]overlay={vit_x}:{vit_y}[hb1];"
        f"[hb1][hhb]overlay={vit_x}:{hb_y}[hb2];"
        f"[hb2][hmg]overlay={vit_x}:{hb_y + hb_h}[hb3];"
        f"[hb3][hav]overlay={av_x}:{pad}[hbot];"
        f"[hmid][hbot]vstack=inputs=2,setsar=1"
    )
    return graph, band_h


def build_video_filter(aspect: str, layout: str, width: int, height: int,
                       crop_x: float, burn_ass: Optional[Path],
                       watermark: str = "", fps: int = 30,
                       hud: Optional[dict] = None) -> Tuple[List[str], List[str]]:
    """(pre, post) filter stages for a render.

    `pre` is everything that moves pixels around (reframe + fps) — it is also
    the chain used to decode frames for face detection, so blur boxes come out
    in the right coordinate space. `post` is everything painted on top
    (watermark, burned captions) and must run *after* the privacy blur so
    subtitles stay sharp.
    """
    parts: List[str] = []
    if aspect == "9:16":
        if layout == "hud_stack":
            parts.append(hud_stack_graph(hud or {}, width, height)[0])
        elif layout == "blur":
            parts.append(
                f"split=2[bg][fg];[bg]scale={width}:{height},"
                f"gblur=sigma=28,crop={width}:{height}[bgb];"
                f"[fg]scale={width}:-2[fgb];[bgb][fgb]overlay=(W-w)/2:(H-h)/2"
            )
        else:
            cx = clamp(crop_x, 0.0, 1.0)
            parts.append(f"scale=-2:{height}")
            parts.append(f"crop={width}:{height}:(in_w-{width})*{cx:.3f}:0")
    elif aspect == "1:1":
        size = min(width, height)
        parts.append(f"scale={size}:{size}:force_original_aspect_ratio=increase")
        parts.append(f"crop={size}:{size}")
    elif aspect == "16:9":
        parts.append(f"scale={width}:{height}:force_original_aspect_ratio=decrease")
        parts.append(f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black")
    # "source" -> no scaling

    parts.append(f"fps={fps}")
    post: List[str] = []
    if watermark and Path(watermark).exists():
        post.append(f"drawtext=textfile={_escape_filter_path(Path(watermark))}:"
                    "x=40:y=40:fontsize=36:fontcolor=white@0.6")
    if burn_ass is not None:
        post.append(f"subtitles={_escape_filter_path(burn_ass)}")
    return parts, post


def privacy_filter_complex(pre: List[str], privacy: str, post: List[str],
                           cap_seq: Optional[dict], fps: int,
                           band_y: int) -> Tuple[str, Optional[str]]:
    """Assemble the filter_complex + final output label for a render.

    Used whenever a render needs more than one stream: privacy blur patches
    (`split` + `overlay`) and/or the pre-rendered caption PNG sequence.
    Returns ("", None) when there is nothing to build.
    """
    segs: List[str] = []
    cur: Optional[str] = None
    if privacy:
        head = f"[0:v]{','.join(pre)}," if pre else "[0:v]"
        segs.append(f"{head}{privacy}[priv]")
        cur = "priv"
    elif pre:
        segs.append(f"[0:v]{','.join(pre)}[geo]")
        cur = "geo"
    if post:
        segs.append(f"[{cur or '0:v'}]{','.join(post)}[post]")
        cur = "post"
    if cap_seq is not None:
        segs.append(f"[1:v]format=rgba,fps={fps}[cap]")
        segs.append(f"[{cur or '0:v'}][cap]overlay=0:{band_y}[vout]")
        return ";".join(segs), "vout"
    if cur is None:
        return "", None
    segs[-1] = segs[-1][: -len(f"[{cur}]")] + "[vout]"
    return ";".join(segs), "vout"


def render_clip(window_path: Path, decision: ClipDecision, render_cfg: dict,
                out_dir: Path, transcript: Optional[Transcript] = None,
                name: Optional[str] = None,
                privacy: Optional["PrivacyManager"] = None) -> Clip:
    """Cut `decision.start`..`decision.end` out of the window file and package it.

    `privacy` (a PrivacyManager) adds face blurring when it is switched on;
    pass None to render untouched.
    """
    require_ffmpeg()
    out_dir = ensure_dir(out_dir)
    name = name or f"clip_{int(decision.start)}_{int(decision.end)}"
    info = probe(window_path)
    total = float(info.get("duration") or 0.0)
    start = clamp(decision.start, 0.0, max(0.0, total - 1.0))
    end = clamp(decision.end, start + 1.0, total if total > 0 else start + 60.0)
    duration = max(1.0, end - start)

    notes: List[str] = []
    srt_path: Optional[Path] = None
    ass_path: Optional[Path] = None
    lines: List[dict] = []
    style: dict = {}

    width = int(render_cfg.get("width", 1080))
    height = int(render_cfg.get("height", 1920))
    fps = int(float(render_cfg.get("fps", 30)) or 30)
    aspect = str(render_cfg.get("aspect", "9:16"))
    hud = dict(render_cfg.get("hud_stack") or {})
    layout = str(render_cfg.get("layout", "crop"))
    if layout == "hud_stack":
        layout = resolve_layout(layout, int(info.get("width") or 0),
                                int(info.get("height") or 0), hud)
        if layout != "hud_stack":
            notes.append(f"hud_stack: input {info.get('width')}x{info.get('height')} "
                         f"is not the program feed, rendered with layout {layout}")
    band_h = 0
    if aspect == "9:16" and layout == "hud_stack":
        band_h = hud_stack_graph(hud, width, height)[1]

    if render_cfg.get("captions", True) and transcript is not None and transcript.ok:
        style = dict(render_cfg.get("caption_style", {}))
        style.setdefault("playres_x", width)
        style.setdefault("playres_y", height)
        if band_h:
            # bottom of the camera, clear of the vitals + avatar band
            style["margin_v"] = band_h + int(hud.get("caption_gap", 40))
        lines = caption_lines(
            transcript.slice(start, end),
            max_words=int(style.get("max_words", 3)),
            max_chars=int(style.get("max_chars", 28)),
        )
        if lines:
            written = write_captions(lines, out_dir, style, stem=name)
            srt_path, ass_path = written["srt"], written["ass"]
        else:
            notes.append("no caption lines produced")
    elif render_cfg.get("captions", True):
        notes.append("captions requested but no transcript available")

    # ---- how do we get the captions onto the picture? -----------------------
    # 1) libass `subtitles` filter (best quality) when this ffmpeg has it
    # 2) pre-rendered RGBA PNG sequence + `overlay` (works on every build)
    # 3) give up, but keep the .srt sidecar
    burn_mode = str(style.get("burn", "auto")).lower()
    has_ass = ffmpeg_has_ass()
    use_ass = ass_path is not None and burn_mode != "images" and (has_ass or burn_mode == "ass")

    cap_seq = None
    if ass_path is not None and not use_ass:
        if caption_images.available():
            try:
                states = caption_images.caption_states(lines)
                cap_seq = caption_images.render_caption_sequence(
                    states, duration, out_dir / f"{name}_caps", style,
                    width=width, fps=int(style.get("caption_fps", 12)))
                notes.append("captions burned via pre-rendered PNG overlay "
                             "(this ffmpeg has no libass)")
            except Exception as exc:  # noqa: BLE001
                notes.append(f"PNG caption overlay failed: {exc}")
        else:
            notes.append("ffmpeg lacks libass and Pillow is missing "
                         "(pip install Pillow); srt sidecar kept")

    pre_parts, post_parts = build_video_filter(
        aspect=aspect,
        layout=layout,
        width=width,
        height=height,
        fps=fps,
        crop_x=float(render_cfg.get("crop_x", 0.5)),
        burn_ass=ass_path if use_ass else None,
        watermark=str(render_cfg.get("watermark", "")),
        hud=hud,
    )
    af_parts = ["loudnorm=I=-16:TP=-1.5:LRA=11"] if render_cfg.get("loudnorm", True) else []

    # ---- privacy blur ------------------------------------------------------
    # Detected on frames decoded *through* the reframe chain, so the boxes are
    # already in output pixels and can be handed straight to the filtergraph.
    privacy_frag = ""
    if privacy is not None and privacy.clips_blurred:
        try:
            privacy_frag = privacy.clip_chain(
                window_path, start, end,
                pre_chain=",".join(pre_parts), width=width, height=height)
        except Exception as exc:  # noqa: BLE001
            notes.append(f"privacy blur skipped: {exc}")
        if privacy_frag:
            notes.append(f"privacy blur: {len(privacy.last_scan)} face patch(es)")
        else:
            notes.append("privacy blur: no faces found")

    out_path = out_dir / f"{name}.mp4"
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           "-ss", f"{start:.3f}", "-i", str(window_path)]

    if privacy_frag or cap_seq is not None:
        band_y = 0
        if cap_seq is not None:
            cmd += ["-framerate", str(cap_seq["fps"]), "-i", cap_seq["pattern"]]
            band_y = max(0, height - int(cap_seq["band_height"])
                         - int(style.get("margin_v", 260)))
        fc, out_label = privacy_filter_complex(pre_parts, privacy_frag, post_parts,
                                               cap_seq, fps, band_y)
        if fc and out_label:
            cmd += ["-filter_complex", fc, "-map", f"[{out_label}]"]
        cmd += ["-map", "0:a?"]
    else:
        vf_parts = pre_parts + post_parts
        if vf_parts:
            cmd += ["-vf", ",".join(vf_parts)]
    if af_parts:
        cmd += ["-af", ",".join(af_parts)]
    cmd += ["-t", f"{duration:.3f}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-maxrate", str(render_cfg.get("video_bitrate", "8M")),
            "-bufsize", str(int(re.sub(r"[^0-9]", "", str(render_cfg.get("video_bitrate", "8"))) or 8) * 2) + "M",
            "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.1",
            "-c:a", "aac", "-b:a", str(render_cfg.get("audio_bitrate", "160k")),
            "-ar", "48000", "-movflags", "+faststart", str(out_path)]
    run(cmd, timeout=1800)

    thumb = out_dir / f"{name}.jpg"
    run(["ffmpeg", "-y", "-v", "error", "-ss", "1.0", "-i", str(out_path),
         "-frames:v", "1", "-q:v", "3", str(thumb)], timeout=120, check=False)
    if not thumb.exists():
        thumb = None

    return Clip(path=out_path, start=start, end=end, duration=duration,
                decision=decision, srt=srt_path, ass=ass_path, thumb=thumb,
                captions_burned=use_ass or cap_seq is not None, notes=notes)
