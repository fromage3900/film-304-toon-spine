# Tools/melusina/compose_editorial.py
import json, os, math
from PIL import Image, ImageDraw, ImageFont
import numpy as np

ROOT = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1"
PREVIEW = os.path.join(ROOT, "preview")

INK = (17, 17, 17)
GRAPHITE = (68, 68, 68)
MUTED = (128, 128, 128)
HAIRLINE = (224, 224, 224)
ACCENT = (63, 93, 107)
WHITE = (255, 255, 255)

ARIAL = r"C:\Windows\Fonts\arial.ttf"
ARIAL_B = r"C:\Windows\Fonts\arialbd.ttf"
GEORGIA = r"C:\Windows\Fonts\georgia.ttf"

def f(path, size):
    return ImageFont.truetype(path, size)

def crop_content(im, threshold=245, margin=18):
    arr = np.asarray(im.convert("L"))
    mask = arr < threshold
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return im
    x0 = max(int(xs.min()) - margin, 0)
    y0 = max(int(ys.min()) - margin, 0)
    x1 = min(int(xs.max()) + margin, im.width)
    y1 = min(int(ys.max()) + margin, im.height)
    return im.crop((x0, y0, x1, y1))

def fit(im, w, h):
    scale = min(w / float(im.width), h / float(im.height))
    return im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)

def build_sheet(panels, cols, rows, tw, th, title, subtitle, out_path, spec, note):
    gap, margin, header = 24, 56, 160
    label_h = 30
    W = margin * 2 + cols * tw + (cols - 1) * gap
    H = header + rows * (th + label_h) + (rows - 1) * 16 + 100
    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)
    d.text((margin, 34), title, font=f(GEORGIA, 64), fill=INK)
    d.text((margin + 2, 110), subtitle, font=f(ARIAL, 18), fill=GRAPHITE)
    meta1 = "BRENNAN SHEPHERD"
    meta2 = "MAYA 2027  /  66-JOINT HIK"
    d.text((W - margin - d.textlength(meta1, font=f(ARIAL_B, 13)), 44), meta1, font=f(ARIAL_B, 13), fill=INK)
    d.text((W - margin - d.textlength(meta2, font=f(ARIAL, 12)), 66), meta2, font=f(ARIAL, 12), fill=MUTED)
    d.line([margin, 146, W - margin, 146], fill=ACCENT, width=2)

    for idx, (name, label) in enumerate(panels):
        col = idx % cols
        row = idx // cols
        x = margin + col * (tw + gap)
        y = header + row * (th + label_h + 16)
        im = Image.open(os.path.join(PREVIEW, name)).convert("RGBA")
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(bg, im).convert("RGB")
        im = crop_content(im)
        im = fit(im, tw, th)
        px = x + (tw - im.width) // 2
        py = y + (th - im.height) // 2
        img.paste(im, (px, py))
        d.line([x, y + th + 4, x + tw, y + th + 4], fill=HAIRLINE, width=1)
        d.text((x, y + th + 9), label, font=f(ARIAL_B, 12), fill=GRAPHITE)

    sy = H - 92
    d.line([margin, sy, W - margin, sy], fill=HAIRLINE, width=1)
    d.text((margin, sy + 12), spec, font=f(ARIAL, 11), fill=GRAPHITE)
    d.text((margin, sy + 34), note, font=f(ARIAL, 10), fill=MUTED)
    img.save(out_path, quality=95)
    print("saved", out_path)

def main():
    probe = json.load(open(os.path.join(ROOT, "report", "probe_portfolio.json"), encoding="utf-8"))
    ds = [math.dist(a, b) for a, b in zip(probe["pos_bind"], probe["pos_portfolio"])]
    mean_d = sum(ds) / len(ds)
    max_d = max(ds)
    hair = json.load(open(os.path.join(ROOT, "report", "hair_verify.json"), encoding="utf-8"))
    hair_verts = sum(h["vertices"] for h in hair["hair"])
    hair_sc = len(hair["hair"])
    spec = "66 JOINTS  |  25 MESHES  |  3 HAIR MESHES / {:,} VERTS  |  4 INFLUENCES  |  MAYA 2027  |  CM / FILM / Y-UP".format(hair_verts)
    note = "Weights verified from skinCluster.weightList: sums 1.000, max 4 influences. Hair skinClusters: {}. Bind-to-portfolio sample vertex delta: mean {:.1f} cm / max {:.1f} cm.".format(hair_sc, mean_d, max_d)

    panels = [
        ("v2_bind_three_quarter.png", "BIND  /  3-4"),
        ("v2_bind_front.png", "BIND  /  FRONT"),
        ("v2_bind_back.png", "BIND  /  BACK"),
        ("v2_hair_head.png", "HAIR  /  DETAIL"),
        ("v2_portfolio_three_quarter.png", "PORTFOLIO  /  3-4"),
        ("v2_portfolio_front.png", "PORTFOLIO  /  FRONT"),
        ("v2_bones_three_quarter.png", "SKELETON  /  3-4"),
        ("v2_bones_front.png", "SKELETON  /  FRONT"),
    ]
    build_sheet(panels, 4, 2, 360, 480, "MELUSINA", "HUMANI K DEFORM RIG  /  ASSIGNMENT 1",
                os.path.join(PREVIEW, "Brennan_Shepherd_Assignment1_editorial_sheet.png"), spec, note)

    portfolio_panels = [
        ("v2_portfolio_three_quarter.png", "PORTFOLIO  /  3-4"),
        ("v2_portfolio_front.png", "PORTFOLIO  /  FRONT"),
        ("v2_hair_head.png", "HAIR  /  DETAIL"),
        ("v2_bones_three_quarter.png", "SKELETON  /  3-4"),
    ]
    build_sheet(portfolio_panels, 2, 2, 480, 640, "MELUSINA", "HUMANI K DEFORM RIG  /  PORTFOLIO POSE",
                os.path.join(PREVIEW, "Brennan_Shepherd_Assignment1_editorial_portfolio_sheet.png"), spec, note)

main()