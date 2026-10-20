# Notes: 22-lincoln, Abraham Lincoln: The Collected Great Speeches

Kind: transcription. All seven texts are by Abraham Lincoln (died 1865), in English, so no translator applies. Each is public domain: pre-1929 publication, and the two inaugurals are also US government works.

## Length and runtime

- `wc -w speech.md`: 19,341 words, counting headings, context lines and cues.
- Spoken text only: 19,133 words.
- Estimated runtime at 140 wpm: about 137 minutes (2 hours 17 minutes). That clears the two-hour target, and nothing was padded.

| Speech | Words (whitespace count) | Approx. minutes at 140 wpm |
|---|---|---|
| Lyceum Address, 1838 | 3,539 | 25 |
| House Divided, 1858 | 3,152 | 23 |
| Cooper Union, 1860 | 7,715 | 55 |
| Farewell at Springfield, 1861 | 150 | 1 |
| First Inaugural, 1861 | 3,620 | 26 |
| Gettysburg Address (Bliss copy), 1863 | 264 (272 when dashed words are counted separately) | 2 |
| Second Inaugural, 1865 | 693 | 5 |

## Outline (speech.md sections)

I–II. Lyceum Address (split at "While ever a state of feeling such as this...")
III–IV. A House Divided (split at "It should not be overlooked that...")
V. Cooper Union: what the fathers understood (opening through the historical argument)
VI. Cooper Union: to the Southern people (from "And now, if they would listen...")
VII. Cooper Union: to Republicans (from "A few words now to Republicans.")
VIII. Farewell at Springfield
IX–X. First Inaugural (split at "All profess to be content in the Union...")
XI. Gettysburg Address, Bliss copy
XII. Second Inaugural

## Sources (fetched October 2026 through the Wikisource API)

1. Lyceum Address: https://en.wikisource.org/wiki/Life_and_Works_of_Abraham_Lincoln/Volume_3/The_Perpetuation_of_Our_Political_Institutions (Marion Mills Miller, ed., *Life and Works of Abraham Lincoln*, 1907).
2. House Divided: https://en.wikisource.org/wiki/Life_and_Works_of_Abraham_Lincoln/Volume_4/A_House_Divided_Against_Itself_Cannot_Stand (same edition).
3. Cooper Union: https://en.wikisource.org/wiki/Cooper_Union_Speech (the Wikisource page does not name its printed source edition).
4. Farewell at Springfield: https://en.wikisource.org/wiki/Abraham_Lincoln%27s_Farewell_Address
5. First Inaugural: https://en.wikisource.org/wiki/Abraham_Lincoln%27s_First_Inaugural_Address (from *Life and Works*). Cross-checked against the Avalon Project text at https://avalon.law.yale.edu/19th_century/lincoln1.asp. The wording matches. Capitalization and punctuation differ in small ways, such as "government" against "Government" and "battle-field" against "battlefield". The Wikisource text was used.
6. Gettysburg Address, Bliss copy: https://en.wikisource.org/wiki/Gettysburg_Address_(Bliss_copy) (transcribed from the manuscript images).
7. Second Inaugural: https://en.wikisource.org/wiki/Abraham_Lincoln%27s_Second_Inaugural_Address (from *Life and Works*, v6, pp. 245–247 of the scan).

## Editorial handling

- Spoken text is verbatim from the sources above. A script compared every word of `speech.md`, after removing headings, context lines and cues, against the fetched text, and it matched exactly.
- Long source paragraphs were broken at sentence boundaries into paragraphs of up to about 4 sentences so they read better on the HUD. No words were changed.
- Left out: editorial titles and datelines from the printed edition, Wikisource image captions and licence boxes, and the Bliss copy's heading ("Address delivered at the dedication of the cemetery at Gettysburg.") and its closing date and signature, since none of these were spoken.
- Section headings, one italic context line per speech, and a few delivery cues were added, as the brief allows.

## Caveats

- Lyceum date: the *Life and Works* heading dates the address January 27, 1837. It was in fact delivered on January 27, 1838, as the brief and standard references say. The context line uses 1838.
- The Lyceum text keeps the editor's bracketed "[our]" ("the vicious portion of [our] population") exactly as printed.
- Farewell at Springfield: the text used is the commonly printed version that Lincoln and his secretary wrote down on the train afterwards. Newspapers of the day printed somewhat different versions of what he actually said.
- Cooper Union: Wikisource gives no edition for its text, so the edition behind it could not be confirmed.
