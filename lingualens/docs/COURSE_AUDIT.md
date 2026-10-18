# LinguaLens course audit — Japanese, and how Spanish was built from it

*2026-10-18. Measured against the running course data (`Course("ja")`), not
the README. Every number below can be reproduced from `server/course/ja/`.*

## Verdict

The **method** is sound. A second-language-acquisition specialist would
approve of it. Production is gated, retrieval is spaced, the learner has to
answer in their own words, and listening is tested blind. The **content**
does not deliver what the labels promise. The course calls itself JLPT N5 → N1+.
What it actually teaches is a solid polite-register survival course, roughly
N5–N4 grammar with a business-Japanese veneer at the top. The four fixes that
matter most are honest band labels, plain-form (casual) speech, finishing the
kana, and a word bank the lessons actually reach.

## What an expert would sign off on

| practice | where | why it is right |
|---|---|---|
| Retrieval, not re-reading | recall rounds with a 5 s `anticipation_seconds` blank before the cue | the testing effect: recall attempts build memory, exposure doesn't |
| Expanding spaced review out to 18 months | `drills.STAGE_INTERVALS` | matches the spacing literature, and long gaps make a pass informative |
| A pronunciation gate that never auto-advances, with fading support | `max_attempts: 0`, slow replay and reveal after 2 misses | mastery learning plus scaffolding that withdraws |
| Free response every lesson | `freeform.py`, 2 per lesson | pushed output (Swain): composing ≠ repeating |
| Blind listening | `_hearing_steps`, voice rotation, natural rate | trains decoding a signal, not reading along |
| Scene before the dialogue | `scenes.py` | context, and in Japanese the register, before the first word |
| Grammar pages with `contrast` and `watch` | `grammar*.py` | names the error learners actually make |
| Placement at the first band you *can't* do | `placement.py` | errs low, which protects motivation |
| Kanji drawn from the lesson's own words | `kanji.py` | characters anchored to known words stick |

## Findings, most serious first

### 1. The JLPT labels overclaim — high

| band | lessons | what the grammar pages actually teach |
|---|---|---|
| N5 | 1–15 | survival phrases (fine) |
| N4 | 16–25 | shopping, time, 〜と思う (fine) |
| "N3" | 26–37 | ごろ/ぐらい (N5), のほうが (N4/N5), 〜たことがある (N4) |
| "N2" | 38–49 | そうだ hearsay, ので, passive, causative, はず, たら/ば/なら, ても, 予定, てしまう: **all N4** |
| N1 / N1+ | 50–73 | some real N2/N1 (こそ, にもかかわらず), mostly polite business set phrases |

73 lessons and 7,498 characters of dialogue cannot reach N1. Japanese is an
FSI Category IV language (about 2,200 classroom hours). N1 assumes about
10,000 words and 2,000 kanji. At 3 kanji per lesson the course meets about
220. A learner who trusts the "N2" label and sits the exam will fail it, and
that does more harm than an honest "N4" label would.

**Fix:** relabel the bands by what is taught (N5, N4, N4+, N3 preview…), or
expand the middle bands. Do not ship "N1+" on a 12-lesson band.

### 2. The learner never speaks casual Japanese — high

219 of 223 learner lines end in です/ます or a humbler form. Plain form is
N5/N4 grammar. Every subordinate clause needs it (〜と思う, 〜たことがある,
〜ので all attach to it), and you cannot talk to a friend without it. Genki I
introduces it around chapter 8. The free-response grader is even told to
expect です/ます. A learner who finishes this course talks to friends like a
hotel clerk.

**Fix:** from N4 on, write friend scenes in plain form and make the learner
produce it. Have the grader check register against the scene, not against
です/ます.

### 3. The word bank is ~93 % unreachable from the lessons — high

`vocab.inject_per_lesson: 4` walks each band's bank in order:

| band | bank | reached by lessons |
|---|---|---|
| N5 | 341 | 60 |
| N4 | 484 | 40 |
| N3 | 708 | 48 |
| N2 | 904 | 48 |
| N1 | 924 | 48 |
| N1+ | 1,013 | 48 |
| **total** | **4,374** | **292 (6.7 %)** |

The other 4,082 words only show up if the learner opens a topic session
from the menu, and then they come as a bare list. The course's own header
says words are "introduced inside that conversation, never in lists first".

**Fix:** either size the banks to the lessons, or schedule topic sessions
through the review queue so they become due rather than optional. In both
cases, put each word into a sentence frame (see finding 5).

### 4. Kana instruction stops at り — high, trivial to fix

`kana: {per_lesson: 5, through_lesson: 8}` shows 40 of the 104 rows. る れ ろ
わ を ん, every voiced kana (が ざ だ ば ぱ) and every contracted sound (きゃ
しゅ) are never taught. Lesson 1 already uses ございます and げんき.

**Fix:** set `through_lesson: 21` (or `per_lesson: 13`). It is one line in
`config.ja.yaml` and the `LANG_DEFAULTS` entry.

### 5. Beginners get no substitution drills of their own — medium

All 25 N5/N4 lessons have `patterns: []`. They all fall back to the same five
generic frames (`drills.BASE_PATTERNS["ja"]`), so lesson 3 and lesson 24
drill the same {x}をください. Those frames are mostly untagged, so
`drills.recombine` (old words in new frames, i.e. interleaving) never runs
for a beginner. Beginners are exactly where pattern practice pays off most.

**Fix:** author 2+ patterns with a `kind` for every N5/N4 lesson.

### 6. The learner hears the target structure more than they say it — medium

In the N3/N2 lessons the point of the lesson usually appears in one learner
line. The other uses are in the other speaker's lines. For example, lesson
39, "Giving a reason", never has the learner say ので. Recall rounds repeat
that one line three times, but always in the same frame. Both Pimsleur and
the output research say the learner has to say it, several ways.

**Fix:** an authoring rule, "≥2 learner lines use the point", plus a check
in `grammar.check()`.

### 7. Pitch accent is invisible — medium

Nothing teaches it, Azure ja-JP does not score it, and the `min_tone_score`
on the N5/N4 gate never fires. Experts disagree on how much to drill pitch
accent. They agree that a learner should at least *know* it exists (箸/橋,
雨/飴) and should hear native models. Browser TTS pitch accent is uneven.

**Fix:** a short N5 note with minimal pairs. Record native audio for the N5
dialogues; that is about 90 lines.

### 8. Little input, and the learner plays a character — medium

All the dialogue in the course adds up to 7,500 characters, plus one short
passage per lesson. That is a skeleton, not the volume of input that
acquisition needs. Separately, the learner says マイクです and reads about Mike
instead of saying their own name. Personal relevance is the cheapest
retention lever available.

**Fix:** have pattern and free-response steps ask for the learner's own
facts. Link graded readers (e.g. Tadoku) per band.

### 9. Smaller things

- The blind-listening note read 只听，不看 (Chinese) on the Japanese course.
  **Fixed in this pass:** each course now has its own note (`engine._HEAR_NOTE`).
- `tests/smoke.py` builds sessions with `load_config("ja")`. That is a path,
  not a language, so Japanese is tested on the built-in defaults rather than
  `config.ja.yaml`. The Spanish tests use the real file; the old helper is
  unchanged.

## Priority order

1. Kana `through_lesson` (5 minutes)
2. Honest band labels (an afternoon)
3. N5/N4 patterns with kinds (a few days of authoring)
4. A plain-form track from N4 (a unit)
5. Schedule the word bank through review (code, ~a day)
6. Native audio for N5, and a pitch-accent note

---

## Spanish: built against this audit

`./run.sh es`, or pick Español in the course switcher. CEFR A1 is written:
3 units × 5 lessons, 90 bank words, 30 free-response prompts, 15 passages,
a grammar page and a scene for every lesson.

| audit finding | what the Spanish course does instead |
|---|---|
| 1 overclaiming | it is labelled A1, and A1 is what it covers |
| 2 one register | tú and usted are produced from lesson 2; lesson 5 switches between them mid-scene |
| 3 unreachable bank | 90 words, 6 per lesson × 15 lessons: every word reached once (tested) |
| 5 no beginner patterns | 2 tagged patterns in every lesson; old words recombine into lessons 7, 9, 10, 14, 15 |
| 6 learner doesn't say it | the learner says the target structure in their own lines (rule in `a1.py`) |
| 8 learner plays a character | free-response prompts ask about *you*; the notes say to drill your own name |
| (variety) | one standard, Peninsular (es-ES voice and scorer); Latin American forms go in notes (boleto, jugo, derecho) |

Engine changes needed for the first language written with spaces between words:
- Answer relevance and coverage now compare **words**, not letters. Any two
  Spanish sentences share most of their letters, so letter matching passed
  almost anything. Accents are folded, because "si" for "sí" is the
  transcriber's fault, not the learner's. A small lemma table matches
  soy/eres/es, so "Soy de Canadá" counts as an answer to "¿De dónde eres?".
- iFlytek is never used for Spanish (it has no Spanish evaluation). Before
  this, `auto` with Chinese keys set would have scored Spanish as Chinese.
- Drill, grader, think-mode and UI fallbacks no longer default to Mandarin.
- Word ownership across bands follows the course's own level order, because
  CEFR counts up and JLPT counts down. Mandarin and Japanese ownership was
  checked and is unchanged.

**Still open:**
- A2 and up are not written.
- There is no sound-system module (the five vowels, r/rr, b=v, the soft d,
  stress and written accents). Those are covered only in notes, where
  Japanese gets a kana module.
- Recombination reaches only 5 of 15 lessons, because slot kinds rarely
  repeat this early.
- Vosotros is recognised but not taught.
- A native-speaker editor should review the lines before learners use them.
