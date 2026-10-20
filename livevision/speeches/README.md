# Speeches

Twenty-eight two-hour scripts for the LiveVision HUD teleprompter.

| # | category | count |
|---|---|---|
| 01 | satire: Israel as the 51st state | 1 |
| 02–06 | Esketian philosophy | 5 |
| 07–11 | American mental health | 5 |
| 12–16 | the AI economy and a working-class depression | 5 |
| 17–21 | falling birth rates | 5 |
| 22–28 | famous speeches, public-domain transcriptions | 7 |

## The loop

```
manifest.json ──► for each entry ──► spawn one agent with BRIEF.md + entry
                                         │
                       research ─► outline ─► write by section ─► wc -w check
                                         │
                         speeches/<id>/speech.md + notes.md
```

- `manifest.json`: one entry per speech (id, kind, title, topic brief and,
  for originals, the famous orator whose rhetoric to borrow).
- `BRIEF.md`: the shared contract every agent follows (format, length,
  research and honesty rules, transcription rules).
- Each agent works only in its own folder, so all 28 run in parallel.

To redo one speech, give an agent this prompt:

> Read `livevision/speeches/BRIEF.md` and the entry `<id>` in
> `livevision/speeches/manifest.json`, then write that speech.

Each speech's `notes.md` has its word count, runtime at 140 wpm, outline
and sources.
