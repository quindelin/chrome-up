# Fluency targets: what "A1–C2" has to mean

A course used to call itself A1–C2 because its lessons covered the A1–C2
grammar syllabus. That says nothing about exposure. The first eight new
courses, and Spanish, each had 76 lessons, about 1,200 words and about 35
hours of material. That is A1-sized vocabulary and a few hours of listening,
whatever the syllabus says.

So the course now reports three numbers, and the app shows all three:

```
grammar C2 · words A1 · listening pre-A1
```

- **grammar** is what the lessons cover.
- **words** is the vocabulary the course teaches.
- **listening** is the graded input it holds.

`server/fluency.py` computes them. The gate (`tools/validate_course.py <code>
--fluency [BAND]`) fails a course whose content does not back up a band.

## The targets (cumulative)

| CEFR | words taught | running words of graded input (FSI cat. 1) | deck words met in a story |
|---|---|---|---|
| A1 | 600   | 5,000   | 80% |
| A2 | 1,200 | 20,000  | 80% |
| B1 | 2,500 | 60,000  | 80% |
| B2 | 4,000 | 130,000 | 80% |
| C1 | 6,000 | 230,000 | 80% |
| C2 | 8,000 | 350,000 | 80% |

- **Words taught** = lesson vocab + bank (`vocab_*.py`) + deck (`deck.py`).
- **Graded input** = lesson passages + library stories (`library.py`), in
  running words. An unspaced script counts characters ÷ `CHARS_PER_WORD`
  (meta.py, default 1.7).
- **Scaling by language difficulty:** the input targets are multiplied by
  the language's FSI category (`FSI_CATEGORY` in meta.py, or the table in
  fluency.py):

  | FSI category | languages | factor |
  |---|---|---|
  | 1 | es, fr, it, pt | 1.0 |
  | 2 | de | 1.15 |
  | 3 | ru, hi | 1.3 |
  | 4 | ar, ko, zh, ja | 1.6 |

- **The earned level** is the highest band whose three targets are all met,
  with every band below it met too.

## Where the numbers come from

- **Vocabulary per band:** Milton & Alexiou (2009) and Milton (2010) measured
  learners at each CEFR level. Roughly: A2 is under 2,000 lemmas, B1 is
  2,000–3,000, B2 is 3,000–4,000, and C1–C2 is 4,000–8,000+. The numbers vary
  by language and test. These targets sit at the generous end, because
  speaking and listening need more than recognition.
- **Listening coverage:** Nation (2006) puts comfortable comprehension of
  speech at 98% word coverage, which takes 6,000–7,000 word families. That
  coverage only comes from volume of input. The input targets add up to
  roughly 45 hours of unique audio at C2 at 130 words a minute. Hearing each
  story twice (blind first, then read-along) brings that to about 90 hours.
- **Study hours:** FSI's estimates to professional working proficiency
  (about B2/C1) are about 600–750 classroom hours for category 1 languages
  and about 2,200 for category 4. The FSI factor above is a deliberately
  smaller ratio. The app is the structured core, and real-world input
  (conversation, media, the glasses out in the world) supplies the rest.
- **Context:** a word learned only as a flashcard is half learned. Learning
  from meaningful input plus deliberate study beats either alone
  (Nation & Webb 2011). That is why deck words must also occur in stories.

## Honest limits

- **Content can earn a band; only a learner can reach it.** A course that
  passes `--fluency C2` holds enough to get there. The learner still has to
  do it, and real conversation still matters.
- **Generated text needs native review.** The agents write the decks and
  stories, and a reviewer pass catches what it can. Every
  `docs/<CODE>_COURSE.md` keeps a "For human review" list, which is the work
  a native-speaker teacher should do before the course is sold as anything.
- **"Met in a story" is matched loosely.** It uses a folded word prefix
  (with the course's `word_key`), not a lemmatizer. It is a floor, not a
  linguistic analysis.
- **HSK and JLPT map to CEFR by position.** HSK 1 ≈ A1 … HSK 6 ≈ C1/C2 and
  N5 ≈ A1 … N1 ≈ C1. This is an approximation; the official equivalences are
  disputed.
