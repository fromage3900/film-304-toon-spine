"""Apply Film304 E1 material instances to the baked skyline and roof actors.

This is a live-level staging helper. It edits only component material overrides
in the open L_Film_Office world, writes a readback report, and never saves a
map or material asset. Call run(apply=False) to inspect the planned changes or
run(apply=True) to apply the reversible in-memory preview.
"""

import json
from pathlib import Path

import unreal


REPO = Path(r"G:\film-304-toon-spine")
REPORT_PATH = REPO / "Saved" / "Audit" / "film304_baked_env_material_preview.json"
EXPECTED_WORLD_PREFIX = "/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office"
TARGET_FOLDERS = {
    "Baked_Brutalist_Skyline",
    "Baked_Skyline_Rooftops",
    "Baked_Skyline_Cables",
}
FILM_MATERIALS = {
    "Asphalt": "/Game/Materials/Instances/Film304/Scene/MI_Film304_EnvE1_Asphalt",
    "Glazing": "/Game/Materials/Instances/Film304/Scene/MI_Film304_EnvE1_Glazing",
    "Concrete": "/Game/Materials/Instances/Film304/Scene/MI_Film304_EnvE1_Concrete",
}
EXPECTED_PARENT = "/Game/Materials/Instances/Film304/MI_Film304_Toon.MI_Film304_Toon"


def _assignment_key(actor_label, component_name, slot_index):
    return "{}|{}|{}".format(actor_label, component_name, slot_index)


def _existing_baseline(world_path):
    if not REPORT_PATH.exists():
        return {}
    try:
        saved = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if saved.get("world") != world_path:
        return {}
    return {
        _assignment_key(item.get("actor"), item.get("component"), item.get("slot_index")): item.get("previous_material")
        for item in saved.get("assignments", [])
        if item.get("previous_material")
    }


def _slot_name(static_mesh, index):
    slots = static_mesh.get_editor_property("static_materials")
    if index >= len(slots):
        return ""
    return str(slots[index].get_editor_property("material_slot_name"))


def _target_for(slot_name, current_material):
    slot = (slot_name or "").lower()
    current = current_material.get_name().lower() if current_material else ""

    if "glaz" in slot or "glass" in slot or "window" in slot:
        return "Glazing"
    if "asphalt" in slot or "ground" in slot or "street" in slot or "road" in slot:
        return "Asphalt"
    if "concrete" in slot or "facade" in slot or "wall" in slot or "massing" in slot:
        return "Concrete"

    # A few single-slot roof accessories have generic slot names; retain their
    # established surface intent from the currently assigned Film304 MI.
    for material_kind in ("Asphalt", "Glazing", "Concrete"):
        if "brutalist" + material_kind.lower() in current:
            return material_kind
        if "film304_enve1_" + material_kind.lower() in current:
            return material_kind
        if material_kind == "Glazing" and "film304_glazing_" in current:
            return material_kind
    return None


def run(apply=False):
    world = unreal.EditorLevelLibrary.get_editor_world()
    world_path = world.get_path_name() if world else ""
    if not world_path.startswith(EXPECTED_WORLD_PREFIX):
        raise RuntimeError("Refusing to touch a world other than L_Film_Office: " + world_path)

    materials = {kind: unreal.load_asset(path) for kind, path in FILM_MATERIALS.items()}
    for kind, material in materials.items():
        if not material:
            raise RuntimeError("Film304 material is missing: " + FILM_MATERIALS[kind])
        parent = material.get_editor_property("parent")
        parent_path = parent.get_path_name() if parent else ""
        if parent_path != EXPECTED_PARENT:
            raise RuntimeError("Unexpected parent on {}: {}".format(kind, parent_path))

    baseline = _existing_baseline(world_path)
    report = {
        "world": world_path,
        "apply_requested": bool(apply),
        "map_saved": False,
        "material_assets_saved": False,
        "target_folders": sorted(TARGET_FOLDERS),
        "film_materials": FILM_MATERIALS,
        "assignments": [],
        "skipped_instanced_components": [],
        "unmapped_slots": [],
    }

    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        folder = str(actor.get_folder_path())
        if folder not in TARGET_FOLDERS:
            continue

        for component in actor.get_components_by_class(unreal.StaticMeshComponent):
            component_class = component.get_class().get_name()
            if "InstancedStaticMesh" in component_class:
                report["skipped_instanced_components"].append({
                    "actor": actor.get_actor_label(),
                    "folder": folder,
                    "component": component.get_name(),
                    "class": component_class,
                    "reason": "The Film304 E1 parent has not been enabled and verified for instanced static meshes.",
                })
                continue

            static_mesh = component.get_editor_property("static_mesh")
            if not static_mesh:
                continue

            for index in range(component.get_num_materials()):
                current = component.get_material(index)
                current_path = current.get_path_name() if current else None
                current_name = current.get_name() if current else ""
                key = _assignment_key(actor.get_actor_label(), component.get_name(), index)
                slot_name = _slot_name(static_mesh, index)
                kind = _target_for(slot_name, current)
                if not kind:
                    report["unmapped_slots"].append({
                        "actor": actor.get_actor_label(),
                        "component": component.get_name(),
                        "mesh": static_mesh.get_path_name(),
                        "slot_index": index,
                        "slot_name": slot_name,
                        "current_material": current_path,
                    })
                    continue

                target = materials[kind]
                target_path = target.get_path_name()
                changed = current_path != target_path
                if changed and apply:
                    component.set_material(index, target)
                readback = component.get_material(index)
                readback_path = readback.get_path_name() if readback else None
                report["assignments"].append({
                    "actor": actor.get_actor_label(),
                    "folder": folder,
                    "component": component.get_name(),
                    "mesh": static_mesh.get_path_name(),
                    "slot_index": index,
                    "slot_name": slot_name,
                    "previous_material": baseline.get(key, current_path),
                    "material_before_call": current_path,
                    "previous_material_name": current_name,
                    "film_material": target_path,
                    "changed": changed,
                    "readback": readback_path,
                    "readback_pass": readback_path == target_path if (apply or not changed) else None,
                })

    report["changed_count"] = sum(1 for item in report["assignments"] if item["changed"])
    report["readback_pass"] = (
        all(bool(item["readback_pass"]) for item in report["assignments"])
        if apply
        else None
    )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({
        "apply_requested": bool(apply),
        "changed_count": report["changed_count"],
        "assignment_count": len(report["assignments"]),
        "readback_pass": report["readback_pass"],
        "skipped_instanced_components": len(report["skipped_instanced_components"]),
        "unmapped_slots": report["unmapped_slots"],
        "map_saved": False,
        "report_path": str(REPORT_PATH),
    }, separators=(",", ":")))
    return report


def restore_preview():
    """Restore the original component overrides from the latest apply report."""
    world = unreal.EditorLevelLibrary.get_editor_world()
    world_path = world.get_path_name() if world else ""
    if not world_path.startswith(EXPECTED_WORLD_PREFIX):
        raise RuntimeError("Refusing to restore in a world other than L_Film_Office: " + world_path)
    if not REPORT_PATH.exists():
        raise RuntimeError("No material preview report exists to restore.")

    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    actor_by_label = {a.get_actor_label(): a for a in unreal.EditorLevelLibrary.get_all_level_actors()}
    restored, already_original, conflicts = [], [], []

    for item in report.get("assignments", []):
        actor = actor_by_label.get(item.get("actor"))
        if not actor:
            conflicts.append({"item": item, "reason": "actor_missing"})
            continue
        component = next((c for c in actor.get_components_by_class(unreal.StaticMeshComponent)
                          if c.get_name() == item.get("component")), None)
        if not component:
            conflicts.append({"item": item, "reason": "component_missing"})
            continue
        index = int(item.get("slot_index", -1))
        current = component.get_material(index) if 0 <= index < component.get_num_materials() else None
        current_path = current.get_path_name() if current else None
        original_path = item.get("previous_material")
        target_path = item.get("film_material")
        if current_path == original_path:
            already_original.append(item)
            continue
        if current_path != target_path:
            conflicts.append({"item": item, "reason": "current_material_changed", "current_material": current_path})
            continue
        original = unreal.load_asset(original_path) if original_path else None
        if not original:
            conflicts.append({"item": item, "reason": "original_material_missing"})
            continue
        component.set_material(index, original)
        readback = component.get_material(index)
        if readback and readback.get_path_name() == original_path:
            restored.append(item)
        else:
            conflicts.append({"item": item, "reason": "restore_readback_failed"})

    report["restore_requested"] = True
    report["restore_readback_pass"] = not conflicts
    report["restored_count"] = len(restored)
    report["already_original_count"] = len(already_original)
    report["restore_conflicts"] = conflicts
    report["map_saved"] = False
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({
        "restore_readback_pass": report["restore_readback_pass"],
        "restored_count": len(restored),
        "already_original_count": len(already_original),
        "restore_conflicts": conflicts,
        "map_saved": False,
    }, separators=(",", ":")))
    return report


if __name__ == "__main__":
    run(apply=False)
