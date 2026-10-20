# Expanding a course to the fluency targets

[FLUENCY_TARGETS.md](FLUENCY_TARGETS.md) says what each band needs. This is
the procedure one agent follows to get its course there, **one band per
wave**. Each wave stops at a checkpoint where the orchestrator gates and
spot-checks every language before sending the next band. That way a
mistake in this playbook is caught at A1, not after 8,000 words in eleven
languages.

## 1. Files you touch

```
lingualens/server/course/<code>/
├── deck.py            DECKS = {band: [topic, ...]}      merges deck_<band>.py
├── deck_<band>.py     one band's extra words, by topic (a1, a2 … or hsk1, n5 …)
├── library.py         STORIES = [story, ...]             merges library_<band>.py
├── library_<band>.py  one band's graded stories
lingualens/docs/<CODE>_COURSE.md   add a "Deck and library" section + review list
```

You may also fix your own course's lesson files when the gate or the
reviewer finds a problem in them.

**Never edit shared engine files** (server/*.py, web, iOS, tools, tests,
other courses). If you need an engine change, stop and report it.

`deck.py` and `library.py` only merge the band files, the same way
`readings.py` merges band passages: import each `deck_<band>` /
`library_<band>` that exists and combine. A missing band file is fine.

## 2. The deck: the rest of each band's vocabulary

```python
DECKS = {1: [
    {"id": "a1-deck-home", "title": "At home", "title_native": "En casa",
     "words": [("la ventana", "", "window"), ...]},
]}
```

- **Size:** cumulative words taught (lesson vocab + bank + deck) must reach
  the band's target: A1 600, A2 1,200, B1 2,500, B2 4,000, C1 6,000,
  C2 8,000. The gate prints how many you still need.
- **Choose by frequency.** Take the most frequent general words of the
  language that the course does not teach yet, in rough frequency order,
  and put them in the band where a learner needs them. Use your knowledge
  of the language's frequency profile, but do not paste a published
  frequency list wholesale. Leave out proper nouns. Multi-word expressions
  (collocations, set phrases) may be at most 15% of a band.
- **Same entry format as the bank:** nouns with their article or gender;
  `reading` filled the way the course's reading rules say for that band
  (romanisation, stress marks, harakat…); a short, accurate English gloss.
- **Topics** of 15–30 words with a real theme. Ids look like
  `<band>-deck-<slug>` and are unique across the course.
- **No duplicates.** A word in the bank or in any lesson's vocab must not
  appear again; the gate checks this.

## 3. The library: graded stories, the hours of input

```python
STORIES = [
    {"id": "a1-001", "band": 1, "title": "La llave", "title_en": "The key",
     "voices": 1,                      # 2 = a dialogue, speakers alternate by line
     "chunks": [("Ana llega a casa tarde.", "", "Ana gets home late."), ...],
     "questions": [gist, detail, ...]},  # same shape as readings.py questions
]
```

The engine plays a story like this:

1. heard blind (nothing on screen);
2. the gist question (`questions[0]`), answered aloud;
3. followed line by line with the text and English shown;
4. the remaining questions.

So write it like this:

- **Volume:** cumulative running words (lesson passages + stories) must
  reach the band's input target × your FSI factor (see FLUENCY_TARGETS.md).
  The gate prints the shortfall.
- **Length per story** (running words): A1 50–160, A2 100–260, B1 180–420,
  B2 300–650, C1 400–950, C2 500–1,200. One sentence per chunk, under about
  25 words.
- **Comprehensible:** at least 95% of running words are words taught at or
  below this band (lessons, bank, deck), plus names. At most three
  untaught words per story, each guessable from context.
- **Recycle the deck:** each story uses 4 or more deck words of its band.
  Across the band, every deck word should occur in a story, and the gate
  requires 80% of deck words to. Aim for each word appearing 2–3 times
  across the library; that is how the word sticks.
- **Variety:** narrative, dialogue (`voices: 2`), messages and voicemails,
  announcements, instructions, news-style reports from B1, opinion and
  argument from B2, and lectures, interviews and essays from C1. Recurring
  characters are good. So is the course's culture: real places, customs and
  food, in the course's one variety.
- **Questions:** the first is gist and answerable after one blind hearing;
  the rest are detail. `q`, `q_en`, a sample answer `a` with `a_en`,
  `keywords` (1–3 content words from the answer) and `min_chars`, all in the
  target language.
- **Register** follows the scene, as in the lessons. Never mix varieties.
- **Story ids** are `<band>-<nnn>`, unique.

## 4. One wave = one band

1. `git merge main` into your branch, so you have the engine, the gate and
   this playbook. Resolve any conflicts in your own files only.
2. Run `.venv/bin/python tools/validate_course.py <code> --fluency <BAND>`
   from `lingualens/`. Read the table: it says exactly how many words and
   running words this band still needs.
3. Write the band's deck file, then its library file. Write in batches of
   10–20 stories, re-running the gate as you go.
4. **Reviewer pass.** When the gate passes, start one reviewer subagent (the
   Agent tool, fresh context). Tell it to read this band's deck and library
   files as a demanding native-speaker teacher and list every error with
   the exact line: wrong gloss, unnatural phrasing, wrong gender, article,
   case or register, mixed variety, a story above the band's level, a
   question whose answer is not in the story. Fix every real error. Add
   anything doubtful to "For human review" in `docs/<CODE>_COURSE.md`,
   quoting the line.
5. Gate again: `validate_course.py <code> --fluency <BAND>` must say PASS,
   and `.venv/bin/python tests/smoke.py` must stay green.
6. Commit: `lingualens <code>: <BAND> deck + library`.
7. **Stop and report.** Give:
   - the gate's fluency table;
   - the counts you added (words, stories, running words);
   - three sample stories' titles;
   - the reviewer's error count and what you fixed;
   - the new human-review lines;
   - any engine change you need.

   Do not start the next band until you are told to. Do not merge into main
   or push.

## 5. For legacy courses (zh, ja)

Before your first band, make the course pass the base gate:

```bash
.venv/bin/python tools/validate_course.py <code> --lenient
```

That means tagged drill kinds, no duplicate words, and two passage questions
per lesson. Commit that on its own first.
