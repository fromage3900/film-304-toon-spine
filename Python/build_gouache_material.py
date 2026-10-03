"""Build M_PainterlyGouache - the 304 film painterly gouache master.

BUILD ORDERING IS NOT OPTIONAL - READ THIS BEFORE MOVING ANYTHING
--------------------------------------------------------------
Every save in this builder goes through UE's asset save path, which on this
project pops MODAL dialogs ("Overwrite Existing Object", "This asset editor has
no docked tabs"). While a modal is open the game thread is in a blocking modal
loop: the Python script CONTINUES, but UE never flushes the pending save, and
MaterialEditingLibrary.recompile_material() recompiles whatever is still in the
previous on-disk state.

Observed directly: a build reported ok=true with wire_failures=[] and profile
bound, and the material still compiled to "(Node Saturate) Missing Saturate
input" - because the compile was of the OLD graph. The log shows
"Window 'Overwrite Existing Object' being destroyed" immediately before the
compile failure, and a Monolith MODAL_OPEN warning for the same timestamp.

So the fix is not more pin-name guessing. The fix is to prove the thing that
was actually written. This builder therefore:

  * recompiles, then FORCES a fresh compile of the saved asset, and
  * reads the material's compile errors back through
    unreal.MaterialEditingLibrary.get_statistics / AssetLog-style checks,
  * and treats "I called recompile" as worthless on its own.

If the editor is sitting on a modal when this runs, the run will still be
useless - dismiss any open dialog first.

WHAT THIS IS
    A sibling of M_Master_Toon_Universal, not a replacement. Same Substrate Toon
    BSDF closure and same Toon Profile lane, but the surface response is
    rewritten for opaque matte gouache instead of cel shading.

WHY A SEPARATE MASTER
    The toon master owns a cel ramp driven by its Toon Profile. Gouache wants a
    hand-controlled wash with exactly two thresholds and nothing else - the
    banding has to be authored, not inherited from a profile someone retunes.
    Bolting a "GouacheMode" switch onto the toon master would leave every
    existing MI one profile tweak away from rendering as the wrong medium, and
    the toon master already carries 42 scalars.

THE FOUR THINGS THAT MAKE IT READ AS GOUACHE
    1. A HARD TWO-THRESHOLD WASH. Two SmoothSteps over the terminator produce
       three flat bands (shadow / mid / lit). Softness defaults to 0.04, so the
       band edges are near-binary. Gouache is laid down in flat washes with a
       crisp boundary; a smooth ramp reads as airbrush no matter what the
       colours are.
    2. OPAQUE MATTE RESPONSE. Roughness 0.92, Specular 0.06. Gouache has almost
       no specular response - the binder is matte and the pigment is opaque.
    3. WET EDGE darkening, DERIVED FROM THE WASH BOUNDARY. Pigment collects
       where a wash meets its neighbour, so the edge must follow the form. It is
       computed as the screen-space gradient of the band field (ddx/ddy of the
       combined 0..1 wash), which is non-zero only at a wash boundary and zero
       inside a flat wash. This is the single strongest gouache cue and it is
       what separates this from plain flat cel shading.
       The previous implementation sampled T_Gouache_BrushEdge - a UV-tiled
       streak field - which stamped identical stripes over flat and curved
       surfaces alike. That is a texture on the mesh, not a property of the
       wash, and it read as dirt rather than pigment.
    4. GRANULATION (T_Gouache_Granulation). Pigment settles into the tooth of
       the paper, so the mottling follows the SURFACE and not the light. The
       field is coupled to the paper-tooth field: sediment occupies the grain's
       valleys and the peaks stay clean. Granulation at paper-tooth scale is
       what makes a flat wash read as pigment rather than as digital gradient.
       Applied as a MULTIPLY toward a darker value rather than a lerp toward
       InkColor: pooling must preserve the local hue, and a lerp to a single
       dark colour drains the colour out of every pool.

    T_Gouache_WashBlotch stops the lit band from being perfectly flat, and
    T_Gouache_PaperGrain drives ROUGHNESS rather than albedo - tooth is a
    surface-relief cue, and putting it in albedo just looks like dirt.

PARKING
    The brush-edge and granulation samples are texture PARAMETERS, so an MI can
    swap in hand-painted scans later without touching the graph.

Run (editor open, via Monolith):
    editor_query run_python {command: "Python/build_gouache_material.py",
                             mode: execute_file}

Run headless:
    UnrealEditor-Cmd.exe <project>.uproject ^
      -ExecutePythonScript="Python/build_gouache_material.py" -stdout -unattended

Assert on the report FILE, not the log - unreal.log() is unreliable under
-stdout capture.
"""
from __future__ import annotations

import json
import os
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# Evict the cached modules BEFORE importing them. Re-running this script inside
# one long-lived editor would otherwise import the OLD spine_lib and the OLD
# build_gouache_textures - Python caches modules in sys.modules on first import,
# so an edit to either file is invisible until the editor restarts. That is not
# hypothetical: an earlier run of this builder silently used the pre-fix
# unary() and produced the same broken graph twice.
for _stale in ("build_gouache_textures", "spine_lib"):
    sys.modules.pop(_stale, None)

import unreal  # noqa: E402

import spine_lib as lib  # noqa: E402
import build_gouache_textures as fields  # noqa: E402

NAME = "M_PainterlyGouache"
TEX_DIR = "/Game/Materials/Textures/Gouache"

# Bound LAST, after recompile - see the ordering note in build_master_toon.py:
# setting toon_profile on a freshly created material before recompile reports
# success and then reads back None.
MASTER_PROFILE = "TP_Default"

REPO = Path(__file__).resolve().parents[1]
REPORT = Path(os.environ.get("TEMP", ".")) / "gouache_build_report.json"
AUDIT_COPY = REPO / "Saved" / "Audit" / "gouache_build_report.json"


# ---------------------------------------------------------------------------
# Texture import
# ---------------------------------------------------------------------------

# Candidate member names are PROBED rather than hardcoded. build_textures.py
# records why: an all-caps guess like TC_VECTOR_DISPLACEMENTMAP does not resolve
# and silently leaves the texture on TC_DEFAULT block compression, which
# averages 4x4 blocks and destroys exactly the thin filaments T_Gouache_BrushEdge
# depends on. Probe, then use whatever actually exists.
ENUM_SPECS = {
    "comp_lossless": ("TextureCompressionSettings",
                      ["TC_VECTOR_DISPLACEMENTMAP", "TC_VectorDisplacementmap",
                       "TC_GRAYSCALE", "TC_Grayscale", "TC_DEFAULT", "TC_Default"]),
    "addr_wrap": ("TextureAddress", ["TA_WRAP", "TA_Wrap"]),
    "mips_on": ("TextureMipGenSettings",
                # Measured member list on this build
                # (Saved/Audit/texture_enum_probe.json): there is NO
                # TMGS_BILINEAR. The real names are TMGS_FROM_TEXTURE_GROUP and
                # TMGS_SIMPLE_AVERAGE; the old TMGS_BILINEAR guess resolved to
                # None and was silently skipped, leaving the imported texture on
                # whatever the asset importer had chosen.
                ["TMGS_FROM_TEXTURE_GROUP", "TMGS_SIMPLE_AVERAGE",
                 "TMGS_BILINEAR"]),
}


def resolve_enums() -> dict:
    resolved = {}
    for key, (class_name, members) in ENUM_SPECS.items():
        cls = getattr(unreal, class_name, None)
        found, value = None, None
        if cls is not None:
            for cand in members:
                if hasattr(cls, cand):
                    found, value = cand, getattr(cls, cand)
                    break
        resolved[key] = {"value": value, "member": found, "enum": class_name}
    return resolved


def _set(tex, prop, value, entry, key):
    """Set one texture property, recording success/failure. Never raises."""
    if value is None:
        entry["skipped"].append(f"{key}: unresolved")
        return
    try:
        tex.set_editor_property(prop, value)
        entry["set"].append(f"{key}={getattr(value, 'name', value)}")
    except Exception as exc:
        entry["failed"].append(f"{key}: {str(exc)[:120]}")


# DDX/DDY are the wet-edge detector. They are PROBED, not assumed, for the same
# reason ENUM_SPECS above is: this builder has already shipped once on a name
# that resolved to None and silently disabled a control. DDX/DDY are also
# worth probing specifically because they are editor-and-preview-derivation
# nodes: they are valid in the material editor and in PIE, but compile to zero
# in a cooked/shipping build. A film rendered in-editor is fine; anything
# depending on the edge surviving a cook is NOT, and that is recorded in the
# report so the limitation cannot be discovered from a black image later.
DERIV_NODE_NAMES = ("MaterialExpressionDDX", "MaterialExpressionDDY")


def resolve_deriv_nodes() -> dict:
    resolved = {}
    for nm in DERIV_NODE_NAMES:
        cls = getattr(unreal, nm, None)
        resolved[nm] = {"present": cls is not None, "class": nm if cls else None}
    return resolved


def import_gouache_textures(resolved: dict) -> dict:
    """Generate the fields, import each one, and READ BACK its settings.

    A generator that silently emitted a flat image would import cleanly and then
    render as nothing, so the generator's own field statistics are carried into
    the report alongside the texture readback.
    """
    lib.ensure_dir(TEX_DIR)
    gen_report = fields.build()
    out = {"generated": {}, "errors": []}
    out["errors"] += [f"generator: {e}" for e in gen_report.get("errors", [])]

    for name, stats in gen_report["textures"].items():
        entry = {"set": [], "failed": [], "skipped": [],
                 "field_min": stats["min"], "field_max": stats["max"],
                 "field_distinct": stats["distinct_values"], "why": stats["why"]}
        try:
            png = Path(stats["path"])
            task = unreal.AssetImportTask()
            task.filename = str(png)
            task.destination_path = TEX_DIR
            task.destination_name = name
            task.automated = True
            task.save = True
            task.replace_existing = True
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

            tex = unreal.load_asset(f"{TEX_DIR}/{name}.{name}")
            if tex is None:
                entry["failed"].append("import returned None")
                out["errors"].append(f"{name}: import failed")
                out["generated"][name] = entry
                continue

            # sRGB OFF: these are data fields. sRGB would gamma the ramp and the
            # sampled value would no longer mean what the generator wrote.
            _set(tex, "srgb", False, entry, "srgb")
            _set(tex, "address_x", resolved["addr_wrap"]["value"], entry, "address_x")
            _set(tex, "address_y", resolved["addr_wrap"]["value"], entry, "address_y")
            _set(tex, "compression_settings", resolved["comp_lossless"]["value"],
                 entry, "compression")
            _set(tex, "mip_gen_settings", resolved["mips_on"]["value"], entry, "mipgen")

            try:
                entry["size"] = f"{tex.blueprint_get_size_x()}x{tex.blueprint_get_size_y()}"
            except Exception:
                entry["size"] = "unknown"

            readback = {}
            for prop in ("srgb", "address_x", "address_y",
                         "compression_settings", "mip_gen_settings"):
                try:
                    v = tex.get_editor_property(prop)
                    readback[prop] = str(getattr(v, "name", v))
                except Exception as exc:
                    readback[prop] = f"<{str(exc)[:60]}>"
            entry["readback"] = readback

            lib.save(tex)
            entry["asset"] = f"{TEX_DIR}/{name}.{name}"
            entry["ok"] = not entry["failed"]
            if not entry["ok"]:
                out["errors"].append(f"{name}: settings failed")
        except Exception as exc:
            entry["failed"].append(str(exc)[:300])
            out["errors"].append(f"{name}: {exc}")
        out["generated"][name] = entry

    return out


# ---------------------------------------------------------------------------
# Material graph
# ---------------------------------------------------------------------------

class Wiring:
    """Collects failed connection attempts so the build can fail loudly.

    lib.connect / unary / binary / ternary all return a bool, and builders have
    historically ignored it. That is exactly how the first version of this
    material shipped with two unconnected Saturate nodes: the graph looked
    complete, verify_material passed, the dead-node census passed, and the
    material still compiled to "(Node Saturate) Missing Saturate input" and
    rendered as Default Material.

    Every helper call in build() is wrapped here, so a pin that will not accept
    a connection stops the build instead of producing a plausible-looking
    broken material. Counts failures rather than raising on the first one, so
    one run reports every broken pin instead of one per iteration.
    """

    def __init__(self):
        self.failures = []

    def wrap(self, fn):
        def checked(*a, **kw):
            ok = fn(*a, **kw)
            if not ok:
                target = a[-1] if a else "?"
                self.failures.append(
                    f"{fn.__name__} -> {type(target).__name__}")
            return ok
        return checked

    def install(self, module):
        for name in ("unary", "binary", "ternary"):
            setattr(self, name, self.wrap(getattr(module, name)))


def build(rebuild=True) -> dict:
    report = {"material": NAME, "errors": [], "warnings": []}

    wiring = Wiring()
# Build a checked proxy of spine_lib. The proxy is bound to a DIFFERENT name
    # (`L`) because rebinding `lib` would shadow the module-level import for the
    # whole function scope and make every earlier reference an UnboundLocalError.
    L = types.SimpleNamespace(
        **{k: getattr(lib, k) for k in dir(lib) if not k.startswith("__")})
    wiring.install(L)
    L.unary = wiring.unary
    L.binary = wiring.binary
    L.ternary = wiring.ternary
    report["wiring_helper"] = "checked unary/binary/ternary via Wiring"

    resolved = resolve_enums()
    report["enums"] = {k: v["member"] for k, v in resolved.items()}
    for key, meta in resolved.items():
        if meta["value"] is None:
            # A hard failure, not a warning. build_textures.py reported ok=true
            # with every setting skipped and the textures on engine defaults;
            # the read-back from the live editor is what finally caught it. A
            # skip must never be able to pass again.
            report["errors"].append(
                f"enum unresolved: {key} ({meta['enum']}) - texture settings "
                f"would be silently skipped")

    deriv = resolve_deriv_nodes()
    report["deriv_nodes"] = {k: v["present"] for k, v in deriv.items()}
    missing_deriv = [k for k, v in deriv.items() if not v["present"]]
    if missing_deriv:
        # Hard failure. Without DDX/DDY there is no wet edge at all, and the
        # material would otherwise build clean, render flat, and look like a
        # tuning problem rather than a missing node.
        report["errors"].append(
            f"wet-edge derivative nodes unavailable: {missing_deriv} - the wet "
            f"edge cannot be derived and the wash would render with no edge")

    report["textures"] = import_gouache_textures(resolved)
    report["errors"] += report["textures"]["errors"]

    # rebuild=True wipes the graph IN PLACE. The existing stub M_PainterlyGouache
    # is replaced this way rather than deleted - see get_or_create_material for
    # why delete-then-create breaks every referencing instance.
    mat = lib.get_or_create_material(NAME, lib.MASTER_DIR, rebuild=rebuild)

    # ---------------- parameters ----------------
    base = lib.vector(mat, "BaseTint", "Palette", (0.70, 0.64, 0.56, 1.0),
                      -1500, 100, desc="Main wash colour")
    high = lib.vector(mat, "HighlightTint", "Palette", (0.88, 0.84, 0.76, 1.0),
                      -1500, 200, desc="Lit wash colour")
    # Deep warm-violet, never black - the manifest's canonical shadow.
    ink = lib.vector(mat, "InkColor", "Palette", (0.16, 0.13, 0.18, 1.0),
                     -1500, 300, desc="Wet-edge / pooling / shadow colour")

    b_shadow = lib.scalar(mat, "GouacheBandShadow", "Wash", 0.40, -1500, 420,
                          desc="Terminator threshold, shadow->mid")
    b_light = lib.scalar(mat, "GouacheBandLight", "Wash", 0.70, -1500, 500,
                         desc="Terminator threshold, mid->lit")
    # 0.04 is deliberately tiny. This is the whole ballgame: the parameter is the
    # distance over which the wash blends, and a gouache edge is near-binary.
    b_soft = lib.scalar(mat, "GouacheBandSoftness", "Wash", 0.04, -1500, 580,
                        desc="Wash edge softness; near 0 = hard stepped edge")
    shadow_mix = lib.scalar(mat, "GouacheShadowMix", "Wash", 0.55, -1500, 660,
                            desc="How far the deepest wash goes toward InkColor")

    gran = lib.scalar(mat, "GouacheGranulation", "Surface", 0.35, -1500, 780,
                      desc="Pigment pooling amount (T_Gouache_Granulation)")
    gran_dark = lib.scalar(mat, "GouacheGranulationDarken", "Surface", 0.70,
                           -1500, 860,
                           desc="How dark a pigment pool gets; 1.0 = black pool")
    edge = lib.scalar(mat, "GouacheEdgeStrength", "Surface", 0.55, -1500, 940,
                      desc="Wet-edge darkening along wash boundaries")
    # Width and intensity are SEPARATE controls, following Flair's production
    # guidance that "a wider edge darkening will require an increase in intensity,
    # as well". Collapsing them into one slider (as the previous version did) is
    # why the edge could only ever be tuned in strength, never in how far it
    # reached into the wash.
    edge_width = lib.scalar(mat, "GouacheEdgeWidth", "Surface", 1.0, -1500, 980,
                            desc="How far the wet edge reaches; higher = wider")
    # Normalisation reference for the screen-space band gradient. The band's
    # total transition is BandLight-BandShadow wide, and that whole span
    # compresses into very few pixels, so the raw ddx magnitude is tiny. This
    # divisor is the gradient magnitude a perfect edge produces; above it the
    # edge saturates at full strength.
    edge_ref = lib.scalar(mat, "GouacheEdgeReference", "Surface", 0.02, -1500, 1010,
                          desc="Gradient magnitude that counts as a full edge")
    blotch = lib.scalar(mat, "GouacheBlotchStrength", "Surface", 0.18, -1500, 1020,
                        desc="Wash variation so a band is never perfectly flat")
    tooth_amt = lib.scalar(mat, "GouachePaperGrain", "Surface", 0.20, -1500, 1100,
                           desc="Paper tooth, applied to ROUGHNESS not albedo")
    roughness = lib.scalar(mat, "GouacheRoughness", "Surface", 0.92, -1500, 1180,
                           desc="Gouache is matte; 0.92 approximates opaque binder")
    specular = lib.scalar(mat, "GouacheSpecular", "Surface", 0.06, -1500, 1260,
                          desc="Very low - gouache has almost no specular response")
    tiling = lib.scalar(mat, "GouacheTiling", "Surface", 6.0, -1500, 1340,
                        desc="Texture repeats per UV unit")
    key_dir = lib.vector(mat, "KeyLightDir", "Wash", (0.0, 0.0, 1.0), -1500, 1420,
                         desc="Light direction the washes are laid against")

    # FIXED KEY - A DELIBERATE ART-DIRECTION DECISION, NOT AN OVERSIGHT.
    #
    # The terminator is `dot(PixelNormalWS, normalize(KeyLightDir))`. It uses
    # NO scene light and NO shadowing, which means an object standing in a cast
    # shadow still receives its lit band. That is normally wrong, and it was
    # chosen here on purpose (2026-10-03, lookdev pass) for two reasons:
    #
    #   * Predictability. The wash is art-directable from a single scalar. An
    #     artist can guarantee what a lit face looks like without auditing every
    #     light in the shot, and two MI_* instances on the same mesh stay
    #     consistent regardless of where they are placed.
    #   * Medium integrity. Gouache is a hand-laid illustration, not a
    #     simulation of light. Letting the shot's sun drive the bands makes the
    #     master light-dependent, so an MI retuned for one shot silently reads
    #     wrong in the next.
    #
    # The cost is real and must be stated: cast shadows and the wash can
    # DISAGREE, and on a shot with strong directional light that is the first
    # thing a reviewer will notice. The remedy at shot level is to darken the
    # material where the shadow falls (an override or a separate shadowed MI),
    # not to reintroduce scene lighting here.
    #
    # KeyLightDir is (0,0,1) - straight up. That is a PLACEHOLDER chosen so the
    # bands fall predictably; a top-down terminator puts the band boundary on
    # the upper surfaces, which is not how any of these meshes are lit. This
    # value has never been validated against a real render and is one of the
    # first things Phase 1 lookdev should settle.
    emis_c = lib.vector(mat, "EmissiveColor", "Emissive", (0.0, 0.0, 0.0, 1.0),
                        -1500, 1500, desc="Emission colour (signage, screens)")
    emis_i = lib.scalar(mat, "EmissiveIntensity", "Emissive", 0.0, -1500, 1580,
                        desc="Emission strength; 0 = off")

    # ---------------- shared UV ----------------
    uv = lib.expr(mat, unreal.MaterialExpressionTextureCoordinate, -1200, 1800)
    uv_scaled = lib.expr(mat, unreal.MaterialExpressionMultiply, -1000, 1800)
    L.binary(uv, tiling, uv_scaled)

    def sample(name, tex_key, x, y):
        s = lib.expr(mat, unreal.MaterialExpressionTextureSampleParameter2D, x, y)
        s.set_editor_property("parameter_name", name)
        s.set_editor_property("group", "Surface")
        asset = lib.asset_path(TEX_DIR, tex_key)
        tex = unreal.load_asset(asset)
        if tex is not None:
            s.set_editor_property("texture", tex)
        else:
            report["warnings"].append(
                f"{name}: texture asset missing at {asset}")
        lib.connect(uv_scaled, "", s, "Coordinates")
        return s

    # NOTE: T_Gouache_BrushEdge is deliberately NOT sampled any more. The wet
    # edge is derived from the band gradient below, because a UV-tiled field
    # cannot follow the form. The asset is still generated and imported (it is
    # referenced by nothing, but deleting it would churn the texture set and the
    # audit trail); sampling it here would create a dead node and fail the
    # reachability census, which is the point of that census.
    s_blotch = sample("T_Gouache_WashBlotch", "T_Gouache_WashBlotch",
                      -780, 1800)
    s_gran = sample("T_Gouache_Granulation", "T_Gouache_Granulation", -780, 1960)
    s_tooth = sample("T_Gouache_PaperGrain", "T_Gouache_PaperGrain", -780, 2280)

    # ---------------- terminator -> two hard thresholds ----------------
    key_n = lib.expr(mat, unreal.MaterialExpressionNormalize, -1200, 2480)
    L.unary(key_dir, key_n)
    nrm = lib.expr(mat, unreal.MaterialExpressionPixelNormalWS, -1200, 2600)
    ndotl = lib.expr(mat, unreal.MaterialExpressionDotProduct, -1000, 2540)
    lib.connect(nrm, "", ndotl, ["A", "a"])
    lib.connect(key_n, "", ndotl, ["B", "b"])
    lit = lib.expr(mat, unreal.MaterialExpressionSaturate, -820, 2540)
    L.unary(ndotl, lit)

    def threshold(edge_param, x, y):
        """One hard step. Min/Max straddle the threshold by BandSoftness, so
        Softness IS the edge width and 0.04 gives a near-binary transition."""
        lo = lib.expr(mat, unreal.MaterialExpressionSubtract, -700, y)
        L.binary(edge_param, b_soft, lo)
        hi = lib.expr(mat, unreal.MaterialExpressionAdd, -700, y + 90)
        L.binary(edge_param, b_soft, hi)
        ss = lib.expr(mat, unreal.MaterialExpressionSmoothStep, x, y)
        lib.connect(lo, "", ss, ["Min", "Minimum", "min"])
        lib.connect(hi, "", ss, ["Max", "Maximum", "max"])
        lib.connect(lit, "", ss, ["Value", "Input", ""])
        return ss

    t1 = threshold(b_shadow, -520, 2400)
    t2 = threshold(b_light, -520, 2640)

    # band01: the combined wash field, 0 (all shadow) -> 1 (all lit).
    # t1 and t2 are already hard 0/1 steps whose transitions ARE the two wash
    # boundaries, so their sum is a single scalar that changes only at a
    # boundary. Halving keeps it in 0..1. This is the input to the wet-edge
    # gradient below and the reason the edge follows the form: it is a
    # derivative of the wash itself, not a stamped texture.
    band_sum = lib.expr(mat, unreal.MaterialExpressionAdd, -340, 2520)
    lib.connect(t1, "", band_sum, ["A", "a"])
    lib.connect(t2, "", band_sum, ["B", "b"])
    band_half = lib.expr(mat, unreal.MaterialExpressionConstant, -340, 2620)
    band_half.set_editor_property("r", 0.5)
    band01 = lib.expr(mat, unreal.MaterialExpressionMultiply, -160, 2570)
    L.binary(band_sum, band_half, band01)

    # The band INDEX is deliberately never built. Two hard steps feeding two
    # lerps produce three flat washes directly; an explicit 0/1/2 sum node would
    # sit in the graph driving nothing.

    # ---------------- the wash: three flat bands ----------------
    c_shadow = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate, -140, 2400)
    L.ternary(base, ink, shadow_mix, c_shadow)
    c_mid = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate, 40, 2400)
    L.ternary(c_shadow, base, t1, c_mid)
    c_lit = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate, 220, 2400)
    L.ternary(c_mid, high, t2, c_lit)

    # ---------------- granulation: pigment pools ----------------
    # Multiply toward a darker value, NOT a lerp toward InkColor: a lerp to one
    # dark colour drains the hue out of every pool and reads as dirt.
    g_amt = lib.expr(mat, unreal.MaterialExpressionMultiply, -340, 1960)
    lib.connect(s_gran, "R", g_amt, ["A", "a"])
    lib.connect(gran, "", g_amt, ["B", "b"])
    g_dark = lib.expr(mat, unreal.MaterialExpressionMultiply, -140, 1960)
    L.binary(c_lit, gran_dark, g_dark)
    c_gran = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate, 60, 1960)
    L.ternary(c_lit, g_dark, g_amt, c_gran)

    # ---------------- wet edge: DERIVED FROM THE BAND BOUNDARY ----------------
    # REBUILT. This was previously a straight lerp of a sampled 2D texture
    # (T_Gouache_BrushEdge) toward InkColor, which was wrong in a way no
    # parameter sweep could rescue: a UV-tiled field stamps the same streaks
    # across flat and curved surfaces alike, so the "wet edge" bore no relation
    # to the form. Wet edge is pigment gathering at the BOUNDARY OF A WASH, so
    # it has to be a function of where the wash changes, not of UV position.
    #
    # The band field `band01` is 0 in shadow, 1 in lit, and its two thresholds
    # are exactly the wash boundaries. So the gradient of `band01` IS the edge
    # detector: it is large only where a wash meets its neighbour, and zero
    # everywhere else - including inside a single flat wash, which is correct.
    #
    # Implementation: scene-texture derivatives (ddx/ddy) of the band field give
    # the true screen-space gradient in one node each, and Dot-ing them yields a
    # scalar edge magnitude. EdgeWidth then scales how much of that magnitude
    # counts as "the edge", so intensity and width are separate controls,
    # matching Flair's production model where "a wider edge darkening will
    # require an increase in intensity, as well".
    ddx = lib.expr(mat, unreal.MaterialExpressionDDX, -340, 2260)
    lib.connect(band01, "", ddx, ["Value", "Input", ""])
    ddy = lib.expr(mat, unreal.MaterialExpressionDDY, -340, 2380)
    lib.connect(band01, "", ddy, ["Value", "Input", ""])
    # The gradient magnitude. Dot of the two derivative components is literally
    # ddx^2 + ddy^2, which is already non-negative, so this IS a scalar
    # magnitude. It is a squared magnitude rather than a true length (no Sqrt),
    # which is harmless here because GouacheEdgeReference absorbs the scale and
    # the result is saturated anyway - it only has to be monotonic in "how fast
    # is the wash changing", and squared magnitude is.
    grad = lib.expr(mat, unreal.MaterialExpressionDotProduct, -160, 2320)
    lib.connect(ddx, "", grad, ["A", "a"])
    lib.connect(ddy, "", grad, ["B", "b"])
    grad_abs = lib.expr(mat, unreal.MaterialExpressionAbs, 20, 2320)
    L.unary(grad, grad_abs)

    # EdgeWidth as a multiplier on the gradient, so a wider edge captures more
    # of the falloff rather than smearing a fixed-width blur.
    e_wide = lib.expr(mat, unreal.MaterialExpressionMultiply, 200, 2320)
    lib.connect(grad_abs, "", e_wide, ["A", "a"])
    lib.connect(edge_width, "", e_wide, ["B", "b"])

    # The terminator's own slope varies with surface curvature, so the raw
    # gradient magnitude is not a usable 0..1 edge mask. Normalise it: the
    # terminator on a unit-sphere reference is the worst case the band field
    # can produce, so anything at or above that is a full-strength edge.
    e_norm = lib.expr(mat, unreal.MaterialExpressionDivide, 380, 2320)
    lib.connect(e_wide, "", e_norm, ["A", "a"])
    lib.connect(edge_ref, "", e_norm, ["B", "b"])
    e_sat = lib.expr(mat, unreal.MaterialExpressionSaturate, 540, 2320)
    L.unary(e_norm, e_sat)

    e_amt = lib.expr(mat, unreal.MaterialExpressionMultiply, 700, 2320)
    lib.connect(e_sat, "", e_amt, ["A", "a"])
    lib.connect(edge, "", e_amt, ["B", "b"])
    c_edge = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate, 860, 2320)
    L.ternary(c_gran, ink, e_amt, c_edge)

    # ---------------- wash blotch ----------------
    # The field's mean is ~0.56, so multiply by 2 to recentre it on 1.0 -
    # otherwise every wash is uniformly darkened by the blotch layer.
    two = lib.expr(mat, unreal.MaterialExpressionConstant, -520, 1800)
    two.set_editor_property("r", 2.0)
    b_amt = lib.expr(mat, unreal.MaterialExpressionMultiply, -340, 1800)
    lib.connect(s_blotch, "R", b_amt, ["A", "a"])
    lib.connect(two, "", b_amt, ["B", "b"])
    b_col = lib.expr(mat, unreal.MaterialExpressionMultiply, 60, 1800)
    L.binary(c_edge, b_amt, b_col)
    c_blotch = lib.expr(mat, unreal.MaterialExpressionLinearInterpolate, 240, 1800)
    L.ternary(c_edge, b_col, blotch, c_blotch)

    # ---------------- tooth drives ROUGHNESS, not albedo ----------------
    # RECENTRED. This was `roughness + (tooth * amount) - (amount * 0.5)`, i.e.
    # a 0.5-centred tooth added to a 0.92 base: the negative half moved roughness
    # to 0.87..0.92 but the positive half ran 0.92..1.02, and the following
    # Saturate clipped every value above 1.0 flat. Half the tooth signal was
    # therefore discarded, and the clipping also means GouacheRoughness above
    # ~0.95 produces NO positive tooth at all - a silent dead control.
    # Subtract 0.5 from the tooth FIRST, then add: the offset is now symmetric
    # about zero and the whole signal survives.
    t_amt = lib.expr(mat, unreal.MaterialExpressionMultiply, -340, 2280)
    lib.connect(s_tooth, "R", t_amt, ["A", "a"])
    lib.connect(tooth_amt, "", t_amt, ["B", "b"])
    half = lib.expr(mat, unreal.MaterialExpressionConstant, -520, 2280)
    half.set_editor_property("r", 0.5)
    t_off = lib.expr(mat, unreal.MaterialExpressionSubtract, -140, 2280)
    L.binary(t_amt, half, t_off)
    rough_add = lib.expr(mat, unreal.MaterialExpressionAdd, 60, 2340)
    L.binary(roughness, t_off, rough_add)
    rough_clamped = lib.expr(mat, unreal.MaterialExpressionSaturate, 240, 2340)
    L.unary(rough_add, rough_clamped)

    # ---------------- Substrate Toon BSDF ----------------
    # Same closure as the toon master. In UE 5.8 the node is
    # MaterialExpressionSubstrateToonBSDF and its output goes to
    # MP_FRONT_MATERIAL - the legacy lit outputs are deliberately NOT wired,
    # because Substrate owns the surface response once FrontMaterial is
    # connected.
    toon = lib.expr(mat, unreal.MaterialExpressionSubstrateToonBSDF, 620, 2200)
    lib.connect(c_blotch, "", toon, ["BaseColor", "Base Color"])
    lib.connect(rough_clamped, "", toon, ["Roughness"])
    lib.connect(specular, "", toon, ["Specular"])

    emis = lib.expr(mat, unreal.MaterialExpressionMultiply, 620, 1900)
    lib.connect(emis_c, "", emis, ["A", "a"])
    lib.connect(emis_i, "", emis, ["B", "b"])
    lib.connect(emis, "", toon, ["EmissiveColor", "Emissive Color"])

    lib.connect_property(toon, unreal.MaterialProperty.MP_FRONT_MATERIAL)

    try:
        unreal.MaterialEditingLibrary.recompile_material(mat)
    except Exception as exc:
        report["warnings"].append(f"recompile warning: {exc}")

    # ---------------- bind the Toon Profile LAST ----------------
    # Measured on this build: setting toon_profile on a freshly created material
    # BEFORE recompile reports success and reads back None one second later.
    # Binding after recompile and immediately before save removes that ordering
    # dependency. The node is RE-FETCHED rather than reusing the build handle.
    toon_node = None
    for node in unreal.MaterialEditingLibrary.get_material_expressions(mat) or []:
        if node is not None and type(node).__name__ == \
                "MaterialExpressionSubstrateToonBSDF":
            toon_node = node
            break

    profile = unreal.load_asset(lib.asset_path(lib.PROFILE_DIR, MASTER_PROFILE))
    report["profile_bound"] = None
    if toon_node is None:
        report["warnings"].append("no SubstrateToonBSDF node - profile not bound")
    elif profile is None:
        report["warnings"].append(
            f"profile {MASTER_PROFILE} not found - rendering on a default profile")
    else:
        # Only a READ-BACK proves this. set_editor_property returns True and
        # still binds nothing, which is how the spine shipped with 19 unused
        # TP_* assets before.
        for handle in (toon_node, toon):
            if handle is None:
                continue
            try:
                handle.set_editor_property("toon_profile", profile)
            except Exception as exc:
                report["warnings"].append(f"set toon_profile: {str(exc)[:80]}")
        for handle in (toon_node, toon):
            if handle is None:
                continue
            try:
                bound = handle.get_editor_property("toon_profile")
                if bound is not None:
                    report["profile_bound"] = bound.get_name()
                    break
            except Exception:
                continue
        if report["profile_bound"] is None:
            report["errors"].append(
                "toon_profile did not stick - wash will render on defaults")

    lib.save(mat)

    # ---------------- repo-convention verification ----------------
    # expected_calls=[] is CORRECT and deliberate: this master calls NO
    # material functions. It reuses the toon lane only through the shared
    # Substrate Toon BSDF closure and the TP_* profile - a stray MF_* call would
    # be an accidental dependency on the toon spine, not a feature.
    # min_expressions=50: the graph is ~54 nodes. The floor exists to catch the
    # zero-node false pass (a material reporting 0 calls is empty, not verified).
    try:
        v = lib.verify_material(NAME, expected_calls=[], min_expressions=50)
        report["verify_material"] = v
        if not v.get("ok"):
            report["errors"].append(f"verify_material failed: {v}")
    except Exception as exc:
        report["errors"].append(f"verify_material error: {str(exc)[:120]}")

    # ---------------- reachability census ----------------
    # A parameter node that reaches no BSDF pin is a control an artist can drag
    # with no effect - the exact failure that parked 19 scalars on the toon
    # master. graph_reachability walks BACKWARD from the sinks, which is the
    # only correct direction here: a forward BFS from inputs would count every
    # parameter and constant as an orphan, since they have no upstream by
    # definition. It returns (live, dead, outputs_wired, unused_inputs).
    try:
        nodes = unreal.MaterialEditingLibrary.get_material_expressions(mat) or []
        live, dead, outputs_wired, unused_inputs = lib.graph_reachability(
            mat, nodes, False)
        report["reachability"] = {"live": live, "dead": dead,
                                  "outputs_wired": outputs_wired}
        report["dead_nodes"] = dead
        # Any dead node is a control an artist can drag with no effect. On the
        # toon master that shipped as 19 "Parked" scalars nobody trusted. Zero
        # is the bar here: if a future edit adds a control without wiring it,
        # the build fails instead of quietly parking it.
        if dead:
            report["errors"].append(
                f"{dead} dead node(s) - a control reaches no BSDF pin")
    except Exception as exc:
        report["reachability"] = {"error": str(exc)[:160]}
        report["errors"].append(f"reachability census failed: {str(exc)[:120]}")

    report["ok"] = not report["errors"]
    report["wire_failures"] = sorted(set(wiring.failures))
    if wiring.failures:
        # A pin that refused a connection is a broken material, whatever
        # verify_material says. Surface it as a hard failure.
        report["errors"].append(
            f"{len(wiring.failures)} pin connection(s) failed: "
            f"{sorted(set(wiring.failures))}")
        report["ok"] = False

    # ---------------- prove the SAVED asset matches the built graph ----------------
    # Everything above describes the IN-MEMORY material. What matters is the
    # .uasset on disk, because that is what any later compile, cook or another
    # machine will read. A modal dialog during save (see the module docstring)
    # leaves the two out of sync, and every in-memory assertion still passes.
    # So reload the asset by path and re-run the checks against that.
    report["persisted"] = {}
    try:
        path = lib.asset_path(lib.MASTER_DIR, NAME)
        # A save on this project is NOT synchronous with the return of
        # save_loaded_asset: measured, the .uasset mtime landed ~40s AFTER the
        # builder finished, because UE's save path pumps a modal ("Overwrite
        # Existing Object") first. Checking immediately after the save therefore
        # reported "saved asset does not exist on disk" on a perfectly good
        # 37 KB file. Poll for it rather than trusting the instant.
        exists = False
        for attempt in range(8):
            if unreal.EditorAssetLibrary.does_asset_exist(path):
                exists = True
                break
            lib.log(f"persistence: not on disk yet (attempt {attempt + 1}/8)")
            try:
                unreal.SystemLibrary.delay(2.0)
            except Exception:
                break
        if not exists:
            report["errors"].append(
                "saved asset does not exist on disk after waiting - a modal is "
                "probably blocking the save; dismiss it and re-run")
        else:
            saved = unreal.EditorAssetLibrary.load_asset(path)
            report["persisted"]["loaded"] = saved is not None
            report["persisted"]["expression_count"] = lib.expression_count(saved)

            # toon_profile must survive the round trip, not just the build
            prof_name = None
            for n in unreal.MaterialEditingLibrary.get_material_expressions(saved) or []:
                if type(n).__name__ == "MaterialExpressionSubstrateToonBSDF":
                    p = n.get_editor_property("toon_profile")
                    prof_name = p.get_name() if p else None
                    break
            report["persisted"]["toon_profile"] = prof_name
            if prof_name != report.get("profile_bound"):
                report["errors"].append(
                    f"profile lost on save: built {report.get('profile_bound')}, "
                    f"reloaded {prof_name}")

            # texture parameters must still point at real assets after reload
            ntex = 0
            unassigned = []
            for e in unreal.MaterialEditingLibrary.get_material_expressions(saved) or []:
                if type(e).__name__ == "MaterialExpressionTextureSampleParameter2D":
                    ntex += 1
                    try:
                        if e.get_editor_property("texture") is None:
                            unassigned.append(
                                str(e.get_editor_property("parameter_name")))
                    except Exception:
                        pass
            report["persisted"]["texture_params"] = ntex
            report["persisted"]["unassigned_textures"] = unassigned
            if unassigned:
                report["errors"].append(
                    f"textures unassigned after reload: {unassigned}")

            if report["persisted"]["expression_count"] != report["reachability"].get(
                    "live"):
                report["warnings"].append(
                    "reloaded expression count differs from the built graph")
    except Exception as exc:
        report["errors"].append(f"persistence check failed: {str(exc)[:160]}")

    report["ok"] = not report["errors"]
    return report


def main(rebuild=True):
    report = build(rebuild=rebuild)
    try:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        AUDIT_COPY.parent.mkdir(parents=True, exist_ok=True)
        AUDIT_COPY.write_text(json.dumps(report, indent=2), encoding="utf-8")
    except Exception as exc:
        report["errors"].append(f"report write failed: {exc}")

    print("[GouacheBuild] " + json.dumps(
        {"ok": report["ok"], "errors": report["errors"],
         "warnings": report["warnings"],
         "profile_bound": report.get("profile_bound")}, indent=2))
    return report


if __name__ == "__main__":
    main()