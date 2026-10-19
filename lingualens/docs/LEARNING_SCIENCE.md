# How LinguaLens schedules practice, and why

*2026-10-19. This covers the review schedule: what comes back, when, and how
often. Each rule below is enforced in `server/engine.py` and
`server/drills.py`, and `tests/smoke.py` checks it.*

## The evidence it is built on

| finding | source | what it means here |
|---|---|---|
| Retrieving a word again after you first get it right greatly improves recall a week later. Re-studying it does not. | Karpicke & Roediger 2008, *Science* | Recall stays the core activity, and a line is re-tested after its first success. |
| The best gap between sessions grows with how long you need to remember. Packing practice into one sitting is inefficient. | Cepeda et al. 2008, *Psychological Science* | Review gaps grow from minutes to months, and the important repetitions happen on later days. |
| Recall a week later was 20% after one learning session, but 80% after three spaced relearning sessions. | Rawson, Vaughn, Walsh & Dunlosky 2018 | Lines from earlier lessons come back on later days, automatically. |
| Extra correct recalls in the first session help at first. The advantage disappears once spaced relearning follows (the "relearning override"). | Rawson & Dunlosky 2011; Vaughn, Dunlosky & Rawson 2016 | Recalling a line many times today adds little; recalling it again tomorrow adds a lot. |
| A word has to have been heard before recalling it is retrieval and not guessing. | Pimsleur's graduated interval recall | Nothing is asked for before it has been modelled. |

## The rules

1. **Hear it before you are asked for it.** Every character (zh, ja) or word
   (es) in a recall line has been heard earlier in the lesson. If not, the
   line is played and repeated first. (`_model_before_recall`)
2. **Within a lesson: two delayed recalls, then the line drops out.** The
   end-of-lesson review runs as rounds:
   - **Round 1** always runs.
   - **Round 2** always runs, because re-testing after a first success is the
     Karpicke & Roediger effect.
   - **Round 3** only brings back lines that have not yet had
     `recall.criterion` (2) delayed, first-try correct recalls.

   A learner who is getting it right skips round 3. One who is struggling
   gets exactly the lines they missed.
3. **Across days: each lesson opens with a warm-up.** Up to `recall.warmup`
   (6) lines from earlier lessons that are due today, most overdue first,
   are asked for with no model first. This replaces the old opt-in Review
   button, which a learner had to remember to press. The button still works.
4. **A line only moves up the review ladder when it was due.** The ladder:
   5 min → 30 min → 2 h → 1 day → 3 days → 1 week → 16 days → 5 weeks →
   3 months → 8 months → 18 months.
   - Correct answers within the same sitting do not count; previously, five
     passes in a 20-minute lesson pushed a line to a multi-day gap without
     ever testing it after a delay.
   - A correct answer after a long gap credits the gap: a line recalled
     after a day comes back in three days.
   - A miss moves the line down two rungs.
5. **One line, one schedule.** A review updates the line's own entry. The
   old Review button wrote copies under `review:<text>`, so the original
   stayed due forever. A line that appears in two lessons shares one
   schedule.

## Effect

When every answer is right first time, lessons are about 19% shorter. For
example, HSK 1 lesson 1 goes from 84 steps to 68, and Spanish lesson 30
from 202 to 164. That time is spent on the next day's warm-up instead,
which is where the research says it does the most.

## Not done yet

- **A failed line is retried at once.** That is the pronunciation gate's
  rule. Moving a missed line a few items later would turn the retry into a
  delayed recall (Pyc & Rawson 2009 on the effort of retrieval). That needs
  a decision about the gate.
- **The ladder is fixed, not per learner.** An adaptive scheduler such as
  FSRS fits each person's forgetting rate, but needs review history to fit
  against.
