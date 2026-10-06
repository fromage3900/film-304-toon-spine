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


def _texture_path(asset_name):
    """Object reference for import_text, or None when the slot stays empty.

    import_text takes UE property text, where an object property is
    Class'/Game/.../Name.Name'. PROBED 2026-10-02 that this form round-trips;
    a bare path does not bind on import, which would leave the profile
    asserting clean while the hatching texture silently stayed None.
    """
    if not asset_name:
        return None
    return f"Texture2D'/Game/Materials/Textures/{asset_name}.{asset_name}'"


def _profile_text(diffuse, specular, extinction=10.0,
                  diffuse_indirect=1.0, specular_indirect=1.0,
                  hatch_strength=1.0, include_shadow=False,
                  hatch_texture=None, offset_texture=None,
                  offset_strength=0.0):
    hatch = _texture_path(hatch_texture) or "None"
    offset = _texture_path(offset_texture) or "None"
    return (
        f"(DiffuseRamp={_step4(diffuse)},"
        f"DiffuseRampOffsetTexture={offset},"
        f"DiffuseRampOffsetStrength={offset_strength:.6f},"
        f"DiffuseRampOffsetSize=1.000000,"
        f"SpecularRamp={_step4(specular)},"
        f"SpecularRampOffsetTexture=None,"
        f"SpecularRampOffsetStrength=0.000000,"
        f"SpecularRampOffsetSize=1.000000,"
        f"ShadowExtinctionCoefficient={extinction:.6f},"
        f"ShadowHatchingPatternDistributionRamp={_scalar_curve([(1.00, 1.00)])},"
        f"ShadowHatchingPatternTexture={hatch},"
        f"ShadowHatchingPatternSize=1.000000,"
        f"ShadowHatchingPatternStrength={hatch_strength:.6f},"
        f"DiffuseIndirectScale={diffuse_indirect:.6f},"
        f"SpecularIndirectScale={specular_indirect:.6f},"
        f"SpecularIndirectRamp={_scalar_curve([(1.00, 1.00)])},"
        f"SpecularIndirectRampRepetition=0.000000,"
        f"bDiffuseRampIncludeShadow={'true' if include_shadow else 'false'})"
    )


def _unpack(entry):
    """Split a PROFILES row into 7 legacy fields + optional extras dict.

    Backwards compatible on purpose: the 11 pre-existing rows are 7-tuples and
    must keep working untouched, while new rows may append an 8th element
    holding {"hatch_texture": ..., "offset_texture": ...}.
    """
    diffuse, specular, ext, dgi, sgi, hatch, note = entry[:7]
    extras = entry[7] if len(entry) > 7 else {}
    return diffuse, specular, ext, dgi, sgi, hatch, note, extras or {}


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
    "TP_Water": (
        [(0.30, 0.22), (0.50, 0.48), (0.72, 0.75), (1.00, 1.00)],
        [(0.55, None), (0.62, 0.35), (1.00, 0.50)],
        4.0, 1.10, 0.80, 0.0,
        "Stylized water surface. Tight crest specular, lifted shadow floor - "
        "the flow comes from the master's ripple normal, not this profile.",
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

    # ---------------------------------------------------------------- office
    # Added 2026-10-02 for the 304 office film. These 8 map 1:1 onto the eight
    # interior surfaces recorded MISSING in Melodia's office brief
    # (OFFICE_PROPS_WAVE0_WAVE1_2026-10-01.md, Wave 3: carpet, laminate,
    # drop ceiling, troffer, powder coat, screen emissive, polypropylene,
    # whiteboard gloss) - so every row here answers to a named gap.
    #
    # SHADOW FLOOR RULE (Infinity Nikki baroque rule, carried over from the
    # Melodia lane): no ramp reaches 0. The darkest stop is lifted well above
    # black because a toon shadow that hits zero reads as a hole in the film.
    # Note the colour itself lives in the instance's BaseTint - ToonProfile
    # ramps here are scalar-valued, so hue is authored per material, not here.

    "TP_Office_Carpet": (
        [(0.00, 0.30), (0.35, 0.42), (0.70, 0.72), (1.00, 1.00)],
        [(0.80, None), (0.90, 0.15), (1.00, 0.18)],
        3.0, 0.90, 0.25, 0.35,
        "Carpet tile. Very soft, almost no specular; lifted floor so pile never "
        "goes black. Single-direction hatch breaks the shadow without reading "
        "as line art.",
        {"hatch_texture": "T_Hatch_Diagonal"},
    ),
    "TP_Office_Laminate": (
        [(0.00, 0.28), (0.30, 0.45), (0.65, 0.75), (1.00, 1.00)],
        [(0.55, None), (0.68, 0.35), (1.00, 0.45)],
        4.0, 0.85, 0.45, 0.0,
        "Desk laminate. Mid sheen with a narrow band - the horizontal surfaces "
        "that catch the window.",
    ),
    "TP_Office_DropCeiling": (
        [(0.00, 0.34), (0.40, 0.52), (0.75, 0.80), (1.00, 1.00)],
        [(0.88, None), (0.95, 0.12), (1.00, 0.14)],
        2.5, 1.00, 0.30, 0.0,
        "Acoustic drop-ceiling tile. Flattest ramp in the set: troffers light it "
        "evenly, so band structure would be a lie. Noise offset stops the big "
        "flat plane from reading as plastic.",
        {"offset_texture": "T_Noise_White", "offset_strength": 0.08},
    ),
    "TP_Office_Troffer": (
        [(0.00, 0.55), (0.35, 0.75), (0.70, 0.92), (1.00, 1.00)],
        [(0.92, None), (0.97, 0.10), (1.00, 0.12)],
        1.5, 1.30, 0.60, 0.0,
        "Recessed light panel. High floor and very low extinction so the panel "
        "stays lit; this is the surface the EmissiveColor lane feeds.",
    ),
    "TP_Office_PowderCoat": (
        [(0.00, 0.22), (0.42, 0.50), (0.55, 0.85), (1.00, 1.00)],
        [(0.60, None), (0.70, 1.00), (1.00, 1.00)],
        8.0, 0.70, 0.80, 0.40,
        "Powder-coated steel: desk frames, legs, lockers. Hard two-tone with a "
        "tight glint; cross-hatch holds the shadow so the metal stays matte.",
        {"hatch_texture": "T_Hatch_Cross"},
    ),
    "TP_Office_Screen": (
        [(0.00, 0.10), (0.30, 0.22), (0.60, 0.60), (1.00, 1.00)],
        [(0.35, None), (0.45, 0.90), (1.00, 1.00)],
        6.0, 0.50, 0.90, 0.0,
        "Monitor / screen emissive. Deepest floor in the set - it must read as "
        "an emitter, and GI scale stays low so it does not light the room.",
    ),
    "TP_Office_Polypropylene": (
        [(0.00, 0.26), (0.38, 0.48), (0.72, 0.80), (1.00, 1.00)],
        [(0.62, None), (0.74, 0.50), (1.00, 0.60)],
        4.5, 0.80, 0.50, 0.0,
        "Moulded polypropylene: task chairs, monitor arms, bins. Soft mid "
        "specular, no hard terminator.",
    ),
    "TP_Office_Whiteboard": (
        [(0.00, 0.40), (0.25, 0.62), (0.50, 0.88), (1.00, 1.00)],
        [(0.75, None), (0.83, 0.60), (1.00, 0.70)],
        5.0, 1.00, 0.70, 0.0,
        "Whiteboard gloss. Light, crisp and reflective; the brightest floor in "
        "the set so marker ink and the room's key both read.",
    ),

    # ------------------------------------------------------- film / character
    # Added 2026-10-03. TP_Melusina is the film's CANONICAL character profile
    # and was the one named gap: the shot manifest declares
    #   framing_standard.shading_pipeline.toon_profile = "TP_Melusina"
    #   framing_standard.shading_pipeline.shadow_tint_hex = "#352D40"
    # Humber_FinalYear_Prep/GROUP_STAGING_GUIDE.md section 3 mandates it for
    # character shading, the slot-09 material brief requires it, and
    # Tools/dogfood_toon_spine.py asserts it -- while no such asset existed in
    # either repo. Authored here to close that gap.
    #
    # Hue note, same as the office block: ToonProfile ramps are SCALAR-valued
    # (_step4 writes one Value into all three colour curves), so #352D40 cannot
    # live here as a colour. This profile carries the warm-violet *value*
    # structure; the hue itself belongs in the instance BaseTint.

    "TP_Melusina": (
        # Halftone transition, not hard banding - the guide asks for "halftone
        # transitions without banding", so the stops are short but not instant.
        # Floor lifted well off black: #352D40 is a value, never 0.
        [(0.00, 0.24), (0.26, 0.34), (0.42, 0.50), (0.64, 0.66), (0.85, 0.87), (1.00, 1.00)],
        # Specular lifted for the close-ups (SH050 macro_emotion) to hold.
        [(0.55, None), (0.64, 0.62), (1.00, 0.95)],
        6.0, 0.90, 1.20, 0.55,
        "CANONICAL hero character profile. Warm-violet shadow family (#352D40), "
        "halftone transition rather than hard banding, shadow floor lifted off "
        "black. Specular lifted so facial close-ups hold. Binds the manifest's "
        "declared hatching_pattern (T_HatchPattern).",
        {"hatch_texture": "T_HatchPattern"},
    ),
    "TP_Character": (
        # Sibling to TP_Melusina so a second/background character does not
        # inherit hero contrast and blow out against the hero in the same frame.
        [(0.00, 0.30), (0.34, 0.46), (0.68, 0.72), (1.00, 1.00)],
        [(0.68, None), (0.78, 0.35), (1.00, 0.40)],
        5.0, 1.00, 0.70, 0.30,
        "Secondary / background characters. Lower contrast and much less "
        "specular than TP_Melusina so background cast recedes behind the hero "
        "instead of competing with them.",
        {"hatch_texture": "T_Hatch_Diagonal"},
    ),
    "TP_Landscape": (
        # Ground planes. Macro variation lives in the master (two static noise
        # reads), so the profile only needs to hold the band structure steady
        # across that variation - hence a tight 4-key ramp and low extinction
        # (soft terminator: the ground reads as one mass, not a hard split).
        [(0.25, 0.26), (0.50, 0.48), (0.75, 0.76), (1.00, 1.00)],
        [(0.70, None), (0.80, 0.30), (1.00, 0.40)],
        3.5, 1.20, 0.40, 0.0,
        "Ground / terrain. Low-contrast bands with a soft terminator so macro "
        "tint variation (master-driven) carries the read instead of the "
        "terminator, minimal specular - matches TP_Environment's recession "
        "rule but with tighter band steps for closer ground contact shots.",
    ),
    "TP_Face": (
        # Deliberately NARROW band spread around the terminator (keys crowded
        # at 0.44-0.46): the face shadow must hold as a shape, not sweep
        # across the cheek when the head turns. Specular lifted (close-up
        # skin sheen) but extinction low so the terminator stays soft-edged -
        # the anime trick this profile exists to encode.
        [(0.35, 0.32), (0.44, 0.44), (0.46, 0.60), (1.00, 1.00)],
        [(0.60, None), (0.70, 0.55), (1.00, 0.85)],
        4.0, 0.95, 1.15, 0.0,
        "Skin / face. Tight shadow-band keys so the terminator holds its "
        "shape while the head turns, warm-lifted specular for close-up skin "
        "read. The authored FaceShadowTint lerp in M_Master_Toon_Face is a "
        "separate, grade-level layer above this band structure - this "
        "profile owns the bands, the master owns the painted shadow.",
    ),
    "TP_Hair": (
        # Longest diff ramp in the set (5 keys): hair is a vertical gradient
        # surface, so the band structure has more room to step without
        # reading as posterization on a curved mass. Highest specular in the
        # set (sgi 1.4) with LOW extinction - the sheen streak is master-
        # authored (lerp toward AccentTint), this profile just keeps the
        # highlight broad and soft beneath it.
        [(0.38, 0.30), (0.52, 0.52), (0.66, 0.72), (0.84, 0.90), (1.00, 1.00)],
        [(0.45, None), (0.55, 0.70), (1.00, 1.00)],
        5.0, 0.80, 1.40, 0.0,
        "Hair. Broad soft highlight under the master's root->tip gradient "
        "and sheen lerp; enough band steps to follow the gradient without "
        "hard posterization on curved strands.",
    ),
    "TP_Glass": (
        # Earliest terminator in the set (0.40): glass goes to its lit side
        # fast so the interior stays clear-ish and the silhouette edge (the
        # master's fresnel opacity/glow) dominates the read. Lowest specular
        # extinction (0.35) + highest specular strength - a hard bright rim
        # highlight is the whole point of glass.
        [(0.40, 0.45), (0.60, 0.66), (0.82, 0.86), (1.00, 1.00)],
        [(0.35, None), (0.45, 0.85), (1.00, 1.00)],
        2.0, 0.90, 1.50, 0.0,
        "Glass / crystal. Early soft terminator so the interior reads "
        "transparent under the master's fresnel opacity, with the brightest "
        "specular in the set for the hard window/bottle glint.",
    ),

    # --------------------------------------------- office spider (2026-10-06)
    # Five surfaces the storyboard needs that no profile describes: paper,
    # cardboard, dark steel, spider carapace, spider eyes. All obey the
    # shadow-floor rule (no ramp reaches 0). BINDING NOTE, read before
    # assuming these shade anything: a profile reaches a pixel only through
    # the MASTER that binds it (measured 2026-10-02 - instances cannot
    # carry one). Universal binds TP_Default and Character binds
    # TP_Melusina, so until a family master binds one of these, the
    # MI_OfficeSpider_* instances carry the look in their scalars
    # (BaseTint/roughness/rim/lift) on TP_Default's bands. These rows are
    # the authored art-direction record - same status the 8 office
    # profiles shipped in - and become load-bearing the day a master
    # binds them. Do not "fix" this by hand-editing an instance.
    "TP_Paper": (
        [(0.00, 0.55), (0.40, 0.78), (0.75, 0.92), (1.00, 1.00)],
        [(0.90, None), (0.97, 0.10), (1.00, 0.12)],
        2.0, 1.00, 0.25, 0.0,
        "Paper: desk sheets, calendar, cat poster. Brightest matte floor in "
        "the set, near-zero specular; pair with bMatteFinish on the "
        "instance for dead-matte roughness 1.0.",
    ),
    "TP_Cardboard": (
        [(0.00, 0.32), (0.38, 0.52), (0.72, 0.78), (1.00, 1.00)],
        [(0.70, None), (0.82, 0.25), (1.00, 0.30)],
        3.5, 1.00, 0.40, 0.0,
        "Cardboard: the donut box. Kraft mid floor, soft spec; noise offset "
        "gives the corrugation tooth so the flat panels do not read plastic.",
        {"offset_texture": "T_Noise_White", "offset_strength": 0.06},
    ),
    "TP_SteelDark": (
        [(0.00, 0.18), (0.42, 0.48), (0.58, 0.85), (1.00, 1.00)],
        [(0.55, None), (0.65, 1.00), (1.00, 1.00)],
        9.0, 0.65, 0.90, 0.40,
        "Dark steel: coffee machine body, chair legs. Hard near-two-tone "
        "with a tight glint, cross-hatch holds the shadow; floor lifted "
        "off black so the machine separates from the p12-2 corner.",
        {"hatch_texture": "T_Hatch_Cross"},
    ),
    "TP_Spider_Body": (
        [(0.00, 0.16), (0.35, 0.38), (0.62, 0.68), (1.00, 1.00)],
        [(0.50, None), (0.60, 0.80), (1.00, 0.90)],
        7.0, 0.60, 1.10, 0.50,
        "Spider carapace. Deep-but-lifted floor, glossy carapace glint, "
        "diagonal hatch for leg-segment read; designed to hold under "
        "RimStrength + ShadowLift on the instance, not to carry the dark "
        "corner alone.",
        {"hatch_texture": "T_Hatch_Diagonal"},
    ),
    "TP_Spider_Eye": (
        [(0.00, 0.08), (0.30, 0.20), (0.60, 0.55), (1.00, 1.00)],
        [(0.30, None), (0.40, 1.00), (1.00, 1.00)],
        8.0, 0.40, 1.30, 0.0,
        "Spider eyes. Deepest floor in the set - the read comes from the "
        "instance's red EmissiveColor + FlickerDepth throb, with a hard "
        "wet glint on top.",
    ),
}


def build_profile(name):
    """Create one ToonProfile and import its authored settings."""
    diffuse, specular, ext, dgi, sgi, hatch, note, extras = _unpack(PROFILES[name])

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
    text = _profile_text(diffuse, specular, ext, dgi, sgi, hatch,
                         hatch_texture=extras.get("hatch_texture"),
                         offset_texture=extras.get("offset_texture"),
                         offset_strength=extras.get("offset_strength", 0.0))
    if not settings.import_text(text):
        raise RuntimeError(f"import_text failed for {name}")

    tp.set_editor_property("settings", settings)
    lib.try_set(tp, "description", note)
    lib.save(tp)
    return tp


def _field_value(text: str, field: str):
    """Read one top-level field's value out of an exported property string.

    Values may themselves contain commas, brackets and quotes (an object
    reference does), so the value runs to the next `Name=` at nesting depth 0
    rather than to the next comma.
    """
    marker = f"{field}="
    start = text.find(marker)
    if start == -1:
        return None
    i = start + len(marker)
    depth, out = 0, []
    while i < len(text):
        ch = text[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            if depth == 0:
                break
            depth -= 1
        elif ch == "," and depth == 0:
            break
        out.append(ch)
        i += 1
    return "".join(out).strip()


def verify_profile(name):
    """Read settings back and confirm the import actually landed."""
    path = lib.asset_path(PROFILE_DIR, name)
    tp = unreal.load_asset(path)
    _, _, _, _, _, _, _, extras = _unpack(PROFILES[name])
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

    # A row that ASKS for a hatching/offset texture must prove it bound.
    # FIX 2026-10-02: the first version of this check compared against an
    # invented exact string ("...=Texture2D'/Game/...'" with no quotes and no
    # /Script/Engine prefix) and failed 3 healthy profiles. Probing
    # (Saved/Audit/toon_texture_ref_probe.json) showed UE 5.8 exports object
    # properties as a QUOTED, fully-qualified form:
    #   ShadowHatchingPatternTexture="/Script/Engine.Texture2D'/Game/.../T.X'"
    # so the field was bound all along and the ASSERTION was wrong. Check the
    # field's own value instead: it must not be None and must name the asset.
    result["hatch_texture_applied"] = True
    for field, key in (("ShadowHatchingPatternTexture", "hatch_texture"),
                       ("DiffuseRampOffsetTexture", "offset_texture")):
        want = extras.get(key)
        if not want:
            continue
        value = _field_value(text, field)
        ok = value not in (None, "", "None") and want in value
        if not ok:
            result["hatch_texture_applied"] = False
            result.setdefault("texture_mismatch", []).append(
                f"{key}={want}: field reads {value!r}")

    result["ok"] = (result["has_diffuse_ramp"] and result["has_specular_ramp"]
                    and result["extinction_applied"]
                    and result["hatch_texture_applied"])
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
