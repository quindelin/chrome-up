# Drop a Live2D avatar in here

HUDstream ships **no** character models. That's deliberate — Kirito, Eren, and
most other anime protagonists are copyrighted, and so are nearly all the
community Live2D rips of them. Bring your own model via one of three routes.

## Route A — VTube Studio (easiest, works with any model you own)

1. Buy / install [VTube Studio](https://denchisoft.com/) and load whatever
   model you legally own (its model store, a commissioned model, your own art).
2. Turn on the Plugin API: **Settings → Plugins → "Start API Server"**.
3. In HUDstream's `config.yaml`, set `vtube_studio.enabled: true` and fill in
   the hotkey IDs you see in VTube Studio's UI:

   ```yaml
   vtube_studio:
     enabled: true
     hotkeys:
       agility: "<id of your 'run / sweat' hotkey>"
       combat:  "<id of your 'angry' hotkey>"
       rizz:    "<id of your 'blush' hotkey>"
       shout_fus: "<id of your 'shout' hotkey>"
   ```

4. Route your mic to VTube Studio (see **Audio routing** in the main README)
   so the model lip-syncs to exactly the same audio that goes to stream.

The HUD then triggers those hotkeys automatically whenever the matching skill
fires or you shout. Nothing else needed.

## Route B — free CC0 / CC-BY Live2D base, rendered in the overlay

Put four things in this folder:

```
overlay/assets/live2d/
  manifest.json
  model.moc3
  texture_00.png
  live2dcubismcore.min.js      <- from https://www.live2d.com/en/sdk/download/web/
```

`manifest.json`:

```json
{
  "name": "my-anime-base",
  "moc3": "model.moc3",
  "textures": ["texture_00.png"],
  "sdk": "live2dcubismcore.min.js",
  "scale": 0.18,
  "offset": [0, 0]
}
```

Then set `avatar.engine: live2d` in `config.yaml` and restart. If the SDK or
the manifest is missing, the HUD silently falls back to the procedural
canvas avatar — it never hard-fails.

Where to find licensed-free anime bases: filter for **Commercial use allowed**
+ redistributable terms and always read the license file that ships with the
model. A lot of "free" models are personal-use-only, which still breaks the
moment you stream with ads or subs.

## Route C — recolor the built-in procedural avatar

No downloads, no licenses, works today. Set `avatar.theme` in `config.yaml`
to one of:

| theme | look |
| --- | --- |
| `dark_swordsman` | black hair, blue eyes, dark cloak |
| `green_scout` | brown hair, green eyes, forest jacket |
| `silver_knight` | silver hair, red eyes, white cloak |
| `blonde_prince` | blonde, teal eyes, blue coat |
| `hacker` | black hair, neon-green eyes, dark terminal gear |

These are original recolorings of the HUD's own anime base — not copies of
any specific character. You can also edit `overlay/src/themes.js` to add your
own palette.

## Licensing reality check

- Kirito / Eren: copyrighted by their rights holders. We will not ship or
  fetch them, and rips circulate in a legal grey zone.
- A model you commission or draw yourself: clean to use.
- CC0 models: clean to use, usually must still respect the not-a-trademark
  clause if it looks close to a real character.
- Always check whether a "free" model permits **commercial** use before you
  stream with monetization enabled.
