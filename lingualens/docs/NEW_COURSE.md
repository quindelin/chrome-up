# Building a new LinguaLens course

This is the procedure one agent follows to build one language, from nothing
to a merged CEFR A1–C2 course. Several agents can do it in parallel, each in
its own git worktree and branch, because **a course touches only its own
files**. The gate is `tools/validate_course.py <code>`: a course is done when
it passes.

The reference is Spanish (`server/course/es/`, `config.es.yaml`). Copy its
shape. Read first:
[LEARNING_SCIENCE.md](LEARNING_SCIENCE.md), [SPANISH_AUDIT.md](SPANISH_AUDIT.md)
and [COURSE_AUDIT.md](COURSE_AUDIT.md). They explain the mistakes the rules
below exist to prevent.

## 1. The files you create, and the only files you touch

```
lingualens/
├── config.<code>.yaml                 copy config.es.yaml; set language, locale, storage path
├── docs/<CODE>_COURSE.md              your decisions, syllabus coverage, lines for human review
└── server/course/<code>/
    ├── __init__.py                    copy es/__init__.py; change only its docstring, LABEL and SPEECH_LANG
    ├── meta.py                        the language, for the engine (fields below)
    ├── a1.py … c2.py                  one band each: LEVEL + SCENES, PROMPTS, GRAMMAR, PASSAGES (+ SUMMARIES at C1/C2)
    ├── vocab_a1.py … vocab_c2.py      one word bank per band
    ├── scenes.py, freeform.py         A1's scenes and prompts (later bands keep theirs in the band file)
    ├── grammar.py, readings.py        merge the band files; copy es versions, change the A1 data
    ├── summaries.py                   copy es/summaries.py unchanged
    ├── deck.py, deck_<band>.py        the rest of each band's words  (EXPAND_COURSE.md)
    └── library.py, library_<band>.py  graded stories, the hours of input (EXPAND_COURSE.md)
```

Passing this playbook gives a course its grammar, A1–C2. It does not give it
the vocabulary or listening volume a band needs. That is the second stage,
[EXPAND_COURSE.md](EXPAND_COURSE.md), measured against
[FLUENCY_TARGETS.md](FLUENCY_TARGETS.md).

**Do not edit any other file.** If your language needs an engine change, stop
and report what is needed instead of making it. Examples: right-to-left
display, word segmentation for a language without spaces, a new script in
the reading line. Another agent may be building another language in
parallel, and a shared-file edit is a merge conflict for everyone.

## 2. Decide, then write it down

Record each decision at the top of `docs/<CODE>_COURSE.md`:

- **Code and variety.** Pick one standard and stay in it, like Spanish's
  Peninsular. Give alternatives in vocab notes, never mixed into lines.
  Examples: pt = Brazilian Portuguese; ar = Modern Standard Arabic, or say
  which dialect; zh-TW is a different course.
- **Ladder.** CEFR A1–C2, as bands 1–6 (A1 = 1). Lesson ids run 1..N without
  gaps. Name the official syllabus you follow per band:
  - fr: CECRL / DELF–DALF referentials
  - de: Profile Deutsch, Goethe
  - it: Profilo della lingua italiana
  - pt: QuaREPE / Celpe-Bras
  - ru: TORFL / ТРКИ
  - ko: TOPIK, mapped to CEFR
  - ar: ACTFL / CEFR-aligned MSA syllabus
  - hi: CEFR-aligned
- **Reading line** (the `reading` slot shown above each line): empty for
  Latin scripts, as in Spanish. Otherwise it is the learner's crutch:
  romanisation for Hindi or Arabic, stress marks for Russian, Revised
  Romanisation for Korean at A1–A2. Fade it out with `ui.reading_by_level`.
- **Speech locale** for TTS and scoring (`SPEECH_LANG`, `pronunciation.language`).
  Check that Azure AI Speech pronunciation assessment supports it, and note
  it if not.
- **TOKENS:** `spaced` if the language writes spaces between words (most
  do), `char` only for scripts without spaces.

## 3. `meta.py` fields

| field | required | what it is |
|---|---|---|
| `CODE`, `NAME`, `NATIVE` | yes | `"fr"`, `"French"`, `"Français"` |
| `ALIASES` | yes | other names and locale tags that should map to the course |
| `BAND_LABEL` | yes | `"CEFR"` |
| `TOKENS` | yes | `"spaced"` or `"char"` |
| `SPEECH_LANG` | yes | BCP-47, e.g. `"fr-FR"` |
| `FUNCTION_WORDS` | yes if spaced | articles, clitics, prepositions, courtesy words: ignored when checking whether an answer is on topic |
| `LEMMAS` | recommended | `{lemma: "form form …"}` for the irregular verbs a question and its answer share (es: ser, estar, ir, tener, hacer) |
| `FILLERS` | yes | hesitation sounds for the fluency check. They are matched without spaces, so nothing that can hide inside a real word. |
| `UI` | yes | `read`, `literacy`, `hearing`, `writing`, `vocab` labels in the language |
| `NOTES` | yes | `hear` ("just listen") and `write` ("in your own words") step notes |
| `GRADER_PROMPT` | yes | the free-answer grader. Copy Spanish's and change the grammar points to check. |
| `THINK_PROMPT` | yes | the English → target-language translator |
| `PHRASEBOOK` | optional | offline translator: `lexicon`, `phrases`, `patterns` |
| `DEFAULTS` | yes | config defaults; copy Spanish's and change the locale, storage path and `seconds_per_char` |
| `normalize_spoken(text)` | recommended | spell out digits and symbols the way dictation writes them (es: "12 €" → "doce euros") |
| `word_key(word)` | optional | count agreement variants as one word (es: un / una / uno) |

`meta.py` is loaded on its own, so use plain data and pure functions, with
no imports from `server`.

## 4. What every lesson has

These are the authoring rules, the same as `es/a1.py`, and the validator
checks them:

- **Dialogue:** 8–10 turns, of which **3 or more are the learner's** lines.
  The learner says the lesson's target structure in at least two of them.
- **Drills:** **2 or more substitution patterns**, each with a `{x}` slot and
  a narrow `kind`. Slot values carry their own article or case. Kinds are
  shared across lessons only where any value really fits any frame of that
  kind.
- **Free response:** **4 prompts** about the learner, never about a character.
- **Scene:** one sentence on who and where, which also makes the register
  (tú / usted, du / Sie, ты / вы…) guessable.
- **Grammar page:** `point`, `formula`, 1–2 `examples`, `contrast`, and
  `watch` (the mistake an English speaker actually makes).
- **Passage:** 3–7 chunks, read aloud, with **two questions**. The second
  must be answerable from the **last chunk alone**, because the listening
  step plays only that one.
- **C1–C2:** a spoken summary (`SUMMARIES`) for every lesson.
- **Hear it first:** never ask for a word that has not been heard earlier in
  the lesson. The engine inserts a model if you do, but write it so it
  doesn't have to.
- **Speakable:** no vocab item that is a formula ("+ subjunctive"), and no
  stage directions in the other speaker's lines (TTS reads them aloud).

Bands: A1 has 15–16 lessons, and A2–C2 have 12 each. Units of 4–5 lessons,
with the last lesson of each unit a review.

**Word banks:** each band's bank is exactly lessons × `inject_by_band[band]`
(A1 6, A2 8, B1–B2 10, C1–C2 12). No word repeats another band's bank or
any lesson's own vocab list. Nouns carry their article or gender.

**Coverage:** keep a table in `docs/<CODE>_COURSE.md` listing the official
syllabus's core grammar per band and the lesson that teaches each item.
Every core item needs a lesson where the learner produces it.

## 5. Work in this order

1. `meta.py`, `config.<code>.yaml`, `__init__.py`; then A1 complete.
2. Run the gate (§6). Commit A1: `lingualens <code>: A1`.
3. A2 → C2, one band at a time. Gate, then commit each band.
4. **Native-speaker review pass.** Reread every band as a demanding native
   teacher would: naturalness, register consistency, one variety
   throughout, idioms that really exist. Fix what you can. List anything
   doubtful under "For human review" in `docs/<CODE>_COURSE.md`, quoting
   the line.
5. Final report:
   - lessons and bank size;
   - validator output;
   - the coverage table's gaps;
   - the human-review list;
   - anything that needed an engine change.

## 6. The gate

```bash
cd lingualens
.venv/bin/python tools/validate_course.py <code>     # must say PASS
.venv/bin/python tests/smoke.py                      # must stay green
```
