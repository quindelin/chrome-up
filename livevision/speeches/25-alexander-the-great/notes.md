# Notes: 25-alexander-the-great

Kind: transcription. These are speeches *as written by ancient historians*.
Arrian wrote in the second century A.D. and Curtius in the first, about four
hundred years after Alexander. They worked from earlier sources and wrote the
speeches themselves, as ancient historians did. None of this is a record of
Alexander's own words, and the script says so in its opening italic line.

## Length and runtime

- `wc -w speech.md`: **11,007 words** (headings, italic context notes and cues included).
- Spoken text only (headings, notes and cues left out): **10,384 words**.
- At 140 wpm: **about 74 minutes** for the spoken text (about 79 minutes counting everything in the file).
- **This is shorter than the two-hour target.** The public-domain speeches the
  manifest asks for (Arrian's Hyphasis and Opis speeches, Coenus' reply, and
  the matching speeches in Curtius) run to about an hour and a quarter. Nothing
  was added to pad it. Other public-domain Alexander speeches exist and could
  go in a later version: Curtius VI.9 (the charge against Philotas), VII.7
  (before crossing the Jaxartes) and VIII.8 (the reply to Hermolaus), all in
  Pratt's translation.

## Outline (spoken words, minutes at 140 wpm)

| # | Section | Source | Words | Min |
|---|---|---|---|---|
| I | Before Issus: the council of officers (reported speech) | Arrian II.7 | 655 | 4.7 |
| II | Before Issus: along the line | Curtius III.10 | 400 | 2.9 |
| III | Before Tyre | Arrian II.17 | 353 | 2.5 |
| IV | Before Gaugamela | Curtius IV.14 (Pratt IV.13) | 374 | 2.7 |
| V | At Hecatompylos | Curtius VI.3 | 813 | 5.8 |
| VI | After the Hydaspes (reported speech) | Curtius IX.1 | 216 | 1.5 |
| VII | At the Hyphasis: Alexander | Arrian V.25–26 | 975 | 7.0 |
| VIII | At the Hyphasis: Coenus | Arrian V.27 | 742 | 5.3 |
| IX | At the Hyphasis: the king gives way (reported speech) | Arrian V.28 | 244 | 1.7 |
| X | At the Hyphasis, as Curtius tells it: Alexander | Curtius IX.2 | 1,361 | 9.7 |
| XI | At the Hyphasis, as Curtius tells it: Coenus | Curtius IX.3 | 622 | 4.4 |
| XII | After the wound: Craterus and Alexander | Curtius IX.6 | 1,256 | 9.0 |
| XIII | At Opis | Arrian VII.9–10 | 1,322 | 9.4 |
| XIV | At Opis: the reconciliation (Callines) | Arrian VII.11 | 96 | 0.7 |
| XV | The mutiny, as Curtius tells it | Curtius X.2 | 640 | 4.6 |
| XVI | To the Asian troops | Curtius X.3 | 315 | 2.2 |

## Sources and translators

1. **Arrian, *The Anabasis of Alexander*, tr. E. J. Chinnock (London: Hodder and
   Stoughton, 1884).** Project Gutenberg eBook #46976.
   https://www.gutenberg.org/ebooks/46976 (plain text used:
   https://www.gutenberg.org/cache/epub/46976/pg46976.txt).
   Sections I, III, VII, VIII, IX, XIII, XIV. Chinnock's chapter numbers match
   the standard book and chapter numbering.

2. **Quintus Curtius Rufus, *The History of Alexander the Great*, tr. Peter Pratt,
   revised edition, 2 vols. (London, 1821; first edition 1809).**
   Internet Archive scans:
   Vol. I https://archive.org/details/india.history.resource.77239,
   Vol. II https://archive.org/details/india.history.resource.77237.
   Checked against the first edition (1809), Internet Archive
   https://archive.org/details/in.ernet.dli.2015.69729 (Vol. I) and
   https://archive.org/details/in.ernet.dli.2015.69733 (Vol. II).
   Sections II, IV, V, XV, XVI. Pratt splits the chapters differently from
   modern editions. The script uses the standard references (III.10, IV.14,
   VI.3, X.2, X.3). Pratt's own chapter numbers match them except for
   Gaugamela, where Pratt prints Alexander's address at the end of his chapter XIII.

3. **J. W. McCrindle, *The Invasion of India by Alexander the Great as described by
   Arrian, Q. Curtius, Diodoros, Plutarch and Justin* (Westminster: Archibald
   Constable, 1893; new edition 1896).** McCrindle made his own translation of
   Curtius books VIII–X. Project Gutenberg eBook #66388.
   https://www.gutenberg.org/ebooks/66388. Cornell's scan of the 1896 edition is
   at https://archive.org/details/cu31924028252546.
   Sections VI, X, XI, XII.

All three translations were published before 1929 and are in the public domain in the US.

## Transcription method and what was changed

- The text is word for word from the translations. Arrian and McCrindle were
  taken from the Project Gutenberg texts. A script checked that every spoken
  paragraph of `speech.md` appears verbatim in its source.
- Pratt is not on Gutenberg or Wikisource, so his passages were transcribed by
  hand from the Internet Archive OCR of the 1821 edition. Where the OCR was
  garbled (stray quotation marks at the start of each line, broken words like
  "penctiated" or "ragée"), it was corrected by checking the same passage in
  the OCR of the 1809 edition. Where the two editions word a passage
  differently (Pratt revised his text in 1821), the 1821 wording is used. For
  example, X.2 reads "The half-naked bands of Philip trample on purple mantles"
  where 1809 reads "The semi-nudes under Philip, trample on purple mantles".
  **Not checked against the page images.** A few small punctuation choices in
  Pratt (where a quotation mark opens, a colon versus a question mark) follow
  the clearer of the two OCR texts.
- Changes that leave the words alone:
  - Footnote markers such as [710] were removed, and so were the translators'
    footnotes. Arrian's in-chapter headings ("CHAPTER XXVI. ALEXANDER'S SPEECH
    (continued)") were removed.
  - Long paragraphs were split at sentence boundaries into paragraphs of up to
    three sentences, to suit the HUD. Paragraphs that continue a speech after a
    split therefore don't start with a new opening quotation mark.
  - Pratt's æ/œ ligatures are written ae/oe (Achaeans, Aeolians, Boeotia,
    Dahae, Massagetae, Sacae).
- One correction: Pratt X.3 prints "Macdeonians" once, in both editions. This
  is a printer's error and is spelled "Macedonians" here.
- Numbers are left as the translators printed them ("20,000", "3000",
  "500 talents"). Spelling them out would have changed the text. Read them aloud as usual.
- Pratt's text has its own oddities, kept as printed: in X.3 he calls Roxane
  "the daughter of Oxartes, the Persian" (she was Bactrian), and he gives the
  name "Darius, [Hystaspes,]" with the bracket in III.10.
- The text added here is limited to what the brief allows: the title, the
  section headings, one italic context line per section (source, translator,
  place, date, occasion) and delivery cues on their own lines.

## Could not verify / not done

- Pratt's passages are checked only against two OCR texts, not against page images.
- Dates in the context lines are the usual dates for these events (Issus 333
  B.C., Tyre 332, Gaugamela 331, Hecatompylos 330, Hydaspes and Hyphasis 326,
  the Malli wound 325, Opis 324). They come from general knowledge and the
  translators' own marginal dates (for example, Pratt dates X.3 "A.C. 324").
  They were not checked separately, because WebSearch was unavailable.
- The runtime is about 74 minutes of speech, not two hours (see above).
