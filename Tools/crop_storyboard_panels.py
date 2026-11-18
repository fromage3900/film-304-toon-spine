"""Crop the individual storyboard panels out of Dawn's 4x3 pages.

Panel borders are thick black rectangles on a white page, so a dark-pixel
projection finds the grid lines.
"""
import os, sys, json, itertools
import numpy as np
from PIL import Image

ROOT = r"G:\film-304-toon-spine"
SRC = os.path.join(ROOT, "Humber_FinalYear_Prep", "Capstone_Pipeline_Scaffold",
                   "01_Preprod", "Storyboard")
OUT = os.path.join(ROOT, "Saved", "Animatic", "Panels")
os.makedirs(OUT, exist_ok=True)

ROWS, COLS = 3, 4


def find_lines(profile, thresh):
    """Return the indices where the profile crosses above thresh, merged."""
    on = profile > thresh
    groups, start = [], None
    for i, v in enumerate(on):
        if v and start is None:
            start = i
        elif not v and start is not None:
            groups.append((start, i - 1))
            start = None
    if start is not None:
        groups.append((start, len(on) - 1))
    return [int((a + b) / 2) for a, b in groups]


def cluster(lines, gap=45):
    """Group nearby lines. Panel borders come in pairs with a gutter between."""
    out = []
    for v in sorted(lines):
        if out and v - out[-1][-1] <= gap:
            out[-1].append(v)
        else:
            out.append([v])
    return out


def crop_page(path, page_no):
    im = Image.open(path).convert("L")
    a = np.asarray(im, dtype=np.float32) / 255.0
    dark = (a < 0.40).astype(np.float32)

    colprof = dark.mean(axis=0)
    rowprof = dark.mean(axis=1)

    vc = cluster(find_lines(colprof, 0.30))
    hc = cluster(find_lines(rowprof, 0.30))

    if len(vc) < COLS + 1 or len(hc) < ROWS + 1:
        return {"page": page_no, "error": "grid not found",
                "vclusters": vc, "hclusters": hc}

    # choose the COLS+1 / ROWS+1 clusters whose gaps are most even
    def best(cl, k):
        if len(cl) == k:
            return cl
        best_g, best_v = None, None
        for combo in itertools.combinations(cl, k):
            gaps = [combo[i + 1][0] - combo[i][-1] for i in range(k - 1)]
            mean = sum(gaps) / len(gaps)
            var = sum((g - mean) ** 2 for g in gaps)
            if best_v is None or var < best_v:
                best_v, best_g = var, list(combo)
        return best_g

    vc = best(vc, COLS + 1)
    hc = best(hc, ROWS + 1)
    vc.sort(key=lambda g: g[0])
    hc.sort(key=lambda g: g[0])

    xs = [(g[0], g[-1]) for g in vc]   # (outer, inner) border of each cluster
    ys = [(g[0], g[-1]) for g in hc]

    rgb = Image.open(path).convert("RGB")
    panels = []
    n = 0
    for r in range(ROWS):
        for c in range(COLS):
            # panel spans from the RIGHT edge of this left-border cluster
            # to the LEFT edge of the next cluster
            x0 = xs[c][1] + 5
            x1 = xs[c + 1][0] - 5
            y0 = ys[r][1] + 5
            y1 = ys[r + 1][0] - 5
            if x1 <= x0 or y1 <= y0:
                continue
            n += 1
            out = os.path.join(OUT, "SB_p%02d_%02d.png" % (page_no, n))
            rgb.crop((x0, y0, x1, y1)).save(out)
            panels.append({"n": n, "rect": [x0, y0, x1, y1], "out": out})
    return {"page": page_no, "panels": len(panels), "detail": panels,
            "vclusters": vc, "hclusters": hc}


if __name__ == "__main__":
    pages = [int(x) for x in (sys.argv[1:] or [1, 2, 3])]
    report = []
    for p in pages:
        name = "SB_OfficeSpider_Page%d.png" % p if p < 4 else "SB_OfficeSpider_Page%02d.png" % p
        path = os.path.join(SRC, name)
        if not os.path.exists(path):
            report.append({"page": p, "error": "missing " + name})
            continue
        report.append(crop_page(path, p))
    json.dump(report, open(os.path.join(OUT, "crop_report.json"), "w"), indent=2)
    for r in report:
        print("page", r.get("page"), "panels", r.get("panels"), r.get("error", ""),
              "v", r.get("vlines"), "h", r.get("hlines"))
