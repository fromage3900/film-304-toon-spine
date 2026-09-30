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
        "EdgeStrength": 1.0,
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
        "EdgeStrength": 1.2,
        "DryRoughness": 0.70,
        "bUsePaintedRamp": False,
        "bContactShadow": True,
    }),
    "MI_Toon_Painterly": ("TP_SoftPainterly", {
        "BaseTint": (0.66, 0.58, 0.50, 1.0),
        "AccentTint": (0.84, 0.72, 0.58, 1.0),
        "InkIntensity": 0.05,
        "OilPaintStrength": 0.55,
        "StrokeStrength": 0.70,
        "BrushScale": 0.060,
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
        "GoldEmissive": 0.15,
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
        "WindSpeed": 0.35,
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
}


def _apply(inst, profile_name, overrides):
    """Set the Toon Profile then every override on a material instance."""
    tp = unreal.load_asset(lib.asset_path(lib.PROFILE_DIR, profile_name))
    if tp is not None:
        lib.try_set(inst, "toon_profile", tp)
        lib.try_set(inst, "override_toon_profile", True)
    else:
        lib.log(f"WARN: profile {profile_name} missing for {inst.get_name()}")

    me = unreal.MaterialEditingLibrary
    for key, value in overrides.items():
        try:
            if isinstance(value, bool):
                if hasattr(me, "set_material_instance_static_switch_parameter_value"):
                    me.set_material_instance_static_switch_parameter_value(
                        inst, key, value)
                else:
                    lib.try_set(inst, key, value)
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
    master = unreal.load_asset(lib.asset_path(lib.MASTER_DIR,
                                              "M_Master_Toon_Universal"))
    if master is None:
        raise RuntimeError("master material missing - run build_master_toon first")

    lib.ensure_dir(INSTANCE_DIR)
    tools = unreal.AssetToolsHelpers.get_asset_tools()

    made = []
    for name, (profile_name, overrides) in INSTANCES.items():
        path = lib.asset_path(INSTANCE_DIR, name)
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            if rebuild:
                lib.log(f"rebuild: deleting {name}")
                unreal.EditorAssetLibrary.delete_asset(path)
            else:
                made.append(path)
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
        lib.log(f"MI OK {name} -> {profile_name}")

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


def verify_instance(name, expected_overrides=None):
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
    result["ok"] = (result["parent"] in ("M_Master_Toon_Universal",
                                         "M_Outline_InvertedHull")
                    and not wrong)
    if wrong:
        result["error"] = "; ".join(wrong[:4])
    lib.log(f"VERIFY {name}: ok={result['ok']} parent={result['parent']} "
            f"checked={checked} {result.get('error','')}")
    return result
