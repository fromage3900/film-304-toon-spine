"""Build the toon texture library from code - PNGs generated, never hand-made.

WHY GENERATED (CONTENT_CONVENTIONS: assets are generated from code)
    The film repo ships zero T_* textures. Melodia's Content/Stylization holds
    the proven set (T_Dither_Bayer, T_Hatch_Cross, T_Hatch_Diagonal,
    T_Ramp_2Band/3Band/4Band/Smooth, T_Noise_White) but copying .uasset files
    between projects is the documented failure - a copied asset keeps its old
    package path and can silently drop its content (AUDIT_2026-09-30 findings,
    spine_lib.py header). So the VALUES are ported and the pixels are
    regenerated here from pure stdlib (zlib/struct), and this builder is the
    source of truth.

    No PIL and no numpy in this Python - hence the inline PNG writer.

WHAT THESE ARE FOR
    T_Dither_Bayer        ordered dither - exact 16-level Bayer, needs nearest
                          filtering and NO BC compression (it would corrupt it)
    T_Hatch_Cross         cross-hatch ink for ToonProfile
                          ShadowHatchingPatternTexture
    T_Hatch_Diagonal      single-direction hatch
    T_HatchPattern        the canonical name referenced by BOTH
                          specs/humber_toon_spine/humber_toon_spine_manifest
                          .v1.json (shading_pipeline.hatching_pattern) and
                          Melodia's specs/toon_profiles/tp_melusina.json.
                          Dangling in both repos - this creates it.
    T_Ramp_*              luminance -> colour LUTs for MF_RampLUT
                          (coloured shadow, never neutral: the manifest's
                          canonical #352D40 warm-violet shadow)
    T_Noise_White         band-breakup noise for DiffuseRampOffsetTexture
    T_SDF_Strokes         baked signed-distance stroke field (RG) for
                          MF_ProceduralPatterns CellIndex 12; R = continuous
                          triangle distance (bilinear-safe soft edges),
                          G = per-stroke width jitter hash
    T_SDF_{Cross,Dots,Scales,Cracks,Leaf}
                          the tilable SDF map library (2026-10-03): engraving
                          cross-hatch, soft halftone dots, scale/feather
                          arcs, Worley-border cracks, and the leaf cover
                          field the foliage master cuts opacity on. All RG:
                          R = mark field in the house polarity (1 at the
                          mark, 0 clear) except Leaf (1 = inside cover),
                          G = per-cell width jitter; sRGB off, wrap,
                          lossless, no mips, tile-exact integer periods

SETTINGS THAT MATTER (applied defensively and READ BACK into the report -
enum member names move between engine versions, so nothing is assumed to have
worked):
    dither/hatch  sRGB off (data), nearest/bilinear, no mips, lossless
    ramps         sRGB on (colour), TA_Clamp so lum=0 and lum=1 hit the ends
                  exactly instead of wrapping
    masks         TA_Wrap - they tile across a surface

Output: Content/Materials/Textures/*.uasset  (PNGs under Saved/, gitignored)
Verify: Saved/Audit/texture_build_report.json - assert on the FILE.
"""
from __future__ import annotations

import binascii
import json
import math
import random
import struct
import sys
import zlib
from pathlib import Path

import unreal

# Report + PNG staging live in Saved/, not next to the source. This is not
# cosmetic: .gitignore only re-includes Saved/Audit/*.{json,md,txt}, so a report
# written into Python/ would land in the source tree as an untracked file on
# every regeneration - exactly the "generated output committed by accident" trap
# CONTENT_CONVENTIONS.md warns about.
OUT = (Path(__file__).resolve().parents[1] / "Saved" / "Audit"
       / "texture_build_report.json")
TEX_DIR = "/Game/Materials/Textures"
PNG_DIR = Path(__file__).resolve().parents[1] / "Saved" / "GeneratedTextures"

# The manifest's canonical shadow: warm violet, carries colour, never black.
SHADOW = (53, 45, 64)      # #352D40
LIGHT = (255, 255, 255)
MID = (140, 128, 160)


# ---------------------------------------------------------------------------
# PNG writer - 8-bit RGB (colour type 2), no third-party dependency
# ---------------------------------------------------------------------------

def write_png(path: Path, width: int, height: int, rows) -> None:
    """rows: iterable of bytes, each exactly width*3 long."""
    raw = b"".join(b"\x00" + bytes(r) for r in rows)  # filter byte 0 per scanline

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", binascii.crc32(tag + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", zlib.compress(raw, 9))
           + chunk(b"IEND", b""))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)


# ---------------------------------------------------------------------------
# Pattern generators - each returns (width, height, rows)
# ---------------------------------------------------------------------------

# Standard 4x4 ordered-dither threshold matrix (Bayer). Values 0..15.
BAYER4 = [[0, 8, 2, 10],
          [12, 4, 14, 6],
          [3, 11, 1, 9],
          [15, 7, 13, 5]]


def gen_dither(size: int = 64):
    """Bayer 4x4 tiled to size. Greyscale as RGB, 16 exact levels."""
    rows = []
    for y in range(size):
        row = bytearray()
        for x in range(size):
            v = int(round((BAYER4[y % 4][x % 4] + 0.5) / 16.0 * 255.0))
            row += bytes((v, v, v))
        rows.append(bytes(row))
    return size, size, rows


def gen_hatch(size: int = 128, spacing: int = 16, width_px: int = 3,
              cross: bool = True):
    """Diagonal hatch. White = ink line, black = clear.

    cross=True adds the 135-degree family (engraving / pencil hatch). Lines are
    drawn hard - a cel look wants a step, not an antialiased gradient, which is
    the same reasoning SDF_PATTERN_PIPELINE.md gives for thresholding fields.
    """
    rows = []
    for y in range(size):
        row = bytearray()
        for x in range(size):
            on = (x + y) % spacing < width_px
            if cross:
                on = on or ((x - y) % spacing) < width_px  # python % >= 0
            row += bytes((255, 255, 255)) if on else bytes((0, 0, 0))
        rows.append(bytes(row))
    return size, size, rows


def _lut_colour(t, stops):
    """Piecewise colour along 0..1 against [(pos, (r,g,b)), ...]."""
    if t <= stops[0][0]:
        return stops[0][1]
    for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
        if t <= p1:
            f = 0.0 if p1 == p0 else (t - p0) / (p1 - p0)
            return tuple(int(round(c0[i] + (c1[i] - c0[i]) * f)) for i in range(3))
    return stops[-1][1]


def _snap(t, stops):
    """Quantise t onto plateau centres - flat bands for a hard cel ramp."""
    edges = [p for p, _ in stops]
    best = edges[0]
    for p in edges:
        if t >= p:
            best = p
    idx = edges.index(best)
    if idx + 1 < len(edges):
        return best + (edges[idx + 1] - best) * 0.4
    return best


def gen_ramp(stops, width: int = 256, height: int = 8, hard: bool = False):
    """Horizontal luminance->colour strip. Rows identical (sampled at y=0.5).

    hard=True snaps each segment to a flat plateau with a short transition -
    a band ramp. hard=False is the smooth gradient.
    """
    rows = []
    for _ in range(height):
        row = bytearray()
        for x in range(width):
            t = x / (width - 1)
            if hard:
                t = _snap(t, stops)
            r, g, b = _lut_colour(t, stops)
            row += bytes((r, g, b))
        rows.append(bytes(row))
    return width, height, rows


def gen_noise(size: int = 64, seed: int = 1337):
    """Deterministic white noise - identical pixels on every machine and run."""
    rng = random.Random(seed)
    rows = []
    for _ in range(size):
        row = bytearray()
        for _ in range(size):
            v = rng.randint(0, 255)
            row += bytes((v, v, v))
        rows.append(bytes(row))
    return size, size, rows


def _hash01(a, b, ka, kb):
    """frac(sin(a*ka + b*kb) * 43758.5453) - the standard cheap value hash.

    python % already returns non-negative for positive modulus, but a negative
    sin product would need the +1.0 correction, so it is explicit here.
    """
    v = (math.sin(a * ka + b * kb) * 43758.5453) % 1.0
    return v if v >= 0.0 else v + 1.0


def gen_sdf_cross(size: int = 256, strokes: int = 8,
                  wave_amp: float = 0.30, wave_cycles: int = 3):
    """Baked cross-hatch SDF - the nearest mark of two wavy line families.

    The texture sibling of _crosshatch (CellIndex 5): family A runs along
    (u+v), family B along (u-v), each sine-displaced so the crossing reads as
    pen work rather than a wire grid. R = max of the two families' fields -
    house polarity (1 at the stroke centre, 0 in clear space) - so it flows
    through the same Density/Softness cut as every other pattern. G = family
    A's per-stroke width hash. Tiles exactly: each family's coordinate
    advances an integer number of strokes across u, and the wave completes
    integer cycles across v.
    """
    rows = []
    for y in range(size):
        v = y / size
        wv = wave_amp * math.sin(2.0 * math.pi * wave_cycles * v)
        row = bytearray()
        for x in range(size):
            u = x / size
            s_a = (u + v) * strokes + wv
            s_b = (u - v) * strokes + wv
            fa = abs(2.0 * (s_a - math.floor(s_a)) - 1.0)
            fb = abs(2.0 * (s_b - math.floor(s_b)) - 1.0)
            r = max(fa, fb)
            cell = int(math.floor(s_a)) % strokes
            g = _hash01(cell, 0.0, 12.9898, 78.233)
            row += bytes((int(r * 255), int(g * 255), 128))
        rows.append(bytes(row))
    return size, size, rows


def gen_sdf_dots(size: int = 256, rows_n: int = 10):
    """Soft-edged dot field on a half-offset lattice - the baked halftone.

    The texture sibling of _halftone (CellIndex 0): alternate rows offset by
    half a cell, and the dot edge is a CONTINUOUS distance falloff, so
    bilinear filtering yields soft screentone dots the analytic lattice
    cannot produce without aliasing. R = 1 at the dot centre, saturating to 0
    at half a cell out; G = per-dot width hash for the material's jitter.
    rows_n must be EVEN - the half-offset pattern repeats after two rows.
    """
    if rows_n % 2:
        raise ValueError("rows_n must be even for the offset lattice to tile")
    rows = []
    for y in range(size):
        v = y / size
        j = int(v * rows_n)
        fv = v * rows_n - j
        row = bytearray()
        for x in range(size):
            u = x / size
            i = int(u * rows_n)
            fu = u * rows_n - i
            dx = fu - (0.5 + 0.5 * (j % 2))
            dy = fv - 0.5
            if dx > 0.5:        # the governing centre may sit one cell across
                dx -= 1.0       # the half-offset seam - wrap the distance
            elif dx < -0.5:
                dx += 1.0
            d = math.hypot(dx, dy)
            r = 1.0 - d / 0.5
            if r < 0.0:
                r = 0.0
            cell = (i + j * rows_n) % (rows_n * rows_n)
            g = _hash01(cell, 0.0, 12.9898, 78.233)
            row += bytes((int(r * 255), int(g * 255), 128))
        rows.append(bytes(row))
    return size, size, rows


def gen_sdf_scales(size: int = 256, rows_n: int = 8):
    """Scale/feather arcs - the baked mark for Melusina's tail and roof tiles.

    Each row's visible boundary is the arc of the row ABOVE's circles
    (half-offset rows), so the field is distance to that arc only - the
    classic fish-scale / roof-tile rhythm. R = 1 ON the arc, fading to 0
    within 6% of a cell (thin arcs; the Density cut thickens them); G =
    per-cell width hash. Tiles with an integer rows_n.
    """
    rows = []
    for y in range(size):
        v = y / size
        j = int(v * rows_n)
        fv = v * rows_n - j
        row = bytearray()
        for x in range(size):
            u = x / size
            i = int(u * rows_n)
            fu = u * rows_n - i
            # the governing circle: row above (j+1), half-offset in x.
            # row k's centres sit at x = i + 0.5 + 0.5*(k % 2) within the row;
            # in row j's frame the centre above is at fv = -0.5 (one cell up,
            # half a cell over) - BUGFIX 2026-10-03: this used fv - 1.5 (two
            # rows up), which put the radius-0.5 ring tangent to the border
            # and the field read all-zero.
            cx = (0.5 + 0.5 * ((j + 1) % 2)) - fu
            if cx > 0.5:
                cx -= 1.0
            elif cx < -0.5:
                cx += 1.0
            cy = fv + 0.5                   # centre of the row above
            d = math.hypot(cx, cy)
            r = 1.0 - abs(d - 1.0) / 0.06   # arc ring at radius 1.0 cell
            if r < 0.0:
                r = 0.0
            cell = (i + j * rows_n) % (rows_n * rows_n)
            g = _hash01(cell, 0.0, 12.9898, 78.233)
            row += bytes((int(r * 255), int(g * 255), 128))
        rows.append(bytes(row))
    return size, size, rows


def gen_sdf_cracks(size: int = 256, cells: int = 6, jitter: float = 0.35):
    """Crack network - the baked Worley-border mark (stone, dry earth, plaster).

    F2-F1 of a jittered lattice: zero on the cell border, so R is INVERTED to
    the house mark polarity (1 ON the crack, fading out over the border
    band). The 3x3 search tracks the two smallest SQUARED distances (sqrt is
    monotonic, argmin unchanged) around per-cell feature points from the
    standard hash, with per-cell jitter on the feature position. G = per-cell
    width hash. Tiles with an integer `cells`.
    """
    pts = {}
    for j in range(-1, cells + 1):
        for i in range(-1, cells + 1):
            ci, cj = i % cells, j % cells
            h1 = _hash01(ci, cj, 127.1, 311.7)
            h2 = _hash01(ci, cj, 269.5, 183.3)
            pts[(i, j)] = (i + (h1 - 0.5) * 2.0 * jitter + 0.5,
                           j + (h2 - 0.5) * 2.0 * jitter + 0.5)
    rows = []
    for y in range(size):
        v = y / size * cells
        cv = int(math.floor(v))
        row = bytearray()
        for x in range(size):
            u = x / size * cells
            cu = int(math.floor(u))
            d1 = d2 = 1e9
            for dj in (-1, 0, 1):
                for di in (-1, 0, 1):
                    fx, fy = pts[(cu + di, cv + dj)]
                    dd = (u - fx) ** 2 + (v - fy) ** 2
                    if dd < d1:
                        d2 = d1
                        d1 = dd
                    elif dd < d2:
                        d2 = dd
            c = math.sqrt(d2) - math.sqrt(d1)
            r = 1.0 - min(1.0, c / 0.14)
            if r < 0.0:
                r = 0.0
            cell = (cu % cells) + (cv % cells) * cells
            g = _hash01(cell, 0.0, 12.9898, 78.233)
            row += bytes((int(r * 255), int(g * 255), 128))
        rows.append(bytes(row))
    return size, size, rows


def gen_sdf_leaf(size: int = 256, leaves: int = 7, seed: int = 90210):
    """Leaf-cluster cover field - the foliage master's opacity mask source.

    Unioned capsules (a leaf = stalk segment with a radius), soft silhouette
    edges, geometry from a seeded RNG so every regeneration is identical.
    R = 1 INSIDE the cover, saturating to 0 at the silhouette - the master
    cuts opacity on R; G = per-leaf hash, spare for width variation.
    Leaves keep a margin from the tile edge so the cluster tiles without
    clipped silhouettes; best used 1:1 per card rather than repeated across
    a surface.
    """
    rng = random.Random(seed)
    # margin must exceed radius + falloff so the soft silhouette stays inside
    # the tile (radius up to 0.09 + 0.05 falloff = 0.14; 0.16 keeps slack).
    # BUGFIX 2026-10-03: 0.12 let the falloff cross the tile edge (seam v=77).
    margin = 0.16
    segs = []
    for _ in range(leaves):
        cx = rng.uniform(margin, 1.0 - margin)
        cy = rng.uniform(margin, 1.0 - margin)
        ang = rng.uniform(0.0, 2.0 * math.pi)
        ln = rng.uniform(0.18, 0.42)
        rad = rng.uniform(0.045, 0.09)
        segs.append((cx, cy, ang, ln, rad))
    cosl = [(math.cos(a), math.sin(a)) for (_, _, a, _, _) in segs]
    rows = []
    for y in range(size):
        py = y / size
        row = bytearray()
        for x in range(size):
            px = x / size
            cover = 0.0
            for k, (cx, cy, _, ln, rad) in enumerate(segs):
                ex = cx + cosl[k][0] * ln * 0.5
                ey = cy + cosl[k][1] * ln * 0.5
                sx = cx - cosl[k][0] * ln * 0.5
                sy = cy - cosl[k][1] * ln * 0.5
                vx, vy = px - sx, py - sy
                wx, wy = ex - sx, ey - sy
                l2 = wx * wx + wy * wy
                t = 0.0 if l2 == 0.0 else (vx * wx + vy * wy) / l2
                t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
                dxp = px - (sx + wx * t)
                dyp = py - (sy + wy * t)
                d = math.hypot(dxp, dyp) - rad
                c = 0.5 - d / 0.10
                if c > cover:
                    cover = c
            r = 0.0 if cover < 0.0 else (1.0 if cover > 1.0 else cover)
            row += bytes((int(r * 255), 128, 128))
        rows.append(bytes(row))
    return size, size, rows


def gen_sdf_strokes(size: int = 256, strokes: int = 6,
                    wave_amp: float = 0.45, wave_cycles: int = 3):
    """Baked signed-distance stroke field - the texture sibling of _crosshatch.

    Sampled by MF_ProceduralPatterns CellIndex 12 through the same
    Density/Softness cut as the analytic patterns. Baking buys what an
    analytic frac() chain cannot: the field is a CONTINUOUS triangle of the
    wrapped stroke coordinate, so bilinear filtering produces wide clean soft
    edges without sawtooth wrap seams, and a sine displacement bends the
    strokes organically.

    R = |2*frac(s) - 1| with s = u*strokes + wave_amp*sin(2*pi*wave_cycles*v).
    1 at the stroke centre, 0 midway between strokes - _grid's polarity, so a
    low Density inks wide strokes and a high Density thins them.
    G = hash of the nearest stroke index (round(s) mod strokes, standard
    12.9898 / 78.233 / 43758.5453 GLSL hash) for per-stroke width jitter.
    Looked up by NEAREST stroke so the wrapped seam stroke resolves to the
    same cell on both sides of the tile edge.
    B = 128 spare.

    Tiles exactly: s advances by `strokes` (an integer) across u, and the
    wave completes wave_cycles integer periods across v.
    """
    rows = []
    for y in range(size):
        v = y / size
        wave = wave_amp * math.sin(2.0 * math.pi * wave_cycles * v)
        row = bytearray()
        for x in range(size):
            u = x / size
            s = u * strokes + wave
            fr = s - math.floor(s)
            r = abs(2.0 * fr - 1.0)
            cell = int(round(s)) % strokes
            g = (math.sin(cell * 12.9898 + 78.233) * 43758.5453) % 1.0
            if g < 0:
                g += 1.0
            row += bytes((int(r * 255), int(g * 255), 128))
        rows.append(bytes(row))
    return size, size, rows


# ---------------------------------------------------------------------------
# Catalogue
# ---------------------------------------------------------------------------

# (name, generator, sRGB, filter, address, compression, mips, why)
# sRGB off for masks (they are data, not colour), on for colour ramps.
# Compression must be LOSSLESS for the dither: BC averages 4x4 blocks, which
# would destroy the 16 exact Bayer levels.
CATALOG = [
    ("T_Dither_Bayer", lambda: gen_dither(64), False, "nearest", "wrap",
     "maskless", False,
     "Ordered dither. Needs exact levels + nearest + no mips, or it is garbage."),
    ("T_Hatch_Cross", lambda: gen_hatch(128, cross=True), False, "bilinear",
     "wrap", "maskless", False,
     "Cross-hatch ink for ToonProfile.ShadowHatchingPatternTexture."),
    ("T_Hatch_Diagonal", lambda: gen_hatch(128, cross=False), False, "bilinear",
     "wrap", "maskless", False,
     "Single-direction hatch - lighter than cross for mid-tone shadow."),
    ("T_HatchPattern", lambda: gen_hatch(128, cross=True), False, "bilinear",
     "wrap", "maskless", False,
     "Canonical name referenced by humber_toon_spine_manifest.v1.json "
     "(shading_pipeline.hatching_pattern) and Melodia tp_melusina.json - "
     "dangling in both repos until now."),
    ("T_Ramp_2Band", lambda: gen_ramp(_BAND2, hard=True), True, "bilinear",
     "clamp", "maskless", False,
     "Hard two-tone: violet shadow -> light. For bUsePaintedRamp."),
    ("T_Ramp_3Band", lambda: gen_ramp(_BAND3, hard=True), True, "bilinear",
     "clamp", "maskless", False,
     "Three plateau cel ramp - the stock UE cel shape."),
    ("T_Ramp_4Band", lambda: gen_ramp(_BAND4, hard=True), True, "bilinear",
     "clamp", "maskless", False,
     "Four plateau ramp for richer architecture falloff."),
    ("T_Ramp_Smooth", lambda: gen_ramp(_BAND3, hard=False), True, "bilinear",
     "clamp", "maskless", False,
     "No terminator at all - soft gradient for background/airbrushed depth."),
    ("T_Noise_White", lambda: gen_noise(64), False, "bilinear", "wrap",
     "maskless", True,
     "Band-breakup noise for ToonProfile.DiffuseRampOffsetTexture."),
    ("T_SDF_Strokes", lambda: gen_sdf_strokes(), False, "bilinear", "wrap",
     "maskless", False,
     "Baked signed-distance stroke field for MF_ProceduralPatterns "
     "CellIndex 12 (SDFMap). A continuous triangle of the wrapped stroke "
     "coordinate: bilinear-safe wide soft edges the analytic frac() chain "
     "cannot give without aliasing. G carries per-stroke width jitter."),
    ("T_SDF_Cross", lambda: gen_sdf_cross(), False, "bilinear", "wrap",
     "maskless", False,
     "Baked cross-hatch SDF: max of two sine-displaced (u+v)/(u-v) line "
     "families - CellIndex 12's engraving sibling. G = width jitter."),
    ("T_SDF_Dots", lambda: gen_sdf_dots(), False, "bilinear", "wrap",
     "maskless", False,
     "Baked halftone SDF: soft-edged dots on a half-offset lattice "
     "(rows_n even). G = per-dot size jitter."),
    ("T_SDF_Scales", lambda: gen_sdf_scales(), False, "bilinear", "wrap",
     "maskless", False,
     "Baked scale/feather arcs (half-offset rows, arc of the row above): "
     "Melusina's tail, roof tiles, feather rows. G = width jitter."),
    ("T_SDF_Cracks", lambda: gen_sdf_cracks(), False, "bilinear", "wrap",
     "maskless", False,
     "Baked Worley-border crack network (F2-F1, inverted to mark polarity): "
     "stone, dry earth, plaster. G = per-cell width jitter."),
    ("T_SDF_Leaf", lambda: gen_sdf_leaf(), False, "bilinear", "wrap",
     "maskless", False,
     "Leaf-cluster cover SDF (unioned capsules, seeded RNG) - the foliage "
     "master's opacity mask source. R = cover, soft silhouette edges."),
]

# Coloured-shadow stops. #352D40 warm violet is the manifest's canonical
# shadow (spec/toon_profiles/tp_melusina.json: shadow carries colour).
_BAND2 = [(0.0, SHADOW), (0.5, SHADOW), (0.5, LIGHT), (1.0, LIGHT)]
_BAND3 = [(0.0, SHADOW), (0.30, SHADOW), (0.30, MID),
          (0.70, MID), (0.70, LIGHT), (1.0, LIGHT)]
_BAND4 = [(0.0, SHADOW), (0.25, SHADOW), (0.25, MID),
          (0.50, MID), (0.50, (190, 182, 205)), (0.75, (190, 182, 205)),
          (0.75, LIGHT), (1.0, LIGHT)]


# ---------------------------------------------------------------------------
# Defensive enum resolution - member names move between engine builds, so
# candidates are tried and the one that resolved is RECORDED, not assumed.
# ---------------------------------------------------------------------------

def _pick(candidates, members, upper=True):
    """First candidate present in `members`, trying case variants."""
    for cand in candidates:
        for variant in ({cand, cand.upper(), cand.title()} if upper else {cand}):
            if variant in members:
                return variant
    return None


RESOLVED = {}


def _resolve_all():
    """Resolve each setting enum by direct member probing, and record the result.

    REGRESSION NOTE 2026-10-02: a previous version located the enum CLASS by
    scanning dir(unreal) with a regex and reading cls.__members__. On this build
    that returned empty for all seven, so every setting was silently SKIPPED
    ("unresolved") while the build still reported ok=true - the textures loaded
    at engine defaults. A read-back from the live editor is what caught it
    (filter=TF_DEFAULT when nearest was requested). Enum member names are
    probed directly instead, because that is what actually works here.
    """
    specs = {
        "filter_nearest": ("TextureFilter", ["TF_NEAREST", "TF_Nearest"]),
        "filter_bilinear": ("TextureFilter", ["TF_BILINEAR", "TF_Bilinear"]),
        "addr_wrap": ("TextureAddress", ["TA_WRAP", "TA_Wrap"]),
        "addr_clamp": ("TextureAddress", ["TA_CLAMP", "TA_Clamp"]),
        # TC_VECTOR_DISPLACEMENTMAP is the uncompressed format, and it is the
        # one that MATTERS here: TC_DEFAULT is block compression, which
        # averages 4x4 blocks and would destroy the exact 16-level Bayer
        # matrix T_Dither_Bayer depends on. The name was measured on this build
        # (Saved/Audit/texture_enum_probe.json) after two wrong guesses -
        # TC_Maskless and TC_VectorDisplacementmap do not exist.
        "comp_lossless": ("TextureCompressionSettings",
                          ["TC_VECTOR_DISPLACEMENTMAP", "TC_GRAYSCALE",
                           "TC_DEFAULT"]),
        "mips_off": ("TextureMipGenSettings",
                     ["TMGS_NO_MIPMAPS", "TMGS_NOMIPMAPS", "MOS_NO_MIPMAPS"]),
        "mips_on": ("TextureMipGenSettings",
                    ["TMGS_BILINEAR", "TMGS_SIMPLE_AVERAGE", "MOS_BILINEAR"]),
    }
    for key, (class_name, members) in specs.items():
        enum_cls = getattr(unreal, class_name, None)
        found, value = None, None
        if enum_cls is not None:
            for cand in members:
                if hasattr(enum_cls, cand):
                    found, value = cand, getattr(enum_cls, cand)
                    break
        RESOLVED[key] = {
            "value": value,
            "enum": class_name if enum_cls is not None else None,
            "member": found,
            "available": members,
        }
    return RESOLVED


def _set(tex, prop, value, rep, key):
    """Set one texture property, recording success/failure. Never raises."""
    if value is None:
        rep["skipped"].append(f"{key}: unresolved")
        return
    try:
        tex.set_editor_property(prop, value)
        rep["set"].append(f"{key}={getattr(value, 'name', value)}")
    except Exception as exc:
        rep["failed"].append(f"{key}: {str(exc)[:120]}")


def _readback(tex, props, rep):
    """Read properties back - mtime-style proof the write landed."""
    got = {}
    for prop in props:
        try:
            v = tex.get_editor_property(prop)
            got[prop] = str(getattr(v, "name", v))
        except Exception as exc:
            got[prop] = f"<{str(exc)[:60]}>"
    rep["readback"] = got


def _import_png(name: str, png: Path) -> unreal.Texture2D:
    """Import one PNG into TEX_DIR, replacing any previous copy."""
    task = unreal.AssetImportTask()
    task.filename = str(png)
    task.destination_path = TEX_DIR
    task.destination_name = name
    task.automated = True
    task.save = True
    task.replace_existing = True
    # NOT set: automated_import_should_be_imported - that attribute does not
    # exist on this build (measured 2026-10-02: raising it failed every import).
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    return unreal.load_asset(f"{TEX_DIR}/{name}.{name}")


def build() -> dict:
    """Generate every PNG, import it, apply and READ BACK its settings."""
    lib_log = print
    report = {"textures": {}, "errors": [], "resolved_enums": {}}
    resolved = _resolve_all()
    report["resolved_enums"] = {
        k: {"enum": v["enum"], "member": v["member"]}
        for k, v in resolved.items()}

    # HARD GATE, added 2026-10-02. Previously an unresolvable enum was skipped
    # into entry["skipped"] and the build still reported ok=true - so a texture
    # library where NOTHING was configured shipped green and was only caught by
    # reading the live editor back. An unresolved setting is now a build failure.
    unresolved = [k for k, v in resolved.items() if v["value"] is None]
    if unresolved:
        report["errors"].append(
            "unresolved texture settings enums: " + ", ".join(unresolved))

    if not unreal.EditorAssetLibrary.does_directory_exist(TEX_DIR):
        unreal.EditorAssetLibrary.make_directory(TEX_DIR)

    PNG_DIR.mkdir(parents=True, exist_ok=True)

    for (name, gen, srgb, filt, addr, comp, mips, why) in CATALOG:
        entry = {
            "why": why, "set": [], "failed": [], "skipped": [],
            "ok": False,
        }
        try:
            w, h, rows = gen()
            png = PNG_DIR / f"{name}.png"
            write_png(png, w, h, rows)
            entry["png"] = str(png)
            entry["pixels"] = f"{w}x{h}"

            tex = _import_png(name, png)
            if tex is None:
                entry["failed"].append("import returned None")
                report["textures"][name] = entry
                report["errors"].append(f"{name}: import failed")
                continue

            # --- settings, each recorded rather than assumed ---
            _set(tex, "srgb", bool(srgb), entry, "srgb")
            fkey = "filter_nearest" if filt == "nearest" else "filter_bilinear"
            _set(tex, "filter", resolved[fkey]["value"], entry, f"filter({filt})")
            akey = "addr_clamp" if addr == "clamp" else "addr_wrap"
            _set(tex, "address_x", resolved[akey]["value"], entry, "address_x")
            _set(tex, "address_y", resolved[akey]["value"], entry, "address_y")
            _set(tex, "compression_settings",
                 resolved["comp_lossless"]["value"], entry, "compression")
            mkey = "mips_on" if mips else "mips_off"
            _set(tex, "mip_gen_settings", resolved[mkey]["value"], entry,
                 f"mip_gen({mkey})")

            _readback(tex, ("srgb", "filter", "address_x", "address_y",
                            "compression_settings", "mip_gen_settings"), entry)

            # Proof the asset is real: dimensions, not just "no exception".
            try:
                entry["size"] = f"{tex.blueprint_get_size_x()}x{tex.blueprint_get_size_y()}"
            except Exception:
                try:
                    entry["size"] = f"{tex.get_editor_property('sizeX')}x" \
                                    f"{tex.get_editor_property('sizeY')}"
                except Exception as exc:
                    entry["size"] = f"<{str(exc)[:60]}>"

            unreal.EditorAssetLibrary.save_loaded_asset(tex, only_if_is_dirty=False)
            entry["asset"] = f"{TEX_DIR}/{name}.{name}"
            entry["ok"] = not entry["failed"]
            lib_log(f"[TEX] {name} ok={entry['ok']} size={entry['size']}")
        except Exception as exc:
            entry["failed"].append(str(exc)[:300])
            report["errors"].append(f"{name}: {exc}")
        report["textures"][name] = entry

    report["ok"] = not report["errors"] and all(
        e["ok"] for e in report["textures"].values())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    lib_log(f"[TEX] wrote {OUT} ok={report['ok']} "
            f"count={len(report['textures'])}")
    return report


def main() -> int:
    rep = build()
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
