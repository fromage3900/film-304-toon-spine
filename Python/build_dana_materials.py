"""Build and stage Dana's film toon materials in the Humber office level.

The imported Dana OpenPBR materials stay as source references. This builder
creates simple, editable Humber material instances, applies them only to the
staged Dana actor in L_Toon_Shot_Office, and saves that level after a complete
slot map has been confirmed.

Run with UnrealEditor-Cmd.exe HumberToonShader.uproject
    -ExecutePythonScript=Python/build_dana_materials.py -stdout -unattended
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import unreal  # noqa: E402
import spine_lib as lib  # noqa: E402


REPO = Path(__file__).resolve().parents[1]
INSTANCE_DIR = f"{lib.MATERIALS_ROOT}/Instances"
MAP_PATH = "/Game/Maps/L_Toon_Shot_Office"
DANA_MESH_PATH = "/Game/Meshes/Office/Props/C_DanaRenderTest_OSC"
REPORT = REPO / "Saved" / "Audit" / "dana_material_stage_report.json"
TEMP_REPORT = Path(os.environ.get("TEMP", ".")) / "dana_material_stage_report.json"
RENDER_DIR = REPO / "Saved" / "Renders" / "office_stage"
RENDER_STEM = "DANA_SH030_material_v01"


# Palette guided by the Dana source turntable: clear teal blouse, restrained
# violet skirt, warm neutral skin, and low-key trim. Values are linear colors.
# The only texture detail is a faint weave on cloth; there is no animated,
# iridescent, emissive, or game-state driven response in this set.
DANA_MATERIALS = {
    "MI_Dana_Skin": ("M_Master_Toon_Character", {
        "BaseTint": (0.54, 0.35, 0.28, 1.0),
        "AccentTint": (0.82, 0.57, 0.45, 1.0),
        "InkColor": (0.10, 0.055, 0.045, 1.0),
        "InkIntensity": 0.07,
        "DryRoughness": 0.78,
        "RampStrength": 0.70,
        "RimStrength": 0.12,
        "bUsePaintedRamp": False,
        "bContactShadow": True,
    }),
    "MI_Dana_Shirt": ("M_Master_Toon_Character", {
        "BaseTint": (0.035, 0.24, 0.27, 1.0),
        "AccentTint": (0.10, 0.46, 0.49, 1.0),
        "InkColor": (0.018, 0.075, 0.085, 1.0),
        "InkIntensity": 0.10,
        "DryRoughness": 0.84,
        "RampStrength": 0.75,
        "PatternIndex": 11.0,
        "PatternScale": 48.0,
        "PatternStrength": 0.08,
        "RimStrength": 0.12,
        "bUsePaintedRamp": False,
        "bContactShadow": True,
    }),
    "MI_Dana_Skirt": ("M_Master_Toon_Character", {
        "BaseTint": (0.22, 0.10, 0.32, 1.0),
        "AccentTint": (0.46, 0.27, 0.58, 1.0),
        "InkColor": (0.055, 0.03, 0.08, 1.0),
        "InkIntensity": 0.09,
        "DryRoughness": 0.84,
        "RampStrength": 0.75,
        "PatternIndex": 11.0,
        "PatternScale": 44.0,
        "PatternStrength": 0.05,
        "RimStrength": 0.10,
        "bUsePaintedRamp": False,
        "bContactShadow": True,
    }),
    "MI_Dana_Shoes": ("M_Master_Toon_Character", {
        "BaseTint": (0.075, 0.055, 0.09, 1.0),
        "AccentTint": (0.18, 0.13, 0.21, 1.0),
        "InkColor": (0.025, 0.02, 0.035, 1.0),
        "InkIntensity": 0.11,
        "DryRoughness": 0.66,
        "RampStrength": 0.72,
        "RimStrength": 0.08,
        "bUsePaintedRamp": False,
        "bContactShadow": True,
    }),
    "MI_Dana_Button": ("M_Master_Toon_Character", {
        "BaseTint": (0.30, 0.16, 0.055, 1.0),
        "AccentTint": (0.56, 0.34, 0.13, 1.0),
        "InkColor": (0.08, 0.045, 0.015, 1.0),
        "InkIntensity": 0.08,
        "DryRoughness": 0.42,
        "RampStrength": 0.80,
        "RimStrength": 0.05,
        "bUsePaintedRamp": False,
        "bContactShadow": True,
    }),
    "MI_Dana_Hair": ("M_Master_Toon_Hair", {
        "RootTint": (0.055, 0.030, 0.025, 1.0),
        "TipTint": (0.16, 0.080, 0.052, 1.0),
        "SheenStrength": 0.18,
        "RampStrength": 0.90,
        "InkIntensity": 0.08,
        "DryRoughness": 0.62,
        "RimStrength": 0.15,
        "bUsePaintedRamp": False,
    }),
    "MI_Dana_EyeWhite": ("M_Master_Toon_Face", {
        "BaseTint": (0.64, 0.58, 0.51, 1.0),
        "AccentTint": (0.87, 0.80, 0.70, 1.0),
        "FaceShadowTint": (0.49, 0.42, 0.39, 1.0),
        "FaceShadowMask": 0.0,
        "RampStrength": 0.55,
        "InkIntensity": 0.035,
        "DryRoughness": 0.55,
        "RimStrength": 0.04,
        "bUsePaintedRamp": False,
    }),
    "MI_Dana_Iris": ("M_Master_Toon_Face", {
        "BaseTint": (0.15, 0.065, 0.040, 1.0),
        "AccentTint": (0.34, 0.16, 0.080, 1.0),
        "FaceShadowTint": (0.07, 0.03, 0.02, 1.0),
        "FaceShadowMask": 0.0,
        "RampStrength": 0.50,
        "InkIntensity": 0.045,
        "DryRoughness": 0.28,
        "RimStrength": 0.06,
        "bUsePaintedRamp": False,
    }),
    "MI_Dana_EyeInterior": ("M_Master_Toon_Face", {
        "BaseTint": (0.035, 0.025, 0.030, 1.0),
        "AccentTint": (0.12, 0.075, 0.080, 1.0),
        "FaceShadowTint": (0.018, 0.012, 0.018, 1.0),
        "FaceShadowMask": 0.0,
        "RampStrength": 0.35,
        "InkIntensity": 0.02,
        "DryRoughness": 0.55,
        "RimStrength": 0.0,
        "bUsePaintedRamp": False,
    }),
    "MI_Dana_Cornea": ("M_Master_Toon_Glass", {
        "BaseTint": (0.72, 0.79, 0.82, 1.0),
        "AccentTint": (0.92, 0.95, 0.97, 1.0),
        "FresnelColor": (0.80, 0.90, 0.96, 1.0),
        "OpacityBase": 0.12,
        "FresnelPower": 4.0,
        "RampStrength": 0.35,
        "DryRoughness": 0.08,
        "bUsePaintedRamp": False,
    }),
}


# The last slot is the importer's generic OpenPBR fallback. It uses the neutral
# skin instance so every section leaves the source game shader behind.
SLOT_TO_INSTANCE = {
    "danahair_mat": "MI_Dana_Hair",
    "danairis_mat": "MI_Dana_Iris",
    "danaeye_mat": "MI_Dana_EyeWhite",
    "danacornea_mat": "MI_Dana_Cornea",
    "danaeyeint_mat": "MI_Dana_EyeInterior",
    "danashoes_mat": "MI_Dana_Shoes",
    "danapantsbutton_mat": "MI_Dana_Button",
    "danapants_mat": "MI_Dana_Skirt",
    "danashirt_mat": "MI_Dana_Shirt",
    "danaskin_mat": "MI_Dana_Skin",
    "openpbr_shader1": "MI_Dana_Skin",
}


def write_report(report: dict) -> None:
    text = json.dumps(report, indent=2, sort_keys=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text, encoding="utf-8")
    TEMP_REPORT.write_text(text, encoding="utf-8")


def build_instance(name: str, parent_name: str, overrides: dict):
    path = lib.asset_path(INSTANCE_DIR, name)
    inst = unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if inst is None:
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        lib.ensure_dir(INSTANCE_DIR)
        inst = tools.create_asset(
            name, INSTANCE_DIR, unreal.MaterialInstanceConstant,
            unreal.MaterialInstanceConstantFactoryNew())
    if inst is None:
        raise RuntimeError("could not create %s" % name)

    parent = unreal.load_asset(lib.asset_path(lib.MASTER_DIR, parent_name))
    if parent is None:
        raise RuntimeError("missing Humber parent master %s" % parent_name)
    unreal.MaterialEditingLibrary.set_material_instance_parent(inst, parent)

    me = unreal.MaterialEditingLibrary
    for key, value in overrides.items():
        if isinstance(value, bool):
            me.set_material_instance_static_switch_parameter_value(inst, key, value)
        elif isinstance(value, tuple):
            me.set_material_instance_vector_parameter_value(
                inst, key, unreal.LinearColor(*value))
        elif isinstance(value, (float, int)):
            me.set_material_instance_scalar_parameter_value(inst, key, float(value))
        else:
            raise TypeError("unsupported %s parameter value: %s" %
                            (key, type(value).__name__))
    lib.save(inst)

    # Read the effective values back from the instance after save. Unknown
    # parameter names and type mismatches must stop staging before the map save.
    wrong = []
    for key, wanted in overrides.items():
        if isinstance(wanted, bool):
            actual = bool(me.get_material_instance_static_switch_parameter_value(
                inst, key))
            expected = wanted
        elif isinstance(wanted, tuple):
            actual_color = me.get_material_instance_vector_parameter_value(inst, key)
            actual = tuple(round(float(c), 4) for c in
                           (actual_color.r, actual_color.g,
                            actual_color.b, actual_color.a))
            expected = tuple(round(float(c), 4) for c in wanted)
        else:
            actual = round(float(me.get_material_instance_scalar_parameter_value(
                inst, key)), 4)
            expected = round(float(wanted), 4)
        if actual != expected:
            wrong.append("%s=%s (expected %s)" % (key, actual, expected))

    actual_parent = inst.get_editor_property("parent")
    if actual_parent is None or actual_parent.get_name() != parent_name:
        wrong.append("parent=%s (expected %s)" %
                     (actual_parent.get_name() if actual_parent else None,
                      parent_name))
    if wrong:
        raise RuntimeError("%s parameter readback failed: %s" %
                           (name, "; ".join(wrong)))
    return inst


def dana_actor_and_component() -> tuple[object, object, object]:
    matches = []
    for actor in unreal.EditorLevelLibrary.get_all_level_actors() or []:
        for comp in actor.get_components_by_class(unreal.SkeletalMeshComponent):
            mesh = comp.skeletal_mesh
            if mesh and mesh.get_path_name().split(".")[0] == DANA_MESH_PATH:
                matches.append((actor, comp, mesh))
    if len(matches) != 1:
        raise RuntimeError("expected one staged Dana skeletal actor in %s; found %d" %
                           (MAP_PATH, len(matches)))
    return matches[0]


def apply_dana_materials(report: dict) -> None:
    loaded = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    if not loaded:
        raise RuntimeError("could not load %s" % MAP_PATH)
    actor, comp, mesh = dana_actor_and_component()

    slots = []
    for index, slot in enumerate(mesh.materials):
        slot_name = str(slot.material_slot_name)
        instance_name = SLOT_TO_INSTANCE.get(slot_name.lower())
        if instance_name is None:
            raise RuntimeError("no Dana material route for slot %d %s" %
                               (index, slot_name))
        material = unreal.load_asset(
            lib.asset_path(INSTANCE_DIR, instance_name))
        if material is None:
            raise RuntimeError("staged material is missing: %s" % instance_name)
        comp.set_material(index, material)
        slots.append({"index": index, "slot": slot_name,
                      "instance": material.get_path_name()})

    expected_slots = {str(slot.material_slot_name).lower()
                      for slot in mesh.materials}
    if expected_slots != set(SLOT_TO_INSTANCE):
        raise RuntimeError("Dana slot contract changed: found %s, builder covers %s" %
                           (sorted(expected_slots), sorted(SLOT_TO_INSTANCE)))

    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    saved = unreal.EditorLoadingAndSavingUtils.save_map(world, MAP_PATH)
    if not saved:
        raise RuntimeError("failed to save Dana overrides to %s" % MAP_PATH)

    # Reload the saved map before accepting the stage. This catches transient
    # component overrides that were never serialized.
    if not unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH):
        raise RuntimeError("saved map could not be reloaded")
    actor, comp, mesh = dana_actor_and_component()
    readback = []
    for index, slot in enumerate(mesh.materials):
        wanted = lib.asset_path(
            INSTANCE_DIR, SLOT_TO_INSTANCE[str(slot.material_slot_name).lower()])
        actual = comp.get_material(index)
        actual_path = actual.get_path_name() if actual else None
        readback.append({"index": index,
                         "slot": str(slot.material_slot_name),
                         "material": actual_path,
                         "ok": actual_path == wanted})
    if not all(row["ok"] for row in readback):
        raise RuntimeError("Dana material readback failed after level reload")

    report["stage"] = {
        "level": MAP_PATH,
        "actor": actor.get_actor_label(),
        "actor_location": [actor.get_actor_location().x,
                           actor.get_actor_location().y,
                           actor.get_actor_location().z],
        "mesh": mesh.get_path_name(),
        "saved": bool(saved),
        "slot_assignments": slots,
        "fresh_level_readback": readback,
        "all_slots_assigned": len(slots) == len(SLOT_TO_INSTANCE),
        "all_slots_persisted": all(row["ok"] for row in readback),
    }


def main() -> None:
    report = {
        "result": "running",
        "instances": [],
        "stage": None,
        "scope": "Dana material instances and Dana actor overrides only",
        "source_materials_preserved": True,
        "melodia_dependencies": [],
        "game_only_effects": [],
    }
    try:
        for name, (parent, overrides) in DANA_MATERIALS.items():
            inst = build_instance(name, parent, overrides)
            report["instances"].append({
                "name": name,
                "path": inst.get_path_name(),
                "parent": parent,
                "parameter_count": len(overrides),
                "readback": "pass",
            })
        apply_dana_materials(report)
        report["result"] = "pass"
    except Exception as exc:
        report["result"] = "fail"
        report["error"] = "%s: %s" % (type(exc).__name__, exc)
        write_report(report)
        raise
    write_report(report)
    unreal.log("DANA_MATERIAL_STAGE " + json.dumps({
        "result": report["result"],
        "instances": len(report["instances"]),
        "slots": len(report["stage"]["slot_assignments"]),
        "level": report["stage"]["level"],
        "report": str(REPORT),
    }))


main()
