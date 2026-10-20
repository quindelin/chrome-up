# chrome_up

Two products for the Meta Ray-Ban Display glasses, kept side by side.

| folder | product | what it is |
|---|---|---|
| [`livevision/`](livevision/) | **LiveVision** | Live POV streaming: the Skyrim-style HUD overlay for OBS, autoclip (finds, cuts and posts clips), the LiveVision iOS companion that streams the glasses camera, and the OBS cloud VM (`livevision/deploy/obs-vps`). |
| [`lingualens/`](lingualens/) | **LinguaLens** | A spoken language coach on the glasses: Mandarin, Japanese and Spanish courses, the server (Cloud Run: `lingualens/deploy/deploy.sh`), and the iOS and Android apps. |

They share no code. The one link between them is a URL: the OBS stack can
show a read-only LinguaLens panel on stream (`LINGUALENS_URL`).

## Quick start

```bash
cd livevision && ./run.sh          # HUD server, http://127.0.0.1:8787
cd livevision && ./run_autoclip.sh doctor
cd lingualens && ./run.sh zh       # LinguaLens server, http://127.0.0.1:8899  (zh | ja | es)
```

Each product's own README has the details. Agents: read
[`livevision/AGENTS.md`](livevision/AGENTS.md) before touching autoclip.
