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

AXIS RULE (2026-10-06): cells that need INDEPENDENT x/y logic (checker,
crosshatch, weave parity, subway rows, blind cords, brushed columns,
chevron guides, frost rows) derive from the scalar tx/ty axes returned by
_uv_basis - never from u-vs-v. u and v are identical float2 vectors at the
default Angle 0, so u-vs-v logic is provably degenerate there (checker was
an impulse, weave parity identically 0, crosshatch family B exactly 0).
Cells that only need 2D lattice position keep the float2 frame.

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
                    map's G channel. Added 2026-10-03. ANY baked T_SDF_* map
                    can ride this cell through the master's per-instance
                    PatternSDFMap - the office tilables need no new cell.
    13 SubwayTile - running-bond offset courses; kitchen/washroom walls
    14 Blinds      - broad slat faces + lift-cord shadows; window walls
    15 PaperFiber  - fine two-axis laid grain gated by cell hash; paper tooth
    16 Brushed     - per-column phase streaks; brushed steel, no banding
    17 Chevron     - zigzag line; baffles, lobby feature walls
    18 FrostBands  - smooth sine gradient bands; frosted glazing (the only
                    soft-profile analytic pattern)

    Rows 13-18 added 2026-10-06 for the Office Spider set. Every one tiles
    on the integer lattice (frac-wrap math, rational cord/offset
    positions) and uses only node classes the 2026-10-05 freeze already
    proves on this build - no new expression types.

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


def _axis(tx_node_owner, tex, rx, ry, x, y):
    """One scalar texture axis: Dot(tex, axis-unit).

    Dot(float2, float2) -> float1 is plain HLSL and the axis units are
    Constant2Vector with r/g props - both patterns proven on this build
    (postcomposite's Constant2Vector r/g; the master's DotProduct A/B).
    ComponentMask CANNOT do this job: it zeroes channels but keeps the
    float2 type, so parity/row math built on it stays mirrored.
    """
    fn = tx_node_owner
    unit = lib.expr(fn, unreal.MaterialExpressionConstant2Vector, x, y)
    unit.set_editor_property("r", rx)
    unit.set_editor_property("g", ry)
    d = lib.expr(fn, unreal.MaterialExpressionDotProduct, x + 160, y)
    lib.connect(tex, "", d, ["A", "a"])
    lib.connect(unit, "", d, ["B", "b"])
    return d


def _uv_basis(fn, angle_source, x=-2000):
    """Build a rotated UV frame driven by `angle_source` (degrees).

    Returns (texcoord, u, v, tx, ty). Rotation is the standard 2x2 frame:
        u' = u*cos - v*sin
        v' = u*sin + v*cos

    tx/ty are the SCALAR texture axes (added 2026-10-06). u and v are
    float2 throughout this function, and at the default Angle 0 they are
    IDENTICAL vectors - so any logic that needs INDEPENDENT axes (checker
    squares, weave parity, crosshatch diagonals, brick-row parity, blind
    cords, brushed columns, chevron guides, frost rows) must derive from
    tx/ty, never from u-vs-v. Three cells shipped degenerate on exactly
    this: _checker compared a value against 0.5 twice from the same input
    (an impulse at 0.5, not squares), _weave's parity was identically 0
    (no over-under alternation), and _crosshatch's second family was
    u-v = 0 (single stripes, not crosshatch) - all at the default angle.
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

    # Scalar axes split out of the raw texcoord (NOT out of u/v, which are
    # identical at Angle 0 - see docstring). Independent-axis logic reads
    # these; the float2 frame above is untouched for every existing user.
    tx = _axis(fn, tex, 1.0, 0.0, x + 740, 900)
    ty = _axis(fn, tex, 0.0, 1.0, x + 740, 1120)

    return tex, u, v, tx, ty


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


def _step(fn, value, x, y):
    """Unit step at 0.5: 1 above, 1 on (measure-zero, keeps continuity), else 0.

    The If-pin convention, fixed 2026-10-06: the value goes on the
    comparison-matched pins, NOT inverted (the old _checker wired 0.0 to
    "A > B", which is why it could only ever output an impulse).
    """
    st = lib.expr(fn, unreal.MaterialExpressionIf, x, y)
    lib.connect(value, "", st, ["A"])
    lib.connect(lib.scalar_const(fn, 0.5, x, y + 80), "", st, ["B"])
    lib.connect(lib.scalar_const(fn, 1.0, x, y + 160), "", st, ["A > B"])
    lib.connect(lib.scalar_const(fn, 1.0, x, y + 240), "", st, ["A == B"])
    lib.connect(lib.scalar_const(fn, 0.0, x, y + 320), "", st, ["A < B"])
    return st


def _checker(fn, tx, ty, scale, x=-1100, y_offset=400):
    """Real checkerboard (rewritten 2026-10-06).

    The old version fed the SAME scaled vector into both If inputs and
    compared once against 0.5 with inverted pins - provably an impulse at
    exactly 0.5, i.e. a ~zero field, never squares. This one steps each
    SCALAR axis independently (tx/ty from _uv_basis) and returns
    |sx - sy|: 1 on alternating squares, 0 elsewhere. Scalar in, scalar
    out. Graphic flats, VCT grout pairing, prop texture.
    """
    sx = lib.expr(fn, unreal.MaterialExpressionMultiply, x, y_offset)
    lib.binary(tx, scale, sx)
    fx = lib.expr(fn, unreal.MaterialExpressionFrac, x + 150, y_offset)
    lib.unary(sx, fx)
    stepx = _step(fn, fx, x + 300, y_offset)

    sy = lib.expr(fn, unreal.MaterialExpressionMultiply, x, y_offset + 220)
    lib.binary(ty, scale, sy)
    fy = lib.expr(fn, unreal.MaterialExpressionFrac, x + 150, y_offset + 220)
    lib.unary(sy, fy)
    stepy = _step(fn, fy, x + 300, y_offset + 220)

    d = lib.expr(fn, unreal.MaterialExpressionSubtract, x + 620, y_offset + 110)
    lib.binary(stepx, stepy, d)
    ad = lib.expr(fn, unreal.MaterialExpressionAbs, x + 780, y_offset + 110)
    lib.unary(d, ad)
    return ad


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


def _crosshatch(fn, tx, ty, scale, x=-1100, y_offset=2450):
    """Cross-hatch: two 45-degree line families, the engraving / pencil hatch.

    Rewritten 2026-10-06 onto the scalar axes: family A from (tx+ty),
    family B from (tx-ty) - true diagonals at the default angle. The old
    version built both families from the float2 frame (u+v)/(u-v), but u
    and v are IDENTICAL vectors at Angle 0, so family B was exactly 0 and
    the "cross"hatch was single-family stripes. Each family is a 1D
    distance field and the ink sits where either is near its line, so the
    two families cross into a lattice. Scalar in, scalar out.
    """
    a = lib.expr(fn, unreal.MaterialExpressionAdd, x, y_offset)
    lib.binary(tx, ty, a)
    b = lib.expr(fn, unreal.MaterialExpressionSubtract, x, y_offset + 220)
    lib.binary(tx, ty, b)

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


def _weave(fn, u, v, tx, ty, scale, x=-1100, y_offset=9000):
    """Warp/weft weave - cubicle fabric and acoustic cloth.

    Alternates which axis carries the thread profile by the parity of the cell
    (floor(tx) + floor(ty)), so consecutive cells read as over-under weaving
    rather than a plain grid - that is _grid's job, not this one.

    Parity fixed 2026-10-06: the old block floored the same float2 frame
    twice (floor(u*s) and floor(v*s) with u IDENTICAL to v), so the "sum"
    was always even and parity identically 0 - one thread profile
    everywhere, i.e. stripes, never weave. The cell coords below are the
    INDEPENDENT scalar axes, so Fx+Fy genuinely alternates.
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

    # parity = frac((Fx + Fy) * 0.5) * 2  -> 0 or 1, with Fx/Fy the
    # independent scalar cell coords (see docstring - the float2 frame
    # cannot supply these). Sum of two independent ints varies; double of
    # one int never does.
    txs = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 640, y_offset + 300)
    lib.binary(tx, scale, txs)
    tys = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 640, y_offset + 440)
    lib.binary(ty, scale, tys)
    gu = lib.expr(fn, unreal.MaterialExpressionFloor, x + 640, y_offset + 520)
    lib.unary(txs, gu)
    gv = lib.expr(fn, unreal.MaterialExpressionFloor, x + 640, y_offset + 660)
    lib.unary(tys, gv)
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


def _subway(fn, tx, ty, scale, x=-1100, y_offset=10600):
    """Running-bond subway tile - kitchen and washroom walls.

    Alternate rows offset by half a cell (parity from Frac(Floor/2) of the
    scalar ROW coord), field = grout distance (Max of centred axes, x2)
    like _grid. Row parity MUST come from ty alone: built on the float2
    frame the shift would vary per column (diagonal slide, not courses).
    Scalar in, scalar out; offset rows tile exactly.
    """
    txs = lib.expr(fn, unreal.MaterialExpressionMultiply, x, y_offset)
    lib.binary(tx, scale, txs)
    tys = lib.expr(fn, unreal.MaterialExpressionMultiply, x, y_offset + 140)
    lib.binary(ty, scale, tys)

    fl = lib.expr(fn, unreal.MaterialExpressionFloor, x + 160, y_offset + 140)
    lib.unary(tys, fl)
    half = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 320, y_offset + 140)
    lib.binary(fl, lib.scalar_const(fn, 0.5, x + 320, y_offset + 220), half)
    fr = lib.expr(fn, unreal.MaterialExpressionFrac, x + 480, y_offset + 140)
    lib.unary(half, fr)
    odd = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 640, y_offset + 140)
    lib.binary(fr, lib.scalar_const(fn, 2.0, x + 640, y_offset + 220), odd)
    shift = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 800, y_offset + 140)
    lib.binary(odd, lib.scalar_const(fn, 0.5, x + 800, y_offset + 220), shift)

    su_s = lib.expr(fn, unreal.MaterialExpressionAdd, x + 960, y_offset)
    lib.binary(txs, shift, su_s)
    fsu = lib.expr(fn, unreal.MaterialExpressionFrac, x + 1120, y_offset)
    lib.unary(su_s, fsu)
    fsv = lib.expr(fn, unreal.MaterialExpressionFrac, x + 1120, y_offset + 140)
    lib.unary(tys, fsv)

    eu = lib.expr(fn, unreal.MaterialExpressionSubtract, x + 1280, y_offset)
    lib.binary(fsu, lib.scalar_const(fn, 0.5, x + 1280, y_offset + 80), eu)
    au = lib.expr(fn, unreal.MaterialExpressionAbs, x + 1440, y_offset)
    lib.unary(eu, au)
    ev = lib.expr(fn, unreal.MaterialExpressionSubtract, x + 1280, y_offset + 140)
    lib.binary(fsv, lib.scalar_const(fn, 0.5, x + 1280, y_offset + 220), ev)
    av = lib.expr(fn, unreal.MaterialExpressionAbs, x + 1440, y_offset + 140)
    lib.unary(ev, av)

    mx = lib.expr(fn, unreal.MaterialExpressionMax, x + 1600, y_offset + 70)
    lib.binary(au, av, mx)
    twice = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 1760, y_offset + 70)
    lib.binary(mx, lib.scalar_const(fn, 2.0, x + 1760, y_offset + 150), twice)
    return twice


def _blinds(fn, tx, ty, scale, x=-1100, y_offset=11400):
    """Venetian blinds - slat faces plus lift-cord shadows.

    Slat face is broad (1 minus the triangle, so the Density cut reads
    louvres not wires); two cord lines at fixed quarter positions max in
    on top. Cords MUST derive from tx alone: on the float2 frame the same
    math draws horizontal lines too (a windowpane grid, not cords).
    Analytic sibling of the baked T_SDF_Blinds (which adds per-slat dust
    hash the graph cannot hold). Scalar in, scalar out.
    """
    tys = lib.expr(fn, unreal.MaterialExpressionMultiply, x, y_offset + 140)
    lib.binary(ty, scale, tys)
    txs = lib.expr(fn, unreal.MaterialExpressionMultiply, x, y_offset)
    lib.binary(tx, scale, txs)

    fr = lib.expr(fn, unreal.MaterialExpressionFrac, x + 160, y_offset + 140)
    lib.unary(tys, fr)
    # face = 1 - |2f-1|: 1 at the slat centre, 0 at the gaps, range 0..1.
    t2 = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 320, y_offset + 140)
    lib.binary(fr, lib.scalar_const(fn, 2.0, x + 320, y_offset + 220), t2)
    c = lib.expr(fn, unreal.MaterialExpressionSubtract, x + 480, y_offset + 140)
    lib.binary(t2, lib.scalar_const(fn, 1.0, x + 480, y_offset + 220), c)
    a = lib.expr(fn, unreal.MaterialExpressionAbs, x + 640, y_offset + 140)
    lib.unary(c, a)
    face = lib.expr(fn, unreal.MaterialExpressionOneMinus, x + 800, y_offset + 140)
    lib.unary(a, face)

    fsu = lib.expr(fn, unreal.MaterialExpressionFrac, x + 160, y_offset)
    lib.unary(txs, fsu)
    d1 = lib.expr(fn, unreal.MaterialExpressionSubtract, x + 320, y_offset)
    lib.binary(fsu, lib.scalar_const(fn, 0.25, x + 320, y_offset + 80), d1)
    a1 = lib.expr(fn, unreal.MaterialExpressionAbs, x + 480, y_offset)
    lib.unary(d1, a1)
    d2 = lib.expr(fn, unreal.MaterialExpressionSubtract, x + 320, y_offset + 160)
    lib.binary(fsu, lib.scalar_const(fn, 0.75, x + 320, y_offset + 240), d2)
    a2 = lib.expr(fn, unreal.MaterialExpressionAbs, x + 480, y_offset + 160)
    lib.unary(d2, a2)
    mn = lib.expr(fn, unreal.MaterialExpressionMin, x + 640, y_offset + 80)
    lib.binary(a1, a2, mn)
    w = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 800, y_offset + 80)
    lib.binary(mn, lib.scalar_const(fn, 50.0, x + 800, y_offset + 160), w)
    sat = lib.expr(fn, unreal.MaterialExpressionSaturate, x + 960, y_offset + 80)
    lib.unary(w, sat)
    cord = lib.expr(fn, unreal.MaterialExpressionOneMinus, x + 1120, y_offset + 80)
    lib.unary(sat, cord)

    fld = lib.expr(fn, unreal.MaterialExpressionMax, x + 1280, y_offset + 110)
    lib.binary(face, cord, fld)
    return fld


def _paperfiber(fn, u, v, scale, x=-1100, y_offset=12200):
    """Paper fibre - fine two-axis grain broken by hash.

    Horizontal laid lines dominate (0.65) over vertical (0.35), the whole
    gated by (0.6 + 0.4 * cell hash) so it reads fibrous, never ruled.
    Analytic sibling of T_SDF_PaperGrain for surfaces that must stay
    texture-free; keep Density low - this is tooth, not ink.
    """
    su = lib.expr(fn, unreal.MaterialExpressionMultiply, x, y_offset)
    lib.binary(u, scale, su)
    sv = lib.expr(fn, unreal.MaterialExpressionMultiply, x, y_offset + 140)
    lib.binary(v, scale, sv)

    # centred triangles |2f-1| (a bare Abs(Frac) is a 0..1 ramp, useless
    # as a thread profile - both axes go through x2, -1, Abs).
    su3 = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 160, y_offset)
    lib.binary(su, lib.scalar_const(fn, 3.0, x + 160, y_offset + 80), su3)
    fh = lib.expr(fn, unreal.MaterialExpressionFrac, x + 320, y_offset)
    lib.unary(su3, fh)
    h2 = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 480, y_offset)
    lib.binary(fh, lib.scalar_const(fn, 2.0, x + 480, y_offset + 80), h2)
    hc = lib.expr(fn, unreal.MaterialExpressionSubtract, x + 640, y_offset)
    lib.binary(h2, lib.scalar_const(fn, 1.0, x + 640, y_offset + 80), hc)
    th = lib.expr(fn, unreal.MaterialExpressionAbs, x + 800, y_offset)
    lib.unary(hc, th)

    sv5 = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 160, y_offset + 140)
    lib.binary(sv, lib.scalar_const(fn, 5.0, x + 160, y_offset + 220), sv5)
    fv = lib.expr(fn, unreal.MaterialExpressionFrac, x + 320, y_offset + 140)
    lib.unary(sv5, fv)
    v2 = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 480, y_offset + 140)
    lib.binary(fv, lib.scalar_const(fn, 2.0, x + 480, y_offset + 220), v2)
    vc = lib.expr(fn, unreal.MaterialExpressionSubtract, x + 640, y_offset + 140)
    lib.binary(v2, lib.scalar_const(fn, 1.0, x + 640, y_offset + 220), vc)
    tv = lib.expr(fn, unreal.MaterialExpressionAbs, x + 800, y_offset + 140)
    lib.unary(vc, tv)

    cu = lib.expr(fn, unreal.MaterialExpressionFloor, x + 160, y_offset + 300)
    lib.unary(su, cu)
    cv = lib.expr(fn, unreal.MaterialExpressionFloor, x + 160, y_offset + 440)
    lib.unary(sv, cv)
    h = _hash2(fn, cu, cv, 12.9898, 78.233, x + 320, y_offset + 370)

    wh = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 960, y_offset)
    lib.binary(th, lib.scalar_const(fn, 0.65, x + 960, y_offset + 80), wh)
    wv = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 960, y_offset + 140)
    lib.binary(tv, lib.scalar_const(fn, 0.35, x + 960, y_offset + 220), wv)
    base = lib.expr(fn, unreal.MaterialExpressionAdd, x + 1120, y_offset + 70)
    lib.binary(wh, wv, base)

    hg = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 1440, y_offset + 370)
    lib.binary(h, lib.scalar_const(fn, 0.4, x + 1440, y_offset + 450), hg)
    gate = lib.expr(fn, unreal.MaterialExpressionAdd, x + 1600, y_offset + 370)
    lib.binary(hg, lib.scalar_const(fn, 0.6, x + 1600, y_offset + 450), gate)

    fld = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 1760, y_offset + 220)
    lib.binary(base, gate, fld)
    return fld


def _brushed(fn, tx, ty, scale, x=-1100, y_offset=13000):
    """Brushed metal - streaks with per-column phase.

    Column index (from tx ONLY) hashes to a phase offset added to the
    vertical run, so streaks run full-length without synchronising into
    bands. Built on the float2 frame the phase would key off 2D cells and
    streaks would chop per row. Analytic sibling of T_SDF_Brushed.
    Coffee machine, filing cabinets, chair legs. Scalar in, scalar out.
    """
    txs = lib.expr(fn, unreal.MaterialExpressionMultiply, x, y_offset)
    lib.binary(tx, scale, txs)
    tys = lib.expr(fn, unreal.MaterialExpressionMultiply, x, y_offset + 140)
    lib.binary(ty, scale, tys)

    col = lib.expr(fn, unreal.MaterialExpressionFloor, x + 160, y_offset)
    lib.unary(txs, col)
    zero = lib.scalar_const(fn, 0.0, x + 160, y_offset + 300)
    ph = _hash2(fn, col, zero, 12.9898, 78.233, x + 320, y_offset + 150)

    sv2 = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 160, y_offset + 500)
    lib.binary(tys, lib.scalar_const(fn, 2.0, x + 160, y_offset + 580), sv2)
    s = lib.expr(fn, unreal.MaterialExpressionAdd, x + 1000, y_offset + 325)
    lib.binary(sv2, ph, s)
    fr = lib.expr(fn, unreal.MaterialExpressionFrac, x + 1160, y_offset + 325)
    lib.unary(s, fr)
    # centred triangle |2f-1|: lines at the streak borders, seamless wrap.
    t2 = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 1320, y_offset + 325)
    lib.binary(fr, lib.scalar_const(fn, 2.0, x + 1320, y_offset + 405), t2)
    tc = lib.expr(fn, unreal.MaterialExpressionSubtract, x + 1480, y_offset + 325)
    lib.binary(t2, lib.scalar_const(fn, 1.0, x + 1480, y_offset + 405), tc)
    tri = lib.expr(fn, unreal.MaterialExpressionAbs, x + 1640, y_offset + 325)
    lib.unary(tc, tri)
    return tri


def _chevron(fn, tx, ty, scale, x=-1100, y_offset=13800):
    """Chevron zigzag - acoustic baffles, lobby feature walls.

    TRUE chevron (fixed 2026-10-06): guide is a triangle of the ROW axis
    (|2Frac(ty)-1|), position reads the COLUMN axis (Frac(tx)) - the line
    is |fu - zv| = 0, a zigzag running down the tile. On the float2 frame
    both axes carried both coordinates (a mirrored double chevron at best).
    Mark sits ON the line at fixed width. Scalar in, scalar out; tiles
    exactly - integer lattice math throughout.
    """
    txs = lib.expr(fn, unreal.MaterialExpressionMultiply, x, y_offset)
    lib.binary(tx, scale, txs)
    tys = lib.expr(fn, unreal.MaterialExpressionMultiply, x, y_offset + 140)
    lib.binary(ty, scale, tys)

    # triangle guide |2f-1| (a bare Abs(Frac) would be a sawtooth ramp -
    # the zigzag needs the fold, or rows never mirror).
    fv = lib.expr(fn, unreal.MaterialExpressionFrac, x + 160, y_offset + 140)
    lib.unary(tys, fv)
    f2 = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 320, y_offset + 140)
    lib.binary(fv, lib.scalar_const(fn, 2.0, x + 320, y_offset + 220), f2)
    fc = lib.expr(fn, unreal.MaterialExpressionSubtract, x + 480, y_offset + 140)
    lib.binary(f2, lib.scalar_const(fn, 1.0, x + 480, y_offset + 220), fc)
    zv = lib.expr(fn, unreal.MaterialExpressionAbs, x + 640, y_offset + 140)
    lib.unary(fc, zv)
    fu = lib.expr(fn, unreal.MaterialExpressionFrac, x + 160, y_offset)
    lib.unary(txs, fu)
    d = lib.expr(fn, unreal.MaterialExpressionSubtract, x + 800, y_offset + 70)
    lib.binary(fu, zv, d)
    ad = lib.expr(fn, unreal.MaterialExpressionAbs, x + 960, y_offset + 70)
    lib.unary(d, ad)
    w = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 1120, y_offset + 70)
    lib.binary(ad, lib.scalar_const(fn, 6.0, x + 1120, y_offset + 150), w)
    sat = lib.expr(fn, unreal.MaterialExpressionSaturate, x + 1280, y_offset + 70)
    lib.unary(w, sat)
    line = lib.expr(fn, unreal.MaterialExpressionOneMinus, x + 1440, y_offset + 70)
    lib.unary(sat, line)
    return line


def _frostbands(fn, ty, scale, x=-1100, y_offset=14600):
    """Frosted-glass bands - the only smooth-profile analytic pattern.

    0.5 + 0.5 * Sine(scaled ty): a true gradient, not a thresholded
    triangle. Read from the ROW axis alone so bands run horizontally -
    on the float2 frame the sine ran on both components (cross-hatch
    ripple, not bands). The Density cut positions the frost edge;
    Softness is nearly irrelevant here (the profile IS soft).
    Conference-door glazing with T_SDF_FrostBands behind it for etch
    variance. Scalar in, scalar out.
    """
    tys = lib.expr(fn, unreal.MaterialExpressionMultiply, x, y_offset)
    lib.binary(ty, scale, tys)
    sn = lib.expr(fn, unreal.MaterialExpressionSine, x + 160, y_offset)
    sn.set_editor_property("period", 1.0)
    lib.unary(tys, sn)
    half = lib.expr(fn, unreal.MaterialExpressionMultiply, x + 320, y_offset)
    lib.binary(sn, lib.scalar_const(fn, 0.5, x + 320, y_offset + 80), half)
    fld = lib.expr(fn, unreal.MaterialExpressionAdd, x + 480, y_offset)
    lib.binary(half, lib.scalar_const(fn, 0.5, x + 480, y_offset + 80), fld)
    return fld


def build(rebuild=True):
    lib.log(f"=== {NAME} ===")
    fn = lib.get_or_create_function(NAME, rebuild=rebuild)
    lib.try_set(fn, "description",
                "SDF-style procedural patterns (halftone/checker/stripes/crackle/ink/"
                "crosshatch/stipple/rings/voronoi/grid/perforation/weave/sdfmap/"
                "subway/blinds/paperfiber/brushed/chevron/frostbands) with "
                "a Density coverage knob. "
                "UE 5.8 has no SDF node; 0-11 and 13-18 are analytic distance "
                "constructions, 12 samples a baked signed-distance map texture.")

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
    for i, mult in enumerate([1.0] * 19):
        scales[i] = lib.expr(fn, unreal.MaterialExpressionMultiply, -1900, 700 + i * 60)
        lib.connect(scale_in, "", scales[i], ["A"])
        lib.connect(lib.scalar_const(fn, mult, -1900, 780 + i * 60), "", scales[i], ["B"])

    # rotated UV frame, shared by every pattern. Built at angle 0 from
    # TextureCoordinate; Angle is applied per-instance via the input.
    # tx/ty are the scalar axes for independent-axis cells (2026-10-06).
    tex, u, v, tx, ty = _uv_basis(fn, angle_in)

    # ---------------- pattern fields ----------------
    # 0-7 are the 2026-10-01 set; 8-11 added 2026-10-02 for the office film;
    # 13-18 added 2026-10-06 for the Office Spider set (SDF_PATTERN_PIPELINE
    # .md S3 table is the authority for what each is for).
    fields = {
        0: _halftone(fn, u, scales[0]),
        1: _checker(fn, tx, ty, scales[1]),
        2: _stripes(fn, u, scales[2]),
        3: _crackle(fn, u, scales[3]),
        4: _inksplat(fn, u, scales[4]),
        5: _crosshatch(fn, tx, ty, scales[5]),
        6: _stipple(fn, u, v, scales[6]),
        7: _rings(fn, u, v, scales[7]),
        8: _voronoi(fn, u, v, scales[8]),
        9: _grid(fn, u, v, scales[9]),
        10: _perforation(fn, u, v, scales[10]),
        11: _weave(fn, u, v, tx, ty, scales[11]),
        12: _sdfmap(fn, u, v, scales[12], sdf_in),
        13: _subway(fn, tx, ty, scales[13]),
        14: _blinds(fn, tx, ty, scales[14]),
        15: _paperfiber(fn, u, v, scales[15]),
        16: _brushed(fn, tx, ty, scales[16]),
        17: _chevron(fn, tx, ty, scales[17]),
        18: _frostbands(fn, ty, scales[18]),
    }

    # ---------------- pattern selector (nested static-free If chain) ----------------
    # Static switches would bake per-instance; an If chain on CellIndex stays
    # dynamic so one material instance can switch pattern at runtime.
    #
    # CORRECTNESS NOTE 2026-10-06 - this chain shipped INVERTED and has been
    # wrong since it was written (found by code reading + the live pin-name
    # probe: MaterialExpressionIf inputs are A, B, "A > B", "A == B",
    # "A < B", exactly as used here). The old wiring put fields[idx] on
    # "A > B" with current on both other pins: tracing the dataflow (the
    # final output is the idx=0 node, whose "current" input is node 1's
    # output, and so on up) shows CellIndex 0 selected the TOP field and
    # every other index selected field 0 - the whole library routed to one
    # pattern. It survived because PatternStrength defaults to 0 (the
    # pattern path is inert until an instance opts in) and because
    # Substrate lookdev is driver-blocked on the authoring machine, so no
    # pixel ever accused it. Structure-only verification cannot see this
    # class: pin names confirmed live via get_expression_pin_info.
    #
    # Correct descending form: "A > B" takes current (the already-resolved
    # higher set - by induction it answers every index above idx), "A == B"
    # takes fields[idx] (exact-integer CellIndex values hit equality), and
    # "A < B" takes current (out of this subtree's domain; the node below
    # resolves it - and the bottom node 0 answers 0 exactly on equality,
    # so every valid index terminates on its own field).
    current = None
    for idx in sorted(fields, reverse=True):
        if current is None:
            current = fields[idx]
            continue
        cond = lib.expr(fn, unreal.MaterialExpressionIf, -700 + idx * 180, 2200)
        lib.connect(cell_in, "", cond, ["A"])
        lib.connect(lib.scalar_const(fn, float(idx), -700 + idx * 180, 2300), "", cond, ["B"])
        lib.connect(current, "", cond, ["A > B"])
        lib.connect(fields[idx], "", cond, ["A == B"])
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
