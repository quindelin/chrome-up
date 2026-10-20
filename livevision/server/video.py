"""Camera / POV video analyzer.

Produces:
  motion energy, face count, person count, brightness
  activity classification (idle / walking / running / boxing / lifting) from the
  *shape* of the motion signal: global scene flow vs central-region flow,
  transient spike rate and cadence.

Accepts a local camera index, a video file, or an RTSP/HTTP stream (that is how
the Meta Ray-Ban Display POV feed reaches this box today: phone camera app ->
RTSP). Falls back to a simulated scene when OpenCV or the source is missing.
"""
from __future__ import annotations

import collections
import random
import threading
import time

import numpy as np

try:
    import cv2
except Exception:  # pragma: no cover - optional dependency
    cv2 = None

from .state import VisionSnapshot

WINDOW_S = 3.0


class VideoAnalyzer:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.enabled = bool(cfg.get("enabled", True)) and cv2 is not None
        self.source = cfg.get("source", 0)
        self.width = int(cfg.get("width", 640))
        self.height = int(cfg.get("height", 360))
        self.fps = float(cfg.get("fps", 15))
        self.use_people = bool(cfg.get("people_detect", True))
        self.use_activity = bool(cfg.get("activity", True))
        self.motion_threshold = float(cfg.get("motion_threshold", 0.35))
        # activity: motion energy that counts as walking / running. A head-worn
        # camera moves with every glance, so these sit well above "something moved"
        self.walk_motion = float(cfg.get("walk_motion", 0.08))
        self.run_motion = float(cfg.get("run_motion", 0.45))
        self.run_center = float(cfg.get("run_center", 0.25))

        self._lock = threading.Lock()
        self._snap = VisionSnapshot(source="sim")
        self._thread = None
        self._sim_thread = None
        self._sim_running = False
        self._running = False
        self._cap = None

        # motion signature buffers (shared by real + simulated paths)
        maxlen = int(max(8, self.fps * WINDOW_S))
        self._t = collections.deque(maxlen=maxlen)
        self._global = collections.deque(maxlen=maxlen)
        self._center = collections.deque(maxlen=maxlen)
        self._last_spike = 0.0

        # face crops for the opt-in attribute module
        self._frame = None
        self._face_rects = []

    # ------------------------------------------------------------------ lifecycle
    def start(self) -> str:
        if not self.enabled:
            self._start_sim()
            return "sim"
        # open in a watchdog thread: RTSP sources can block for a long time
        box: dict = {}
        th = threading.Thread(target=lambda: box.update(cap=self._open()), daemon=True)
        th.start()
        th.join(5.0)
        self._cap = box.get("cap")
        if self._cap is None:
            print(f"[video] cannot open source {self.source!r}; using simulated vision")
            self.enabled = False
            self._start_sim()
            return "sim"
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return str(self.source)

    def stop(self) -> None:
        self._running = False
        self._sim_running = False
        for th in (self._thread, self._sim_thread):
            if th is not None:
                th.join(timeout=2.0)
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass

    # ------------------------------------------------------------------ worker
    def _open(self):
        src = self.source
        if isinstance(src, str) and src.isdigit():
            src = int(src)
        cap = cv2.VideoCapture(src)
        if not cap.isOpened():
            return None
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        cap.set(cv2.CAP_PROP_FPS, self.fps)
        return cap

    def _loop(self):
        if self._cap is None or not self._cap.isOpened():
            return

        face_cascade = None
        try:
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )
        except Exception:
            pass

        hog = None
        if self.use_people:
            try:
                hog = cv2.HOGDescriptor()
                hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
            except Exception:
                hog = None

        prev = None
        prev_center = None
        motion_ema = 0.0
        people = 0
        last_people_t = 0.0
        frame_count = 0
        fps_t = time.time()
        fps = 0.0

        while self._running:
            ok, frame = self._cap.read()
            if not ok or frame is None:
                time.sleep(0.2)
                continue
            small = cv2.resize(frame, (self.width, self.height))
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (7, 7), 0)
            center = gray[self.height // 5: self.height * 4 // 5,
                          self.width // 4: self.width * 3 // 4]

            motion = 0.0
            center_motion = 0.0
            if prev is not None:
                motion = float(np.clip(np.mean(cv2.absdiff(gray, prev)) / 255.0 * 14.0, 0, 1))
                center_motion = float(np.clip(
                    np.mean(cv2.absdiff(center, prev_center)) / 255.0 * 14.0, 0, 1))
            prev, prev_center = gray, center
            motion_ema = motion_ema * 0.7 + motion * 0.3
            brightness = float(np.mean(gray) / 255.0)

            rects = []
            if face_cascade is not None:
                fsmall = cv2.resize(gray, (self.width // 2, self.height // 2))
                found = face_cascade.detectMultiScale(fsmall, scaleFactor=1.2,
                                                      minNeighbors=5, minSize=(24, 24))
                # rects were found on the half-size image
                rects = [(int(x * 2), int(y * 2), int(w * 2), int(h * 2))
                         for (x, y, w, h) in found]
            faces = len(rects)

            now = time.time()
            if hog is not None and now - last_people_t > 0.5:
                last_people_t = now
                try:
                    boxes, _ = hog.detectMultiScale(small, winStride=(8, 8),
                                                    padding=(8, 8), scale=1.05)
                    people = len(boxes)
                except Exception:
                    people = 0
            people = max(people, faces)

            activity, cadence = self._activity(now, motion, center_motion)
            text_rows = self._text_rows(gray)

            frame_count += 1
            if now - fps_t >= 1.0:
                fps = frame_count / (now - fps_t)
                frame_count = 0
                fps_t = now

            with self._lock:
                self._frame = small
                self._face_rects = rects
                self._snap = VisionSnapshot(
                    motion=float(motion_ema),
                    people=int(people or faces),
                    faces=int(faces),
                    brightness=brightness,
                    running=bool(motion_ema > self.motion_threshold),
                    moving=bool(motion_ema > 0.08),
                    fps=round(fps, 1),
                    source=str(self.source),
                    activity=activity,
                    cadence=round(cadence, 2),
                    text_rows=text_rows,
                )
            time.sleep(max(0.0, 1.0 / max(1.0, self.fps) - 0.005))

    # --------------------------------------------------------- text detection
    def _text_rows(self, gray) -> int:
        """Count distinct horizontal text-like rows in the central crop.
        Useful as a fallback 'you are reading' signal when the desktop
        module is not available."""
        try:
            crop = gray[self.height // 5: self.height * 4 // 5,
                        self.width // 4: self.width * 3 // 4]
            edges = cv2.Sobel(crop, cv2.CV_8U, 0, 1, ksize=3)
            row = edges.mean(axis=1)
            m, s = float(row.mean()), float(row.std())
            thr = m + s
            runs, in_run, cur = 0, False, 0
            for v in row:
                if v > thr:
                    if not in_run:
                        in_run = True
                        cur = 0
                    cur += 1
                else:
                    if in_run and cur >= 2:
                        runs += 1
                    in_run = False
            return runs
        except Exception:
            return 0

    # --------------------------------------------------------- motion signature
    def _activity(self, now: float, motion: float, center_motion: float):
        """Classify the wearer's activity from the shape of the motion signal."""
        self._t.append(now)
        self._global.append(motion)
        self._center.append(center_motion)
        if not self.use_activity or len(self._t) < 8:
            return "idle", 0.0

        times = np.array(self._t)
        vals = np.array(self._global)
        span = max(0.5, times[-1] - times[0])
        mean = float(np.mean(vals))
        std = float(np.std(vals))
        center_mean = float(np.mean(self._center))

        # transient spike rate (a punch / rep is a sharp burst)
        thresh = mean + max(0.05, 1.6 * std)
        spikes = 0
        last = 0.0
        for t, v in zip(times, vals):
            if v > thresh and t - last > 0.15:
                spikes += 1
                last = t
        rate = spikes / span

        # cadence from zero crossings of the mean-removed signal
        signed = np.sign(vals - mean)
        crossings = int(np.sum(np.abs(np.diff(signed)) > 0))
        cadence = crossings / (2.0 * span)

        if mean > self.run_motion and center_mean > self.run_center:
            activity = "running"
        elif center_mean > 0.10 and rate >= 1.2 and 1.0 <= cadence <= 6.0:
            activity = "boxing"
        elif center_mean > 0.09 and 0.15 <= cadence <= 1.3 and mean < 0.35:
            activity = "lifting"
        elif mean > self.walk_motion:
            activity = "walking"
        else:
            activity = "idle"
        return activity, cadence

    # ------------------------------------------------------------------ simulated
    def _start_sim(self):
        self._sim_running = True
        self._sim_thread = threading.Thread(target=self._sim_loop, daemon=True)
        self._sim_thread.start()

    def _sim_loop(self):
        motion = 0.05
        mode_t = 0.0
        mode = "idle"
        while self._sim_running:
            now = time.time()
            mode_t -= 0.1
            if mode_t <= 0:
                mode_t = random.uniform(3.0, 7.0)
                mode = random.choice(["idle", "walking", "running", "boxing", "lifting", "crowd"])
            target = {"idle": 0.04, "walking": 0.18, "running": 0.62,
                      "boxing": 0.30, "lifting": 0.22, "crowd": 0.12}[mode]
            motion += (target - motion) * 0.18 + random.uniform(-0.03, 0.03)
            motion = float(np.clip(motion, 0.0, 1.0))
            people = 4 if mode == "crowd" else (1 if random.random() < 0.4 else 0)
            cadence = {"idle": 0.0, "walking": 1.8, "running": 2.8,
                       "boxing": 3.2, "lifting": 0.6, "crowd": 0.5}[mode]
            activity = "walking" if mode == "crowd" else mode
            self._t.append(now)
            self._global.append(motion)
            self._center.append(motion * (1.4 if mode in ("boxing", "lifting") else 0.9))
            with self._lock:
                self._snap = VisionSnapshot(
                    motion=motion,
                    people=people,
                    faces=max(0, people - 1) if people else 0,
                    brightness=0.5,
                    running=motion > self.motion_threshold,
                    moving=motion > 0.08,
                    fps=15.0,
                    source="sim",
                    activity=activity,
                    cadence=cadence,
                    text_rows=0,
                )
            time.sleep(0.1)

    # ------------------------------------------------------------------ access
    def faces_for_attributes(self):
        with self._lock:
            return self._frame, list(self._face_rects)

    def latest_frame(self):
        """Return the most recent BGR frame (downsampled), or None in sim mode."""
        with self._lock:
            return self._frame

    def tick(self, dt: float) -> VisionSnapshot:
        with self._lock:
            return self._snap
