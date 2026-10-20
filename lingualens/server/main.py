"""LinguaLens server: curriculum engine + pronunciation gate + glasses UI.

One server, one language at a time (`language: zh | ja` in the config), but the
same routes, the same gate and the same glasses UI for both.
"""
from __future__ import annotations

import argparse
import json
import os
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import uvicorn
from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import asr, fluency, progress
from .access import AccessKey
from .config import load_config, resolve_provider
from .course import LANG_NAMES, meta_get, native_label, normalize, supported


def course_meta_ui(lang: str) -> dict:
    """The step labels a course's meta.py declares (empty: the page's own)."""
    ui = meta_get(lang, "UI", {}) or {}
    return {k: ui[k] for k in ("read", "literacy", "hearing", "writing") if k in ui}
from .courses import CourseNotReady, Registry
from .curriculum import Course
from .engine import Session
from .models import Score
from . import placement
from .pronunciation import coverage_of, read_wav, score_attempt, simulated_score
from .think import translate

WEB_DIR = Path(__file__).parent / "web"


class ProgressStore:
    """One JSON file holds every client's progress for every course.

    The shape is in `server/progress.py`; old single-course documents are
    migrated in place the first time they are read.
    """

    def __init__(self, path: str):
        self.path = Path(path)
        self.lock = threading.Lock()
        self.data: Dict[str, dict] = {}
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                self.data = {}

    def learner(self, client_id: str, default_lang: str) -> "progress.Learner":
        with self.lock:
            entry = self.data.get(client_id)
            if not isinstance(entry, dict):
                entry = {}
                self.data[client_id] = entry
            learner = progress.Learner(entry, default_lang)
            migrated = learner.migrated
        if migrated:
            self.save()  # a legacy document is rewritten once, on sight
        return learner

    def save(self) -> None:
        with self.lock:
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(self.path)


class App:
    """Courses, sessions and per-course progress for everybody connected."""

    def __init__(self, cfg: Dict):
        self.cfg = cfg
        self.registry = Registry(cfg)
        self.store = ProgressStore(cfg["storage"]["path"])
        self.sessions: Dict[Tuple[str, str], Session] = {}  # (client, lang) -> Session
        # a placement test while it runs; the verdict itself goes into progress
        self.placements: Dict[Tuple[str, str], object] = {}
        self.sockets: Dict[str, List[WebSocket]] = {}
        self.default_lang = self.registry.default_lang()
        try:
            boot_cfg = self.registry.config_for(self.default_lang)
            self.provider = resolve_provider(boot_cfg)
            self.asr_provider = asr.resolve(boot_cfg)
        except CourseNotReady:
            self.provider = "mock"
            self.asr_provider = "mock"

    # -- sessions -----------------------------------------------------------
    def session_for(self, client_id: str, lang: Optional[str] = None) -> Session:
        """The session for one learner on one course, created on demand."""
        learner = self.store.learner(client_id, self.default_lang)
        lang = normalize(lang) if lang else normalize(learner.active)
        course = self.registry.get(lang)  # raises CourseNotReady when unavailable
        key = (client_id, lang)
        sess = self.sessions.get(key)
        if sess is None:
            sess = Session(course, self.registry.config_for(lang), learner.course(lang))
            self.sessions[key] = sess
        learner.set_active(lang)
        return sess

    def provider_for(self, lang: str) -> str:
        try:
            return resolve_provider(self.registry.config_for(lang))
        except CourseNotReady:
            return "mock"

    def asr_for(self, lang: str) -> str:
        try:
            return asr.resolve(self.registry.config_for(lang))
        except CourseNotReady:
            return "mock"

    def _review_due(self, lang: str, course_progress: Dict) -> int:
        """How many lines are due. A throwaway session: no state is kept."""
        try:
            sess = Session(
                self.registry.get(lang), self.registry.config_for(lang), course_progress
            )
        except CourseNotReady:
            return 0
        return sess.review_queue_size()

    def _course_row(self, desc: Dict, learner: "progress.Learner") -> Dict:
        """One course + this learner's numbers on it, for the switcher."""
        lang = desc["id"]
        cp = learner.course(lang) if learner.has(lang) else None
        row = dict(desc)
        row["active"] = lang == learner.active
        row["lessons_done"] = len(cp.get("completed") or []) if cp else 0
        row["words_learned"] = sum(
            1
            for w in (cp or {}).get("words", {}).values()
            if isinstance(w, dict) and (w.get("kind") or "") == "word"
        )
        stats = (cp or {}).get("stats") or {}
        row["minutes"] = round(float(stats.get("seconds") or 0.0) / 60.0, 1)
        row["streak_days"] = progress.streak_days(cp) if cp else 0
        row["review_due"] = self._review_due(lang, cp) if cp else 0
        return row

    def course_rows(self, client_id: str) -> List[Dict]:
        learner = self.store.learner(client_id, self.default_lang)
        return [self._course_row(c, learner) for c in self.registry.all()]

    # -- state --------------------------------------------------------------
    def state(self, client_id: str, lang: Optional[str] = None) -> dict:
        learner = self.store.learner(client_id, self.default_lang)
        target = normalize(lang) if lang else normalize(learner.active)
        try:
            sess = self.session_for(client_id, target)
        except CourseNotReady:
            return self._unready_state(client_id, learner.active, learner)
        payload = sess.state()
        payload["client_id"] = client_id
        payload["active"] = target
        payload["language"] = target
        payload["language_name"] = LANG_NAMES.get(target, target)
        payload["native"] = native_label(target)
        payload["speech_lang"] = sess.course.speech_lang
        payload["provider"] = self.provider_for(target)
        payload["azure_ready"] = payload["provider"] == "azure"
        payload["asr"] = self.asr_for(target)
        payload["courses"] = self.course_rows(client_id)
        payload["config"] = {
            "display_size": sess.cfg["ui"].get("display_size", 600),
            "show_english_default": bool(sess.cfg["ui"].get("show_english_default", False)),
            "vocab_label": sess.cfg["ui"].get("vocab_label", "Vocabulary"),
            # step labels for the page (read / characters / listen / summary),
            # from the course's meta.py UI block when it has one
            "step_labels": course_meta_ui(sess.lang),
            # listening: several voices, at something nearer natural speed
            "listening_rate": (sess.cfg.get("listening") or {}).get("rate") or {},
            "listening_vary_pitch": bool(
                (sess.cfg.get("listening") or {}).get("vary_pitch", True)
            ),
            "listening_rotate_voices": bool(
                (sess.cfg.get("listening") or {}).get("rotate_voices", True)
            ),
        }
        return payload

    def _unready_state(self, client_id: str, lang: str, learner) -> dict:
        return {
            "client_id": client_id,
            "active": lang,
            "language": lang,
            "language_name": LANG_NAMES.get(lang, lang),
            "native": native_label(lang),
            "speech_lang": None,
            "provider": "mock",
            "azure_ready": False,
            "asr": "mock",
            "courses": self.course_rows(client_id),
            "step": None,
            "position": {"index": 0, "total": 0},
            "message": "Course not ready yet.",
        }

    def persist(self, client_id: str) -> None:
        self.store.save()

    # -- websockets ---------------------------------------------------------
    async def register(self, client_id: str, ws: WebSocket) -> None:
        self.sockets.setdefault(client_id, []).append(ws)

    async def unregister(self, client_id: str, ws: WebSocket) -> None:
        conns = self.sockets.get(client_id, [])
        if ws in conns:
            conns.remove(ws)

    async def broadcast(self, client_id: str, lang: Optional[str] = None) -> None:
        try:
            payload = json.dumps(self.state(client_id, lang), ensure_ascii=False)
        except Exception:
            return
        for ws in list(self.sockets.get(client_id, [])):
            try:
                await ws.send_text(payload)
            except Exception:
                await self.unregister(client_id, ws)


def _placement_key(client_id: str, course: str, state: "App") -> Tuple[str, str]:
    """Which placement test: one learner, one course."""
    learner = state.store.learner(client_id, state.default_lang)
    return (client_id, normalize(course) if course else learner.active)


def build_app(cfg: Dict) -> FastAPI:
    app = FastAPI(title="LinguaLens", version="0.2.0")
    state = App(cfg)
    app.state.lingualens = state

    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    async def glasses_ui():
        return FileResponse(WEB_DIR / "index.html")

    @app.get("/phone", include_in_schema=False)
    async def phone_ui():
        return FileResponse(WEB_DIR / "phone.html")

    @app.get("/api/languages")
    async def languages():
        return {"current": state.default_lang, "supported": supported()}

    @app.get("/api/health")
    async def health():
        rows = []
        for desc in state.registry.all():
            row = {
                "id": desc["id"],
                "name": desc["name"],
                "native": desc["native"],
                "ready": desc["ready"],
                "lessons": desc["lessons"],
                "vocab": desc["vocab"],
                "prompts": desc["prompts"],
                "speech_lang": desc.get("speech_lang"),
            }
            if not desc["ready"]:
                row["error"] = desc.get("error")
            rows.append(row)
        return {
            "ok": True,
            "default": state.default_lang,
            "provider": state.provider,
            "tone_aware": state.provider == "iflytek",
            "azure_ready": state.provider == "azure",
            "asr": state.asr_provider,
            "courses": rows,
        }

    @app.get("/api/courses")
    async def courses(client_id: str = Query("default")):
        """Every course, with this learner's numbers on each one."""
        learner = state.store.learner(client_id, state.default_lang)
        return {
            "active": learner.active,
            "courses": [state._course_row(c, learner) for c in state.registry.all()],
        }

    @app.get("/api/course")
    async def course(course: str = Query(""), client_id: str = Query("default")):
        """The ladder for one course. Defaults to what this learner is on."""
        if course:
            lang = normalize(course)
        else:
            lang = state.store.learner(client_id, state.default_lang).active
        try:
            return state.registry.get(lang).to_dict()
        except CourseNotReady as exc:
            raise HTTPException(404, str(exc))

    @app.post("/api/course/select")
    async def course_select(client_id: str = Form("default"), course: str = Form("")):
        """Switch which course this learner is studying right now."""
        lang = normalize(course) if course else state.default_lang
        if not state.registry.ready(lang):
            raise HTTPException(409, f"course '{lang}' is not ready: {state.registry.error(lang)}")
        learner = state.store.learner(client_id, state.default_lang)
        learner.set_active(lang)
        state.persist(client_id)
        await state.broadcast(client_id, lang)
        return {"active": lang, "state": state.state(client_id, lang)}

    @app.get("/api/progress")
    async def progress_of(client_id: str = Query("default"), course: str = Query("")):
        """Lessons done, words learned, minutes, streak - for one course."""
        learner = state.store.learner(client_id, state.default_lang)
        lang = normalize(course) if course else learner.active
        try:
            course_obj = state.registry.get(lang)
        except CourseNotReady as exc:
            raise HTTPException(404, str(exc))
        cp = learner.course(lang)
        review = state._review_due(lang, cp) if learner.has(lang) else 0
        return JSONResponse(
            progress.summary(
                lang, cp, course_obj, review_due=review,
                name=LANG_NAMES.get(lang, lang), native=native_label(lang),
            )
        )

    @app.get("/api/progress/words")
    async def words_of(
        client_id: str = Query("default"),
        course: str = Query(""),
        kind: str = Query(""),          # word | phrase | "" for both
        band: Optional[int] = Query(None),
        q: str = Query(""),             # search text / reading / English
        limit: int = Query(100),
        offset: int = Query(0),
    ):
        """The words this learner has actually passed the gate on."""
        learner = state.store.learner(client_id, state.default_lang)
        lang = normalize(course) if course else learner.active
        if not state.registry.ready(lang):
            raise HTTPException(404, f"course '{lang}' is not ready")
        return JSONResponse(
            progress.word_list(
                learner.course(lang), kind=kind, band=band, query=q,
                limit=max(1, min(limit, 500)), offset=max(0, offset),
            )
        )

    @app.post("/api/placement/start")
    async def placement_start(
        client_id: str = Form("default"),
        course: str = Form(""),
    ):
        """Begin a placement test. ~4 lines from each band, spoken and gated."""
        learner = state.store.learner(client_id, state.default_lang)
        lang = normalize(course) if course else learner.active
        try:
            reg_course = state.registry.get(lang)
        except Exception:
            return JSONResponse({"error": "course unavailable"}, status_code=503)
        test = placement.Placement(reg_course, state.registry.config_for(lang))
        state.placements[(client_id, lang)] = test
        return JSONResponse({
            "total": len(test.items),
            "item": test.current(),
            "progress": f"0/{len(test.items)}",
        })

    @app.get("/api/placement")
    async def placement_state(
        client_id: str = Query("default"),
        course: str = Query(""),
    ):
        state_ = state.placements.get(_placement_key(client_id, course, state))
        if not state_:
            return JSONResponse({"running": False})
        return JSONResponse({
            "running": True,
            "progress": f"{state_.pos}/{len(state_.items)}",
            "item": state_.current(),
            "recommended": state_.recommended() if state_.pos >= len(state_.items) else None,
        })

    @app.post("/api/placement/submit")
    async def placement_submit(
        client_id: str = Form("default"),
        course: str = Form(""),
        quality: str = Form("good"),
    ):
        """Grade one probe and move on. A failed probe never blocks."""
        key = _placement_key(client_id, course, state)
        test = state.placements.get(key)
        if not test:
            return JSONResponse({"error": "no placement running"}, status_code=409)
        lang = key[1]
        reference = (test.current() or {}).get("text", "") or "你好"
        out = test.submit(simulated_score(reference, quality, lang))
        if out.get("done"):
            # the point of the test: start where the learner actually is
            recommended = out.get("recommended")
            if recommended:
                learner = state.store.learner(client_id, state.default_lang)
                cp = learner.course(lang)
                cp["lesson_id"] = int(recommended)
                cp["placed"] = True
                state.store.save()
            state.placements.pop(key, None)
        return JSONResponse(out)

    @app.get("/api/diagnostics")
    async def diagnostics_of(
        client_id: str = Query("default"),
        course: str = Query(""),
        limit: int = Query(12),
    ):
        """What to fix first: your worst tones and initials/finals.

        Every attempt already produces a score per syllable and it was being
        thrown away, so the app could say "your tones are 78" but never which
        ones. This is the aggregate. Empty until a course has a few attempts
        behind it, which is deliberate - one bad go at 好 is noise.
        """
        learner = state.store.learner(client_id, state.default_lang)
        lang = normalize(course) if course else learner.active
        return JSONResponse(
            progress.diagnostics(
                learner.course(lang), limit=max(1, min(limit, 50))
            )
        )

    @app.get("/api/state")
    async def get_state(client_id: str = "default", course: str = ""):
        return JSONResponse(state.state(client_id, course or None))

    @app.websocket("/ws")
    async def ws(websocket: WebSocket, client_id: str = "default", course: str = ""):
        await websocket.accept()
        await state.register(client_id, websocket)
        try:
            await websocket.send_text(
                json.dumps(state.state(client_id, course or None), ensure_ascii=False)
            )
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass
        finally:
            await state.unregister(client_id, websocket)

    # Every route below takes `course`: the learner can be studying Mandarin
    # now and Japanese five minutes later, and the two never mix.
    @app.post("/api/lesson/start")
    async def start_lesson(
        client_id: str = Form("default"),
        lesson_id: Optional[int] = Form(None),
        course: str = Form(""),
    ):
        sess = state.session_for(client_id, course or None)
        if lesson_id:
            sess.start_lesson(int(lesson_id))
        state.persist(client_id)
        await state.broadcast(client_id, sess.lang)
        return JSONResponse(state.state(client_id, sess.lang))

    @app.post("/api/next")
    async def next_step(
        client_id: str = Form("default"), course: str = Form(""), at: int = Form(-1)
    ):
        """Advance past listening / recall-round prompts only.

        `at` is the step index the caller is looking at. The glasses page and
        the phone share one session, so both can ask to move past the same
        line; with `at` the second request is a no-op instead of a skip.
        """
        sess = state.session_for(client_id, course or None)
        moved = sess.advance_non_speech(at if at >= 0 else None)
        await state.broadcast(client_id, sess.lang)
        return JSONResponse({"advanced": moved, "state": state.state(client_id, sess.lang)})

    @app.post("/api/attempt")
    async def attempt(
        client_id: str = Form("default"),
        file: UploadFile = File(...),
        encoding: str = Form("wav"),
        sample_rate: int = Form(0),
        recognized: str = Form(""),  # Web Speech API text, when the phone has it
        course: str = Form(""),
    ):
        sess = state.session_for(client_id, course or None)
        if not sess.needs_speech():
            await state.broadcast(client_id, sess.lang)
            return JSONResponse(
                {"passed": False, "reasons": ["Nothing to speak right now - listen first."],
                 "state": state.state(client_id, sess.lang)}
            )

        data = await file.read()
        try:
            if encoding == "pcm_s16le":
                sr = int(sample_rate) or int(sess.cfg["audio"]["target_sample_rate"])
                pcm = data
            else:
                sr, pcm = read_wav(data)
        except Exception as exc:  # bad upload
            raise HTTPException(status_code=400, detail=f"unreadable audio: {exc}")

        max_seconds = float(sess.cfg["audio"].get("max_seconds", 15))
        limit = int(max_seconds * sr * 2)
        pcm = pcm[: limit]

        step = sess.current()
        result: Dict[str, object] = {}
        if step and step.kind in ("answer", "converse"):
            # listen first: we cannot grade what we have not heard
            heard, asr_name = asr.transcribe(pcm, sr, sess.cfg, client_text=recognized)
            result["asr"] = asr_name
            result["heard"] = heard
            if heard:
                score: Score = score_attempt(pcm, sr, heard, sess.cfg)
                score.recognized = heard
                score.coverage = coverage_of(heard, heard)
            else:
                # no dictation service configured: drill the model answer
                score = score_attempt(pcm, sr, step.sample_text or step.text, sess.cfg)
                score.reasons.append(
                    "No dictation service - graded against the model answer."
                )
        else:
            score = score_attempt(pcm, sr, sess.reference_text(), sess.cfg)
        result.update(sess.submit(score))
        state.persist(client_id)
        result["score"] = score.to_dict()
        result["state"] = state.state(client_id, sess.lang)
        await state.broadcast(client_id, sess.lang)
        return JSONResponse(result)

    @app.post("/api/attempt/sim")
    async def attempt_sim(
        client_id: str = Form("default"),
        quality: str = Form("good"),
        course: str = Form(""),
    ):
        """Dev shortcut: grade without a microphone."""
        sess = state.session_for(client_id, course or None)
        if not sess.needs_speech():
            sess.advance_non_speech()
        step = sess.current()
        if step and step.kind in ("answer", "converse"):
            reference = step.sample_text or (step.text or "")
        else:
            reference = sess.reference_text() or (step.text if step else "") or "你好"
        score = simulated_score(reference, quality, sess.lang)
        result = sess.submit(score)
        state.persist(client_id)
        result["score"] = score.to_dict()
        result["state"] = state.state(client_id, sess.lang)
        await state.broadcast(client_id, sess.lang)
        return JSONResponse(result)

    @app.post("/api/review/start")
    async def review(client_id: str = Form("default"), limit: int = Form(20), course: str = Form("")):
        """Endless spaced review of everything you have already passed."""
        sess = state.session_for(client_id, course or None)
        queued = sess.start_review(int(limit))
        state.persist(client_id)
        await state.broadcast(client_id, sess.lang)
        return JSONResponse({"queued": queued, "state": state.state(client_id, sess.lang)})

    @app.post("/api/vocab/start")
    async def vocab_start(
        client_id: str = Form("default"),
        topic_id: str = Form(""),
        course: str = Form(""),
    ):
        """Drill one themed slice of the word bank."""
        sess = state.session_for(client_id, course or None)
        queued = sess.start_vocab(topic_id)
        state.persist(client_id)
        await state.broadcast(client_id, sess.lang)
        return JSONResponse({"queued": queued, "state": state.state(client_id, sess.lang)})

    @app.get("/api/library")
    async def library(course: str = Query(""), client_id: str = Query("default")):
        """Every story in the course library, by band, with what this learner
        has finished."""
        lang = normalize(course) if course else state.store.learner(
            client_id, state.default_lang).active
        try:
            c = state.registry.get(lang)
        except CourseNotReady as exc:
            raise HTTPException(404, str(exc))
        learner = state.store.learner(client_id, state.default_lang)
        cp = learner.course(lang) if learner.has(lang) else {}
        done = set((cp or {}).get("stories") or [])
        bands = []
        for lv in c.levels:
            stories = c.stories_of_band(lv.band)
            if not stories:
                continue
            bands.append({
                "band": lv.band, "code": lv.code,
                "stories": [dict(st.to_dict(brief=True), done=st.id in done) for st in stories],
            })
        return {"language": lang, "bands": bands, "done": len(done)}

    @app.post("/api/library/start")
    async def library_start(
        client_id: str = Form("default"),
        story_id: str = Form(""),
        course: str = Form(""),
    ):
        """Play one library story: heard blind, then followed line by line."""
        sess = state.session_for(client_id, course or None)
        queued = sess.start_story(story_id)
        state.persist(client_id)
        await state.broadcast(client_id, sess.lang)
        return JSONResponse({"queued": queued, "state": state.state(client_id, sess.lang)})

    @app.get("/api/fluency")
    async def fluency_of(course: str = Query("")):
        """What the course's content backs up, band by band (server/fluency.py)."""
        lang = normalize(course) if course else state.default_lang
        try:
            c = state.registry.get(lang)
        except CourseNotReady as exc:
            raise HTTPException(404, str(exc))
        return fluency.report(c, state.registry.config_for(lang))

    @app.get("/api/vocab/topic")
    async def vocab_topic(topic_id: str = "", course: str = ""):
        lang = normalize(course) if course else state.default_lang
        if state.registry.ready(lang):
            topic = state.registry.get(lang).topic(topic_id)
            if topic:
                return JSONResponse(topic.to_dict())
        # fall back: the topic may belong to another course
        for desc in state.registry.all():
            if not desc["ready"]:
                continue
            topic = state.registry.get(desc["id"]).topic(topic_id)
            if topic:
                return JSONResponse(topic.to_dict())
        raise HTTPException(status_code=404, detail="no such topic")

    @app.post("/api/think")
    async def think(client_id: str = Form("default"), text: str = Form(""), course: str = Form("")):
        text = (text or "").strip()
        if not text:
            raise HTTPException(status_code=400, detail="empty thought")
        sess = state.session_for(client_id, course or None)
        target = translate(text, sess.cfg)
        sess.set_think(target)
        await state.broadcast(client_id, sess.lang)
        return JSONResponse({"target": target.to_dict(), "state": state.state(client_id, sess.lang)})

    @app.post("/api/think/exit")
    async def think_exit(client_id: str = Form("default"), course: str = Form("")):
        sess = state.session_for(client_id, course or None)
        sess.exit_think()
        await state.broadcast(client_id, sess.lang)
        return JSONResponse(state.state(client_id, sess.lang))

    @app.post("/api/reset")
    async def reset(client_id: str = Form("default"), course: str = Form("")):
        """Wipe progress for one course, or for the whole learner."""
        learner = state.store.learner(client_id, state.default_lang)
        if course:
            learner.raw.setdefault("courses", {}).pop(normalize(course), None)
        else:
            state.store.data.pop(client_id, None)
        for key in [k for k in list(state.sessions) if k[0] == client_id]:
            state.sessions.pop(key, None)
        state.store.save()
        await state.broadcast(client_id)
        return JSONResponse(state.state(client_id))

    return app


def default_config(lang: str) -> str:
    # config.yaml is Mandarin's; every other course has config.<code>.yaml
    key = normalize(lang)
    root = Path(__file__).resolve().parents[1]
    named = f"config.{key}.yaml"
    return named if key != "zh" and (root / named).exists() else "config.yaml"


def main() -> None:
    parser = argparse.ArgumentParser(description="LinguaLens language coach")
    parser.add_argument("--config", default=None,
                        help="config file; default config.yaml (zh) or config.<lang>.yaml")
    parser.add_argument("--lang", default=None, choices=sorted(supported()),
                        help="which course to load (picks the default config too)")
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    args = parser.parse_args()

    cfg = load_config(args.config or default_config(args.lang or "zh"))
    # cloud deployment (Cloud Run): progress lives on a mounted bucket
    if os.getenv("LINGUALENS_STATE"):
        cfg["storage"]["path"] = os.environ["LINGUALENS_STATE"]
    if args.lang:
        cfg["language"] = normalize(args.lang)
        cfg["language_name"] = LANG_NAMES.get(cfg["language"], cfg["language"])

    host = args.host or cfg["server"]["host"]
    port = args.port or int(os.getenv("PORT") or 0) or cfg["server"]["port"]
    access_key = os.getenv("LINGUALENS_KEY", "")
    provider = resolve_provider(cfg)

    registry = Registry(cfg)
    print("LinguaLens - language coach for display glasses")
    print(f"  pronunciation provider : {provider}"
          + ("" if provider != "mock" else "  (set a speech key for real scoring)"))
    for desc in registry.all():
        if desc["ready"]:
            ready_cfg = registry.config_for(desc["id"])
            print(f"  course {desc['id']} ({desc['native']})".ljust(24)
                  + f": {desc['lessons']} lessons · {desc['vocab']} words · "
                    f"{desc['speech_lang']} · asr={asr.resolve(ready_cfg)}")
        else:
            print(f"  course {desc['id']} ({desc['native']})".ljust(24)
                  + f": NOT READY - {desc.get('error')}")
    print(f"  progress store         : {cfg['storage']['path']} (every course)")
    print(f"  glasses display        : http://127.0.0.1:{port}/")
    print(f"  phone companion        : http://127.0.0.1:{port}/phone")

    if access_key:
        print("  access                 : key required (?key=... once, then a cookie)")
    # proxy_headers: Cloud Run terminates TLS, so trust its X-Forwarded-Proto
    uvicorn.run(AccessKey(build_app(cfg), access_key), host=host, port=port,
                log_level="info", proxy_headers=True, forwarded_allow_ips="*")


if __name__ == "__main__":
    main()
