# LinguaLens — Mandarin & Japanese on Meta Ray‑Ban Display

A Pimsleur‑style language coach built for the Meta display glasses: the line you have to
say sits in front of your eyes with its reading above it (pinyin for Mandarin, kana for
Japanese), audio models it for you, and **you do not move to the next line until your
pronunciation passes** — tones included.

**Three courses ship in one app.** `./run.sh` is Mandarin, `./run.sh ja` is Japanese, `./run.sh es` is Spanish. Same
server, same gate, same glasses UI — only the course data, the speech locale and the
scoring engine change.

| | Mandarin | Japanese | Spanish |
|---|---|---|---|
| ladder | HSK 1 → HSK 7‑9 | JLPT N5 → N1, plus an above‑N1 band | CEFR A1 → C2 |
| config | `config.yaml` | `config.ja.yaml` | `config.es.yaml` |
| course data | `server/course/zh/` | `server/course/ja/` | `server/course/es/` |
| speech locale | `zh-CN` | `ja-JP` | `es-ES` |
| default scorer | iFlytek ISE (**tone aware**) | Azure AI Speech | Azure AI Speech |
| reading line | pinyin | kana (furigana) | none (spelled as said) |

A lesson runs in this order:

0. **Scene** — one English sentence on the glasses: *who you are talking to, and where.*
   Then the audio starts, and it is 100 % in the target language.
1. **Conversation** — you hear a line, you say it, the gate decides if you move on.
2. **Word bank** — new words are folded in from a graded bank (HSK‑graded / JLPT‑graded):
   you hear each one modelled, then you produce it from the English alone.
3. **Free response** — the model asks you a question and there is **no scripted line**.
   You compose the answer yourself. This is the step that turns repetition into speech.
4. **Characters** — 汉字 (or kanji) as an object in its own right: you meet the
   character, then you have to recognise it (§3h).
5. **Reading** — a real passage, read aloud, then a comprehension question (§3i).
6. **Listening** — the same passage again with the screen blank (§3i).
7. **缩写** — from HSK 6: say the passage back, shorter (§3j).

Steps 4–7 are on for Mandarin from HSK 1 (characters, reading, listening) and
HSK 6 (缩写); the Japanese course runs reading and listening from N5.

Also included: **“Think in the language”** — give an English thought, get the Mandarin or
Japanese, and drill it until you get it right.

```
┌──────────────────────────────────────────────────────────────────┐
│  glasses (600×600 waveguide)   ← what to say + your score          │
│  phone wrapper (mic + TTS)     ← records you, plays models, haptic │
│  LinguaLens server             ← curriculum, gate, scoring         │
└──────────────────────────────────────────────────────────────────┘
```

---

## 0. On the go (phone + glasses, no laptop)

LinguaLens runs on Google Cloud Run, so the phone and the glasses reach it
anywhere over HTTPS. It scales to zero, so an idle day costs nothing.

```bash
deploy/lingualens/deploy.sh        # build + deploy (keeps the same key)
deploy/lingualens/deploy.sh url    # your phone / glasses / OBS links
```

- **Phone:** open the `phone` link (it records you and plays the model audio
  through the glasses speakers). Add it to the home screen.
- **Glasses:** load the `glasses web app` link as a Meta Ray-Ban Display Web App.
- **Same `client_id` on both** = one shared session.
- The key in the link is needed once per device (then a cookie). Anyone with
  the link can use the app, so don't post it.
- Progress is kept in a Cloud Storage bucket, so it survives restarts.
- **On stream:** say "show lingualens" / "hide lingualens" (see
  `deploy/obs-vps`); OBS shows a read-only copy of the same session.

## 1. Quick start

```bash
cd lingualens
./run.sh                 # Mandarin  — config.yaml     (HSK 1-7)
./run.sh ja              # Japanese  — config.ja.yaml  (JLPT N5-N1)
./run.sh es              # Spanish   — config.es.yaml  (CEFR A1-C2)
```

Both create `.venv`, install deps and start on `:8899`. Pick the course with the first
argument; `python -m server.main --lang ja` does the same thing.

- glasses display → <http://127.0.0.1:8899/>
- phone companion → <http://127.0.0.1:8899/phone>  (open this one to talk)
- both share state via `?client_id=…` (default `default`)

With no API keys it runs on the **mock scorer** (duration + loudness only) so the plumbing
works offline. Two real engines are wired in:

| provider | env vars | tone aware |
|---|---|---|
| **iFlytek ISE** (default choice) | `IFLYTEK_APPID`, `IFLYTEK_API_KEY`, `IFLYTEK_API_SECRET` | **yes** — `tone_score` (调型), `phone_score` (声韵), per‑syllable |
| Azure AI Speech | `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION` | no — accuracy/fluency/completeness + word errors |
| mock | – | no |

```bash
export IFLYTEK_APPID=...      # console.xfyun.cn → 我的应用 → 语音评测
export IFLYTEK_API_KEY=...    # the "APIKey" used in the MD5 signature
./run.sh
curl -s localhost:8899/api/health   # -> "provider":"iflytek", "tone_aware":true
```

### How the iFlytek call works

```
POST https://ise-api.xfyun.cn/v2/ise
X-Appid, X-CurTime, X-Param = base64(json), X-CheckSum = MD5(APIKey + X-CurTime + X-Param)
body: audio=<base64 16k/16bit/mono PCM>&text=<the reference hanzi>
```

`extra_ability=multi_dimension` is what unlocks **tone_score / phone_score** for `zh_cn`;
`result_level=entirety` adds the per‑syllable nodes, so a failure can say
*"tone on 机 is off (58)"* instead of just "not clear enough".
`config.yaml → pronunciation.iflytek` controls all of it, and `category: auto` picks
`read_syllable` / `read_word` / `read_sentence` from the length of the line.

The provider interface is one function in `server/pronunciation.py`. Registering another
engine (Chivox, SpeechSuper, iFlytek SDK) touches nothing else — `Score.tone`,
`Score.syllables` and `gate.min_tone_score` are already understood everywhere.

---

## 2. The gate

| rule | HSK 1 | → | HSK 6 | → | HSK 7‑9 |
|---|---|---|---|---|---|
| pronunciation | 62 | → | 80 | → | 82 |
| accuracy (声韵) | 62 | → | 80 | → | 82 |
| completeness | 78 | → | 92 | → | 94 |
| **tone (调型)** | 60 | → | 75 | → | 78 |
| reference coverage | 75 % | | 75 % | | 75 % |
| `max_attempts` | `0` | | `0` | | `0` |

`max_attempts: 0` means **never auto‑advance** — failing keeps you on the same line, replays
the model slower, shows pinyin/English after 2 tries, and names the syllable whose tone is
wrong. Every HSK band tightens the numbers, so the bar rises as you climb.

### 2b. Fluency — from HSK 5

Knowing a line and being able to *use* it are different things. From HSK 5 the gate adds
two measures that no accuracy score captures (`gate → fluency`, off by default):

| measure | floor | what it catches |
|---|---|---|
| speaking rate | 2.0 characters/s | line‑by‑line translation that never gets fast |
| filler ratio | ≤ 20 % | 那个… 就是… 嗯 — the stall while you compose |

Both are eased on free response and 缩写, where composing is the point. Below HSK 5
they are not measured: a beginner who is slow is a beginner, not a failure.

### 2c. Where to start — the placement test

Everybody used to begin at lesson 1 with 你好. Right for most people, quietly terrible for
the rest. `POST /api/placement/start` runs ~28 probes — four lines sampled from each band,
spoken and gated exactly as a lesson is — and sets your starting lesson to the **first band
you cannot do**, not the last one you can. Being placed slightly low costs a few lessons of
easy review; being placed slightly high costs the confidence to continue at all.

The probes are real dialogue lines, not invented test items: a line from lesson 40 is
exactly what lesson 40 would ask you to say.

---

## 3. Course: HSK 1 → HSK 7‑9

```
HSK 1   · First contact      15 lessons   greetings, directions, ordering
HSK 2   · Everyday errands   10 lessons   shopping, bargaining, time, plans
HSK 3   · Real life          12 lessons   routine, weather, health, 比, 过
HSK 4   · Precision          12 lessons   把, complements, 越来越, 被, connectives
HSK 5   · Opinions           12 lessons   与其…不如, 难免, 未必, 换句话说, 见仁见智
HSK 6   · Mastery            12 lessons   成语, formal register, literature, argument
HSK 7‑9 · Native register    12 lessons   盛极而衰, 中庸之道, 差强人意, 无可厚非, debate
```

85 lessons · 19 units · 533 dialogue turns · **170 free‑response questions** (146 in the
shared bank + 24 authored into the HSK 7‑9 lessons) · **85 reading passages / 5,047
characters / 170 comprehension questions** · **576 汉字 in a staged recognition course** ·
1,264 words in the bank (58 topics).

Every lesson follows the Pimsleur shape: conversation first, vocabulary introduced *inside*
it, then **substitution drills** (one frame × N slot values: 我要__ / __在哪里 / 这件事__),
then **graduated interval recall** at 10 s → 30 s → 75 s.

### 3b. Free response — the step that isn't scripted

Repetition teaches form; only production teaches speech. Every lesson ends with two
questions you have never seen a scripted answer for (`server/course/freeform.py`):

```
HSK 1   你好，你叫什么名字？        →  我叫李华，很高兴认识你。
HSK 4   你把手机放哪儿了？          →  我把手机放在桌子上了。
HSK 6   你怎么看信息过载？          →  平台和用户都有责任。
```

You answer in your own words. The engine then checks, in order:
did you *answer* rather than repeat the question · did you say a whole sentence ·
is it on topic (shared meaning‑carrying characters with the question) · was it
intelligible (the normal tone gate, **relaxed 6 points** — composing while speaking is
harder than repeating). The model answer is hidden until you have missed twice, then
shown and drilled.

This needs dictation. `server/asr.py` picks one automatically:

| ASR | source | notes |
|---|---|---|
| `client` | phone browser Web Speech API (`zh‑CN`) | **no key, no cloud** — the default on phone |
| `iflytek` | iFlytek IAT (`/v2/iat`) | same app credentials as scoring |
| `azure` | Azure short‑form recognition | same key as scoring |
| `mock` | – | grades against the model answer, still usable |

`config.yaml → free.asr: auto`. Without any dictation the step degrades to drilling the
model answer instead of failing.

### 3c. 词汇 — the word bank

`server/course/vocab_hsk*.py`: 1,264 HSK‑graded words in 58 themed topics
(食物, 交通, 工作, 情绪, 网络, 环境, 成语 …). Two ways in:

- **Folded into lessons** — `vocab.inject_per_lesson: 4` adds four new words to every
  lesson's recall pool, walking the band's whole bank as you walk its lessons.
  Each one is met **heard first, then produced from English**: a modelled `listen`
  pass so the word exists in your ear, then a `recall` step that shows only the
  English and hides the characters until you have spoken. Asking you to produce a
  word you have never heard is not recall, it is guessing, and it only fails the
  gate.
- **Dedicated sessions** — menu → `HSK n` → **词汇** (or `JLPT band` → **単語**) → topic:
  hear each word, say it, then two recall rounds (`POST /api/vocab/start`).

Every Chinese entry is machine‑checked: `python -m server.course.zh.pinyin_check` validates
all 1,264 + 170 + lesson pinyin against the table of legal Mandarin syllables and flags
duplicates, so a wrong tone cannot slip in.

### 3d. Pinyin fades out

Pinyin is a crutch: if it is always on you never learn to read Chinese.

| HSK | mode | what you see |
|---|---|---|
| 1–2 | `always` | pinyin on every line |
| 3–4 | `fade` | pinyin when a line is taught, **hidden when you must retrieve it** |
| 5–6 | `reveal` | hidden until you have failed twice |

`config.yaml → ui.reading_mode` (`auto` follows the ladder above; also `always`, `fade`,
`reveal`, `never`).

### 3e. Where you are standing — the scene

A line of Chinese spoken by a stranger with no setting is noise: there is nothing to hang
it on, so there is nothing to retrieve later. This is Pimsleur's *organic learning*, and
it is the whole reason a Pimsleur lesson opens in English with "You are in a taxi in
Beijing, and you want to go to the airport."

LinguaLens has a screen, so it does not have to spend audio on it. Every lesson opens with
one **printed** English sentence answering exactly two questions — who you are talking to,
and where you are standing:

> You are at a Shanghai metro exit, trying to reach the train station on time.

That is all it does. It never translates a word and never explains the grammar: the scene
is a signpost, not the road. 85 for Mandarin, 73 for Japanese, in
`server/course/{zh,ja}/scenes.py`.

It fades on the same curve as the reading line, for the same reason — by the top bands you
can work the setting out from the first spoken line:

| HSK | mode | what you see |
|---|---|---|
| 1–2 | `always` | every lesson opens with its scene |
| 3–4 | `first` | only the first lesson of each unit |
| 5–6 | `tip` | not printed; **↓** reveals it |

`config.yaml → ui.scene_mode` (`auto` follows the ladder; also `always`, `first`, `tip`,
`never`). `ui.scene_seconds` is how long it stays up — a tap skips it.

### 3f. Anticipation — the pause before the English

The other half of the method is the **principle of anticipation**: the English cue arrives
and you are given a pause to retrieve before any answer is supplied.
`recall.anticipation_seconds` (default `5`) does that per item — the cue area stays blank,
a countdown runs, and the English appears only if you draw a blank. It is a rescue, not a
prompt.

Picking up the mic cancels the pause, so the gap is only ever dead time when you are
actually stuck, and the English never lands in the middle of your own sentence. Waiting
out every gap in a lesson is ~5 minutes, which is about what Pimsleur spends on pauses
anyway.

This is separate from `recall.intervals`, which is the gap **between** rounds
(10 s → 30 s → 75 s). Anticipation is inside an encounter; intervals are between them.

### 3g. 汉字 — characters as a first‑class object

Characters are not vocabulary with extra steps. 明 is 日 + 月 ("bright" = sun + moon), and
that composition is the thing that makes two hundred characters stick instead of twenty.
`server/course/zh/hanzi.py` holds **576 characters** in six stages, each with its
components, its radical, and the words it appears in:

| stage | characters | what it covers |
|---|---|---|
| 1 | 126 | 人 口 日 月 大 小 — the pieces everything else is built from |
| 2 | 131 | 明 好 休 家 — compounds of stage 1 |
| 3 | 104 | 河 话 饭 — the semantic‑phonetic pattern |
| 4 | 72 | 意 想 感 — the abstract vocabulary |
| 5 | 99 | 经济 环境 技术 — HSK 5‑6 abstractions |
| 6 | 48 | 盛 衰 庸 — HSK 7‑9 literary register |

Three per lesson, always met before the line that uses them, and always **recognised
before produced**: you see the character and say it, which is the skill reading actually
needs. `config.yaml → hanzi.recognition`.

### 3h. 阅读理解 — reading, then listening

Conversation teaches speech and nothing else. HSK 阅读 is a separate skill with separate
material: a passage of 200–1,000 characters growing across the ladder, in
`server/course/zh/readings.py` (85 passages, 5,047 characters). Each lesson gives you:

1. **Read** — the passage in chunks, each modelled aloud, then read by you and gated.
   The reading line (pinyin) fades on the normal curve, so by HSK 5 you are reading
   characters, not pinyin.
2. **Comprehension** — two questions about the passage, answered in Chinese. These are
   `answer` steps: no scripted line, graded on whether you answered rather than on
   wording (§3b).
3. **听力** — the *same* passage again with the screen **blank**. Reading it first is
   what makes the audio comprehensible; hearing it with nothing on screen is what makes
   it listening practice. One per lesson, `config.yaml → reading.comprehension`.

That ordering is the whole point: audio with no visual support is the hardest version of
the material, and it only works because the text is already known.

### 3i. 缩写 — writing, spoken

HSK 6 写作 is a 缩写: read ~1,000 characters, produce ~400, in ten minutes. There is no
way to get there from memorised lines, and there is no keyboard on a pair of glasses —
but the *hard part* of 缩写 is deciding what to leave out while keeping the point, under
time pressure, in the target language. That is exactly as hard spoken as written.

So from HSK 6 each lesson ends with a prompt (`server/course/zh/summaries.py`):

> 用两三句话说说张经理是个什么样的人。

and you say the passage back, shorter. It is graded on **coverage, not wording** —
`free.grade_writing` checks that the passage's key points survived, never that the
sentences match a reference. A fluent, grammatical summary that drops the point has
failed, and that is precisely the failure a wording check cannot see:

```
"会议改到下周了，麻烦大家调整时间，谢谢配合。"   →  FAIL  (dropped 下周一 and 不便)
```

`config.yaml → writing.min_band: 6` — below HSK 6 a summary is not worth asking for.

### 3j. Diagnostics — where your tones actually break

`GET /api/diagnostics` aggregates every failed syllable into a per‑tone heatmap: not
"your tones are weak" but *third tone in second position is where you break*, with the
worst syllables named. It is read from the same `Score.syllables` the gate already
collects, so it needs no extra pass and no extra audio.

### 3k. The Japanese course

`./run.sh ja`. Everything above applies unchanged — the gate, the free response, SRS
review, the haptic menu and “think in the language” are the same code. What differs:

```
N5  · First contact        15 lessons   greetings, please/sorry, directions, ordering
N4  · Everyday errands     10 lessons   shopping, prices, paying, time, plans, opinions
N3  · Daily life           12 lessons   routine, home, weather, health, family, 〜たことがある
N2  · Precision            12 lessons   〜てしまう, 〜ておく, 〜てみる, 〜ば〜ほど, passive/causative
N1  · Opinions & society   12 lessons   work, education, environment, culture, debate
N1+ · Native register      12 lessons   四字熟語, ことわざ, 敬語, news, literature, nuance
```

73 lessons · 17 units · dialogue, drills, recall and free response per lesson · a
JLPT‑graded bank in themed topics (人と家族, 旅行, 仕事, 四字熟語 …).

The **reading line is kana**, not pinyin — the furigana slot. Kanji is a bigger reading
problem than hanzi, so the kana crutch survives one band longer than pinyin does:

| band | mode | what you see |
|---|---|---|
| N5–N3 | `always` | kana on every line |
| N2–N1 | `fade` | kana when a line is taught, hidden when you must retrieve it |
| N1+ | `reveal` | hidden until you have failed twice |

`config.ja.yaml → ui.reading_mode`.

The English **scene** runs one band longer for exactly the same reason — and it also
carries information the reading line cannot: at N3 you still cannot guess whether you
are meant to be speaking です/ます or 敬語. N5–N3 `always`, N2–N1 `first`, N1+ `tip`
(`config.ja.yaml → ui.scene_mode`).

**Scoring.** Azure AI Speech `ja-JP` is the default: accuracy / fluency / completeness /
pron score plus word‑level error types. Pitch accent (高低アクセント) is the Japanese
equivalent of Mandarin tone, and `Score.tone` + `gate.min_tone_score` are already wired
for it — but no mainstream cloud engine reports it, so the gate stays dormant instead of
failing you on a number nobody measured. iFlytek ISE works too if your account has the
Japanese service (`pronunciation.iflytek.language: ja_jp`).

**“Think in Japanese”** has its own offline phrasebook (~70 phrases + a pattern matcher:
`{x}に行きたいです`, `{x}はどこですか`, `{x}が好きです` …) and a Japanese LLM prompt.

### How many hours is that?

Measured from the actual step lists (4.5 syll/s model speech, 3.0 syll/s learner,
1.2 s cloud scoring, ~2 min of interval waits per lesson). The 5 s anticipation pause is
**not** counted: it is time you spend talking, and picking up the mic cancels it — only
waiting it out would add ~5 min per lesson.

| track | time |
|---|---|
| lesson track (85 lessons, 7,264 learner utterances) | **11.6 h** (≈14.5 h at 2 attempts/line) |
| 词汇 track (1,264 words, 58 topics) | **4.3 h** |
| **total** | **≈15.9 h** |

On top of that:

- **Review** (`/api/review/start`) is endless: everything you pass is scheduled at
  5 min → 30 min → 2 h → 1 d → 3 d → 1 w → 2 w → 5 w → 3 mo → 8 mo → **18 mo** and comes
  back forever (`review_due` in state). The ladder runs out to 18 months on purpose:
  a line you revisit every 3 days for a year is maintenance, not retention — it never
  tests whether you still know it.
- **Think in the language** turns any English thought into a line you must then pass.
- Substitution drills multiply any lesson if you raise `drills.per_pattern`.

Reaching real HSK 6 (or N1) takes far more than 13 hours of study — nobody can hand‑author
that — so the design is: scripted conversations for new material, free response for
production, the word bank for breadth, drills for volume, SRS review forever. Adding
content is data‑only: append to `server/course/zh/hskN.py` and `server/course/zh/vocab_hskN.py`,
or `server/course/ja/jlptN.py` and `server/course/ja/vocab_nN.py`, plus the shared
`server/course/{zh,ja}/freeform.py`.

---

## 4. Menu & haptic actions

The glasses UI has a full menu driven only by the inputs the platform gives you:

| input | action |
|---|---|
| swipe up / down (Neural Band or temple) | `ArrowUp` / `ArrowDown` — move selection; outside the menu: toggle English / tip |
| tap (thumb‑index pinch) | `Enter` — open level → unit → lesson; outside: replay the model |
| swipe back / long press | `Escape` — open the menu, or step back one level |
| `ArrowLeft` | back |

Top level: **Continue**, **Review (N due)**, **HSK 1 … HSK 7‑9** → units → lessons.
Every move / select / pass / fail fires a haptic through `window.LinguaLensHaptics`
(injected by the native wrapper), falling back to `navigator.vibrate`.

---

## 5. Running on real hardware

### Web app (fastest path)

Host the server over HTTPS with a valid certificate (the glasses refuse plain HTTP and
self-signed certs). It is a Python server with a websocket, so a static host
(Vercel/Netlify/GitHub Pages) is not enough: put it behind nginx/Caddy or a
Cloudflare tunnel. Enable developer mode in the Meta AI app (tap the version 5×;
needs Meta AI app v272+, glasses firmware v125+), then load `/` on the glasses.
600×600, no scrolling, black renders transparent on the waveguide.

What the Web App runtime does and does not give you, and how LinguaLens deals with it
([Meta WebApps docs](https://wearables.developer.meta.com/docs/develop/webapps/build)):

| constraint | what LinguaLens does |
|---|---|
| no microphone | `/phone` (or the Android/iOS wrapper) records |
| TTS has **one en-US voice** and ignores `lang` | the glasses page never speaks; model audio comes from the phone/wrapper, which plays through the glasses speakers over Bluetooth |
| Back is `history.back()`, not an Escape key; with no history it opens the system menu | menu, menu levels and the grammar page each push a history entry (max 5, shell limit) |
| no Escape key to open the menu | swipe **left** opens the menu |
| one session shared by glasses + phone | `/api/next` takes `at=<step index>` so two clients cannot skip a line |

### Native wrapper (Android, DAT 1.0.1)

`android/` builds against `com.meta.wearable:mwdat-core/-display/-mockdevice:1.0.1`
(`./gradlew assembleDebug`). It routes the mic to the glasses over HFP
(`setCommunicationDevice(TYPE_BLUETOOTH_SCO)` + `MODE_IN_COMMUNICATION`). HFP is
**8 kHz mono**, so the scorers get narrowband audio: expect lower accuracy on
s/sh/x and し/す than with the phone mic. HFP is released after every take, because
it drops the glasses speaker to 8 kHz while it is active.

An optional native display mode (`window.LinguaLensGlasses.startDisplay()`) draws
the line with `mwdat-display`. A DAT display session takes the whole glasses
display, so the Web App is hidden while it runs, and Back (two-finger temple tap)
ends it. Attestation IDs go in `android/local.properties` (`mwdat_application_id`,
`mwdat_client_token`). Leave them unset while you are in developer mode.

### RF Scope (a second feature, same wrapper)

The same Android wrapper hosts an RF scanner that walks the room, classifies
what it sees (iBeacon, Eddystone, Apple Find My, generic), fits a first-harmonic
bearing model against the user's heading (phone compass today, glasses IMU once
DAT is pinned), and renders a 600×600 HUD on Meta Ray-Ban Display. See
[`docs/RF_SCOPE.md`](../docs/RF_SCOPE.md) for the design, accuracy caveats and
the iOS status.

### Native wrapper (mic + display + haptics)

Scaffolded for both platforms — the parts a web app cannot do:

```
android/                      Kotlin, Gradle, WebView + OkHttp + AudioRecord
  app/src/main/java/com/lingualens/glasses/
    MainActivity.kt     WebView host, push-to-talk, JS haptics bridge
    AudioCapture.kt     16 kHz mono WAV (BT SCO = glasses mic when paired)
    LessonClient.kt     server API
    GlassesBridge.kt    DAT: mwdat-core pairing + mwdat-display
    Haptics.kt          vibration per interaction
ios/
  LinguaLens/Package.swift + Sources/LinguaLensCore/   client + AVAudioEngine capture
  LinguaLensApp/LinguaLensApp.swift                    SwiftUI host, WebKit bridge, DAT
```

```bash
# Android
cd android && ./gradlew :app:installDebug
# set server_url / client_id in SharedPreferences, or edit DEFAULT_URL in MainActivity.kt

# iOS: open Xcode, add LinguaLens as a local package, add the mwdat-* SPM packages
```

The DAT SDK symbol names in `GlassesBridge.kt` / `GlassesViewModel` are marked with
`DAT:` comments — verify them against the version you pin in `app/build.gradle.kts`
(`com.meta.wearable:mwdat-core:0.1.x`). Everything is guarded so the app still runs with
no glasses attached, which is also how you test with **MockDeviceKit**.

---

## 5b. Several courses, one app

The server loads **every course package that imports cleanly** and keeps their
progress apart in one file (`state.json`):

```json
{ "alice": { "active": "zh",
             "courses": { "zh": {"lesson_id": 12, "completed": [...], "words": {...}, "stats": {...}},
                          "ja": {"lesson_id": 7,  "completed": [...], "words": {...}, "stats": {...}} } } }
```

- `server/courses.py` — the registry. Packages are imported **lazily**, and a
  half-written course (`ja` while it is being authored) is reported as
  `ready: false` with the import error instead of taking the server down. A
  failure is retried 30 s later, so a course appears as soon as it compiles —
  no restart.
- `server/progress.py` — the per-course ledger: lessons completed, the **word
  list** (every item you passed the gate on, with reading, English, how often
  and when), plus minutes spoken and the day streak. Old single-course
  documents are migrated in place the first time they are read.

The phone shows all of it: a course switcher, one row of numbers per course,
a level-by-level breakdown, and a searchable list of the words you have
actually learned — pick any course, filter by level, tap a word to hear it.

## 6. API

| route | purpose |
|---|---|
| `GET /api/state` | session snapshot: level, unit, lesson, step, gate, score, `review_due` |
| `WS /ws?client_id=` | live push to glasses + phone |
| `POST /api/attempt` | multipart audio (`encoding=wav` or `pcm_s16le`) → grade + maybe advance; add `recognized=` to pass the phone's own dictation |
| `POST /api/attempt/sim` | grade without a mic (`quality=good\|bad`) |
| `POST /api/next` | advance past listening / recall‑round prompts |
| `POST /api/lesson/start` | jump to a lesson (used by the menu) |
| `POST /api/review/start` | endless spaced review of everything you passed |
| `POST /api/vocab/start` | drill one word-bank topic (`topic_id=h3-travel`, `n5-food`) |
| `GET /api/vocab/topic` | one topic with all its words |
| `POST /api/placement/start` | begin the placement test (§2c) |
| `GET /api/placement` | current probe and progress |
| `POST /api/placement/submit` | grade one probe; on the last one it sets `lesson_id` |
| `GET /api/diagnostics` | per-tone error heatmap + worst syllables (§3j) |
| `POST /api/think`, `/api/think/exit` | Think in Chinese / Japanese |
| `GET /api/languages` | which courses exist and which one is loaded |
| `GET /api/course`, `/api/health` | full ladder (for the menu), provider status |
| `GET /api/courses` | every course + this learner's numbers on each |
| `POST /api/course/select` | switch which course you are studying |
| `GET /api/progress` | lessons / words / minutes / streak / level breakdown |
| `GET /api/progress/words` | the words you have learned (`kind`, `band`, `q`) |

Every session route (`/api/state`, `/ws`, `/api/next`, `/api/attempt`,
`/api/lesson/start`, `/api/vocab/start`, `/api/review/start`, `/api/think`)
also takes `course=zh|ja`; without it you get the course you are on.

---

## 7. Files

```
server/course/
  __init__.py             language registry: which course package to load
  zh/                     Mandarin
    course_zh.py          hand-authored foundation units (HSK 1-2 content)
    hsk1.py … hsk7.py     HSK 3-7 data
    freeform.py           146 free-response questions + model answers
    readings.py           85 reading passages (5,047 chars) + 170 questions
    hanzi.py              576 characters in 6 stages: components, radical, words
    summaries.py          24 缩写 prompts (HSK 6-7), graded on coverage
    vocab_hsk*.py         1,264 words in 58 themed topics (the word bank)
    scenes.py             the English scene for each of the 85 lessons
    pinyin_check.py       validates every syllable in the corpus
  ja/                     Japanese
    course_ja.py          hand-authored foundation units (N5-N4 content)
    jlpt5.py … jlpt0.py   N5, N4, N3, N2, N1, N1+ levels
    freeform.py           146 free-response questions + model answers
    vocab_n*.py           960 words in 48 themed topics (the word bank)
    scenes.py             the English scene for each of the 73 lessons
server/course.py          language codes, display names, speech locales
server/courses.py          registry: lazy + fault-tolerant course loading
server/progress.py         per-course ledger: lessons, words, streak, minutes
server/curriculum.py      levels -> units -> lessons, word bank, per-band gates
server/drills.py          substitution drills + spaced review queue (out to 18 mo)
server/engine.py          session state machine - the gate lives here
server/placement.py       where to start: probes per band, first band you can't do
server/free.py            free-response + 缩写 grading (no scripted reference)
server/asr.py             dictation: client | iFlytek IAT | Azure | mock
server/pronunciation.py   iFlytek ISE (tones) | Azure | mock + evaluate()
server/think.py           English -> target language (LLM or offline phrasebook)
server/main.py            FastAPI routes, per-course progress store, websockets
server/web/               600x600 glasses UI + phone companion + haptic menu
                          progress.js/.css: per-course stats + learned words
config.yaml               Mandarin course config  (./run.sh)
config.ja.yaml            Japanese course config  (./run.sh ja)
android/ ios/             DAT wrappers
```
