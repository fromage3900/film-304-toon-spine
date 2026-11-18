"""Assemble the trim-sheet atlas, normal map and ORM from the COP2 tiles.

Atlas placement and map derivation are plain 2D work, done here rather than in
a COP network (a COP2 network takes its canvas size from its first node, which
makes large-atlas compositing awkward).
"""
import json, os
import numpy as np
from PIL import Image

OUT = r"G:\film-304-toon-spine\Film304_Packages\Office_TrimSheet_2026-11-17"
ATLAS = OUT + r"\01_Atlas"
TILE, COLS, ROWS = 512, 4, 2
AW, AH = TILE * COLS, TILE * ROWS

ORDER = ["tbar", "troffer", "duct", "panel", "base", "mullion", "slat", "reveal"]

def load(suffix, name):
    return np.asarray(Image.open(os.path.join(ATLAS, "_t_%s_%s.png" % (name, suffix))).convert("RGB"), dtype=np.float64)

TINTS = {"tbar": (0.55, 0.56, 0.58), "troffer": (0.88, 0.88, 0.86),
         "duct": (0.62, 0.64, 0.66), "panel": (0.78, 0.74, 0.68),
         "base": (0.70, 0.68, 0.64), "mullion": (0.30, 0.32, 0.36),
         "slat": (0.72, 0.70, 0.66), "reveal": (0.80, 0.78, 0.74)}

H = np.zeros((AH, AW, 3))
A = np.zeros((AH, AW, 3))
for i, name in enumerate(ORDER):
    r, c = divmod(i, COLS)
    ys, xs = r * TILE, c * TILE
    H[ys:ys + TILE, xs:xs + TILE] = load("h", name)
    a = load("a", name)
    # the COP2 tint multiply did not take (colour COP feeds multiply as alpha);
    # apply the per-tile tint here so the albedo carries the material colour
    A[ys:ys + TILE, xs:xs + TILE] = np.clip(a / 255.0 * np.array(TINTS[name]) * 255.0, 0, 255)

Image.fromarray(H.astype(np.uint8)).save(os.path.join(ATLAS, "T_OfficeTrim_Height_2048x1024.png"))
Image.fromarray(A.astype(np.uint8)).save(os.path.join(ATLAS, "T_OfficeTrim_Albedo_2048x1024.png"))

# ---- tangent-space normal from height (Sobel), OpenGL convention (+Y up)
g = H.mean(axis=2)
kx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float64)
ky = np.array([[1, 2, 1], [0, 0, 0], [-1, -2, -1]], dtype=np.float64)

def conv(img, k):
    pad = np.pad(img, 1, mode="edge")
    out = np.zeros_like(img)
    for dy in range(3):
        for dx in range(3):
            out += k[dy, dx] * pad[dy:dy + img.shape[0], dx:dx + img.shape[1]]
    return out

strength = 2.0
dx = conv(g, kx) * strength
dy = conv(g, ky) * strength
n = np.dstack([-dx, dy, np.ones_like(g)])
n /= np.linalg.norm(n, axis=2, keepdims=True)
N = ((n * 0.5) + 0.5) * 255.0
Image.fromarray(N.clip(0, 255).astype(np.uint8)).save(
    os.path.join(ATLAS, "T_OfficeTrim_Normal_2048x1024.png"))

# ---- ORM: R = AO (from height cavity), G = roughness, B = metallic
ao = 1.0 - np.clip((g.max() - g) / 255.0 * 1.5, 0, 1) * 0.6
rough = np.clip(0.55 + (g - 128) / 255.0 * 0.9, 0.08, 1.0)
met = np.zeros_like(g)
ORM = np.dstack([ao, rough, met])
Image.fromarray((ORM * 255).astype(np.uint8)).save(
    os.path.join(ATLAS, "T_OfficeTrim_ORM_2048x1024.png"))

# ---- report
rep = {"atlas": [AW, AH], "tile": TILE, "cols": COLS, "rows": ROWS, "order": ORDER,
       "maps": ["T_OfficeTrim_Height_2048x1024.png", "T_OfficeTrim_Albedo_2048x1024.png",
                "T_OfficeTrim_Normal_2048x1024.png", "T_OfficeTrim_ORM_2048x1024.png"],
       "normal_convention": "tangent space, OpenGL +Y up, derived from height (Sobel, strength 2.0)",
       "orm": "R = cavity AO from height, G = roughness, B = metallic (0)"}
for f in rep["maps"]:
    im = np.asarray(Image.open(os.path.join(ATLAS, f)).convert("RGB"), dtype=float)
    rep[f] = {"seam_left_right": round(float(np.abs(im[:, 0, :] - im[:, -1, :]).mean()), 4),
              "seam_top_bottom": round(float(np.abs(im[0, :, :] - im[-1, :, :]).mean()), 4)}

# the atlas is a LAYOUT: the seam guarantee is per tile, not across tile borders
tile_seams = {}
for name in ORDER:
    th = np.asarray(Image.open(os.path.join(ATLAS, "_t_%s_h.png" % name)).convert("RGB"), dtype=float)
    ta = np.asarray(Image.open(os.path.join(ATLAS, "_t_%s_a.png" % name)).convert("RGB"), dtype=float)
    tile_seams[name] = {
        "height_seam_left_right": round(float(np.abs(th[:, 0, :] - th[:, -1, :]).mean()), 4),
        "height_seam_top_bottom": round(float(np.abs(th[0, :, :] - th[-1, :, :]).mean()), 4),
        "albedo_seam_left_right": round(float(np.abs(ta[:, 0, :] - ta[:, -1, :]).mean()), 4),
        "albedo_seam_top_bottom": round(float(np.abs(ta[0, :, :] - ta[-1, :, :]).mean()), 4)}
rep["per_tile_seams"] = tile_seams
rep["note"] = ("atlas edges are tile BORDERS and are not expected to match; "
               "each 512x512 tile is seamless on both axes")
open(os.path.join(ATLAS, "atlas_report.json"), "w").write(json.dumps(rep, indent=2))
print(json.dumps(rep, indent=2))
