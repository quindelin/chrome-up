"""Generate the LiveVision app icon (light, dark, tinted) as 1024px PNGs.

Glasses silhouette whose right lens holds a red LIVE dot with broadcast arcs.
Writes SVG, rasterizes with rsvg-convert, flattens with Pillow (no alpha on
the light icon). Run: .venv/bin/python companion/ios/branding/make_icon.py
"""
import io
import subprocess
from pathlib import Path

from PIL import Image

OUT = Path(__file__).resolve().parent.parent / "LiveVisionApp/Assets.xcassets/AppIcon.appiconset"
RED = "#E6303B"
W, TOP, BOT = 352, 372, 680   # lens width / top / bottom
HALF = 196                    # lens center offset from the icon center
CY = 535                      # dot center


def lens(cx):
    # rounded-trapezoid wayfarer lens, centered on cx
    w, top, bot = W, TOP, BOT
    l, r = cx - w / 2, cx + w / 2
    return (f"M{l+30},{top} L{r-30},{top} Q{r+6},{top} {r},{top+40} "
            f"L{r-16},{bot-80} Q{r-26},{bot} {r-110},{bot} L{l+110},{bot} "
            f"Q{l+26},{bot} {l+16},{bot-80} L{l},{top+40} Q{l-6},{top} {l+30},{top} Z")


def svg(variant):
    frame = "#FFFFFF" if variant != "tinted" else "#FFFFFF"
    dot = RED if variant != "tinted" else "#FFFFFF"
    L, R = 512 - HALF, 512 + HALF
    if variant == "light":
        bg = """<radialGradient id="bg" cx="50%" cy="38%" r="75%">
          <stop offset="0" stop-color="#2A1530"/><stop offset="0.55" stop-color="#140B1C"/>
          <stop offset="1" stop-color="#07060C"/></radialGradient>"""
        bgrect = '<rect width="1024" height="1024" fill="url(#bg)"/>'
    else:
        bg = ""
        bgrect = '<rect width="1024" height="1024" fill="#000000"/>'
    glow = "" if variant == "tinted" else f"""
      <circle cx="{R}" cy="{CY}" r="175" fill="url(#glow)"/>"""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">
  <defs>{bg}
    <radialGradient id="glow"><stop offset="0" stop-color="{RED}" stop-opacity="0.55"/>
      <stop offset="1" stop-color="{RED}" stop-opacity="0"/></radialGradient>
    <linearGradient id="glass" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#FFFFFF" stop-opacity="0.10"/>
      <stop offset="1" stop-color="#FFFFFF" stop-opacity="0.02"/></linearGradient>
  </defs>
  {bgrect}
  <g fill="url(#glass)" stroke="{frame}" stroke-width="50" stroke-linejoin="round">
    <path d="{lens(L)}"/><path d="{lens(R)}"/>
  </g>
  <!-- brow bar + bridge -->
  <path d="M{L-W/2},{TOP} L{R+W/2},{TOP}" stroke="{frame}" stroke-width="72" stroke-linecap="round"/>
  <path d="M{L+W/2-10},{TOP+56} Q512,{TOP+10} {R-W/2+10},{TOP+56}" fill="none" stroke="{frame}" stroke-width="44" stroke-linecap="round"/>
  {glow}
  <circle cx="{R}" cy="{CY}" r="58" fill="{dot}"/>
  <g fill="none" stroke="{dot}" stroke-width="28" stroke-linecap="round">
    <path d="M{R-92},{CY-64} A112,112 0 0 0 {R-92},{CY+64}"/>
    <path d="M{R+92},{CY-64} A112,112 0 0 1 {R+92},{CY+64}"/>
  </g>
  <!-- glare on the left lens -->
  <path d="M{L-110},{TOP+150} L{L-20},{TOP+60} M{L-112},{TOP+226} L{L+56},{TOP+58}" stroke="#FFFFFF"
        stroke-opacity="0.22" stroke-width="26" stroke-linecap="round"/>
</svg>"""


def render(variant):
    png = subprocess.run(["rsvg-convert", "-w", "1024", "-h", "1024"],
                         input=svg(variant).encode(), capture_output=True, check=True).stdout
    im = Image.open(io.BytesIO(png)).convert("RGBA")
    flat = Image.new("RGB", im.size, (0, 0, 0))
    flat.paste(im, mask=im.split()[3])
    if variant == "tinted":
        flat = flat.convert("L").convert("RGB")
    return flat


if __name__ == "__main__":
    names = {"light": "AppIcon-1024.png", "dark": "AppIcon-1024-dark.png", "tinted": "AppIcon-1024-tinted.png"}
    for v, n in names.items():
        render(v).save(OUT / n, optimize=True)
        print(OUT / n)
