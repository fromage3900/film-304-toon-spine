"""Build the v04 storyboard-vs-render comparison sheet."""
from __future__ import annotations

from PIL import Image, ImageDraw
import os

PAGE = r"G:/film-304-toon-spine/Humber_FinalYear_Prep/Capstone_Pipeline_Scaffold/01_Preprod/Storyboard/SB_OfficeSpider_Page16.png"
STILLS = r"G:/film-304-toon-spine/Saved/Playblasts/Layout_62-66/stills"
OUT = r"G:/film-304-toon-spine/Saved/Playblasts/Layout_62-66/compare"

page = Image.open(PAGE).convert("RGB")
W, H = page.size
os.makedirs(OUT, exist_ok=True)
x0, x1 = 0.025, 0.975
y0, y1 = 0.055, 0.975
cols, rows = 4, 3
cw = (x1 - x0) / cols
ch = (y1 - y0) / rows
panels = [
    ("62", 0, 0), ("63A", 1, 0), ("63B", 2, 0), ("64A", 3, 0),
    ("64B", 0, 1), ("65", 1, 1), ("66A", 2, 1), ("66B", 3, 1),
]
stills = {
    "62": "v04_shot62.png", "63A": "v04_shot63a.png", "63B": "v04_shot63b.png",
    "64A": "v04_shot64a.png", "64B": "v04_shot64b.png", "65": "v04_shot65.png",
    "66A": "v04_shot66a.png", "66B": "v04_shot66b.png",
}
tiles = []
for label, c, r in panels:
    box = (int((x0 + c * cw) * W), int((y0 + r * ch) * H),
           int((x0 + (c + 1) * cw) * W), int((y0 + (r + 1) * ch) * H))
    crop = page.crop(box)
    sb = Image.new("RGB", (480, 270), (255, 255, 255))
    cc = crop.copy()
    cc.thumbnail((470, 255))
    sb.paste(cc, ((480 - cc.width) // 2, (270 - cc.height) // 2))
    d = ImageDraw.Draw(sb)
    d.text((8, 8), f"PANEL {label}", fill=(0, 0, 0))
    st = Image.new("RGB", (480, 270), (30, 30, 30))
    p = os.path.join(STILLS, stills[label])
    if os.path.exists(p):
        im = Image.open(p).convert("RGB")
        im.thumbnail((480, 270))
        st.paste(im, ((480 - im.width) // 2, (270 - im.height) // 2))
    dd = ImageDraw.Draw(st)
    dd.text((8, 8), f"v04 {label}", fill=(255, 255, 255))
    pair = Image.new("RGB", (960, 270), (0, 0, 0))
    pair.paste(sb, (0, 0))
    pair.paste(st, (480, 0))
    pair.save(os.path.join(OUT, f"compare_v04_{label}.png"))
    tiles.append(pair)
sheet = Image.new("RGB", (960, 270 * 8), (0, 0, 0))
for i, t in enumerate(tiles):
    sheet.paste(t, (0, i * 270))
sheet.save(os.path.join(OUT, "compare_v04_sheet.png"))
print("V04_COMPARE", os.path.join(OUT, "compare_v04_sheet.png"))
