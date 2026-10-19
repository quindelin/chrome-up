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
