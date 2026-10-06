"""Build MF_ProceduralPatterns - SDF-style procedural patterns for the toon spine.

NO SDF NODE EXISTS IN UE 5.8. Probed 2029-09-30:
    unreal.MaterialExpressionSDF           -> absent
    unreal.MaterialExpressionShaderToRGB   -> absent
    unreal.MaterialExpressionSmoothMin     -> absent

Only DistanceFieldApproxAO / DistanceFieldGradient ship, and those read a mesh's
baked field - they cannot author shapes. So this module composes analytic
distance-style fields from the nodes that DO exist: Sine, Frac, Abs, Floor,
Sign, Distance, DotProduct, Normalize, SmoothStep, If.

Each pattern is a classic signed-distance-style construction evaluated on a UV
lattice, then hard-thresholded with SmoothStep. Hard edges are the point: they
stay crisp at any zoom and under camera move, which is what a cel look needs and
what a filtered texture cannot give.

Inputs
    UV          float2 - lattice coordinate, drive with TexCoord or UV scale
    Scale       scalar - pattern frequency (defaults per-pattern below)
    Softness    scalar - edge width of the hard threshold (0 = razor sharp)
    Angle       scalar - pattern rotation in degrees
    CellIndex   scalar - selects which pattern to return
    Density     scalar - ink coverage 0..1; the level the field is cut against
    SDFMap      texture2D - baked stroke field for CellIndex 12; MUST be
                connected by every caller or the function fails to compile
                ("Missing function input", the same hard error an unwired
                Softness produced 2026-10-03)

Outputs
    Pattern     scalar - 0..1 field for the selected pattern
    Mask        scalar - same field, hard-thresholded

Patterns
    0  Halftone   - offset dot lattice, screen-print cell shading
    1  Checker    - hard checkerboard
    2  Stripes    - hard parallel bars
    3  Crackle    - Worley-ish cell breakup from fractional sine distance
    4  InkSplat   - radial falloff rings, high contrast
    5  CrossHatch - two 45-degree line families; engraving / pencil hatch
    6  Stipple    - hashed points; dry-brush / graphite grain
    7  Rings      - concentric focal lines; manga screentone burst
    8  Voronoi    - F1 distance to nearest jittered feature point (3x3 search);
                    concrete / plaster cell breakup. Added 2026-10-02, closing
                    the SDF_PATTERN_PIPELINE.md S8 "no true Voronoi" gap.
    9  Grid       - grout lines on a square lattice; drop-ceiling and
                    carpet-tile rhythm
    10 Perforation- round holes on a square lattice; acoustic panel / grille
    11 Weave      - warp/weft over-under by cell parity; cubicle fabric
    12 SDFMap     - baked signed-distance stroke field (T_SDF_Strokes via the
                    SDFMap input); continuous triangle distance so bilinear
                    filtering gives wide soft edges the analytic fields cannot
                    without aliasing, plus per-stroke width jitter from the
                    map's G channel. Added 2026-10-03.

Density is what makes these usable in a film rather than as a flat overlay: it
is the cut level, so raising it densifies the hatch the way a painter hatches
into shadow. Drive it from a shadow mask or a Toon Profile and the pattern
becomes automatic shadow hatching.

Research basis (2026-10-01)
    UE 5.8's Substrate Toon BSDF is experimental and its Toon Profile already
    carries ShadowHatchingPattern{Texture,Size,Strength}. This function is the
    art-directable companion: analytic, texture-free, and densifiable per
    instance. Constructions follow the 2D signed-distance literature (Inigo
    Quilez, "2D distance functions") - every pattern is a distance field on a
    UV lattice, hard-thresholded. No SDF node exists in UE 5.8, so the fields
    are composed from Sine/Frac/Abs/Floor/Length/Add/Mul.
"""
from __future__ import annotations

import math

import unreal

import spine_lib as lib

NAME = "MF_ProceduralPatterns"

FI_SCALAR = unreal.FunctionInputType.FUNCTION_INPUT_SCALAR
FI_VECTOR2 = unreal.FunctionInputType.FUNCTION_INPUT_VECTOR2
FI_TEXTURE = unreal.FunctionInputType.FUNCTION_INPUT_TEXTURE2D


def _uv_basis(fn, angle_source, x=-2000):
    """Build a rotated UV frame driven by `angle_source` (degrees).

    Returns (texcoord, u, v). Rotation is the standard 2x2 frame:
        u' = u*cos - v*sin
        v' = u*sin + v*cos
    """
    tex = lib.expr(fn, unreal.MaterialExpressionTextureCoordinate, x, 900)

    to_rad = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 160, 900)
    lib.connect(angle_source, "", to_rad, ["A", "a"])
    lib.connect(lib.scalar_const(fn, math.pi / 180.0, x + 160, 980), "", to_rad, ["B", "b"])

    ang = to_rad

    cos_n = lib.expr(fn, unreal.MaterialExpressionCosine, x + 300, 840)
    sin_n = lib.expr(fn, unreal.MaterialExpressionSine, x + 300, 960)
    lib.unary(ang, cos_n)
    lib.unary(ang, sin_n)

    # u' = u*cos - v*sin
    u_cos = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 440, 840)
    lib.connect(tex, "", u_cos, ["A", "a"])
    lib.connect(cos_n, "", u_cos, ["B", "b"])

    v_sin = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 440, 980)
    lib.connect(tex, "", v_sin, ["A", "a"])
    lib.connect(sin_n, "", v_sin, ["B", "b"])

    u = lib.expr(fn, unreal.MaterialExpressionSubtract, x + 580, 900)
    lib.binary(u_cos, v_sin, u)

    # v' = u*sin + v*cos
    u_sin = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 440, 1120)
    lib.connect(tex, "", u_sin, ["A", "a"])
    lib.connect(sin_n, "", u_sin, ["B", "b"])

    v_cos = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 440, 1240)
    lib.connect(tex, "", v_cos, ["A", "a"])
    lib.connect(cos_n, "", v_cos, ["B", "b"])

    v = lib.expr(fn, unreal.MaterialExpressionAdd, x + 580, 1180)
    lib.binary(u_sin, v_cos, v)

    return tex, u, v


def _halftone(fn, uv, scale, x=-1100):
    """Offset dot lattice: classic screen-print cell."""
    scaled = lib.expr(fn, unreal.MaterialExpressionMultiply, x, 200)
    lib.connect(uv, "", scaled, ["A", "a"])
    lib.connect(scale, "", scaled, ["B", "b"])

    # offset every other row/column by half a cell -> triangular lattice
    row = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 150, 120)
    lib.connect(scaled, "", row, ["A", "a"])
    lib.connect(scale, "", row, ["B", "b"])

    fract_row = lib.expr(fn, unreal.MaterialExpressionFrac, x + 290, 120)
    lib.unary(row, fract_row)

    cell_x = lib.expr(fn, unreal.MaterialExpressionFloor, x + 290, 260)
    lib.unary(scaled, cell_x)

    paren = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 430, 260)
    lib.binary(cell_x, lib.scalar_const(fn, 0.5, x + 430, 340), paren)

    shifted = lib.expr(fn, unreal.MaterialExpressionAdd, x + 570, 180)
    lib.binary(fract_row, paren, shifted)

    frac_v = lib.expr(fn, unreal.MaterialExpressionFrac, x + 570, 40)
    lib.unary(scaled, frac_v)

    cell_v = lib.expr(fn, unreal.MaterialExpressionFloor, x + 570, -60)
    lib.unary(scaled, cell_v)

    # distance from cell centre in 0..1
    cx = lib.expr(fn, unreal.MaterialExpressionSubtract, x + 710, 180)
    lib.binary(shifted, lib.scalar_const(fn, 0.5, x + 710, 260), cx)

    cy = lib.expr(fn, unreal.MaterialExpressionSubtract, x + 710, 40)
    lib.binary(frac_v, lib.scalar_const(fn, 0.5, x + 710, -20), cy)

    len_n = lib.length2(fn, cx, cy, x + 850, 100)
    return len_n


def _checker(fn, uv, scale, x=-1100, y_offset=400):
    scaled = lib.expr(fn, unreal.MaterialExpressionMultiply, x, y_offset)
    lib.connect(uv, "", scaled, ["A", "a"])
    lib.connect(scale, "", scaled, ["B", "b"])

    a = lib.expr(fn, unreal.MaterialExpressionFrac, x + 150, y_offset)
    lib.unary(scaled, a)
    b = lib.expr(fn, unreal.MaterialExpressionFrac, x + 150, y_offset + 120)
    lib.unary(scaled, b)

    step = lib.expr(fn, unreal.MaterialExpressionIf, x + 320, y_offset + 60)
    lib.connect(a, "", step, ["A"])
    lib.connect(lib.scalar_const(fn, 0.5, x + 320, y_offset + 160), "", step, ["B"])
    lib.connect(lib.scalar_const(fn, 0.0, x + 320, y_offset + 240), "", step, ["A > B"])
    lib.connect(lib.scalar_const(fn, 1.0, x + 320, y_offset + 320), "", step, ["A == B"])
    lib.connect(lib.scalar_const(fn, 0.0, x + 320, y_offset + 400), "", step, ["A < B"])
    return step


def _stripes(fn, uv, scale, x=-1100, y_offset=900):
    scaled = lib.expr(fn, unreal.MaterialExpressionMultiply, x, y_offset)
    lib.connect(uv, "", scaled, ["A", "a"])
    lib.connect(scale, "", scaled, ["B", "b"])

    f = lib.expr(fn, unreal.MaterialExpressionFrac, x + 150, y_offset)
    lib.unary(scaled, f)

    tri = lib.expr(fn, unreal.MaterialExpressionAbs, x + 290, y_offset)
    lib.unary(f, tri)

    centred = lib.expr(fn, unreal.MaterialExpressionSubtract, x + 430, y_offset)
    lib.binary(tri, lib.scalar_const(fn, 0.25, x + 430, y_offset + 100), centred)
    return centred


def _crackle(fn, uv, scale, x=-1100, y_offset=1400):
    """Cell-edge field: fract of two rotated sines, distance to the cell wall."""
    scaled = lib.expr(fn, unreal.MaterialExpressionMultiply, x, y_offset)
    lib.connect(uv, "", scaled, ["A", "a"])
    lib.connect(scale, "", scaled, ["B", "b"])

    s1 = lib.expr(fn, unreal.MaterialExpressionSine, x + 150, y_offset)
    s1.set_editor_property("period", 1.0)
    lib.unary(scaled, s1)

    # second, rotated octave for irregular cells
    rot = lib.expr(fn, unreal.MaterialExpressionAdd, x + 150, y_offset + 160)
    lib.connect(scaled, "", rot, ["A"])
    lib.connect(lib.scalar_const(fn, 2.399963, x + 150, y_offset + 240), "", rot, ["B"])

    s2 = lib.expr(fn, unreal.MaterialExpressionCosine, x + 300, y_offset + 160)
    s2.set_editor_property("period", 1.0)
    lib.unary(rot, s2)

    mix = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 440, y_offset + 60)
    lib.binary(s1, s2, mix)

    f = lib.expr(fn, unreal.MaterialExpressionFrac, x + 580, y_offset + 60)
    lib.unary(mix, f)

    dist = lib.expr(fn, unreal.MaterialExpressionAbs, x + 720, y_offset + 60)
    lib.unary(f, dist)

    centred = lib.expr(fn, unreal.MaterialExpressionSubtract, x + 860, y_offset + 60)
    lib.binary(dist, lib.scalar_const(fn, 0.5, x + 860, y_offset + 140), centred)
    return centred


def _inksplat(fn, uv, scale, x=-1100, y_offset=1900):
    """Radial rings: distance from lattice centre, ringed."""
    scaled = lib.expr(fn, unreal.MaterialExpressionMultiply, x, y_offset)
    lib.connect(uv, "", scaled, ["A", "a"])
    lib.connect(scale, "", scaled, ["B", "b"])

    fr = lib.expr(fn, unreal.MaterialExpressionFrac, x + 150, y_offset)
    lib.unary(scaled, fr)

    cx = lib.expr(fn, unreal.MaterialExpressionSubtract, x + 290, y_offset)
    lib.binary(fr, lib.scalar_const(fn, 0.5, x + 290, y_offset + 80), cx)

    len_n = lib.expr(fn, unreal.MaterialExpressionLength, x + 430, y_offset)
    lib.connect(cx, "", len_n, ["", "None"])

    ring = lib.expr(fn, unreal.MaterialExpressionSine, x + 570, y_offset)
    ring.set_editor_property("period", 1.0)
    lib.unary(len_n, ring)

    half = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 710, y_offset)
    lib.binary(ring, lib.scalar_const(fn, 0.5, x + 710, y_offset + 80), half)

    biased = lib.expr(fn, unreal.MaterialExpressionAdd, x + 850, y_offset)
    lib.binary(half, lib.scalar_const(fn, 0.5, x + 850, y_offset + 80), biased)
    return biased


def _crosshatch(fn, u, v, scale, x=-1100, y_offset=2450):
    """Cross-hatch: two 45-degree line families, the engraving / pencil hatch.

    Lines at -45 come from (u+v); lines at +45 from (u-v). Each is a 1D
    distance field (abs of the fractional part), and the ink sits where either
    family is near its line - so the two families cross into a lattice.
    """
    a = lib.expr(fn, unreal.MaterialExpressionAdd, x, y_offset)
    lib.binary(u, v, a)
    b = lib.expr(fn, unreal.MaterialExpressionSubtract, x, y_offset + 220)
    lib.binary(u, v, b)

    fa = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 150, y_offset)
    lib.connect(a, "", fa, ["A", "a"])
    lib.connect(scale, "", fa, ["B", "b"])
    fr_a = lib.expr(fn, unreal.MaterialExpressionFrac, x + 300, y_offset)
    lib.unary(fa, fr_a)
    da = lib.expr(fn, unreal.MaterialExpressionAbs, x + 450, y_offset)
    lib.unary(fr_a, da)

    fb = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 150, y_offset + 220)
    lib.connect(b, "", fb, ["A", "a"])
    lib.connect(scale, "", fb, ["B", "b"])
    fr_b = lib.expr(fn, unreal.MaterialExpressionFrac, x + 300, y_offset + 220)
    lib.unary(fb, fr_b)
    db = lib.expr(fn, unreal.MaterialExpressionAbs, x + 450, y_offset + 220)
    lib.unary(fr_b, db)

    mn = lib.expr(fn, unreal.MaterialExpressionMin, x + 600, y_offset + 110)
    lib.binary(da, db, mn)
    return mn


def _stipple(fn, u, v, scale, x=-1100, y_offset=3000):
    """Stipple: hashed points (dry-brush / graphite grain).

    A value hash frac(sin(u*12.9898 + v*78.233) * 43758.5453) - the standard
    GLSL hash, which is why it uses those irrational constants. Thresholded
    downstream, it reads as sparse ink flecks rather than a regular lattice.
    """
    su = lib.expr(fn, unreal.MaterialExpressionMultiply, x, y_offset)
    lib.binary(u, scale, su)
    fu = lib.expr(fn, unreal.MaterialExpressionFrac, x + 150, y_offset)
    lib.unary(su, fu)

    sv = lib.expr(fn, unreal.MaterialExpressionMultiply, x, y_offset + 220)
    lib.binary(v, scale, sv)
    fv = lib.expr(fn, unreal.MaterialExpressionFrac, x + 150, y_offset + 220)
    lib.unary(sv, fv)

    h1 = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 300, y_offset)
    lib.binary(fu, lib.scalar_const(fn, 12.9898, x + 300, y_offset + 80), h1)
    h2 = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 300, y_offset + 220)
    lib.binary(fv, lib.scalar_const(fn, 78.233, x + 300, y_offset + 300), h2)

    hs = lib.expr(fn, unreal.MaterialExpressionAdd, x + 450, y_offset + 110)
    lib.binary(h1, h2, hs)

    sn = lib.expr(fn, unreal.MaterialExpressionSine, x + 600, y_offset + 110)
    sn.set_editor_property("period", 1.0)
    lib.unary(hs, sn)

    hm = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 750, y_offset + 110)
    lib.binary(sn, lib.scalar_const(fn, 43758.5453, x + 750, y_offset + 190), hm)

    hf = lib.expr(fn, unreal.MaterialExpressionFrac, x + 900, y_offset + 110)
    lib.unary(hm, hf)
    return hf


def _rings(fn, u, v, scale, x=-1100, y_offset=3700):
    """Rings: concentric focal lines around the UV origin (screentone burst)."""
    su = lib.expr(fn, unreal.MaterialExpressionMultiply, x, y_offset)
    lib.binary(u, scale, su)
    sv = lib.expr(fn, unreal.MaterialExpressionMultiply, x, y_offset + 220)
    lib.binary(v, scale, sv)

    ln = lib.length2(fn, su, sv, x + 180, y_offset + 110)

    fr = lib.expr(fn, unreal.MaterialExpressionFrac, x + 340, y_offset + 110)
    lib.unary(ln, fr)
    return fr


def _hash2(fn, a, b, ka, kb, x, y):
    """frac(sin(a*ka + b*kb) * 43758.5453) - the cheap scalar value hash.

    Same construction and constants as _stipple, generalised to two inputs so
    a cell-coordinate pair can seed two independent random channels.
    """
    pa = lib.expr(fn, unreal.MaterialExpressionMultiply, x, y)
    lib.binary(a, lib.scalar_const(fn, ka, x, y + 80), pa)
    pb = lib.expr(fn, unreal.MaterialExpressionMultiply, x, y + 140)
    lib.binary(b, lib.scalar_const(fn, kb, x, y + 220), pb)
    s = lib.expr(fn, unreal.MaterialExpressionAdd, x + 160, y + 70)
    lib.binary(pa, pb, s)
    sn = lib.expr(fn, unreal.MaterialExpressionSine, x + 320, y + 70)
    sn.set_editor_property("period", 1.0)
    lib.unary(s, sn)
    m = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 480, y + 70)
    lib.binary(sn, lib.scalar_const(fn, 43758.5453, x + 480, y + 150), m)
    fr = lib.expr(fn, unreal.MaterialExpressionFrac, x + 640, y + 70)
    lib.unary(m, fr)
    return fr


def _voronoi(fn, u, v, scale, x=-1100, y_offset=4400):
    """F1 Worley/Voronoi - distance to the nearest jittered feature point.

    A TRUE 3x3 neighbourhood search. The single-cell version would be a
    jittered lattice, not a Voronoi; SDF_PATTERN_PIPELINE.md S8 lists "a true
    F1 Voronoi cell pattern" as the explicit next addition - this is it, used
    for concrete/plaster cell breakup on the brutalist office set.

    Distances stay SQUARED through the 9-way min (sqrt is monotonic so the
    argmin is unchanged) and are square-rooted once at the end: 1 sqrt, not 9.
    Feature points use AppendVector -> Length rather than Length(A,B), because
    Append is the construction MF_RampLUT already proves on this build.
    """
    su = lib.expr(fn, unreal.MaterialExpressionMultiply, x, y_offset)
    lib.binary(u, scale, su)
    sv = lib.expr(fn, unreal.MaterialExpressionMultiply, x, y_offset + 140)
    lib.binary(v, scale, sv)

    cu = lib.expr(fn, unreal.MaterialExpressionFloor, x + 160, y_offset)
    lib.unary(su, cu)
    cv = lib.expr(fn, unreal.MaterialExpressionFloor, x + 160, y_offset + 140)
    lib.unary(sv, cv)

    best = None
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            yy = y_offset + 320 + (dy + 1) * 760 + (dx + 1) * 240
            nu = lib.expr(fn, unreal.MaterialExpressionAdd, x + 320, yy)
            lib.binary(cu, lib.scalar_const(fn, float(dx), x + 320, yy + 80), nu)
            nv = lib.expr(fn, unreal.MaterialExpressionAdd, x + 320, yy + 150)
            lib.binary(cv, lib.scalar_const(fn, float(dy), x + 320, yy + 230), nv)

            hx = _hash2(fn, nu, nv, 127.1, 311.7, x + 500, yy)
            hy = _hash2(fn, nu, nv, 269.5, 183.3, x + 500, yy + 420)

            fu = lib.expr(fn, unreal.MaterialExpressionAdd, x + 1180, yy)
            lib.binary(nu, hx, fu)                      # feature point x
            fv = lib.expr(fn, unreal.MaterialExpressionAdd, x + 1180, yy + 150)
            lib.binary(nv, hy, fv)                      # feature point y

            du = lib.expr(fn, unreal.MaterialExpressionSubtract, x + 1340, yy)
            lib.binary(su, fu, du)
            dv = lib.expr(fn, unreal.MaterialExpressionSubtract, x + 1340, yy + 150)
            lib.binary(sv, fv, dv)

            du2 = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 1500, yy)
            lib.binary(du, du, du2)
            dv2 = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 1500, yy + 150)
            lib.binary(dv, dv, dv2)
            d2 = lib.expr(fn, unreal.MaterialExpressionAdd, x + 1660, yy + 75)
            lib.binary(du2, dv2, d2)

            if best is None:
                best = d2
            else:
                mn = lib.expr(fn, unreal.MaterialExpressionMin, x + 1820, yy + 75)
                lib.binary(best, d2, mn)
                best = mn

    dist = lib.expr(fn, unreal.MaterialExpressionSquareRoot,
                    x + 1980, y_offset + 900)
    lib.unary(best, dist)
    return dist


def _grid(fn, u, v, scale, x=-1100, y_offset=7400):
    """Grout / ceiling tile - ink along cell boundaries, clear in the tile.

    Field is high AT the grout line (|frac - 0.5| peaks where frac is 0 or 1),
    so a low Density inks only the lines. This is the 600mm drop-ceiling and
    carpet-tile rhythm of the office set.
    """
    su = lib.expr(fn, unreal.MaterialExpressionMultiply, x, y_offset)
    lib.binary(u, scale, su)
    sv = lib.expr(fn, unreal.MaterialExpressionMultiply, x, y_offset + 140)
    lib.binary(v, scale, sv)

    fu = lib.expr(fn, unreal.MaterialExpressionFrac, x + 160, y_offset)
    lib.unary(su, fu)
    fv = lib.expr(fn, unreal.MaterialExpressionFrac, x + 160, y_offset + 140)
    lib.unary(sv, fv)

    eu = lib.expr(fn, unreal.MaterialExpressionSubtract, x + 320, y_offset)
    lib.binary(fu, lib.scalar_const(fn, 0.5, x + 320, y_offset + 80), eu)
    au = lib.expr(fn, unreal.MaterialExpressionAbs, x + 480, y_offset)
    lib.unary(eu, au)

    ev = lib.expr(fn, unreal.MaterialExpressionSubtract, x + 320, y_offset + 140)
    lib.binary(fv, lib.scalar_const(fn, 0.5, x + 320, y_offset + 220), ev)
    av = lib.expr(fn, unreal.MaterialExpressionAbs, x + 480, y_offset + 140)
    lib.unary(ev, av)

    mx = lib.expr(fn, unreal.MaterialExpressionMax, x + 640, y_offset + 70)
    lib.binary(au, av, mx)
    twice = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 800, y_offset + 70)
    lib.binary(mx, lib.scalar_const(fn, 2.0, x + 800, y_offset + 150), twice)
    return twice


def _perforation(fn, u, v, scale, x=-1100, y_offset=8200):
    """Office panel perforations - holes on a square lattice.

    Field peaks AT the hole centre (1 - scaled distance), so ink lands on the
    holes and a high Density closes them. Distinct from _halftone: that offsets
    every other row into a triangular lattice for screen-print dots; this is a
    square grid of round holes - an acoustic panel or speaker grille, both real
    objects in the office prop brief.
    """
    su = lib.expr(fn, unreal.MaterialExpressionMultiply, x, y_offset)
    lib.binary(u, scale, su)
    sv = lib.expr(fn, unreal.MaterialExpressionMultiply, x, y_offset + 140)
    lib.binary(v, scale, sv)

    fu = lib.expr(fn, unreal.MaterialExpressionFrac, x + 160, y_offset)
    lib.unary(su, fu)
    fv = lib.expr(fn, unreal.MaterialExpressionFrac, x + 160, y_offset + 140)
    lib.unary(sv, fv)

    cu = lib.expr(fn, unreal.MaterialExpressionSubtract, x + 320, y_offset)
    lib.binary(fu, lib.scalar_const(fn, 0.5, x + 320, y_offset + 80), cu)
    cv = lib.expr(fn, unreal.MaterialExpressionSubtract, x + 320, y_offset + 140)
    lib.binary(fv, lib.scalar_const(fn, 0.5, x + 320, y_offset + 220), cv)

    pair = lib.expr(fn, unreal.MaterialExpressionAppendVector,
                    x + 480, y_offset + 70)
    lib.connect(cu, "", pair, ["A", "a"])
    lib.connect(cv, "", pair, ["B", "b"])
    ln = lib.expr(fn, unreal.MaterialExpressionLength, x + 640, y_offset + 70)
    lib.connect(pair, "", ln, ["", "None"])

    # centre (0) -> 1, corner (0.707) -> 0: so 1 - saturate(len * 1.4142).
    scaled = lib.expr(fn, unreal.MaterialExpressionMultiply,
                      x + 800, y_offset + 70)
    lib.binary(ln, lib.scalar_const(fn, 1.4142, x + 800, y_offset + 150), scaled)
    sat = lib.expr(fn, unreal.MaterialExpressionSaturate, x + 960, y_offset + 70)
    lib.unary(scaled, sat)
    inv = lib.expr(fn, unreal.MaterialExpressionOneMinus, x + 1120, y_offset + 70)
    lib.unary(sat, inv)
    return inv


def _weave(fn, u, v, scale, x=-1100, y_offset=9000):
    """Warp/weft weave - cubicle fabric and acoustic cloth.

    Alternates which axis carries the thread profile by the parity of the cell
    (floor(u) + floor(v)), so consecutive cells read as over-under weaving
    rather than a plain grid - that is _grid's job, not this one.
    """
    su = lib.expr(fn, unreal.MaterialExpressionMultiply, x, y_offset)
    lib.binary(u, scale, su)
    sv = lib.expr(fn, unreal.MaterialExpressionMultiply, x, y_offset + 140)
    lib.binary(v, scale, sv)

    fu = lib.expr(fn, unreal.MaterialExpressionFrac, x + 160, y_offset)
    lib.unary(su, fu)
    fv = lib.expr(fn, unreal.MaterialExpressionFrac, x + 160, y_offset + 140)
    lib.unary(sv, fv)

    pu = lib.expr(fn, unreal.MaterialExpressionAbs, x + 320, y_offset)
    lib.unary(fu, pu)
    cu = lib.expr(fn, unreal.MaterialExpressionSubtract, x + 480, y_offset)
    lib.binary(pu, lib.scalar_const(fn, 0.5, x + 480, y_offset + 80), cu)

    pv = lib.expr(fn, unreal.MaterialExpressionAbs, x + 320, y_offset + 140)
    lib.unary(fv, pv)
    cv = lib.expr(fn, unreal.MaterialExpressionSubtract, x + 480, y_offset + 140)
    lib.binary(pv, lib.scalar_const(fn, 0.5, x + 480, y_offset + 220), cv)

    # parity = frac((floor(su) + floor(sv)) * 0.5) * 2  -> 0 or 1
    gu = lib.expr(fn, unreal.MaterialExpressionFloor, x + 640, y_offset + 300)
    lib.unary(su, gu)
    gv = lib.expr(fn, unreal.MaterialExpressionFloor, x + 640, y_offset + 440)
    lib.unary(sv, gv)
    gsum = lib.expr(fn, unreal.MaterialExpressionAdd, x + 800, y_offset + 370)
    lib.binary(gu, gv, gsum)
    half = lib.expr(fn, unreal.MaterialExpressionMultiply,
                    x + 960, y_offset + 370)
    lib.binary(gsum, lib.scalar_const(fn, 0.5, x + 960, y_offset + 450), half)
    par_f = lib.expr(fn, unreal.MaterialExpressionFrac, x + 1120, y_offset + 370)
    lib.unary(half, par_f)
    parity = lib.expr(fn, unreal.MaterialExpressionMultiply,
                      x + 1280, y_offset + 370)
    lib.binary(par_f, lib.scalar_const(fn, 2.0, x + 1280, y_offset + 450), parity)

    pick = lib.expr(fn, unreal.MaterialExpressionIf, x + 1440, y_offset + 200)
    lib.connect(parity, "", pick, ["A"])
    lib.connect(lib.scalar_const(fn, 0.5, x + 1440, y_offset + 300),
                "", pick, ["B"])
    lib.connect(cv, "", pick, ["A > B"])
    lib.connect(cv, "", pick, ["A == B"])
    lib.connect(cu, "", pick, ["A < B"])
    return pick


def _sdfmap(fn, u, v, scale, sdf_in, x=-1100, y_offset=9800):
    """Baked SDF stroke map (T_SDF_Strokes) - CellIndex 12.

    Samples the map's R field at the rotated/scaled UV and shifts it by the
    per-stroke width jitter carried in G, then returns it through the shared
    Density/Softness cut like every other pattern. The baked field is a
    continuous triangle of the wrapped stroke coordinate, so bilinear
    filtering gives wide soft edges the analytic frac() fields cannot
    produce without aliasing - that is the reason this one is a texture.
    """
    su = lib.expr(fn, unreal.MaterialExpressionMultiply, x, y_offset)
    lib.binary(u, scale, su)

    # NOTE: u from _uv_basis is the rotated TEXCOORD (float2), and su = u*scale
    # is already the float2 sample UV - the same componentwise convention the
    # analytic fields use. Appending su and sv would build a float4 and trip
    # "Cannot cast from larger type float4 to smaller type float2" at the
    # sample's UVs pin (caught by the 2026-10-03 build).

    sample = lib.expr(fn, unreal.MaterialExpressionTextureSample,
                      x + 320, y_offset + 70)
    # The texture pin is 'Tex' on this build - measured for MF_RampLUT
    # 2026-10-03 ("Missing input texture" when the old candidates missed).
    lib.connect(sdf_in, "", sample, ["Tex", "TextureObject", ""])
    lib.connect(su, "", sample, ["UVs", ""])

    # Channel split via ComponentMask on the RGB output: no reliance on the
    # sample's per-channel pin names, which are not stable across builds.
    r_ch = lib.expr(fn, unreal.MaterialExpressionComponentMask,
                    x + 520, y_offset)
    r_ch.set_editor_property("r", True)
    r_ch.set_editor_property("g", False)
    r_ch.set_editor_property("b", False)
    r_ch.set_editor_property("a", False)
    lib.connect(sample, "", r_ch, ["", "None"])

    g_ch = lib.expr(fn, unreal.MaterialExpressionComponentMask,
                    x + 520, y_offset + 220)
    g_ch.set_editor_property("r", False)
    g_ch.set_editor_property("g", True)
    g_ch.set_editor_property("b", False)
    g_ch.set_editor_property("a", False)
    lib.connect(sample, "", g_ch, ["", "None"])

    # Width jitter: field -+ (G - 0.5) * 0.22 shifts each stroke's effective
    # half-width by up to ~11% of the stroke spacing, hand-inked variance the
    # analytic line families do not have.
    centred = lib.expr(fn, unreal.MaterialExpressionSubtract,
                       x + 700, y_offset + 220)
    lib.binary(g_ch, lib.scalar_const(fn, 0.5, x + 700, y_offset + 300),
               centred)

    jitter = lib.expr(fn, unreal.MaterialExpressionMultiply,
                      x + 860, y_offset + 220)
    lib.binary(centred, lib.scalar_const(fn, 0.22, x + 860, y_offset + 300),
               jitter)

    shifted = lib.expr(fn, unreal.MaterialExpressionAdd,
                       x + 1020, y_offset + 110)
    lib.binary(r_ch, jitter, shifted)
    return shifted


def build(rebuild=True):
    lib.log(f"=== {NAME} ===")
    fn = lib.get_or_create_function(NAME, rebuild=rebuild)
    lib.try_set(fn, "description",
                "SDF-style procedural patterns (halftone/checker/stripes/crackle/ink/"
                "crosshatch/stipple/rings/voronoi/grid/perforation/weave/sdfmap) with "
                "a Density coverage knob. "
                "UE 5.8 has no SDF node; 0-11 are analytic distance constructions, "
                "12 samples a baked signed-distance stroke texture.")

    # ---------------- inputs ----------------
    uv_in = lib.add_function_input(fn, "UV", FI_VECTOR2, x=-2200, y=0)
    scale_in = lib.add_function_input(fn, "Scale", FI_SCALAR,
                                      preview=(12.0, 0, 0, 0), x=-2200, y=200)
    soft_in = lib.add_function_input(fn, "Softness", FI_SCALAR,
                                     preview=(0.02, 0, 0, 0), x=-2200, y=340)
    angle_in = lib.add_function_input(fn, "Angle", FI_SCALAR,
                                      preview=(0.0, 0, 0, 0), x=-2200, y=460)
    cell_in = lib.add_function_input(fn, "CellIndex", FI_SCALAR,
                                     preview=(0.0, 0, 0, 0), x=-2200, y=600)
    # Density = ink coverage. It is the level the field is cut against, so it
    # densifies the pattern the way a painter hatching into shadow does.
    dens_in = lib.add_function_input(fn, "Density", FI_SCALAR,
                                     preview=(0.5, 0, 0, 0), x=-2200, y=740)
    # Baked SDF stroke field for CellIndex 12. A texture2D function input has
    # no preview default, so this MUST be wired by the caller - the master
    # connects a TextureObjectParameter (PatternSDFMap) the same way it feeds
    # MF_RampLUT's RampTexture.
    sdf_in = lib.add_function_input(fn, "SDFMap", FI_TEXTURE,
                                    x=-2200, y=880)

    # per-pattern scale multipliers so one Scale knob still gives each pattern
    # its natural frequency
    scales = {}
    for i, mult in enumerate([1.0] * 13):
        scales[i] = lib.expr(fn, unreal.MaterialExpressionMultiply, -1900, 700 + i * 60)
        lib.connect(scale_in, "", scales[i], ["A"])
        lib.connect(lib.scalar_const(fn, mult, -1900, 780 + i * 60), "", scales[i], ["B"])

    # rotated UV frame, shared by every pattern. Built at angle 0 from
    # TextureCoordinate; Angle is applied per-instance via the input.
    tex, u, v = _uv_basis(fn, angle_in)

    # ---------------- pattern fields ----------------
    # 0-7 are the 2026-10-01 set; 8-11 added 2026-10-02 for the office film
    # (SDF_PATTERN_PIPELINE.md S3 table is the authority for what each is for).
    fields = {
        0: _halftone(fn, u, scales[0]),
        1: _checker(fn, u, scales[1]),
        2: _stripes(fn, u, scales[2]),
        3: _crackle(fn, u, scales[3]),
        4: _inksplat(fn, u, scales[4]),
        5: _crosshatch(fn, u, v, scales[5]),
        6: _stipple(fn, u, v, scales[6]),
        7: _rings(fn, u, v, scales[7]),
        8: _voronoi(fn, u, v, scales[8]),
        9: _grid(fn, u, v, scales[9]),
        10: _perforation(fn, u, v, scales[10]),
        11: _weave(fn, u, v, scales[11]),
        12: _sdfmap(fn, u, v, scales[12], sdf_in),
    }

    # ---------------- pattern selector (nested static-free If chain) ----------------
    # Static switches would bake per-instance; an If chain on CellIndex stays
    # dynamic so one material instance can switch pattern at runtime.
    current = None
    for idx in sorted(fields, reverse=True):
        if current is None:
            current = fields[idx]
            continue
        cond = lib.expr(fn, unreal.MaterialExpressionIf, -700 + idx * 180, 2200)
        lib.connect(cell_in, "", cond, ["A"])
        lib.connect(lib.scalar_const(fn, float(idx), -700 + idx * 180, 2300), "", cond, ["B"])
        lib.connect(fields[idx], "", cond, ["A > B"])
        lib.connect(current, "", cond, ["A == B"])
        lib.connect(current, "", cond, ["A < B"])
        current = cond

    selected = current

    # ---------------- hard threshold ----------------
    # SmoothStep(Min, Max, Value). Softness as the edge width around 0.5:
    #   Min = 0.5 - Softness/2, Max = 0.5 + Softness/2, Value = field
    # Softness 0 collapses to a razor edge, which is the cel look we want.
    half_soft = lib.expr(fn, unreal.MaterialExpressionMultiply, -100, 2400)
    lib.connect(soft_in, "", half_soft, ["A"])
    lib.connect(lib.scalar_const(fn, 0.5, -100, 2480), "", half_soft, ["B"])

    # The cut level is Density, not a fixed 0.5: raising Density inks more of
    # the surface, which is how the pattern reads as shadow hatching.
    lo = lib.expr(fn, unreal.MaterialExpressionSubtract, 40, 2360)
    lib.connect(dens_in, "", lo, ["A"])
    lib.connect(half_soft, "", lo, ["B"])

    hi = lib.expr(fn, unreal.MaterialExpressionAdd, 40, 2560)
    lib.connect(dens_in, "", hi, ["A"])
    lib.connect(half_soft, "", hi, ["B"])

    edge = lib.expr(fn, unreal.MaterialExpressionSmoothStep, 200, 2200)
    lib.connect(lo, "", edge, ["Min"])
    lib.connect(hi, "", edge, ["Max"])
    lib.connect(selected, "", edge, ["Value"])

    out_pattern = lib.add_function_output(fn, "Pattern", x=520, y=2160)
    lib.connect(selected, "", out_pattern, "")

    out_mask = lib.add_function_output(fn, "Mask", x=520, y=2280)
    lib.connect(edge, "", out_mask, "")

    lib.save(fn)
    lib.log(f"{NAME} built with {lib.function_expression_count(fn)} expressions")
    return fn
