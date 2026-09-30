"""Build Toon Profiles - UE 5.8's toon art-direction surface.

WHY import_text
---------------
`ToonProfile` exposes exactly ONE editor property (`settings`), and
`ToonProfileStruct` exposes none of its own: no dir() entries, empty
to_dict()/to_tuple(), and no settable fields. Probed 2026-09-30.

But `struct.export_text()` returns the complete struct in UE property-import
form, including the four diffuse ramp curves with their keys, and
`struct.import_text(s)` round-trips it. So profiles are authored by building
the text and importing it. Verified round-trip in build_toon_profiles.

Field surface, recovered from export_text on a default profile:
    DiffuseRamp                      4 ColorCurves (R,G,B,luminance) with keys
    DiffuseRampOffsetTexture        noise texture to break up the bands
    DiffuseRampOffsetStrength       0 default
    DiffuseRampOffsetSize           1 default
    SpecularRamp                    4 ColorCurves
    SpecularRampOffsetTexture/Strength/Size
    ShadowExtinctionCoefficient     10 default - shadow falloff
    ShadowHatchingPatternDistributionRamp
    ShadowHatchingPatternTexture    procedural hatch pattern
    ShadowHatchingPatternSize/Strength
    DiffuseIndirectScale            GI diffuse scale
    SpecularIndirectScale           GI specular scale
    SpecularIndirectRamp
    SpecularIndirectRampRepetition
    bDiffuseRampIncludeShadow       include shadow in the diffuse ramp

Default diffuse ramp is a 3-band step at 0.25 / 0.5 / 0.75 with near-vertical
transitions - that is the stock UE cel look and the basis for every profile here.
"""
from __future__ import annotations

import unreal

import spine_lib as lib

PROFILE_DIR = lib.PROFILE_DIR


def _keys(*pairs):
    """Build a ColorCurve Key list: pairs of (time, value)."""
    body = "()"
    for t, v in pairs:
        if v is None:
            body += f",(Time={t:.6f})"
        else:
            body += f",(Time={t:.6f},Value={v:.6f})"
    return body


def _step4(pairs):
    """A ColorCurve block: 4 identical channels (R,G,B + luminance)."""
    k = _keys(*pairs)
    ch = f"(Keys={k},DefaultValue=340282346638528859811704183484516925440.000000," \
         f"PreInfinityExtrap=RCCE_Constant,PostInfinityExtrap=RCCE_Constant)"
    return f"(ColorCurves[0]={ch},ColorCurves[1]={ch},ColorCurves[2]={ch}," \
           f"ColorCurves[3]=(Keys=,DefaultValue=340282346638528859811704183484516925440.000000," \
           f"PreInfinityExtrap=RCCE_Constant,PostInfinityExtrap=RCCE_Constant),ExternalCurve=None)"


def _scalar_curve(pairs):
    ch = _keys(*pairs)
    return (f"(EditorCurveData=(Keys={ch},"
            f"DefaultValue=340282346638528859811704183484516925440.000000,"
            f"PreInfinityExtrap=RCCE_Constant,PostInfinityExtrap=RCCE_Constant),"
            f"ExternalCurve=None)")


DEFAULT = "340282346638528859811704183484516925440.000000"

# The stock UE 3-band step: shadow below 0.25, mid to 0.5, light to 0.75.
THREE_BAND = [(0.25, None), (0.26, 0.25), (0.50, 0.25), (0.51, 0.50),
              (0.75, 0.50), (0.76, 0.75), (0.99, 0.75), (1.00, 1.00)]

# A hard two-tone split - maximum graphic read, the anime baseline.
TWO_BAND = [(0.48, None), (0.49, 0.35), (0.52, 0.35), (1.00, 1.00)]

# Soft painterly falloff - no hard terminator anywhere.
SOFT = [(0.00, 0.18), (0.35, 0.45), (0.70, 0.80), (1.00, 1.00)]

# Warm bias: shadows drift toward the accent, highlights stay neutral.
WARM = [(0.20, 0.22), (0.30, 0.38), (0.55, 0.52), (0.80, 0.82), (1.00, 1.00)]


def _profile_text(diffuse, specular, extinction=10.0,
                  diffuse_indirect=1.0, specular_indirect=1.0,
                  hatch_strength=1.0, include_shadow=False):
    return (
        f"(DiffuseRamp={_step4(diffuse)},"
        f"DiffuseRampOffsetTexture=None,"
        f"DiffuseRampOffsetStrength=0.000000,"
        f"DiffuseRampOffsetSize=1.000000,"
        f"SpecularRamp={_step4(specular)},"
        f"SpecularRampOffsetTexture=None,"
        f"SpecularRampOffsetStrength=0.000000,"
        f"SpecularRampOffsetSize=1.000000,"
        f"ShadowExtinctionCoefficient={extinction:.6f},"
        f"ShadowHatchingPatternDistributionRamp={_scalar_curve([(1.00, 1.00)])},"
        f"ShadowHatchingPatternTexture=None,"
        f"ShadowHatchingPatternSize=1.000000,"
        f"ShadowHatchingPatternStrength={hatch_strength:.6f},"
        f"DiffuseIndirectScale={diffuse_indirect:.6f},"
        f"SpecularIndirectScale={specular_indirect:.6f},"
        f"SpecularIndirectRamp={_scalar_curve([(1.00, 1.00)])},"
        f"SpecularIndirectRampRepetition=0.000000,"
        f"bDiffuseRampIncludeShadow={'true' if include_shadow else 'false'})"
    )


# name -> (diffuse curve, specular curve, extinction, diffuse GI, spec GI, hatching, note)
PROFILES = {
    "TP_Default": (
        THREE_BAND, [(0.50, None), (0.51, 1.00), (1.00, 1.00)],
        10.0, 1.0, 1.0, 1.0,
        "Stock UE three-band cel. The baseline every other profile departs from.",
    ),
    "TP_TwoTone": (
        TWO_BAND, [(0.50, None), (0.51, 1.00), (1.00, 1.00)],
        16.0, 1.0, 1.0, 1.0,
        "Hard two-tone split at 0.5. Maximum graphic read for characters.",
    ),
    "TP_SoftPainterly": (
        SOFT, [(0.60, None), (0.70, 0.60), (1.00, 1.00)],
        4.0, 1.15, 0.6, 0.0,
        "No hard terminator anywhere. Painted/illustration read, background art.",
    ),
    "TP_Warm": (
        WARM, [(0.55, None), (0.65, 0.75), (1.00, 1.00)],
        8.0, 1.1, 0.8, 0.0,
        "Warm-biased bands: shadows sit low, highlights stay neutral.",
    ),
    "TP_Cool": (
        [(0.20, 0.20), (0.30, 0.34), (0.55, 0.50), (0.80, 0.80), (1.00, 1.00)],
        [(0.55, None), (0.65, 0.75), (1.00, 1.00)],
        8.0, 0.9, 0.8, 0.0,
        "Cool-biased bands for moonlit/underwater reads.",
    ),
    "TP_Hero": (
        [(0.30, 0.28), (0.34, 0.44), (0.58, 0.55), (0.82, 0.84), (1.00, 1.00)],
        [(0.58, None), (0.66, 0.55), (1.00, 0.9)],
        6.0, 0.85, 1.25, 0.0,
        "Lead character. Moderate contrast, specular lifted for hero highlights.",
    ),
    "TP_Environment": (
        SOFT, [(0.70, None), (0.80, 0.35), (1.00, 0.4)],
        3.0, 1.3, 0.5, 0.0,
        "Background sets. Low contrast, high GI, minimal specular so props recede.",
    ),
    "TP_Foliage": (
        [(0.22, 0.30), (0.32, 0.46), (0.60, 0.60), (0.85, 0.86), (1.00, 1.00)],
        [(0.65, None), (0.78, 0.25), (1.00, 0.3)],
        5.0, 1.2, 0.4, 0.0,
        "Leaves and canopy. Lifted shadow floor so foliage never goes black.",
    ),
    "TP_Gold": (
        [(0.35, 0.42), (0.42, 0.60), (0.62, 0.70), (0.85, 0.90), (1.00, 1.0)],
        [(0.45, None), (0.52, 1.0), (1.00, 1.0)],
        5.0, 0.9, 1.5, 0.0,
        "Metallic trim. Tight low-threshold specular for a hard metal glint.",
    ),
    "TP_Stone": (
        SOFT, [(0.75, None), (0.85, 0.25), (1.00, 0.3)],
        3.0, 1.25, 0.45, 0.0,
        "Rough architecture. Almost no specular response.",
    ),
    "TP_Hatched": (
        [(0.35, 0.25), (0.45, 0.45), (0.65, 0.70), (1.00, 1.0)],
        [(0.60, None), (0.70, 0.4), (1.00, 0.5)],
        12.0, 0.8, 0.7, 1.0,
        "Strong shadow extinction, hatching strength at 1.0. Assign a hatch texture.",
    ),
}


def build_profile(name):
    """Create one ToonProfile and import its authored settings."""
    diffuse, specular, ext, dgi, sgi, hatch, note = PROFILES[name]

    tools = unreal.AssetToolsHelpers.get_asset_tools()
    path = lib.asset_path(PROFILE_DIR, name)
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        tp = unreal.load_asset(path)
    else:
        lib.ensure_dir(PROFILE_DIR)
        tp = tools.create_asset(name, PROFILE_DIR, unreal.ToonProfile,
                                unreal.ToonProfileFactory())
    if tp is None:
        raise RuntimeError(f"could not create ToonProfile {name}")

    settings = tp.get_editor_property("settings")
    text = _profile_text(diffuse, specular, ext, dgi, sgi, hatch)
    if not settings.import_text(text):
        raise RuntimeError(f"import_text failed for {name}")

    tp.set_editor_property("settings", settings)
    lib.try_set(tp, "description", note)
    lib.save(tp)
    return tp


def verify_profile(name):
    """Read settings back and confirm the import actually landed."""
    path = lib.asset_path(PROFILE_DIR, name)
    tp = unreal.load_asset(path)
    result = {"name": name, "loads": tp is not None, "ok": False}
    if tp is None:
        lib.log(f"VERIFY FAIL {name}: does not load")
        return result

    settings = tp.get_editor_property("settings")
    text = settings.export_text()
    result["chars"] = len(text)
    result["has_diffuse_ramp"] = "DiffuseRamp=" in text
    result["has_specular_ramp"] = "SpecularRamp=" in text
    result["has_hatching"] = "ShadowHatchingPatternStrength=" in text
    result["non_trivial"] = len(text) > 100 and result["has_diffuse_ramp"]

    # a default profile also exports >100 chars, so compare against stock
    # by checking our authored marker: the extinction coefficient we asked for
    expected_ext = f"ShadowExtinctionCoefficient={PROFILES[name][2]:.6f}"
    result["extinction_applied"] = expected_ext in text

    result["ok"] = (result["has_diffuse_ramp"] and result["has_specular_ramp"]
                    and result["extinction_applied"])
    lib.log(f"VERIFY {name}: ok={result['ok']} chars={result['chars']} "
            f"ext_applied={result['extinction_applied']}")
    return result


def build(rebuild=True):
    lib.log(f"=== Toon Profiles ({len(PROFILES)}) ===")
    made = []
    for name in PROFILES:
        try:
            made.append(build_profile(name).get_name())
        except Exception as exc:
            lib.log(f"ERROR {name}: {exc}")
    return made
