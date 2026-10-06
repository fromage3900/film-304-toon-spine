"""Generate the Painterly Gouache SDF texture set from pure stdlib.

WHY SEPARATE FROM build_textures.py
    build_textures.py runs INSIDE UE and owns the toon spine's texture library.
    The gouache fields are a different job (continuous surface fields, not cel
    masks) and need to be generated outside the editor so they can be reviewed
    and regenerated without launching UE - which matters here because the editor
    takes minutes per shader compile. This module imports no `unreal`, so it runs
    under plain CPython; the import into the project happens over Monolith.

WHAT GOUACHE ACTUALLY NEEDS (and why each field exists)
    Gouache is opaque, matte, and laid down in flat washes. Three things give it
    away that flat cel shading does not have:

    1. GRANULATION - pigment is heavier than the binder and settles into the
       tooth of the paper. The result is mottling that follows the SURFACE, not
       the light. `gen_granulation` is a tileable Worley F1 field: the cell
       interiors are where pigment pools.

    2. PAPER TOOTH - the high-frequency substrate the pigment settles into.
       `gen_paper_grain` is 4-octave tileable value noise. Kept separate from
       granulation because the two are scaled independently: a painter can have
       fine tooth with no pooling, or heavy pooling on smooth stock.

    3. BRUSH EDGE - the wet edge where a stroke meets its own boundary and the
       pigment collects into a darker rim. This is the single most recognisable
       gouache cue. `gen_brush_edge` is anisotropic noise stretched along the
       stroke direction, thresholded into hard ridges - a wash has a crisp edge,
       it does not fade.

    Plus `gen_wash_blotch`: very low frequency variation so a flat wash is never
    actually flat, which is what stops the result reading as airbrushed.

TILING
    Every field is periodic on its own size. Value noise interpolates a wrapping
    lattice and the Worley feature grid wraps its distance search, so there is no
    visible seam at UV 1.0 - a non-tiling field shows a hard grid line on every
    surface, which is the fastest way to make a material look procedural.

Run standalone:
    python Python/build_gouache_textures.py
Output: Saved/GeneratedTextures/gouache/T_Gouache_*.png
"""
from __future__ import annotations

import base64
import binascii
import json
import math
import random
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "Saved" / "GeneratedTextures" / "gouache"


# ---------------------------------------------------------------------------
# PNG writer - 8-bit greyscale (colour type 0), stdlib only.
#
# Greyscale, not RGB: these are DATA fields. RGB would triple the import size
# for no information, and an sRGB-enabled texture would gamma the ramp and
# destroy the field's meaning.
# ---------------------------------------------------------------------------

def write_png_gray(path: Path, width: int, height: int, rows) -> None:
    """rows: iterable of bytes, each exactly `width` long."""
    raw = b"".join(b"\x00" + bytes(r) for r in rows)

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", binascii.crc32(tag + data) & 0xFFFFFFFF))

    # colour type 0 = greyscale, bit depth 8
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", zlib.compress(raw, 9))
           + chunk(b"IEND", b""))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)


# ---------------------------------------------------------------------------
# Tileable noise primitives
# ---------------------------------------------------------------------------

def _smooth(t: float) -> float:
    """Smoothstep. Value noise interpolates with this, not linearly - linear
    interpolation leaves visible lattice creases in the gradient."""
    return t * t * (3.0 - 2.0 * t)


def value_noise(size: int, period: int, seed: int):
    """Tileable value noise on a `size`x`size` grid, lattice period `period`.

    Returns f(x, y) over reals. The lattice wraps at `period`, which is what
    makes the field seamless: f(period-1) and f(0) are adjacent cells, not a
    cliff.
    """
    rng = random.Random(seed)
    lat = [[rng.random() for _ in range(period)] for _ in range(period)]

    def f(x: float, y: float) -> float:
        xi, yi = int(math.floor(x)), int(math.floor(y))
        xf, yf = _smooth(x - xi), _smooth(y - yi)
        x0, y0 = xi % period, yi % period
        x1, y1 = (xi + 1) % period, (yi + 1) % period
        v00, v10 = lat[y0][x0], lat[y0][x1]
        v01, v11 = lat[y1][x0], lat[y1][x1]
        a = v00 + (v10 - v00) * xf
        b = v01 + (v11 - v01) * xf
        return a + (b - a) * yf

    return f


def make_fbm(size: int, octaves: int, base_period: int, seed: int,
             gain: float = 0.5):
    """Fractional Brownian motion over tileable value noise.

    Every octave's period stays an exact divisor of `size`, so all of them wrap
    on the same boundary and the sum does too.
    """
    layers = []
    period = base_period
    amp = 1.0
    total = 0.0
    for o in range(octaves):
        layers.append((value_noise(size, period, seed + o * 7919), amp, period))
        total += amp
        period *= 2
        amp *= gain

    def f(u: float, v: float) -> float:
        """u,v normalised 0..1 across the texture."""
        acc = 0.0
        for noise, a, p in layers:
            acc += a * noise(u * p, v * p)
        return acc / total

    return f


def aniso_noise(size: int, px: int, py: int, seed: int):
    """Tileable value noise with a DIFFERENT lattice period per axis.

    Anisotropy here comes from two periods, not from a stretch factor. Scaling
    one axis by a non-integer would break the wrap and put a seam on one edge;
    two integer periods both wrap cleanly, and their ratio sets the aspect.
    """
    rng = random.Random(seed)
    lat = [[rng.random() for _ in range(px)] for _ in range(py)]

    def f(x: float, y: float) -> float:
        xi, yi = int(math.floor(x)), int(math.floor(y))
        xf, yf = _smooth(x - xi), _smooth(y - yi)
        x0, x1 = xi % px, (xi + 1) % px
        y0, y1 = yi % py, (yi + 1) % py
        v00, v10 = lat[y0][x0], lat[y0][x1]
        v01, v11 = lat[y1][x0], lat[y1][x1]
        a = v00 + (v10 - v00) * xf
        b = v01 + (v11 - v01) * xf
        return a + (b - a) * yf

    return f


# ---------------------------------------------------------------------------
# Field generators - each returns (size, size, rows)
# ---------------------------------------------------------------------------

def gen_paper_grain(size: int = 256, seed: int = 20261003):
    """4-octave tileable tooth. Broad, high-frequency, no hard edges.

    Paper tooth is isotropic: it has no direction. Deliberately NOT combined with
    the brush field, because the two must stay independently scalable.
    """
    f = make_fbm(size, octaves=4, base_period=16, seed=seed, gain=0.55)
    rows = []
    for y in range(size):
        v = y / size
        row = bytearray()
        for x in range(size):
            # gentle contrast so the tooth reads as surface, not as noise
            n = 0.5 + (f(x / size, v) - 0.5) * 1.35
            n = min(1.0, max(0.0, n))
            row.append(int(round(n * 255.0)))
        rows.append(bytes(row))
    return size, size, rows


def gen_granulation(size: int = 256, cells: int = 96, seed: int = 4242,
                    tooth_seed: int = 20261003):
    """Fine pigment sediment that settles into the paper tooth's VALLEYS.

    REBUILT - the previous field was a plain Worley F1 with `cells=14`, which at
    the material's 6x tiling produced roughly six soft bubbles across the whole
    surface. That is not granulation, it is a stain, and it is why the first
    render read as generic and dirty: the effect was present at a scale the eye
    files under "mottling" instead of "pigment".

    Two changes, both grounded in how granulation actually works:

    1. FREQUENCY. `cells` goes 14 -> 96. Granulation is particle settling, so it
       lives at paper-tooth scale. The old field could not be tuned into working
       by moving a strength slider; the frequency itself was wrong, which is why
       the rebuild regenerates this texture instead of re-scaling it.

    2. TOOTH COUPLING. The field is now multiplied by the INVERTED paper tooth,
       so pigment pools in the grain's valleys and the peaks stay clean. The
       previous version was explicitly independent of the tooth ("a painter can
       have granulation without tooth"), and that independence is precisely why
       it never read as pigment - real granulation IS the tooth catching pigment.

    The tooth is generated here with the SAME parameters gen_paper_grain uses, so
    the two fields describe one paper rather than two unrelated noises.
    """
    rng = random.Random(seed)
    pts = [(rng.random(), rng.random()) for _ in range(cells)]

    tooth = make_fbm(size, octaves=4, base_period=16, seed=tooth_seed, gain=0.55)

    rows = []
    for y in range(size):
        v = y / size
        row = bytearray()
        for x in range(size):
            u = x / size
            best = 1e9
            for (px, py) in pts:
                # wrap-aware delta: the field must not know where the edge is,
                # otherwise the cell crossing UV 1.0 shows a visible seam
                dx = abs(px - u)
                dx = min(dx, 1.0 - dx)
                dy = abs(py - v)
                dy = min(dy, 1.0 - dy)
                d2 = dx * dx + dy * dy
                if d2 < best:
                    best = d2
            # Worley F1 shaped into soft sediment clumps, now HIGH frequency
            t = 1.0 - min(1.0, math.sqrt(best) * 3.4)
            t = t * t * (3.0 - 2.0 * t)

            # Valley mask: 1 where the grain is deep, 0 at the peaks.
            valley = 1.0 - tooth(u, v)
            # Bias toward the valleys but never fully zero the peaks - a hard
            # product reads as dirt on the high points instead of clean paper.
            valley = valley * 1.25 - 0.10
            valley = min(1.0, max(0.0, valley))

            sed = t * valley
            sed = min(1.0, max(0.0, sed))
            row.append(int(round(sed * 255.0)))
        rows.append(bytes(row))
    return size, size, rows


def gen_brush_edge(size: int = 256, angle_deg: float = 28.0, seed: int = 777):
    """Anisotropic tileable noise thresholded into hard ridges - the wet edge.

    Frequency is low along the stroke axis and high across it, which produces
    long parallel ridges like a loaded brush. Then hard-thresholded: a gouache
    wash has a crisp boundary, so a soft gradient here would read as airbrush
    and undo the whole effect. The ramp between lo and hi is deliberately short.
    """
    # px 4 / py 36 => streaks roughly 9x longer than they are wide
    n_along, n_across = 4, 36
    n = aniso_noise(size, n_along, n_across, seed)
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    # Threshold HIGH, not at the midpoint. At a midpoint threshold roughly half
    # the surface survives and the field becomes a hard barcode that renders as
    # stripes. Clipping only the PEAKS leaves a mostly-dark field crossed by thin
    # filaments, which is what a wet edge actually looks like: pigment collects
    # in a narrow rim, it does not cover the wash.
    lo, hi = 0.72, 0.86

    rows = []
    for y in range(size):
        v = y / size
        row = bytearray()
        for x in range(size):
            u = x / size
            # rotate into stroke space; both axes stay in 0..1 so both lattices
            # wrap on the same boundary and the rotated field still tiles
            ru = (u * ca + v * sa) % 1.0
            rv = (-u * sa + v * ca) % 1.0
            fv = n(ru * n_along, rv * n_across)
            if fv <= lo:
                t = 0.0
            elif fv >= hi:
                t = 1.0
            else:
                t = (fv - lo) / (hi - lo)
            row.append(int(round(t * 255.0)))
        rows.append(bytes(row))
    return size, size, rows


def gen_wash_blotch(size: int = 256, seed: int = 999):
    """Very low frequency wash variation. Keeps a flat wash from reading flat."""
    f = make_fbm(size, octaves=2, base_period=3, seed=seed, gain=0.6)
    rows = []
    for y in range(size):
        v = y / size
        row = bytearray()
        for x in range(size):
            n = 0.5 + (f(x / size, v) - 0.5) * 1.8
            n = min(1.0, max(0.0, n))
            row.append(int(round(n * 255.0)))
        rows.append(bytes(row))
    return size, size, rows
# ---------------------------------------------------------------------------
# Catalogue
# ---------------------------------------------------------------------------

CATALOG = [
    ("T_Gouache_PaperGrain", gen_paper_grain,
     "paper tooth substrate - high frequency, isotropic"),
    ("T_Gouache_Granulation", gen_granulation,
     "pigment pooling - Worley F1, the granulation cue"),
    ("T_Gouache_BrushEdge", gen_brush_edge,
     "wet edge / palette-knife ridges - the strongest gouache tell"),
    ("T_Gouache_WashBlotch", gen_wash_blotch,
     "low-frequency wash variation so a wash is never flat"),
]


def build(out_dir: Path = OUT_DIR) -> dict:
    """Generate every field, write the PNGs, and report per-texture statistics.

    The statistics are not decoration. A generator that silently produced a flat
    or clipped image would import without complaint and then render as nothing,
    so min/max/distinct are measured here rather than discovered in a render.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    report = {"out_dir": str(out_dir), "textures": {}, "errors": []}

    for name, gen, why in CATALOG:
        try:
            w, h, rows = gen()
            png_path = out_dir / f"{name}.png"
            write_png_gray(png_path, w, h, rows)
            raw = png_path.read_bytes()

            vals = [b for r in rows for b in r]
            stats = {
                "path": str(png_path),
                "width": w, "height": h,
                "bytes": len(raw),
                "bytes_b64": base64.b64encode(raw).decode("ascii"),
                "min": min(vals), "max": max(vals),
                "mean": round(sum(vals) / len(vals), 2),
                "distinct_values": len(set(vals)),
                "why": why,
            }
            # a field with almost no distinct values is a broken generator
            if stats["distinct_values"] < 8:
                stats["warning"] = "nearly flat - generator likely degenerate"
                report["errors"].append(
                    f"{name}: only {stats['distinct_values']} distinct values")
            if stats["max"] - stats["min"] < 32:
                stats["warning"] = "very low contrast"
            report["textures"][name] = stats
        except Exception as exc:
            report["errors"].append(f"{name}: {exc}")

    report["ok"] = not report["errors"]
    return report


if __name__ == "__main__":
    rep = build()
    # omit the base64 from the console summary, it is far too large to read
    slim = {k: {kk: vv for kk, vv in v.items() if kk != "bytes_b64"}
            for k, v in rep["textures"].items()}
    print(json.dumps({"ok": rep["ok"], "out_dir": rep["out_dir"],
                      "textures": slim, "errors": rep["errors"]}, indent=2))
    sys.exit(0 if rep["ok"] else 1)