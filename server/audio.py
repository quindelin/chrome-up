"""Microphone analyzer: loudness, spectrum bars, speech gate and visemes.

Falls back to a synthetic talker when `sounddevice`/portaudio is unavailable so
the overlay can always be developed and demoed.
"""
from __future__ import annotations

import collections
import math
import random
import shutil
import subprocess
import threading
import time

import numpy as np

try:
    import sounddevice as sd
except Exception:  # pragma: no cover - optional dependency
    sd = None

from .state import AudioSnapshot

BLOCK = 1024


class AudioAnalyzer:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.rate = int(cfg.get("sample_rate", 16000))
        self.gain = float(cfg.get("gain", 1.8))
        self.gate = float(cfg.get("gate", 0.015))
        self.bars = int(cfg.get("bars", 12))
        # Hold the analysis back this long before it moves the mouth: on the
        # VPS the HUD hears the glasses feed almost live, while OBS's media
        # source buffers the same feed before viewers hear it, so without a
        # delay the avatar's lips run ahead of the voice.
        self.delay = max(0.0, float(cfg.get("delay_ms", 0) or 0) / 1000.0)
        self._pending = collections.deque()   # (due time, rms, bands, centroid)
        self.device = cfg.get("device")
        # url: pull audio from a stream (the glasses feed in MediaMTX) through
        # ffmpeg instead of a local mic - how the HUD hears you on the VPS
        self.url = cfg.get("url") or None
        self.enabled = bool(cfg.get("enabled", True)) and (
            sd is not None or bool(self.url and shutil.which("ffmpeg")))
        self._proc = None
        self._stopping = False

        self._lock = threading.Lock()
        self._level = 0.0
        self._bands = np.zeros(self.bars, dtype=float)
        self._centroid = 600.0
        self._last_voice = 0.0
        self._last_level = 0.0
        self._onset = False
        self._history = collections.deque(maxlen=60)  # ~3s at 20Hz
        self._stream = None
        self._window = np.hanning(BLOCK)
        freqs = np.fft.rfftfreq(BLOCK, 1.0 / self.rate)
        self._edges = np.geomspace(80, min(7000, self.rate / 2 - 100), self.bars + 1)
        self._band_idx = [np.where((freqs >= self._edges[i]) & (freqs < self._edges[i + 1]))[0]
                          for i in range(self.bars)]
        self._freqs = freqs

        # sim talker state
        self._sim_phase = 0.0
        self._sim_talk = 0.0
        self._sim_talking = False

    # ------------------------------------------------------------------ lifecycle
    def start(self) -> str:
        """Open the mic in a watchdog thread: macOS can block forever waiting on
        the microphone permission prompt, and that must not stall the server."""
        if not self.enabled:
            return "sim"
        if self.url:
            threading.Thread(target=self._stream_loop, daemon=True).start()
            return "stream"
        box: dict = {}

        def _open():
            try:
                st = sd.InputStream(
                    device=self.device,
                    samplerate=self.rate,
                    blocksize=BLOCK,
                    channels=1,
                    dtype="float32",
                    callback=self._callback,
                )
                st.start()
                box["stream"] = st
            except Exception as exc:
                box["error"] = exc

        th = threading.Thread(target=_open, daemon=True)
        th.start()
        th.join(4.0)
        if "stream" in box:
            self._stream = box["stream"]
            return "mic"
        reason = box.get("error", "timeout (grant microphone access and restart)")
        print(f"[audio] mic unavailable ({reason}); using simulated audio")
        self.enabled = False
        return "sim"

    def stop(self) -> None:
        self._stopping = True
        if self._proc is not None:
            try:
                self._proc.kill()
            except Exception:
                pass
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    # ------------------------------------------------------------------ stream audio
    def _stream_loop(self) -> None:
        """ffmpeg -> 16-bit mono PCM -> the same analysis as the mic. Restarts
        while nobody is publishing (MediaMTX refuses the read until then)."""
        cmd = ["ffmpeg", "-nostdin", "-loglevel", "error",
               "-fflags", "nobuffer", "-flags", "low_delay",
               "-probesize", "32768", "-analyzeduration", "0",
               "-i", self.url, "-vn", "-ac", "1", "-ar", str(self.rate),
               "-f", "s16le", "-"]
        need = BLOCK * 2
        while not self._stopping:
            try:
                self._proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                out = self._proc.stdout
                while not self._stopping:
                    buf = out.read(need)
                    if not buf or len(buf) < need:
                        break
                    frame = np.frombuffer(buf, dtype="<i2").astype(np.float32) / 32768.0
                    self._callback(frame[:, None], BLOCK, None, None)
            except Exception as exc:  # pragma: no cover - network / ffmpeg failures
                print(f"[audio] stream read failed: {exc}")
            finally:
                if self._proc is not None:
                    try:
                        self._proc.kill()
                    except Exception:
                        pass
            if not self._stopping:
                time.sleep(2.0)

    # ------------------------------------------------------------------ real audio
    def _callback(self, indata, frames, time_info, status):
        frame = np.asarray(indata[:, 0], dtype=np.float32)
        rms = float(np.sqrt(np.mean(frame * frame) + 1e-12)) * self.gain

        spec = np.abs(np.fft.rfft(frame * self._window)) / BLOCK
        db = 20.0 * np.log10(spec + 1e-9)
        norm = np.clip((db + 72.0) / 60.0, 0.0, 1.0)
        band_vals = np.array([float(np.mean(norm[idx])) if idx.size else 0.0
                              for idx in self._band_idx], dtype=float)

        mag = spec + 1e-9
        centroid = float(np.sum(self._freqs * mag) / np.sum(mag)) if np.sum(mag) > 0 else 600.0

        if self.delay > 0:
            with self._lock:
                self._pending.append((time.time() + self.delay, rms, band_vals, centroid))
            return
        self._apply(rms, band_vals, centroid)

    def _apply(self, rms: float, band_vals, centroid: float) -> None:
        with self._lock:
            # fast attack / slow release so the ring and mouth feel musical
            self._level = max(rms, self._level * 0.86)
            self._bands = np.maximum(band_vals, self._bands * 0.80)
            self._centroid = self._centroid * 0.8 + centroid * 0.2
            if rms > 0.7 and (rms - self._last_level) > 0.25:
                self._onset = True
            self._last_level = rms
            if rms > self.gate:
                self._last_voice = time.time()

    # ------------------------------------------------------------------ tick
    def tick(self, dt: float) -> AudioSnapshot:
        if not self.enabled:
            self._sim_tick(dt)
        now = time.time()
        while True:
            with self._lock:
                if not self._pending or self._pending[0][0] > now:
                    break
                _, rms, band_vals, centroid = self._pending.popleft()
            self._apply(rms, band_vals, centroid)
        with self._lock:
            level = float(self._level)
            bands = [float(b) for b in self._bands]
            centroid = float(self._centroid)
            onset = bool(self._onset)
            self._onset = False
        speaking = (time.time() - self._last_voice) < 0.28 if self.enabled else level > self.gate
        self._history.append(1.0 if speaking else 0.0)
        talk_ratio = sum(self._history) / max(1, len(self._history))

        openness = float(np.clip(level * 2.6, 0.0, 1.0))
        width = float(np.clip((centroid - 300.0) / 2200.0, 0.0, 1.0))
        return AudioSnapshot(
            level=float(np.clip(level * 3.0, 0.0, 1.0)),
            speaking=bool(speaking),
            talk_ratio=talk_ratio,
            bands=bands,
            viseme=_viseme(openness, centroid),
            openness=openness,
            width=width,
            onset=onset,
            source=("stream" if self.url else "mic") if self.enabled else "sim",
        )

    # ------------------------------------------------------------------ simulated
    def _sim_tick(self, dt: float) -> None:
        """Synthetic speech: bursts of syllables separated by pauses."""
        self._sim_talk -= dt
        if self._sim_talk <= 0:
            self._sim_talk = random.choice([0.8, 1.4, 2.2, 3.0, 4.5]) if random.random() < 0.6 else 0.4
            self._sim_talking = not self._sim_talking
        talking = self._sim_talking
        self._sim_phase += dt * (5.5 if talking else 0.6)
        env = (0.5 + 0.5 * math.sin(self._sim_phase)) ** 2 if talking else 0.0
        level = env * random.uniform(0.25, 0.6)
        bands = [float(np.clip(level * (1.0 - i / (self.bars * 1.4)) * random.uniform(0.6, 1.2), 0, 1))
                 for i in range(self.bars)]
        with self._lock:
            self._level = max(level, self._level * 0.88)
            self._bands = np.maximum(np.array(bands), self._bands * 0.82)
            self._centroid = 500 + 900 * level
            if level > self.gate:
                self._last_voice = time.time()


def _viseme(openness: float, centroid: float) -> str:
    """Map loudness + spectral centroid onto a small mouth-shape set."""
    if openness < 0.06:
        return "closed"
    if openness > 0.62:
        return "O" if centroid < 700 else "A"
    if openness > 0.30:
        return "U" if centroid < 900 else "E"
    return "I" if centroid > 1300 else "e"
