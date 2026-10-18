# Spanish course audit: can it get a learner to fluency?

*2026-10-18. Every number here is measured from the course as it runs
(`Course("es")` and a `Session` built for each of the 75 lessons), not from
the README. The benchmarks are the commonly cited ones: Cambridge's guided
learning hours per CEFR level, the US Foreign Service Institute's estimate
for Spanish, and published vocabulary-size estimates per level.*

## Verdict

**No, not on its own.** The course is a well-built speaking spine, and it
tours the whole A1–C2 grammar and function syllabus. But it delivers about
**25 hours** of practice. Learners usually need **600–1,200 hours** to reach
fluency. Reading input is about **3,000 words** and blind listening about
**6 minutes**, against hundreds of thousands of words and hundreds of hours.

A learner who finishes the course will have:
- solid A2 accuracy on the structures they drilled,
- roughly A2 vocabulary,
- recognition of the C1–C2 structures,
- nowhere near C1–C2 comprehension or fluency.

This is the same flaw the Japanese audit called finding 1: **the band labels
promise more than the volume can deliver.** The grammar for each band is
correctly placed. The exposure for each band is missing.

## The numbers

| band | lessons | est. time | spoken turns | free answers | dialogue words | reading words | blind-listening words | bank + lesson words |
|---|---|---|---|---|---|---|---|---|
| A1 | 15 | 3.8 h | 1,546 | 60 | 733 | 466 | 123 | 180 |
| A2 | 12 | 3.5 h | 1,324 | 48 | 692 | 424 | 115 | 168 |
| B1 | 12 | 3.9 h | 1,444 | 48 | 769 | 504 | 132 | 192 |
| B2 | 12 | 4.2 h | 1,448 | 48 | 809 | 521 | 129 | 192 |
| C1 | 12 | 5.0 h | 1,584 | 60 | 973 | 599 | 153 | 216 |
| C2 | 12 | 5.0 h | 1,576 | 60 | 1,025 | 576 | 142 | 216 |
| **total** | **75** | **≈25 h** | **8,922** | **324** | **5,001** | **3,090** | **794** | **1,164** |

The time estimate assumes each line is modelled once, said once, retried a
quarter of the time, plus a few seconds of overhead per step.

What the course is up against:

| | course | benchmark (cumulative) | share |
|---|---|---|---|
| guided hours to B2 | ≈19 h | 500–600 h (Cambridge) | ~3–4 % |
| guided hours to C2 | ≈25 h | 1,000–1,200 h (Cambridge); FSI: 600–750 class hours for professional proficiency | ~2–4 % |
| vocabulary at B2 | ≈1,160 taught items (~1,860 word forms seen) | ~3,250–3,750 lemmas (Milton) | ~33 % |
| vocabulary to follow native speech / text | — | ~6–7k / 8–9k word families (Nation) | ~15 % |
| reading input | 3,090 words | one A1 graded reader is ~5–10k words; extensive reading is ~a reader a week | under one book |
| blind listening | ~6 minutes | hundreds of hours | ≈0 |

For scale, Pimsleur's five Spanish levels are about 75 hours and claim
roughly intermediate-high speaking. This course is about a third of that.

## Skill by skill

### Speaking — the strongest part, but mostly repetition

**What an expert would approve:**
- The pronunciation gate never auto-advances.
- Graduated recall with a silent pause comes before each English cue.
- Free answers are about the learner themselves, not a character.
- Spoken summaries from C1, matching the DELE summary task.
- Register is a choice from lesson 2 (tú/usted, then vosotros, then formal register).

**What is missing:**
- **88 % of the 8,922 spoken turns are recalls of the same lines** (7,829
  recall steps). Only 324 turns, about 4 per lesson, are composed by the
  learner. Fluency is built by composing, so that ratio should move toward
  1 : 3, not 1 : 25.
- **There is no real conversation.** Every exchange is one question, one
  answer. Nothing replies to what the learner actually said, so turn-taking,
  follow-ups, clarifying and repair are never practised. B1 interaction
  descriptors require all four.
- **Spoken turns stay short at the top.** A C2 learner line averages about
  one sentence. DELE C1/C2 speaking tasks ask for 3–5 minute monologues and
  sustained debate.

### Listening — the weakest part

- **Blind listening is one line per lesson:** the last sentence of the
  passage, about 10 words. That is about 6 minutes of true listening across
  the whole course.
- Everywhere else, the line is printed while it plays. That trains reading
  along, not listening, which the engine's own docstring warns about.
- **All audio is browser speech synthesis.** It is clean, unhurried, a few
  voices, with no overlap, no background noise and no regional accents. C1
  lesson 60 teaches about voseo, but the learner never *hears* a Rioplatense
  speaker.
- **No listening is longer than one sentence.** B1 listening is defined by
  following a few minutes of connected speech; C1 by lectures and radio.

### Reading — present, but a sample rather than a diet

- Every lesson has a graded passage with a question. That is good practice,
  and the C1–C2 passages are well chosen: editorial, contract, science news.
- But **passages are 35–50 words at every band.** A2 should be about 150
  words, B1 about 300, B2 500+, and C1–C2 full articles. A C2 passage the
  same length as an A1 one is not C2 reading.
- **Reading volume** is under one graded reader for the whole course. Every
  extensive-reading study finds gains come from volume.

### Vocabulary

- The bank design is right: each band's bank is sized to what the lessons
  inject, so every word is met (tested).
- But 1,164 taught items is A2-sized, and the C1–C2 banks are 144 words
  each. Even with recognition-only words, B2 needs about three times that,
  and reading native texts needs about eight times.

## Grammar and topic gaps

Checked against a list of the core items in the Instituto Cervantes
curriculum (*Plan curricular*). "Learner says" is the first lesson where a
learner line uses the item.

**Update, 2026-10-18 — gaps closed.** Every gap below is now taught (the
last three rows in a second pass the same day): the learner says it in at least two of their own lines,
it has a pattern with its own `kind`, and it has a grammar page. Thirteen
lessons were revised in place and **one was added** (A1 lesson 5, *¿Cómo
es?*), so A1 now has 16 lessons, the course has **76**, and every lesson
from the old 5 onward moved up by one. All lesson numbers in this section
use the new numbering; "before" is the old finding renumbered to match.
The numbers table above predates this change.

| expected | item | before | now: learner says | grammar page | status |
|---|---|---|---|---|---|
| A1 | present progressive (estoy hablando) | L29, no page | **L5** (and L30 on the phone) | L5 | closed |
| A1 | weather (hace frío / llueve) | never | **L18** (weekend plans by the weather) | L18 | closed, at the start of A2 |
| A1 | days, months, dates, birthdays | incidental | **L20** (birthday plan: el catorce de marzo) | L20 | closed |
| A1 | describing people (alto, pelo, ojos) | L42 | **L5**; in the past at L24 (describing a thief) | L5, L24 | closed |
| A1 | possessives mi/tu/su, nuestro | L61, no page | **L5** (mi, tu, su); **L19** (nuestro) | L5, L19 | closed |
| A2 | **imperative** (tú, usted, negative) | incidental; negative never said | usted **L7** (siga, gire, cruce) and L15 (póngame); tú and negative **L20** (trae, no traigas, no llegues) | L7, L20 | closed |
| A2 | **por vs para** | L10, incidental | **L22** (para ver, pasamos por, por noche, para ti) | L22 | closed |
| A2 | possessive pronouns (el mío) | never | **L19** (la mía, la tuya, ¿es tuya?) | L19 | closed |
| A2 | soler, ordinals | L59 / L16 | soler **L17** (suelo desayunar en casa); ordinals **L8** (la segunda) and **L27** (la primera planta, el tercer piso) | L17; L8, L27 | closed |
| B1 | ser / estar meaning change (es listo / está listo) | never | **L34** (no eres aburrida, estás aburrida) | L34 | closed |
| B1 | accidental se (se me olvidó) | never | **L37** (se me ha perdido, se me olvidó) | L37 | closed |
| B1 | verbs of change (ponerse, volverse, hacerse) | L52 note only | **L38** (se ha vuelto, se ha hecho, se puso) | L38 | closed |
| B1 | future of probability (estará en casa) | L31 note only | **L31** (estará en un atasco, serán unos treinta mil) | L31 | closed |
| B2 | relatives el cual / cuyo / lo cual | never | **L50** (cuyos clientes, lo cual, sin la cual) | L50 | closed |
| B2 | diminutives (-ito) | incidental | **L51** (un ratito, un momentito, pequeñito) | L51 | closed |
| C2 | future subjunctive in legal texts (recognition) | never | **L69** (si el arrendatario abandonare...) — read aloud and explained, recognition only | L69 | closed |

Topics that had no lesson at all:
- ~~the phone, as its own lesson~~ — **L30** *Al teléfono en la oficina*:
  ¿dígame?, ¿de parte de quién?, está hablando por otra línea, taking a
  message.
- ~~emergencies: police, a theft, lost luggage, an urgent pharmacy~~ —
  **L24** *Repaso: en la comisaría* (reporting a theft, 112) and **L37**
  *Mi maleta no ha llegado* (the lost-luggage desk). The urgent pharmacy is
  **L8** (la farmacia de guardia on a Sunday).
- ~~renting a flat and the bank~~ — **L19** *Un piso de alquiler* (rent,
  bills, deposit) and **L31** (asking the bank for a loan).
- ~~appointments and dates~~ — dates at **L20**; booking a doctor's
  appointment by phone at **L25** (quería pedir cita, ¿le va bien...?).
- ~~the weather~~ — **L18**.
- ~~describing people and appearance~~ — **L5**, and **L24** in the past.
- ~~technology and the internet~~ — **L28**: the wifi won't connect, the
  password is wrong, no signal (no puedo conectarme, cargar, descargar).
  Still everyday trouble only; there is no lesson *about* technology.
- ~~food shopping by weight and quantity (un kilo de, media docena)~~ —
  **L15** *En el mercado*, which replaced the old bill-paying lesson; the
  bill moved into the restaurant review (L16).

What changed where:

| lesson | was | now teaches |
|---|---|---|
| L5 (new) | — | describing people, estar + gerund, mi / tu / su |
| L7 | asking the way | + giving directions with usted commands |
| L15 | *La cuenta, por favor* | *En el mercado*: quantities, ¿me pone? / póngame, prices to 100 |
| L18 | weekend plans | + the weather |
| L19 | *Mi casa* | *Un piso de alquiler*: renting, nuestro, el mío, comparisons |
| L20 | turning down a plan | + dates and birthdays, tú commands, negative commands |
| L22 | a trip, irregular preterites | + por and para |
| L24 | a story about bumping into a friend | *En la comisaría*: reporting a theft, describing the thief |
| L30 | handing over work, pronouns | *Al teléfono en la oficina*: a work call, pronouns, progressive |
| L31 | plans for five years' time | the bank and a loan, + the future of probability |
| L34 | feelings + subjunctive | + ser / estar meaning change |
| L37 | a missed flight, pluperfect | *Mi maleta no ha llegado*: lost luggage, + accidental se |
| L38 | reported speech | + verbs of change |
| L50 | subjunctive relatives | + cuyo, el cual, lo cual |
| L8 | is there a... ? | + the duty pharmacy, ordinals |
| L17 | routine, reflexives | + soler |
| L25 | at the doctor's | + booking the appointment by phone |
| L27 | hotel check-in | + ordinals for floors |
| L28 | complaining at the hotel | + the wifi, passwords, no signal |
| L51 | idioms | + diminutives |
| L69 | a lease read aloud | + the future subjunctive (recognition) |

Also still open from the first audit: there is **no sound-system module**
(vowels, r/rr, b=v, soft d, stress and written accents). Japanese gets a
kana module.

## What it would take — in priority order

1. **Be honest in the labels now (minutes).** Call the bands "A1 … C2
   grammar track" in the UI and README, or say plainly that the course covers
   each band's syllabus but not its hours.
2. **Turn existing content into listening (engine, about a day).**
   - Play the *whole* passage blind, not its last line.
   - Replay the whole dialogue blind once its lines are mastered.
   - At B2 and above, play natural speed with varied voices.
   This takes blind listening from about 6 to about 60 minutes with no new
   writing.
3. **Move speaking from recitation to composition (engine + content).**
   - 4–6 free prompts a lesson instead of 2.
   - A multi-turn role-play step: the LLM plays the other speaker in the
     lesson's scene and reacts to what was said. The `think` and `free`
     backends already call an OpenAI-compatible model.
   - From B2, a 1–2 minute monologue step graded on coverage, like the
     summary step.
4. **Fill the grammar gaps (content, about 10 lessons or lesson revisions)** —
   *done 2026-10-18: one new lesson and twenty revisions, see the gaps table.*
   - imperative, por/para, present progressive, weather, people description,
     possessives and dates at A1–A2;
   - ser/estar meaning change, accidental se, verbs of change and future of
     probability at B1;
   - relatives with cuyo / el cual at B2.
5. **Grow the passages with the band**: about 150 / 300 / 500 / 800 words
   from A2 to C2. Add 2–3 comprehension questions each, with the listening
   question on the full text.
6. **Grow the vocabulary to the benchmark.**
   - Build the B1–C2 banks from a Spanish frequency list to about 3,500
     lemmas by B2 and 5,000+ by C2.
   - Words beyond what a lesson can inject should be scheduled through the
     spaced-review queue, not left as an optional menu. That would repeat the
     Japanese mistake.
7. **Point outward for volume.** For each band, list graded readers, podcasts
   and series to add to the course. No app supplies 600 hours of input on its
   own, and the course should tell the learner where the rest comes from.
8. **Add native recordings** for at least the A1 dialogues and the C1 lesson
   on varieties, plus the sound-system module.

## Bottom line

As a structured speaking course the Spanish track is sound and complete in
*shape*: every band, every lesson has dialogue, drills, recall, free answers,
reading, listening, grammar and a scene. It is thin in *volume*.

It can get a disciplined learner speaking accurately at A2 and
**recognising** the structures of C1–C2. On its own it cannot get them to
B2, let alone fluency. Priorities 2 and 3 are mostly engine work and change
the most for the least writing. Priorities 4 and 5 are content. Priority 6
is the long one.
