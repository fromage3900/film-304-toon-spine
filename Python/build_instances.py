"""Build material instances - the art-direction layer between master and actor.

A Toon Profile only shapes shading. Everything an artist actually sets per
asset - palette, band shape, ink, rim, roughness - lives on a MaterialInstance.
This creates a starting set so the first editor open is a shelf of usable looks
rather than an empty project.

Each instance names the Toon Profile it assumes, so the profile a look was
designed against is discoverable without opening every one.
"""
from __future__ import annotations

import unreal

import spine_lib as lib
import build_toon_profiles as profiles

INSTANCE_DIR = f"{lib.MATERIALS_ROOT}/Instances"

# name -> (profile, overrides)
#   V = vector (RGBA), S = scalar, B = static switch bool
INSTANCES = {
    "MI_Toon_Hero": ("TP_Hero", {
        "BaseTint": (0.58, 0.50, 0.55, 1.0),
        "AccentTint": (0.80, 0.70, 0.72, 1.0),
        "InkColor": (0.04, 0.04, 0.07, 1.0),
        "InkIntensity": 0.25,
        "DryRoughness": 0.62,
        "GildingStrength": 0.0,
        "OilPaintStrength": 0.10,
        "bUsePaintedRamp": False,
        "bContactShadow": True,
    }),
    "MI_Toon_TwoTone": ("TP_TwoTone", {
        "BaseTint": (0.62, 0.56, 0.48, 1.0),
        "AccentTint": (0.85, 0.78, 0.66, 1.0),
        "InkIntensity": 0.45,
        "DryRoughness": 0.70,
        "bUsePaintedRamp": False,
        "bContactShadow": True,
    }),
    "MI_Toon_Painterly": ("TP_SoftPainterly", {
        "BaseTint": (0.66, 0.58, 0.50, 1.0),
        "AccentTint": (0.84, 0.72, 0.58, 1.0),
        "InkIntensity": 0.05,
        "OilPaintStrength": 0.55,
        "DryRoughness": 0.80,
        "bUsePaintedRamp": True,
        "bContactShadow": False,
    }),
    "MI_Toon_Environment": ("TP_Environment", {
        "BaseTint": (0.52, 0.54, 0.50, 1.0),
        "AccentTint": (0.70, 0.72, 0.68, 1.0),
        "InkIntensity": 0.0,
        "BandScale": 0.020,
        "BandStrength": 0.06,
        "DryRoughness": 0.85,
        "bUsePaintedRamp": False,
        "bContactShadow": False,
    }),
    "MI_Toon_Stone": ("TP_Stone", {
        "BaseTint": (0.46, 0.45, 0.43, 1.0),
        "AccentTint": (0.62, 0.61, 0.58, 1.0),
        "InkIntensity": 0.10,
        "BandScale": 0.055,
        "BandStrength": 0.20,
        "DryRoughness": 0.90,
        "bUsePaintedRamp": False,
        "bContactShadow": True,
    }),
    "MI_Toon_Gold": ("TP_Gold", {
        "BaseTint": (0.80, 0.62, 0.26, 1.0),
        "AccentTint": (0.95, 0.82, 0.42, 1.0),
        "GoldTint": (0.92, 0.74, 0.34, 1.0),
        "GildingStrength": 0.85,
        "DryRoughness": 0.30,
        "WetRoughness": 0.15,
        "bUsePaintedRamp": False,
        "bContactShadow": False,
    }),
    "MI_Toon_Foliage": ("TP_Foliage", {
        "BaseTint": (0.24, 0.42, 0.22, 1.0),
        "AccentTint": (0.46, 0.66, 0.34, 1.0),
        "InkIntensity": 0.08,
        "DryRoughness": 0.88,
        "bUsePaintedRamp": False,
        "bContactShadow": False,
    }),
    "MI_Toon_Hatched": ("TP_Hatched", {
        "BaseTint": (0.60, 0.56, 0.50, 1.0),
        "AccentTint": (0.78, 0.74, 0.68, 1.0),
        "InkIntensity": 0.35,
        "DryRoughness": 0.75,
        "bUsePaintedRamp": False,
        "bContactShadow": True,
    }),

    # -------------------------------------------------------------- office set
    # Added 2026-10-02, one per TP_Office_* profile. BaseTint carries the HUE:
    # ToonProfile ramps are scalar-valued (build_toon_profiles._step4 writes the
    # same Value into all three colour curves), so shadow colour is authored here
    # rather than in the profile. Tints lean cool-neutral for the office's
    # fluorescent/world mix and stay off pure grey so shadows read as colour.
    "MI_Toon_Office_Carpet": ("TP_Office_Carpet", {
        "BaseTint": (0.34, 0.33, 0.38, 1.0),
        "AccentTint": (0.52, 0.51, 0.57, 1.0),
        "InkIntensity": 0.05,
        "DryRoughness": 0.92,
        "PatternIndex": 6.0,            # Stipple
        "PatternStrength": 0.25,
        "PatternDensity": 0.55,
        "PatternScale": 24.0,
        "bContactShadow": False,
    }),
    "MI_Toon_Office_Laminate": ("TP_Office_Laminate", {
        "BaseTint": (0.62, 0.54, 0.42, 1.0),
        "AccentTint": (0.78, 0.71, 0.58, 1.0),
        "InkIntensity": 0.10,
        "DryRoughness": 0.48,
        "BandScale": 0.030,
        "BandStrength": 0.10,
        "bContactShadow": True,
    }),
    "MI_Toon_Office_DropCeiling": ("TP_Office_DropCeiling", {
        "BaseTint": (0.72, 0.73, 0.71, 1.0),
        "AccentTint": (0.84, 0.85, 0.83, 1.0),
        "InkIntensity": 0.0,
        "DryRoughness": 0.95,
        "BandScale": 0.010,
        "BandStrength": 0.03,
        "bContactShadow": False,
    }),
    "MI_Toon_Office_Troffer": ("TP_Office_Troffer", {
        "BaseTint": (0.90, 0.92, 0.95, 1.0),
        "AccentTint": (0.97, 0.98, 1.00, 1.0),
        "InkIntensity": 0.0,
        "EmissiveColor": (0.86, 0.90, 1.00, 1.0),
        "EmissiveIntensity": 1.0,
        "DryRoughness": 0.60,
        "bContactShadow": False,
    }),
    "MI_Toon_Office_PowderCoat": ("TP_Office_PowderCoat", {
        "BaseTint": (0.44, 0.45, 0.48, 1.0),
        "AccentTint": (0.60, 0.62, 0.66, 1.0),
        "InkIntensity": 0.20,
        "PatternIndex": 5.0,            # CrossHatch
        "PatternStrength": 0.35,
        "PatternDensity": 0.80,
        "DryRoughness": 0.42,
        "bContactShadow": True,
    }),
    "MI_Toon_Office_Screen": ("TP_Office_Screen", {
        "BaseTint": (0.14, 0.15, 0.18, 1.0),
        "AccentTint": (0.30, 0.38, 0.52, 1.0),
        "InkIntensity": 0.15,
        "EmissiveColor": (0.42, 0.62, 0.90, 1.0),
        "EmissiveIntensity": 1.0,
        "DryRoughness": 0.18,
        "bContactShadow": False,
    }),
    "MI_Toon_Office_Polypropylene": ("TP_Office_Polypropylene", {
        "BaseTint": (0.40, 0.42, 0.44, 1.0),
        "AccentTint": (0.56, 0.58, 0.60, 1.0),
        "InkIntensity": 0.12,
        "PatternIndex": 11.0,           # Weave
        "PatternStrength": 0.20,
        "PatternScale": 40.0,
        "DryRoughness": 0.55,
        "bContactShadow": True,
    }),
    "MI_Toon_Office_Whiteboard": ("TP_Office_Whiteboard", {
        "BaseTint": (0.86, 0.87, 0.86, 1.0),
        "AccentTint": (0.94, 0.95, 0.94, 1.0),
        "InkIntensity": 0.08,
        "DryRoughness": 0.20,
        "bContactShadow": False,
    }),

    # ------------------------------------------------------- film / character
    # Added 2026-10-03 alongside TP_Melusina. BaseTint IS the canonical
    # warm-violet #352D40, converted straight from the manifest's
    # framing_standard.shading_pipeline.shadow_tint_hex (0x35,0x2D,0x40 / 255
    # = 0.208, 0.176, 0.251). It lives here rather than in the profile because
    # ToonProfile ramps are scalar-valued and cannot carry per-channel hue --
    # the rule the office block above already follows.
    "MI_Toon_Melusina": ("TP_Melusina", {
        "BaseTint": (0.208, 0.176, 0.251, 1.0),   # #352D40 warm violet
        "AccentTint": (0.72, 0.64, 0.78, 1.0),    # lifted violet for the lit side
        "InkColor": (0.05, 0.04, 0.07, 1.0),
        "InkIntensity": 0.30,
        "DryRoughness": 0.58,
        "BandScale": 0.028,
        "BandStrength": 0.12,
        "GildingStrength": 0.0,
        # THE RAMP MUST BE OPTED IN OR THE PROFILE DOES NOTHING.
        # build_master_toon wires RampStrength (default 0.0) into both
        # MF_ColorRamp3 and MF_RampLUT's Mask, and both end in
        # lerp(base_color, ramp_rgb, mask). At 0 the profile's authored ramp is
        # never consulted, which is exactly what a preview render showed: a
        # smooth falloff, no banding. Measured 2026-10-03 - the character
        # instances were the first to set this, so every TP_* asset shipped
        # before them was structurally verified and visually inert.
        "RampStrength": 1.0,
        "bUsePaintedRamp": False,
        "bContactShadow": True,
        # Opt into the character master's offset rim. RimStrength defaults to
        # 0.0 on the master so nothing changes until an instance asks for it;
        # the hero is the instance that should demonstrate the edge of light.
        "RimStrength": 0.45,
        # THIRD ELEMENT = PARENT MASTER. Without it the default parent applies
        # and this instance shades on TP_Default, because a material instance
        # cannot carry its own Toon Profile on this engine build (measured
        # 2026-10-02). TP_Melusina is named by the shot manifest, GROUP_
        # STAGING_GUIDE.md section 3 and dogfood_toon_spine.py - and it only
        # reaches a pixel when the MASTER binds it. That is what
        # M_Master_Toon_Character does.
    }, "M_Master_Toon_Character"),
    "MI_Toon_Character": ("TP_Character", {
        "BaseTint": (0.30, 0.27, 0.34, 1.0),      # lifted #352D40 family
        "AccentTint": (0.62, 0.57, 0.66, 1.0),
        "InkColor": (0.06, 0.05, 0.08, 1.0),
        "InkIntensity": 0.18,
        "DryRoughness": 0.72,
        # Held below the hero's 1.0 so background cast reads as a softer band
        # than Melusina in the same frame, without a second profile cost.
        "RampStrength": 0.85,
        "bUsePaintedRamp": False,
        "bContactShadow": False,
    }),

    # ------------------------------------------------- tilable SDF map looks
    # Added 2026-10-03: the SDF map library's showcase instances. PatternIndex
    # 12 samples the map carried by PatternSDFMap (a per-instance swappable
    # TextureObjectParameter; texture overrides ride the new "T" support in
    # _apply). The G channel's per-cell width jitter is baked into each map.
    "MI_Toon_Scales": ("TP_Melusina", {
        "BaseTint": (0.17, 0.28, 0.33, 1.0),      # sea-teal tail
        "AccentTint": (0.42, 0.62, 0.68, 1.0),
        "InkColor": (0.03, 0.04, 0.06, 1.0),
        "InkIntensity": 0.35,
        "DryRoughness": 0.42,
        "RampStrength": 1.0,
        "PatternIndex": 12.0,           # SDFMap
        "PatternSDFMap": "/Game/Materials/Textures/T_SDF_Scales",
        "PatternScale": 18.0,
        "PatternStrength": 0.50,
        "PatternDensity": 0.40,
        "PatternSoftness": 0.05,
        "bUsePaintedRamp": False,
        "bContactShadow": True,
        # Melusina's tail: declares TP_Melusina, so it belongs on the same
        # character master - an instance cannot bind a profile itself.
    }, "M_Master_Toon_Character"),
    "MI_Toon_CrackedStone": ("TP_Stone", {
        "BaseTint": (0.42, 0.40, 0.37, 1.0),
        "AccentTint": (0.58, 0.56, 0.52, 1.0),
        "InkIntensity": 0.15,
        "DryRoughness": 0.90,
        "BandScale": 0.055,
        "BandStrength": 0.20,
        "PatternIndex": 12.0,
        "PatternSDFMap": "/Game/Materials/Textures/T_SDF_Cracks",
        "PatternScale": 5.0,
        "PatternStrength": 0.45,
        "PatternDensity": 0.55,
        "bContactShadow": True,
    }),
    # ------------------------------------------------- foliage master set
    "MI_Foliage_Fern": ("TP_Foliage", {
        "BaseTint": (0.20, 0.36, 0.18, 1.0),
        "AccentTint": (0.44, 0.64, 0.30, 1.0),
        "InkIntensity": 0.12,
        "DryRoughness": 0.88,
        "RampStrength": 1.0,
        "PatternIndex": 12.0,
        "PatternSDFMap": "/Game/Materials/Textures/T_SDF_Strokes",
        "PatternScale": 9.0,
        "PatternStrength": 0.35,
        "PatternDensity": 0.45,
        "bUsePaintedRamp": False,
        "bContactShadow": False,
    }, "M_Master_Toon_Foliage"),
    "MI_Foliage_Hedge": ("TP_Foliage", {
        "BaseTint": (0.26, 0.44, 0.24, 1.0),
        "AccentTint": (0.50, 0.70, 0.36, 1.0),
        "InkIntensity": 0.08,
        "DryRoughness": 0.90,
        "RampStrength": 0.8,
        "SwayAmount": 0.10,
        "SwaySpeed": 1.6,
        "bUsePaintedRamp": False,
        "bContactShadow": False,
    }, "M_Master_Toon_Foliage"),
    # ------------------------------------------------- water master set
    "MI_Water_Canal": ("TP_Default", {
        "BaseTint": (0.14, 0.32, 0.36, 1.0),
        "AccentTint": (0.44, 0.70, 0.74, 1.0),
        "InkIntensity": 0.25,
        "DryRoughness": 0.08,
        "RampStrength": 0.80,
        "BandScale": 0.030,
        "BandStrength": 0.25,
        "RippleScale1": 18.0,
        "RippleSpeed1": 1.10,
        "RippleScale2": 29.0,
        "RippleSpeed2": 1.40,
        "RippleStrength": 0.55,
        "bUsePaintedRamp": False,
        "bContactShadow": False,
    }, "M_Master_Toon_Water"),
    "MI_Water_Puddle": ("TP_Default", {
        "BaseTint": (0.18, 0.30, 0.34, 1.0),
        "AccentTint": (0.48, 0.66, 0.70, 1.0),
        "InkIntensity": 0.15,
        "DryRoughness": 0.04,
        "RampStrength": 0.40,
        "BandStrength": 0.10,
        "RippleScale1": 40.0,
        "RippleSpeed1": 0.30,
        "RippleScale2": 61.0,
        "RippleSpeed2": 0.20,
        "RippleStrength": 0.25,
        "bUsePaintedRamp": False,
        "bContactShadow": False,
    }, "M_Master_Toon_Water"),
}


def _apply(inst, profile_name, overrides):
    """Set the Toon Profile then every override on a material instance.

    THE PROFILE CANNOT BE SET HERE - measured 2026-10-02, see
    Saved/Audit/toon_profile_binding_probe_v3.json. Seven candidate property
    names were tried against MaterialInstanceConstant via
    get_editor_property; UE rejected every one of them. The only toon-related
    property a material instance exposes is the boolean `override_toon_profile`.
    The profile asset reference lives on the MaterialExpressionSubstrateToonBSDF
    node inside the MASTER, where it does bind (verified by identity read-back).

    So this line below used to be a guaranteed no-op, swallowed by try_set:

        lib.try_set(inst, "toon_profile", tp)

    It is removed rather than left in place, because a call that cannot work
    reads like a call that does. Per-family profiles therefore need a different
    route - see the note in Docs/TOON_EXPANSION_2026-10-02.md.

    `profile_name` is still used, to keep the instance's intended profile
    discoverable from the builder source, which is what
    CONTENT_CONVENTIONS.md relies on when it says each MI "names the Toon
    Profile it assumes".
    """
    del profile_name  # not settable on an instance; see docstring

    me = unreal.MaterialEditingLibrary
    for key, value in overrides.items():
        try:
            if isinstance(value, bool):
                if hasattr(me, "set_material_instance_static_switch_parameter_value"):
                    me.set_material_instance_static_switch_parameter_value(
                        inst, key, value)
                else:
                    lib.try_set(inst, key, value)
            elif isinstance(value, str):
                # texture parameter override (e.g. PatternSDFMap) - the value
                # is the asset path; resolved and read back by name so a
                # broken path fails the verify, not the render
                tex = unreal.load_asset(value)
                if tex is None:
                    lib.log(f"WARN {inst.get_name()}.{key}: texture not found "
                            f"{value}")
                me.set_material_instance_texture_parameter_value(inst, key, tex)
            elif isinstance(value, tuple):
                me.set_material_instance_vector_parameter_value(
                    inst, key, unreal.LinearColor(*value))
            elif isinstance(value, (int, float)):
                me.set_material_instance_scalar_parameter_value(
                    inst, key, float(value))
        except Exception as exc:
            lib.log(f"WARN {inst.get_name()}.{key}: {exc}")


def build(rebuild=True):
    lib.log(f"=== Material Instances ({len(INSTANCES)}) ===")
    # per-instance parent: entries may carry a third element naming the master
    # (foliage/water sets); the default is the universal toon master.
    DEFAULT_PARENT = "M_Master_Toon_Universal"

    lib.ensure_dir(INSTANCE_DIR)
    tools = unreal.AssetToolsHelpers.get_asset_tools()

    made = []
    for name, spec in INSTANCES.items():
        profile_name, overrides = spec[0], spec[1]
        parent_name = spec[2] if len(spec) > 2 else DEFAULT_PARENT
        path = lib.asset_path(INSTANCE_DIR, name)
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            if rebuild:
                lib.log(f"rebuild: deleting {name}")
                unreal.EditorAssetLibrary.delete_asset(path)
            else:
                made.append(path)
                continue
        master = unreal.load_asset(lib.asset_path(lib.MASTER_DIR, parent_name))
        if master is None:
            lib.log(f"FAIL {name}: parent master {parent_name} missing")
            continue
        inst = tools.create_asset(name, INSTANCE_DIR,
                                  unreal.MaterialInstanceConstant,
                                  unreal.MaterialInstanceConstantFactoryNew())
        if inst is None:
            lib.log(f"FAIL creating {name}")
            continue
        unreal.MaterialEditingLibrary.set_material_instance_parent(inst, master)
        _apply(inst, profile_name, overrides)
        lib.save(inst)
        made.append(path)
        lib.log(f"MI OK {name} -> {profile_name} ({parent_name})")

    # outline instance, parented to the outline master
    outline_master = unreal.load_asset(lib.asset_path(lib.MASTER_DIR,
                                                      "M_Outline_InvertedHull"))
    if outline_master is not None:
        opath = lib.asset_path(INSTANCE_DIR, "MI_Outline_Thin")
        if not unreal.EditorAssetLibrary.does_asset_exist(opath):
            oi = tools.create_asset("MI_Outline_Thin", INSTANCE_DIR,
                                    unreal.MaterialInstanceConstant,
                                    unreal.MaterialInstanceConstantFactoryNew())
            unreal.MaterialEditingLibrary.set_material_instance_parent(oi,
                                                                       outline_master)
            unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
                oi, "InkColor", unreal.LinearColor(0.02, 0.02, 0.04, 1.0))
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
                oi, "Thickness", 0.008)
            lib.save(oi)
            made.append(opath)
            lib.log("MI OK MI_Outline_Thin")

        opath2 = lib.asset_path(INSTANCE_DIR, "MI_Outline_Heavy")
        if not unreal.EditorAssetLibrary.does_asset_exist(opath2):
            oi2 = tools.create_asset("MI_Outline_Heavy", INSTANCE_DIR,
                                     unreal.MaterialInstanceConstant,
                                     unreal.MaterialInstanceConstantFactoryNew())
            unreal.MaterialEditingLibrary.set_material_instance_parent(oi2,
                                                                        outline_master)
            unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
                oi2, "InkColor", unreal.LinearColor(0.01, 0.01, 0.02, 1.0))
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
                oi2, "Thickness", 0.020)
            lib.save(oi2)
            made.append(opath2)
            lib.log("MI OK MI_Outline_Heavy")

    return made


def verify_instance(name, expected_overrides=None, expected_parent=None):
    """Confirm an instance exists, is parented, and kept its overrides."""
    path = lib.asset_path(INSTANCE_DIR, name)
    inst = unreal.load_asset(path)
    result = {"name": name, "loads": inst is not None, "ok": False}
    if inst is None:
        lib.log(f"VERIFY FAIL {name}: does not load")
        return result

    try:
        parent = inst.get_editor_property("parent")
        result["parent"] = parent.get_name() if parent else None
    except Exception:
        result["parent"] = "err"

    # Verify by READING BACK VALUES, not by enumerating stored overrides.
    # Two traps found 2026-09-30:
    #   * MaterialInstanceConstant has no `static_parameters` property in 5.8,
    #     so the enumeration approach silently counted zero switches.
    #   * an override equal to the parent default is not "missing" - it is
    #     indistinguishable from unset by design. Presence is not the question;
    #     the resulting VALUE is.
    me = unreal.MaterialEditingLibrary
    wrong = []
    checked = 0

    for key, want in (expected_overrides or {}).items():
        try:
            if isinstance(want, bool):
                got = me.get_material_instance_static_switch_parameter_value(inst, key)
                got = bool(got)
            elif isinstance(want, str):
                # texture parameter - read back and compare ASSET NAMES, so a
                # broken path or a stale assignment fails the verify
                tex = me.get_material_instance_texture_parameter_value(inst, key)
                got = tex.get_name() if tex else ""
                want = want.rsplit("/", 1)[-1].split(".")[0]
            elif isinstance(want, tuple):
                lc = me.get_material_instance_vector_parameter_value(inst, key)
                # LinearColor exposes .r/.g/.b/.a and is NOT iterable
                got = (round(float(lc.r), 4), round(float(lc.g), 4),
                       round(float(lc.b), 4), round(float(lc.a), 4))
                want = tuple(round(float(c), 4) for c in want)
            else:
                got = round(float(me.get_material_instance_scalar_parameter_value(
                    inst, key)), 4)
                want = round(float(want), 4)
            checked += 1
            if got != want:
                wrong.append(f"{key}: got {got} want {want}")
        except Exception as exc:
            wrong.append(f"{key}: {str(exc)[:60]}")

    result["checked"] = checked
    result["mismatched"] = wrong
    # parent_ok compares the NAME STRING (result["parent"] is get_name();
    # the local `parent` is the UMaterialInterface object and never equals a
    # string - that object-vs-string compare is what failed all 24 verifies
    # in the 17:22 spine run before this fix).
    parent_ok = (result["parent"] == expected_parent if expected_parent
                 else result["parent"] in ("M_Master_Toon_Universal",
                                           "M_Outline_InvertedHull"))
    result["ok"] = parent_ok and not wrong
    if wrong:
        result["error"] = "; ".join(wrong[:4])
    lib.log(f"VERIFY {name}: ok={result['ok']} parent={result['parent']} "
            f"checked={checked} {result.get('error','')}")
    return result
