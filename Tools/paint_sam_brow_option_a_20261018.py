"""Brow Option A: paint stylized brow strokes into an overlay copy of Sam's face UDIM tile.

Source texture is never modified. Output:
  Saved/OfflineIntake/20261018/browA/SamSkin_Tile1_browA.png (+ comparison crop)
"""
from PIL import Image, ImageDraw, ImageFilter
from pathlib import Path

SRC = Path(r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\skin_tiles\Sam\SamSkin_Tile1.png")
OUT = Path(r"G:\film-304-toon-spine\Saved\OfflineIntake\20261018\browA\SamSkin_Tile1_browA.png")
OUT.parent.mkdir(parents=True, exist_ok=True)

base = Image.open(SRC).convert("RGB")
W, H = base.size

ink = (82, 52, 40)  # sRGB ~linear (0.088,0.055,0.042) — a hair lighter than Sam's hair tint
soft = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(soft)

def bezier(p0, p1, p2, t):
    x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
    y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
    return x, y

def brow(p0, mc, p2, wmax, alpha):
    pts = [bezier(p0, mc, p2, i / 40) for i in range(41)]
    for i in range(40):
        a, b = pts[i], pts[i + 1]
        t = i / 40
        w = wmax * (0.45 + 0.55 * (1 - abs(t - 0.5) * 2) ** 0.7)
        aa = int(alpha * 255 * (0.75 + 0.25 * (1 - abs(t - 0.5) * 2)))
        d.line([a, b], fill=ink + (aa,), width=max(2, int(round(w))))
        d.ellipse([a[0] - w * 0.4, a[1] - w * 0.4, a[0] + w * 0.4, a[1] + w * 0.4], fill=ink + (aa,))
        d.ellipse([b[0] - w * 0.4, b[1] - w * 0.4, b[0] + w * 0.4, b[1] + w * 0.4], fill=ink + (aa,))

# LEFT brow (image-left): apex toward outer third, inner tail a step higher toward the nose bridge
brow((812, 568), (852, 538), (918, 552), 17, 0.95)   # main stroke
brow((836, 552), (872, 528), (912, 540), 8, 0.55)    # soft accent above
brow((890, 556), (906, 548), (918, 552), 10, 0.8)    # inner tail thickening

# RIGHT brow (image-right): inner near bridge, apex x~1180, outer end lower
brow((1124, 552), (1180, 536), (1248, 566), 17, 0.95)
brow((1136, 540), (1188, 524), (1236, 546), 8, 0.55)
brow((1122, 550), (1130, 542), (1146, 546), 10, 0.8)

soft = soft.filter(ImageFilter.GaussianBlur(2.2))
outp = base.convert("RGBA")
outp.alpha_composite(soft)
outp = outp.convert("RGB")
outp.save(OUT)
print("wrote", OUT)

c = outp.crop((680, 360, 1340, 760)).resize((1320, 800))
c.save(r"C:\Users\froma\AppData\Local\Temp\opencode\sam_face_crop_browA.png")
print("crop saved")
