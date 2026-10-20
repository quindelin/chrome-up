"""Smoke test for the language course.  Run:  python tests/smoke.py

This exists because two classes of bug reached the app with nothing catching
them:

* a `NameError` in `Session.state()` that broke every Japanese session. It
  survived because the repo's only smoke test covers **autoclip**, a
  different project in the parent directory, and never imports this code.
* a content part file with a syntax error. The merge swallowed the
  exception, several hundred rows vanished, and every check still reported
  clean.

So the two jobs here are: exercise the runtime path, not just the data
tables; and fail loudly when a table is smaller than it should be.

Everything runs against real course data with no network and no audio.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from server.config import course_config, load_config  # noqa: E402
from server.curriculum import Course  # noqa: E402
from server.engine import Session, Step  # noqa: E402
from server.models import Score  # noqa: E402
from server.course.ja import kana_check, kanji, readings, grammar  # noqa: E402

PASS, FAIL = [], []


def check(name: str, fn):
    try:
        fn()
        PASS.append(name)
        print(f"  ok   {name}")
    except Exception as exc:  # noqa: BLE001
        FAIL.append((name, exc))
        print(f"  FAIL {name}: {exc}")


def _session(lang: str, lesson_id: int) -> Session:
    course = Course(lang)
    # the course's own config, the way the server builds it - load_config(lang)
    # finds no file called "es" and quietly hands every course Mandarin's
    return Session(course, course_config(load_config(), lang),
                   {"lesson_id": lesson_id, "completed": [], "mastery": {},
                    "words": {}, "stats": {}})


def _score(text: str) -> Score:
    """A clean attempt that said exactly `text` - no audio, no network."""
    from server.pronunciation import simulated_score
    s = simulated_score(text, "good")
    s.recognized = text
    return s


# --------------------------------------------------------------- 1 the course
def t_course_loads():
    for lang in ("ja", "zh"):
        c = Course(lang)
        assert c.lesson_ids, f"{lang}: no lessons"
        assert c.topics, f"{lang}: no vocabulary topics"
    assert len(Course("ja").lesson_ids) == 73


def t_vocab_no_duplicates():
    """A word belongs to exactly one topic, across the whole bank."""
    seen, dupes = {}, []
    for topic in Course("ja").topics.values():
        for w in topic.words:
            if w.text in seen:
                dupes.append(f"{w.text}: {seen[w.text]} and {topic.id}")
            seen[w.text] = topic.id
    assert not dupes, dupes[:5]


def t_vocab_no_padding():
    """A word must be filed in exactly one topic, not merely drilled once.

    `Course` de-duplicates on load, so `kana_check` reports 0 issues even
    when a word is written into two files - which is how 39 words sat in
    both an N1 topic and an N2 topic without anything failing. The loader
    records what it dropped; that is the real signal that someone is
    padding their bank with words a lower band already owns.
    """
    dupes = Course("ja").duplicate_words
    assert not dupes, [f"{w}: {keep} and {drop}" for w, keep, drop in dupes[:8]]


def t_basic_words_owned_by_easiest_band():
    """The beginner band must own the beginner words.

    Bands run 0 (N1+, hardest) to 5 (N5, easiest). Getting the dedupe
    direction wrong hands 山 to an N3 topic and deletes it from N5, so the
    beginner never meets it - and every other check still passes.
    """
    basic = ("山 川 海 犬 猫 走る 泳ぐ 洗う 地下鉄 出口 入口 信号 交差点 "
             "明るい 暗い 丸い 静か 賑やか").split()
    c = Course("ja")
    bad = []
    for w in basic:
        owners = [(t.id, t.band) for t in c.topics.values()
                  if any(x.text == w for x in t.words)]
        if not owners:
            bad.append(f"{w}: not present at all")
        elif len(owners) > 1:
            bad.append(f"{w}: in {owners}")
        elif owners[0][1] != 5:
            bad.append(f"{w}: owned by {owners[0]} not band 5")
    assert not bad, bad[:5]


# ------------------------------------------------------------ 2 the checkers
def t_kana_check():
    problems = kana_check.check_course(Course("ja"))
    assert not problems, problems[:5]


def t_readings():
    assert not readings.check(), readings.check()[:5]
    assert readings.stats()["passages"] == 73, readings.stats()


def t_grammar():
    assert not grammar.check(), grammar.check()[:5]


def t_kanji():
    assert not kanji.check(), kanji.check()[:5]
    assert kanji.stats()["total"] > 1000, kanji.stats()


def t_parts_actually_loaded():
    """A part file that exists but contributes nothing must not pass.

    This is the guard for the swallowed-import bug: a part with a syntax
    error used to disappear silently while every check reported clean.
    """
    for mod, names in ((readings, ("readings_a", "readings_b", "readings_c")),
                       (grammar, ("grammar_b",)),
                       (kanji, ("kanji_extra1", "kanji_extra2"))):
        dead = mod._parts.dead_parts(names)
        assert not dead, f"{mod.__name__}: parts loaded nothing: {dead}"


# ------------------------------------------------- 3 the runtime path (the gap)
def t_session_state_every_lesson():
    """The bug that started this file: `state()` raised NameError.

    Nothing built a Session and called state(), so the app could be broken
    while every data check was green. Exercise the real path, both
    languages, every lesson.
    """
    for lang in ("ja", "zh"):
        for lid in Course(lang).lesson_ids:
            s = _session(lang, lid)
            st = s.state()
            assert isinstance(st, dict), f"{lang} L{lid}: state() not a dict"
            assert "grammar" in st, f"{lang} L{lid}: state() has no grammar"
            assert isinstance(st["grammar"], list)


def t_grammar_reaches_a_lesson():
    """37-73 have pages; state() must actually carry them through."""
    st = _session("ja", 50).state()
    assert st["grammar"], "lesson 50 has a page but state() carried none"


def t_new_step_kinds_present():
    ja = {st.kind for lid in Course("ja").lesson_ids
          for st in _session("ja", lid).steps}
    for kind in ("kana", "kanji", "read"):
        assert kind in ja, f"no {kind} steps anywhere in the Japanese course"
    # Kana and kanji are Japanese-only - the syllabaries have to be taught
    # outright and kanji are drilled on their own, neither of which has a
    # Chinese counterpart. Reading is NOT Japanese-only: zh carries its own
    # passages, so a `read` step there is correct, not a leak.
    zh = {st.kind for lid in Course("zh").lesson_ids
          for st in _session("zh", lid).steps}
    assert not (zh & {"kana", "kanji"}), f"zh leaked ja steps: {zh}"


def t_read_steps_are_speakable():
    """A read step is graded as speech, so the mic must be enabled for it."""
    s = _session("ja", 20)
    read = [st for st in s.steps if st.kind == "read"]
    assert read, "lesson 20 has no reading step"
    s.pos = s.steps.index(read[0])
    assert s.needs_speech(), "read step is not speech-gated"


def t_zh_new_step_kinds_present():
    zh = {st.kind for lid in Course("zh").lesson_ids
          for st in _session("zh", lid).steps}
    for kind in ("hanzi", "read", "hear", "write"):
        assert kind in zh, f"no {kind} steps anywhere in the Mandarin course"


def t_write_is_speakable_and_graded():
    """A 缩写 is produced by the learner: mic on, and not refused by submit().

    `submit()` rejects anything not in its list of speakable kinds, so a new
    step kind that forgets to register there looks like "the other person's
    line" instead of a bug.
    """
    s = _session("zh", 64)
    write = [st for st in s.steps if st.kind == "write"]
    assert write, "lesson 64 (HSK 6) has no 缩写 step"
    s.pos = s.steps.index(write[0])
    assert s.needs_speech(), "write step is not speech-gated"
    assert s.reference_text() == "", "write step must not grade against a reference"


def t_write_graded_on_coverage_not_wording():
    """The whole reason 缩写 has its own grader.

    A fluent, grammatical, on-topic summary that drops the point must fail.
    Character overlap with the prompt cannot see that; coverage can.
    """
    from server import free

    s = _session("zh", 64)
    step = next(st for st in s.steps if st.kind == "write")
    gate, cfg = s.gate(), s.cfg

    def say(text):
        sc = _score(text)
        return free.grade_writing(sc, step, gate, cfg, "zh", 6)[0]

    assert say(step.sample_text), "the authored sample must pass its own grader"
    assert not say("因为情况有变化，会议改到下周了，麻烦大家调整一下时间。"), \
        "a summary that drops 下周一 and 不便 passed"


def t_placement_places_you():
    from server import placement
    from server.pronunciation import simulated_score

    course = Course("zh")
    items = placement.build(course)
    assert len(items) >= 6, f"only {len(items)} probes - one band is missing"
    assert {i["band"] for i in items} == {1, 2, 3, 4, 5, 6, 7}, \
        sorted({i["band"] for i in items})

    def run(ok_upto):
        t = placement.Placement(course, load_config("zh"))
        while t.current():
            it = t.current()
            t.submit(simulated_score(it["text"], "good" if it["band"] <= ok_upto else "bad"))
        return t.recommended()

    first = {b: Course("zh").lessons_of_band(b)[0].id for b in range(1, 8)}
    assert run(0) == first[1], "a total beginner was not placed at lesson 1"
    assert run(2) == first[3], "clearing 1-2 should place you at HSK 3"
    assert run(7) == first[7], "clearing everything should place you at the top"


def t_drill_frames_only_use_x():
    """The drill engine fills {x} and nothing else, so any other {slot}
    reaches the glasses as literal braces (HSK 7 lessons 80-85 shipped with
    {y})."""
    import re
    for lang in ("zh", "ja"):
        course = Course(lang)
        for lid in course.lesson_ids:
            for p in getattr(course.lesson(lid), "patterns", []) or []:
                for field in (p.text, p.reading, p.en):
                    extra = set(re.findall(r"\{(\w+)\}", field or "")) - {"x"}
                    assert not extra, f"{lang} lesson {lid}: {field!r} has slot(s) {extra}"


def t_next_ignores_a_stale_step_index():
    """Glasses page and phone share one session; both may ask to move past
    the same line. The second request must not skip the following one."""
    sess = _session("zh", 1)
    while sess.current() and sess.current().kind not in ("listen", "info", "kana", "kanji", "hanzi", "hear"):
        sess.pos += 1
    at = sess.pos
    assert sess.advance_non_speech(at), "first request did not advance"
    assert not sess.advance_non_speech(at), "a duplicate request skipped a step"
    assert sess.pos == at + 1


# --------------------------------------------------------------- 4 Spanish
# The first space-delimited course. Every heuristic above was built for 汉字
# and かな, so these check the places where "one character = one unit of
# meaning" would quietly be wrong for Spanish.
def t_es_course_shape():
    """Every lesson, A1 to C2, carries what the audit says the Japanese N5 lacks."""
    from server.course.es import readings as es_readings, grammar as es_grammar
    c = Course("es")
    assert [lv.code for lv in c.levels] == ["A1", "A2", "B1", "B2", "C1", "C2"], [lv.code for lv in c.levels]
    assert len(c.lesson_ids) == 76 and c.lesson_ids == list(range(1, 77)), len(c.lesson_ids)
    bad = []
    for lid in c.lesson_ids:
        l = c.lessons[lid]
        if len(l.patterns) < 2 or any(not p.kind for p in l.patterns):
            bad.append(f"L{lid}: needs 2+ patterns, all with a kind")
        if sum(1 for t in l.dialogue if t.speaker == "you") < 3:
            bad.append(f"L{lid}: fewer than 3 learner lines")
        if len(l.prompts) < 2 or not l.scene or not es_grammar.for_lesson(lid):
            bad.append(f"L{lid}: missing prompts / scene / grammar page")
        if len(es_readings.get(lid).get("questions") or []) < 2:
            bad.append(f"L{lid}: passage needs a read and a hear question")
        if any("+" in v.text for v in l.vocab):
            bad.append(f"L{lid}: a vocab item is a formula, not something you can say")
        if any(t.speaker == "them" and t.text.startswith("(") for t in l.dialogue):
            bad.append(f"L{lid}: a stage direction would be read aloud")
    assert not bad, bad[:5]
    assert not es_readings.check(), es_readings.check()[:3]


def t_es_bank_fully_reached():
    """Each band's lessons x its inject count meet every bank word, once."""
    from server.engine import inject_count
    c = Course("es")
    vocab_cfg = load_config("config.es.yaml")["vocab"]
    assert not c.duplicate_words, c.duplicate_words[:5]
    met = []
    for band in c.vocab_by_band:
        per = inject_count(vocab_cfg, band)
        got = [w.text for l in c.lessons_of_band(band) for w in c.vocab_for_lesson(l, per)]
        bank = len(c.vocab_words(band))
        assert len(set(got)) == bank == len(got), (band, len(set(got)), bank, len(got))
        met += got
    lesson_words = {v.text for l in c.lessons.values() for v in l.vocab}
    overlap = [w for w in met if w in lesson_words]
    assert not overlap, overlap[:5]


def t_es_drills_never_fall_back_to_mandarin():
    c = Course("es")
    from server import drills
    for lid in c.lesson_ids:
        for p in drills.generate(c.lessons[lid], load_config("config.es.yaml"), "es"):
            assert not any("一" <= ch <= "鿿" for ch in p.text), (lid, p.text)
    assert drills.base_patterns("es")[0].text.startswith("Quiero")


def t_es_matching_is_word_level():
    """Letter overlap between any two Spanish lines is near total."""
    from server.curriculum import content_chars
    from server.pronunciation import coverage_of
    assert coverage_of("Me llamo Sam.", "me gusta el pan") < 0.5
    assert coverage_of("Sí, gracias.", "si gracias") == 1.0      # ASR dropped accents
    assert content_chars("¿De dónde eres?", "es") & content_chars("Soy de Canadá.", "es")
    assert not content_chars("¿De dónde eres?", "es") & content_chars("Me gusta el café.", "es")


def t_mock_scorer_passes_short_replies_in_every_course():
    """No speech key: a short, audible reply passes every gate, Spanish included.

    The mock used to report what it heard with the spaces stripped, so the
    Spanish word check saw one long word and failed every attempt - however
    long or well said. With audio.mock_quick (the default) length no longer
    matters; silence and a tap still fail.
    """
    import math
    import struct
    from server.config import course_config
    from server.pronunciation import evaluate, score_attempt
    sr = 16000
    voice = b"".join(struct.pack("<h", int(8000 * math.sin(i * 0.2)) + (i * 7919) % 600 - 300)
                     for i in range(int(0.6 * sr)))
    for lang in ("es", "ja", "zh"):
        cfg, c = course_config(load_config(), lang), Course(lang)
        bad = []
        for lid in c.lesson_ids:
            gate = c.gate_for(lid, cfg["gate"])
            for t in [t for t in c.lessons[lid].dialogue if t.speaker == "you"][:2]:
                ok, why = evaluate(score_attempt(voice, sr, t.text, cfg, provider="mock"), gate)
                if not ok:
                    bad.append((lid, t.text, why))
        assert not bad, (lang, bad[:3])
        assert not evaluate(score_attempt(b"\0\0" * sr, sr, "Hola", cfg, provider="mock"), gate)[0]
        assert not evaluate(score_attempt(voice[: sr // 5], sr, "Hola", cfg, provider="mock"), gate)[0]
    # strict mode still tells a rushed line from a full one - and Spanish can pass it
    cfg = course_config(load_config(), "es")
    cfg["audio"]["mock_quick"] = False
    line, gate = "Me levanto a las siete, pero los lunes, a las seis.", Course("es").gate_for(17, cfg["gate"])
    assert not evaluate(score_attempt(voice, sr, line, cfg, provider="mock"), gate)[0]
    assert evaluate(score_attempt(voice * 8, sr, line, cfg, provider="mock"), gate)[0]


def t_es_digits_in_dictation_still_match():
    """Azure writes "son doce euros" as "Son 12 €" - a right answer must still pass.

    Before the fix every price, time and date line failed the word check
    ("Not all of the words came through") however well it was said.
    """
    import re
    from server import drills
    from server.course import meta
    from server.pronunciation import coverage_of as _cov
    _ES_UNITS = meta("es")._ES_UNITS

    def coverage_of(ref, heard):   # the number spelling is Spanish's own hook
        return _cov(ref, heard, "es")
    assert coverage_of("A las diez, andén tres.", "A las 10, andén 3.") == 1.0
    assert coverage_of("Normalmente me acuesto a las once y media.", "Normalmente me acuesto a las 11:30.") == 1.0
    assert coverage_of("Serán unos treinta mil euros.", "Serán unos 30.000 €.") == 1.0
    assert coverage_of("Tercer piso, gracias.", "3er piso, gracias.") == 1.0
    assert coverage_of("Son doce euros.", "Son 13 euros.") < 1.0          # a wrong number still counts
    # dictate every learner line and drill the way Azure would: number words as digits
    digits = {w: str(i) for i, w in enumerate(_ES_UNITS)}
    digits.update({"treinta": "30", "cuarenta": "40", "cincuenta": "50", "noventa": "90", "cien": "100"})
    word = re.compile(r"\b(" + "|".join(sorted(digits, key=len, reverse=True)) + r")\b")
    c, cfg = Course("es"), load_config("config.es.yaml")
    bad = []
    for lid in c.lesson_ids:
        lines = [t.text for t in c.lessons[lid].dialogue if t.speaker == "you"]
        lines += [p.text for p in drills.generate(c.lessons[lid], cfg, "es")]
        for text in lines:
            heard = word.sub(lambda m: digits[m.group(1)], text)
            if heard != text and coverage_of(text, heard) < 1.0:
                bad.append((lid, text, heard))
    assert not bad, bad[:5]


def t_es_never_scored_by_iflytek():
    """ISE has no Spanish: Chinese keys in the env must not route Spanish to it."""
    import os
    from server.config import course_config, resolve_provider
    old = {k: os.environ.get(k) for k in ("IFLYTEK_APPID", "IFLYTEK_API_KEY")}
    os.environ.update(IFLYTEK_APPID="x", IFLYTEK_API_KEY="y")
    try:
        cfg = load_config("config.yaml")
        assert resolve_provider(course_config(cfg, "es")) != "iflytek"
        assert resolve_provider(course_config(cfg, "zh")) == "iflytek"
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def t_es_summaries_from_c1():
    """C1-C2 lessons end in a spoken summary; earlier bands never do."""
    from server.course.es import summaries
    c = Course("es")
    assert sorted(summaries.SUMMARIES) == list(range(53, 77)), sorted(summaries.SUMMARIES)
    cfg = load_config("config.es.yaml")
    for lid in (52, 53, 76):
        steps = Session(c, cfg, {"lesson_id": lid, "completed": [], "mastery": {},
                                 "words": {}, "stats": {}}).steps
        has = any(st.kind == "write" for st in steps)
        assert has == (lid >= 53), (lid, has)


def t_es_summary_keywords_match_spoken_words():
    """Summary keywords are checked against speech that has lost its spaces."""
    from types import SimpleNamespace
    from server.free import grade_writing
    from server.course.es import summaries
    item = summaries.get(54)
    step = SimpleNamespace(text=item["prompt"], sample_text=item["sample"],
                           keywords=item["keywords"], min_chars=10)
    s = _score(item["sample"].lower().replace("á", "a"))
    ok, why = grade_writing(s, step, {"min_pron_score": 0}, load_config("config.es.yaml"), "es", 5)
    assert ok, why


def t_es_session_every_lesson():
    for lid in Course("es").lesson_ids:
        st = _session("es", lid).state()
        assert isinstance(st, dict) and st.get("grammar"), f"es L{lid}"


# --------------------------------------------------------------- 5 listening and role-play
# Audit priorities 2 and 3 (docs/SPANISH_AUDIT.md): blind listening is the
# whole passage, not its last line; the dialogue comes back blind once it is
# mastered; and a role-play step talks back - or is left out with no key.
def _walk_to(sess: Session, pred) -> Step:
    """Pass every gated step until `pred(step)` holds - no audio, no network."""
    for _ in range(2000):
        st = sess.current()
        if st is None or pred(st):
            return st
        if not sess.advance_non_speech():
            sess.submit(_score(st.sample_text if st.kind in ("answer", "converse") else st.text))
    raise AssertionError("never reached the step")


def t_hear_plays_the_whole_passage():
    from server.course import module_for
    for lang, lid in (("es", 40), ("ja", 30), ("zh", 5)):
        sess = _session(lang, lid)
        chunks = module_for(lang, "readings").get(lid)["chunks"]
        hear = next(st for st in sess.steps if st.key == f"hear:{lid}")
        assert hear.audio_parts == [c[0] for c in chunks], (lang, hear.audio_parts)
        assert chunks[0][0] in hear.audio_text and chunks[-1][0] in hear.audio_text, lang
        d = hear.to_dict()
        assert d["hide_text"] and not d["text"] and not d["en"], lang
        assert d["audio_parts"] == hear.audio_parts, lang
        # the question after it may draw on any part of the passage
        nxt = sess.steps[sess.steps.index(hear) + 1]
        assert nxt.kind == "answer" and nxt.key == f"hear-q:{lid}", (lang, nxt.kind)


def t_natural_speed_from_b2():
    assert next(s for s in _session("es", 41).steps if s.kind == "hear").natural      # B2
    assert not next(s for s in _session("es", 30).steps if s.kind == "hear").natural  # B1
    ja = _session("ja", 1)
    assert not ja._natural()
    ja.band = 2
    assert ja._natural()                                       # JLPT counts down


def t_dialogue_replay_waits_for_mastery():
    sess = _session("es", 20)
    replay = next(st for st in sess.steps if st.key == "hear-dialogue:20")
    lesson = sess.course.lesson(20)
    assert replay.hide_text and len(replay.audio_parts) == len(lesson.dialogue)
    assert set(replay.audio_voices) == {0, 1}, replay.audio_voices
    # not mastered: walked straight over
    at = sess.steps.index(replay)
    sess.pos = at - 1
    sess.progress["mastery"] = {}
    sess.steps[at - 1] = Step(kind="info", en="x")
    sess.advance_non_speech()
    assert sess.current() is not replay, "replayed before the lines were mastered"
    # mastered: it plays
    sess.pos = at - 1
    sess.progress["mastery"] = {k: {"stage": 3} for k in replay.requires}
    sess.advance_non_speech()
    assert sess.current() is replay


def t_converse_left_out_without_a_key():
    import os
    env = load_config("config.es.yaml")["think"].get("api_key_env") or "OPENAI_API_KEY"
    saved = os.environ.pop(env, None)
    try:
        for lang in ("es", "ja", "zh"):
            assert not any(st.kind == "converse" for st in _session(lang, 5).steps), lang
    finally:
        if saved is not None:
            os.environ[env] = saved


def t_converse_talks_back_then_ends():
    import os
    from server import converse
    env = load_config("config.es.yaml")["think"].get("api_key_env") or "OPENAI_API_KEY"
    saved, real = os.environ.get(env), converse.reply
    os.environ[env] = "test-key"
    replies = iter([
        {"reply": "¿Y de qué parte de Boston eres?", "reply_en": "Which part?",
         "hint": "Soy del centro.", "hint_en": "", "done": False},
        None,  # the model goes away mid-scene: the scene ends, not the lesson
    ])
    converse.reply = lambda *a, **k: next(replies)
    try:
        sess = _session("es", 3)
        st = _walk_to(sess, lambda s: s.kind == "converse")
        assert st is not None and st.turns >= 3 and sess.needs_speech()
        assert sess.state()["step"]["kind"] == "converse"
        r = sess.submit(_score(st.sample_text))
        assert r["passed"] and not r["advanced"] and r.get("converse_turn") == 1, r
        assert st.text.startswith("¿Y de qué parte") and len(st.conversation) == 3
        r = sess.submit(_score("Soy del centro de Boston, cerca del parque."))
        assert r["passed"] and r["advanced"], r
        assert "converse:3" not in sess.progress["mastery"]
    finally:
        converse.reply = real
        if saved is None:
            os.environ.pop(env, None)
        else:
            os.environ[env] = saved


def t_es_four_free_prompts_a_lesson():
    c = Course("es")
    assert load_config("config.es.yaml")["free"]["per_lesson"] >= 4
    short = [lid for lid in c.lesson_ids if len(c.lessons[lid].prompts) < 4]
    assert not short, short
    sess = _session("es", 50)
    assert sum(1 for st in sess.steps if st.kind == "answer" and st.key.startswith("free:")) == 4


def t_glasses_card_never_blank():
    """Every step of every course gives the glasses something to show.

    The phone apps used to mirror step.text/reading/en, which a recall step
    leaves empty on purpose - so three steps in four drew a bare "…" on the
    waveguide. The server's card must always have a target, and a recall
    must show its English cue.
    """
    from server.pronunciation import simulated_score
    for lang, cfg_path, lid in (("zh", "config.yaml", 3), ("ja", "config.ja.yaml", 3),
                                ("es", "config.es.yaml", 3)):
        c = Course(lang)
        s = Session(c, load_config(cfg_path),
                    {"lesson_id": lid, "completed": [], "mastery": {}, "words": {}, "stats": {}})
        for i, step in enumerate(s.steps):
            s.pos, s.attempts = i, 0
            g = s.state()["glasses"]
            assert g["target"].strip(), f"{lang} step {i} ({step.kind}): blank card"
            assert g["header"], f"{lang} step {i}: no header"
            if step.kind == "recall":
                assert g["target"] == (step.prompt_en or step.en), (lang, i, g)
                assert step.text not in (g["target"], g["reading"]), "recall gave the answer away"
        # a pass brings the line back in full on the next screen
        i = next(i for i, st in enumerate(s.steps) if st.kind == "recall")
        s.pos, s.attempts = i, 0
        sc = simulated_score(s.steps[i].text, "good")
        sc.recognized = s.steps[i].text
        assert s.submit(sc)["passed"]
        assert s.steps[i].text in s.state()["glasses"]["footer"], lang


def t_never_asked_for_what_you_have_not_heard():
    """A recall is answered from the English alone, so every character (zh,
    ja) or word (es) in it must have been heard earlier in the lesson.

    HSK 1 lesson 1 used to ask for 我要茶 / 厕所在哪里 / 太贵了 from generic
    fallback drills, and for 不客气 before it was ever modelled.
    """
    heard_kinds = ("listen", "speak", "read", "hanzi", "kanji", "kana", "answer",
                   "hear", "converse")
    for lang, cfg_path in (("zh", "config.yaml"), ("ja", "config.ja.yaml"),
                           ("es", "config.es.yaml")):
        c = Course(lang)
        cfg = load_config(cfg_path)
        bad = []
        for lid in c.lesson_ids:
            s = Session(c, cfg, {"lesson_id": lid, "completed": [], "mastery": {},
                                 "words": {}, "stats": {}})
            heard = set()
            for st in s.steps:
                if st.prior:
                    continue
                if st.kind == "recall" and s._units(st.text) - heard:
                    bad.append((lid, st.text))
                if st.kind in heard_kinds:
                    heard |= s._units(st.text or getattr(st, "audio_text", "") or "")
        assert not bad, f"{lang}: {len(bad)} unheard recalls, e.g. {bad[:3]}"


def _play(s, fail_first=()):
    """Drive one lesson: listen steps advance, spoken steps pass first try
    (or fail once first, for keys in fail_first). Returns visited steps."""
    from server.pronunciation import simulated_score
    lid, seen = s.lesson_id, []
    while s.current() and s.lesson_id == lid and len(seen) < 1000:
        st = s.current()
        seen.append(st)
        if st.kind in ("listen", "info", "kana", "kanji", "hanzi", "hear"):
            s.advance_non_speech()
            continue
        txt = st.text or st.sample_text or st.prompt_en or "x"
        if st.key in fail_first and st.round:
            bad = simulated_score(txt, "bad")
            bad.recognized = ""
            s.submit(bad)
        ok = simulated_score(txt, "good")
        ok.recognized = txt
        if not s.submit(ok).get("advanced"):
            s.pos, s.attempts = s.pos + 1, 0
    return seen


def t_review_rounds_drop_out_at_criterion():
    """Rounds 1-2 always run (re-testing after a first success consolidates:
    Karpicke & Roediger 2008); round 3 only brings back lines that have not
    yet had two lagged first-try recalls this lesson."""
    c = Course("zh")
    s = Session(c, load_config("config.yaml"),
                {"lesson_id": 1, "completed": [], "mastery": {}, "words": {}, "stats": {}})
    s.start_lesson(1)
    rounds = [st.round for st in _play(s) if st.kind == "recall" and st.round]
    assert rounds.count(1) and rounds.count(2) == rounds.count(1), rounds
    assert rounds.count(3) == 0, "a clean run should skip round 3"
    s2 = Session(c, load_config("config.yaml"),
                 {"lesson_id": 1, "completed": [], "mastery": {}, "words": {}, "stats": {}})
    s2.start_lesson(1)
    missed = next(st.key for st in s2.steps if st.kind == "recall" and st.round == 1)
    r3 = [st.key for st in _play(s2, fail_first={missed}) if st.round == 3 and st.kind == "recall"]
    assert r3 == [missed], r3


def t_spacing_promotes_only_when_due_and_reviews_hit_the_real_line():
    """Five passes in one sitting are one review, not five; a pass after a
    day jumps past a day; the Review button and the warm-up update the line's
    own schedule instead of minting "review:" copies."""
    import time as _time
    from unittest import mock
    c = Course("zh")
    prog = {"lesson_id": 1, "completed": [], "mastery": {}, "words": {}, "stats": {}}
    t0 = _time.time()
    with mock.patch("time.time", return_value=t0):
        s = Session(c, load_config("config.yaml"), prog)
        s.start_lesson(1)
        _play(s)
    assert {e["stage"] for e in prog["mastery"].values()} == {1}, "same-sitting passes promoted"
    with mock.patch("time.time", return_value=t0 + 26 * 3600):
        s.start_lesson(2)
        warm = [st for st in s.steps if st.prior]
        assert warm, "no warm-up of yesterday's lines"
        assert s.steps[1] is warm[0], "a warm-up line was modelled first"
        _play(s)
        assert prog["mastery"][warm[0].key]["stage"] == 5   # 1 day survived -> 3 days
        assert s.start_review(5) >= 0
        assert not [k for k in prog["mastery"] if k.startswith("review:")]


def t_every_new_course_passes_the_gate():
    """tools/validate_course.py on every course except the two legacy ones
    (zh, ja), so a merged course cannot quietly fall below the bar."""
    sys.path.insert(0, str(ROOT / "tools"))
    from validate_course import validate
    from server.course import supported
    bad = {}
    for code in supported():
        if code in ("zh", "ja"):
            continue
        errors, _ = validate(code, strict=True)
        if errors:
            bad[code] = errors[:3]
    assert not bad, bad


def _with_fake_library(fn):
    """Run fn(course) on Spanish with a two-topic deck and two stories."""
    import types
    from unittest import mock
    from server import course as cp
    deck = types.SimpleNamespace(DECKS={1: [
        {"id": "a1-deck-home", "title": "Home", "title_native": "Casa",
         "words": [("el buzón", "", "mailbox"), ("la persiana", "", "window blind")]}]})
    q = {"q": "¿Qué abre Ana?", "q_en": "What does Ana open?", "a": "Abre la ventana.",
         "a_en": "She opens the window.", "keywords": ["ventana"], "min_chars": 5}
    text = ("Ana llega a casa tarde y busca la llave en su bolso negro. "
            "No la encuentra y llama a su hermano por teléfono. "
            "Su hermano baja, abre la puerta y los dos suben a la cocina. "
            "Ana abre la ventana porque hace mucho calor en el piso. "
            "Después cenan juntos y hablan del trabajo y de la familia.")
    lines = [(t.strip() + ".", "", "line") for t in text.split(".") if t.strip()]
    lib = types.SimpleNamespace(STORIES=[
        {"id": "a1-001", "band": 1, "title": "La llave", "title_en": "The key",
         "chunks": lines, "questions": [q, q]},
        {"id": "a1-002", "band": 1, "title": "Otra", "title_en": "Another",
         "chunks": lines, "questions": [q, q], "voices": 2}])
    real = cp.module_for

    def fake(lang, name):
        if lang == "es" and name == "deck":
            return deck
        if lang == "es" and name == "library":
            return lib
        return real(lang, name)
    with mock.patch.object(cp, "module_for", fake):
        return fn(Course("es"))


def t_library_story_plays_and_is_recorded():
    """A story is heard blind, asked about, followed line by line, asked
    again; finishing it records it and puts the lesson back."""
    def run(c):
        assert c.decks_by_band[1][0].deck and len(c.deck_words(1)) == 2
        assert c.topic("a1-deck-home"), "deck topics must be studyable"
        assert c.vocab_words(1) and "el buzón" not in {w.text for w in c.vocab_words(1)}, \
            "a deck word was injected into lessons"
        prog = {"lesson_id": 3, "completed": [], "mastery": {}, "words": {}, "stats": {}}
        s = Session(c, load_config("config.es.yaml"), prog)
        lesson_steps = len(s.steps)
        assert s.start_story("a1-001") == 5
        kinds = [st.kind for st in s.steps]
        assert kinds[:3] == ["info", "hear", "answer"], kinds
        assert s.steps[1].hide_text and len(s.steps[1].audio_parts) == 5
        assert kinds.count("listen") == 5 and kinds[-1] == "answer"
        assert s.state()["story"]["id"] == "a1-001"
        from server.pronunciation import simulated_score
        for _ in range(100):
            if s.mode != "library":
                break
            st = s.current()
            if st.kind in ("listen", "info", "hear"):
                s.advance_non_speech()
                continue
            ok = simulated_score(st.sample_text or st.text, "good", "es")
            ok.recognized = st.sample_text or st.text
            assert s.submit(ok).get("advanced"), f"stuck on {st.kind} {st.key}"
        assert prog["stories"] == ["a1-001"], prog.get("stories")
        assert s.mode == "lesson" and len(s.steps) == lesson_steps
        s.start_story("a1-002")
        assert s.steps[1].audio_voices[:2] == [0, 1], "a two-voice story alternates"
        return True
    assert _with_fake_library(run)


def t_fluency_report_earns_bands_in_order():
    """The earned level is the highest band whose targets are all met, with
    every band below it met too; the dimension labels go by course totals."""
    from server import fluency
    for code in ("es", "zh"):
        rep = fluency.report(Course(code))
        met = [r["met"] for r in rep["bands"]]
        n = rep["earned_index"]
        assert all(met[:n]) and (n == len(met) or not met[n]), (code, met, n)
        assert len(fluency.gaps(rep, 6)) == met.count(False)
        total = rep["bands"][-1]["words"]
        want = max([c for c, w in fluency.WORDS.items() if total >= w] or [0])
        assert rep["vocabulary"] == fluency.label(want), (code, rep["vocabulary"], total)
    assert fluency.listen_target("ar", 1) > fluency.listen_target("it", 1)


def main() -> int:
    for name, fn in sorted(globals().items()):
        if name.startswith("t_"):
            check(name[2:].replace("_", " "), fn)
    print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
    for name, exc in FAIL:
        print(f"  FAILED {name}: {exc}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
