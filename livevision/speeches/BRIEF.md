# Speech agent brief

You write **one** speech for the LiveVision HUD teleprompter. Your entry
in `manifest.json` (passed to you by `id`) gives the title, the topic, and
for originals a rhetorical model. Work only in `livevision/speeches/<id>/`.
Do not touch git, other speech folders or any code.

## Output

```
livevision/speeches/<id>/
  speech.md     the script, as it will be read aloud
  notes.md      word count, estimated runtime at 140 wpm, outline, sources
```

`speech.md` format, which reads well on a HUD:

- `# Title` and then `## I. Section name` headings, roughly 10 to 14 sections.
- Short paragraphs of 1 to 4 sentences. No bullet lists, tables or footnotes.
- Delivery cues on their own line in brackets, used sparingly: `[PAUSE]`,
  `[SLOW]`, `[BUILD]`, `[LET IT LAND]`.
- Write numbers the way they are spoken ("eight hundred and forty billion
  dollars", not "$840B").

## Originals (`kind: original`)

1. **Research first.** Use WebSearch/WebFetch for every statistic, date, bill,
   vote and quotation. It is October 2026, so check recent events rather than
   relying on memory. Never invent a number, a quote or a source. If you
   cannot verify something, cut it or frame it as opinion. Record every
   source in `notes.md`.
2. **Esketian speeches** (and any speech that touches it): read the source
   document at `manifest.json` → `esketian_source` in full. Stay faithful to
   its ideas and its own honesty: where the author marks something as
   analogy, interpretation or "held loosely", keep that framing.
3. **Length.** Target 16,800 words (two hours at 140 wpm). Minimum 15,000.
   Plan an outline in `notes.md` first with a word budget per section, then
   write `speech.md` section by section, appending as you go. Check with
   `wc -w` and keep writing until you clear the minimum. Length comes from
   more argument, story, evidence and history, never from repetition or
   filler.
4. **Rhetoric.** Use the rhetorical model named in your entry. Study what
   makes it work (anaphora, tricolon, antithesis, the build to a peroration,
   direct address, the concrete story that carries an abstract point) and use
   those techniques in your own words. Do not copy their sentences. Open with
   a hook and end with a peroration worth the two hours.
5. **Tone.** Persuasive and committed to its thesis, as a speech should be,
   but honest. Acknowledge the strongest counterargument and answer it.
   Argue about policies, institutions, economics and ideas, never about the
   inherent worth of an ethnic group, religion or sex. No dehumanizing
   language and no conspiracy tropes.

## Transcriptions (`kind: transcription`)

1. Use **public-domain texts only**: pre-1929 works, US government works, or
   translations old enough to be public domain. Fetch them from Wikisource,
   Project Gutenberg, the Avalon Project (Yale), the Library of Congress,
   the National Archives, the Miller Center or the American Presidency
   Project. Do not reconstruct texts from memory.
2. Transcribe **verbatim**. You may add a speech heading, a one-line context
   note in italics before each speech (date, place, occasion), and delivery
   cues on their own lines. Do not change the words.
3. Record the source URL and translator for each speech in `notes.md`.
4. Report the real runtime. If the public-domain material is shorter than
   two hours, say so in `notes.md`. Do not pad it.

## Finish

End by replying with: `id`, final word count, estimated runtime, and
anything you could not verify or complete.
