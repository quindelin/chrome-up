# HUD sounds

Drop the real Skyrim UI sounds here, extracted from **your own copy** of the
game. The overlay looks for these names (any of `.wav`, `.ogg`, `.mp3`):

| file | Skyrim sound descriptor | plays on |
|---|---|---|
| `levelup.*`  | `UILevelUpSD`       | character level up |
| `skillup.*`  | `UISkillIncreaseSD` | "X increased to N" |
| `discover.*` | location discovered | "Discovered" title |

How to get them:

1. Open `Data/Skyrim - Sounds.bsa` with a BSA tool (Bethesda Archive
   Extractor, or BSArch).
2. Find the files those descriptors point to: open the descriptor in xEdit /
   SSEEdit (`Sound Descriptor` → `UILevelUpSD` → its sound file list), or
   search the archive for `levelup` / `skill`.
3. If a file is `.xwm`, convert it with `ffmpeg -i in.xwm levelup.wav`.
4. Rename and copy here. Refresh the OBS browser source.

These files are Bethesda's audio, so this folder is gitignored and they never
reach the repo. Anything missing falls back to a synthesized stand-in.
In OBS, tick **Control audio via OBS** on the browser source to hear them on
stream.
