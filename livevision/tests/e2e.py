"""End-to-end test of the ffmpeg path.  Run:  python tests/e2e.py

Generates a synthetic 60s 720p clip, feeds it through the pipeline as
`source.mode: file`, then renders a vertical, captioned cut and verifies the
output with ffmpeg. Skipped (exit 0) when ffmpeg is unavailable.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from autoclip.clips import render_clip  # noqa: E402
from autoclip.config import load_config  # noqa: E402
from autoclip.pipeline import Pipeline  # noqa: E402
from autoclip.transcript import Transcript, Word  # noqa: E402
from autoclip.util import require_ffmpeg, run  # noqa: E402

PASS, FAIL = [], []


def check(name: str, fn):
    try:
        fn()
        PASS.append(name)
        print(f"  ok   {name}")
    except Exception as exc:  # noqa: BLE001
        FAIL.append((name, exc))
        print(f"  FAIL {name}: {exc}")


def stream_info(path: Path) -> tuple[int, int, float]:
    proc = subprocess.run([shutil.which("ffmpeg"), "-hide_banner", "-i", str(path)],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    text = proc.stderr.decode("utf-8", "replace")
    import re
    w = h = 0
    m = re.search(r"Stream #\d+:\d+.*Video:.* (\d{2,5})x(\d{2,5})", text)
    if m:
        w, h = int(m.group(1)), int(m.group(2))
    d = 0.0
    md = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", text)
    if md:
        d = int(md.group(1)) * 3600 + int(md.group(2)) * 60 + float(md.group(3))
    return w, h, d


def make_source_video(path: Path, seconds: int = 60) -> None:
    run([shutil.which("ffmpeg"), "-y", "-hide_banner", "-loglevel", "error",
         "-f", "lavfi", "-i", f"testsrc=size=1280x720:rate=30:duration={seconds}",
         "-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}",
         "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-shortest", str(path)], timeout=300)


def main() -> int:
    if shutil.which("ffmpeg") is None:
        print("ffmpeg not found — skipping e2e (brew install ffmpeg)")
        return 0
    require_ffmpeg()

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        video = td / "source.mp4"
        print("generating synthetic source video …")
        make_source_video(video, seconds=60)

        cfg = load_config(ROOT / "autoclip.yaml")
        cfg["workdir"] = str(td / "var")
        cfg["source"]["mode"] = "file"
        cfg["source"]["file"] = str(video)
        cfg["analysis"]["transcribe"] = False
        cfg["publish"]["mode"] = "dry_run"
        cfg["publish"]["platforms"] = ["local"]
        cfg["window"]["seconds"] = 300

        rt = Pipeline(cfg)

        def t_capture():
            win = rt.capture_window()
            assert win.path.exists(), win
            assert win.duration > 50, win.duration
            state["window"] = win

        def t_analyze():
            win = state["window"]
            analysis = rt.analyze(win, with_frames=True)
            assert len(analysis.per_second) > 40, len(analysis.per_second)
            assert analysis.frames, "expected frame stills"
            state["analysis"] = analysis

        def t_frames():
            frames = state["analysis"].frames
            for f in frames[:3]:
                assert Path(f["path"]).exists(), f

        def t_context():
            tr = Transcript(words=[], engine="", note="disabled in test")
            ctx = rt.context(state["window"], state["analysis"], tr)
            brief = ctx.brief()
            assert "moments" in brief and "per_second" in brief

        def t_render():
            from autoclip.agents import ClipDecision

            words = [Word(i * 0.6, i * 0.6 + 0.5, w) for i, w in enumerate(
                "so this is the moment where everything finally happens on stream".split())]
            transcript = Transcript(words=words, text=" ".join(w.text for w in words),
                                    engine="synthetic")
            decision = ClipDecision(start=5.0, end=25.0, score=0.9, title="e2e clip",
                                    caption="captions burned in", hashtags=["e2e"],
                                    platforms=["local"])
            clip = render_clip(state["window"].path, decision, cfg["render"],
                               out_dir=Path(rt.clips_dir), transcript=transcript,
                               name="e2e")
            state["clip"] = clip
            assert clip.path.exists(), clip.path
            assert clip.srt and clip.srt.exists(), "missing srt"
            assert clip.thumb and clip.thumb.exists(), "missing thumbnail"
            w, h, d = stream_info(clip.path)
            assert (w, h) == (1080, 1920), f"expected 1080x1920, got {w}x{h}"
            assert 18.0 <= d <= 22.0, f"expected ~20s clip, got {d}s"
            assert clip.captions_burned, f"captions not burned: {clip.notes}"
            assert "\\kf" in clip.ass.read_text(), "karaoke sweep tags missing"

        def t_render_pop():
            """Word-pop captions must also be accepted by libass."""
            from autoclip.agents import ClipDecision

            render_cfg = dict(cfg["render"])
            render_cfg["caption_style"] = {**render_cfg["caption_style"], "mode": "pop"}
            words = [Word(i * 0.6, i * 0.6 + 0.5, w) for i, w in enumerate(
                "word by word popping captions on this vertical clip".split())]
            transcript = Transcript(words=words, text=" ".join(w.text for w in words),
                                    engine="synthetic")
            decision = ClipDecision(start=5.0, end=25.0, score=0.9, title="pop",
                                    platforms=["local"])
            clip = render_clip(state["window"].path, decision, render_cfg,
                               out_dir=Path(rt.clips_dir), transcript=transcript,
                               name="e2e_pop")
            assert clip.captions_burned, f"pop captions not burned: {clip.notes}"
            w, h, _ = stream_info(clip.path)
            assert (w, h) == (1080, 1920), f"expected 1080x1920, got {w}x{h}"

        def t_publish():
            from autoclip.publishers import publish_all

            results = publish_all(state["clip"], ["local"], cfg["publish"], Path(rt.workdir))
            assert results and results[0].ok, results
            outbox = Path(rt.workdir) / "outbox"
            assert (outbox / "e2e.mp4").exists(), list(outbox.iterdir())

        def t_cycle():
            res = rt.run_cycle(publish=True)
            assert res.id
            print(f"       cycle notes: {res.notes}")
            assert res.window, "cycle produced no window"
            for clip in res.clips:
                d = clip["duration"]
                assert 10.0 <= d <= 30.5, f"clip outside the 10-30s band: {d}s"

        state: dict = {}
        for name, fn in [("capture window", t_capture), ("analyze", t_analyze),
                         ("frame stills", t_frames), ("agent context", t_context),
                         ("render vertical + karaoke captions", t_render),
                         ("render word-pop captions", t_render_pop),
                         ("publish dry-run", t_publish), ("full cycle", t_cycle)]:
            check(name, fn)

    print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
    for name, exc in FAIL:
        print(f"  - {name}: {exc}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
