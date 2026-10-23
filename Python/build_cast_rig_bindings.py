"""Bind the Film 304 cast rigs to their toon material instances.

Reads specs/cast/cast_rigs.v1.json and, for every character whose mesh exists in
the project, assigns one material instance per semantic slot role and verifies
the assignment by reading the asset back. Roles are matched against slot names
after normalisation, so a re-export that renames a slot still binds; any slot
that matches no role is reported rather than silently left null.

The builder refuses to touch anything the spec does not name. It creates a
missing instance only when the spec declares it under instances_to_create, so a
typo in a tint cannot invent a new material in the content tree.

Run inside the editor:

    UnrealEditor-Cmd.exe HumberToonShader.uproject \
      -ExecutePythonScript="Python/build_cast_rig_bindings.py" -stdout -unattended

or from the editor's Python console. The report is the evidence:
Saved/Audit/CastRigs_20261016/cast_bindings.json
"""
from __future__ import annotations

import json
import re
import sys
import traceback
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "specs/cast/cast_rigs.v1.json"
REPORT_PATH = ROOT / "Saved/Audit/CastRigs_20261016/cast_bindings.json"

EAL = unreal.EditorAssetLibrary
ME = unreal.MaterialEditingLibrary
ASSET_TOOLS = unreal.AssetToolsHelpers.get_asset_tools()


def normalise(slot_name: str) -> str:
    """Reduce a Maya/UE slot name to a comparable token.

    danaSkin_mat -> danaskin ;  wolfSpider_fang_L_GEO -> wolfspiderfangl
    """
    token = slot_name.strip().lower()
    token = re.sub(r"_(mat|sg|shader|shd|geo|geometery|surface)$", "", token)
    return re.sub(r"[^a-z0-9]", "", token)


def ensure_dir(path: str) -> None:
    if not EAL.does_directory_exist(path):
        EAL.make_directory(path)


def save(asset) -> None:
    if not EAL.save_loaded_asset(asset, only_if_is_dirty=False):
        raise RuntimeError("save failed: " + asset.get_path_name())


def ensure_instance(name: str, declaration: dict, spec: dict) -> str:
    """Create the instance the spec declares, or verify the one already there."""
    instance_dir = spec["instance_dir"]
    path = instance_dir + "/" + name
    parent_path = spec["masters"][declaration["parent_master"]]

    parent = EAL.load_asset(parent_path)
    if parent is None:
        raise RuntimeError("missing parent master " + parent_path)

    if EAL.does_asset_exist(path):
        instance = EAL.load_asset(path)
        if instance is None:
            raise RuntimeError("instance exists but will not load: " + path)
        created = False
    else:
        ensure_dir(instance_dir)
        instance = ASSET_TOOLS.create_asset(
            name, instance_dir, unreal.MaterialInstanceConstant,
            unreal.MaterialInstanceConstantFactoryNew())
        if instance is None:
            raise RuntimeError("could not create instance " + path)
        created = True

    if ME.set_material_instance_parent(instance, parent) is False:
        raise RuntimeError("could not set parent on " + path)
    for key, value in declaration["overrides"].items():
        if isinstance(value, (list, tuple)):
            ME.set_material_instance_vector_parameter_value(
                instance, key, unreal.LinearColor(*value))
        else:
            ME.set_material_instance_scalar_parameter_value(instance, key, float(value))
    ME.update_material_instance(instance)
    save(instance)

    # readback: the parent and every override must survive the save
    verify = EAL.load_asset(path)
    read_parent = verify.get_editor_property("parent")
    if read_parent is None or read_parent.get_path_name() != parent.get_path_name():
        raise RuntimeError("parent readback mismatch: " + path)
    for key, value in declaration["overrides"].items():
        if isinstance(value, (list, tuple)):
            actual = ME.get_material_instance_vector_parameter_value(verify, key)
            got = tuple(round(float(v), 4) for v in (actual.r, actual.g, actual.b, actual.a))
            if got != tuple(round(float(v), 4) for v in value):
                raise RuntimeError("vector readback mismatch %s.%s: %s != %s" % (path, key, got, value))
        else:
            actual = ME.get_material_instance_scalar_parameter_value(verify, key)
            if round(float(actual), 4) != round(float(value), 4):
                raise RuntimeError("scalar readback mismatch %s.%s" % (path, key))
    return {"path": path, "created": created, "parent": parent.get_path_name()}


def resolve_roles(character: str, entry: dict, slot_names: list[str]) -> tuple[dict, list]:
    """Map slot name -> role key. Longest pattern wins so 'danaEye' does not
    swallow 'danaEyeInt'.

    One role may legitimately claim several slots — gum and tongue are both
    mouth_interior and share one instance. What is ambiguous, and reported, is
    two different roles competing for the same slot.
    """
    claims: list[tuple[int, str, str]] = []
    for role, config in entry["roles"].items():
        for pattern in config["patterns"]:
            claims.append((len(normalise(pattern)), role, normalise(pattern)))
    claims.sort(reverse=True)

    final: dict[str, str] = {}
    conflicts = []
    for slot in slot_names:
        token = normalise(slot)
        best_length, best_roles = None, []
        for length, role, pattern in claims:
            if not pattern or pattern not in token:
                continue
            if best_length is None or length > best_length:
                best_length, best_roles = length, [role]
            elif length == best_length and role not in best_roles:
                best_roles.append(role)
        if not best_roles:
            continue
        if len(best_roles) > 1:
            conflicts.append({
                "slot": slot,
                "roles": best_roles,
                "resolution": "no role assigned; declare a more specific pattern in the spec",
            })
            continue
        final[slot] = best_roles[0]
    return final, conflicts


def bind_character(name: str, entry: dict, spec: dict) -> dict:
    mesh_path = entry.get("mesh")
    result = {
        "mesh": mesh_path,
        "declared_status": entry.get("status"),
        "source_rig": entry.get("source_rig"),
    }

    if not mesh_path:
        result["result"] = "blocked"
        result["blocker"] = "spec names no mesh path for this character"
        return result

    mesh = EAL.load_asset(mesh_path)
    if mesh is None:
        result["result"] = "awaiting_import"
        result["blocker"] = (
            "mesh not in the project yet; import %s as a skeletal mesh first"
            % entry.get("fbx", "the exported FBX"))
        return result

    slots = list(mesh.get_editor_property("materials") or [])
    slot_names = [str(s.material_slot_name) for s in slots]
    result["slot_names"] = slot_names
    result["slot_count"] = len(slots)
    if entry.get("slot_count_expected") and entry["slot_count_expected"] != len(slots):
        result["result"] = "blocked"
        result["blocker"] = (
            "spec expects %d slots, asset has %d; the slot map is stale"
            % (entry["slot_count_expected"], len(slots)))
        return result

    assigned, conflicts = resolve_roles(name, entry, slot_names)
    result["role_conflicts"] = conflicts

    # every instance a resolved role needs must exist or be declared for creation
    needed = {}
    for role in assigned.values():
        needed.setdefault(role, entry["roles"][role]["instance"])
    resolved_instances = {}
    created_instances = []
    for role, instance_name in needed.items():
        declaration = entry.get("instances_to_create", {}).get(instance_name)
        if EAL.does_asset_exist(spec["instance_dir"] + "/" + instance_name):
            resolved_instances[role] = spec["instance_dir"] + "/" + instance_name
        elif declaration is not None:
            info = ensure_instance(instance_name, declaration, spec)
            resolved_instances[role] = info["path"]
            created_instances.append(info)
        else:
            raise RuntimeError(
                "%s role %s needs %s, which does not exist and is not declared in "
                "instances_to_create" % (name, role, instance_name))
    result["instances_created"] = created_instances
    result["instances_used"] = resolved_instances

    # assign
    mesh.modify()
    new_slots = []
    for slot in slots:
        slot_name = str(slot.material_slot_name)
        role = assigned.get(slot_name)
        if role:
            instance = EAL.load_asset(resolved_instances[role])
            if instance is None:
                raise RuntimeError("instance will not load: " + resolved_instances[role])
            slot.material_interface = instance
            new_slots.append({"slot": slot_name, "role": role,
                              "material": instance.get_path_name()})
        else:
            new_slots.append({"slot": slot_name, "role": None,
                              "material": (slot.material_interface.get_path_name()
                                           if slot.material_interface else None)})
    mesh.set_editor_property("materials", slots)
    save(mesh)

    # readback verification against a fresh load
    verify_mesh = EAL.load_asset(mesh_path)
    verify_slots = list(verify_mesh.get_editor_property("materials") or [])
    verified = [{"slot": str(s.material_slot_name),
                 "material": (s.material_interface.get_path_name().split(".")[0]
                              if s.material_interface else None)}
                for s in verify_slots]
    result["readback"] = verified
    result["assigned_count"] = sum(1 for r in assigned.values())
    result["unmapped_slots"] = [row["slot"] for row in new_slots if row["role"] is None]
    result["null_slots_after"] = [row["slot"] for row in new_slots
                                  if row["material"] is None]
    # A slot can be neither null nor correctly bound and still look fine: the
    # FBX importer fills an unbound slot with WorldGridMaterial, which is not a
    # null but is equally not the film's look. Counted separately so it cannot
    # hide behind a "nulls: []" reading.
    result["engine_default_slots"] = [
        row["slot"] for row in verified
        if row["material"] and "WorldGridMaterial" in row["material"]]

    mismatches = []
    for row in new_slots:
        if row["role"] is None:
            continue
        want = resolved_instances[row["role"]]
        got = next((v["material"] for v in verified if v["slot"] == row["slot"]), None)
        if got != want:
            mismatches.append({"slot": row["slot"], "wanted": want, "got": got})
    result["readback_mismatches"] = mismatches
    # "bound" only means every slot the spec could match got the right
    # instance. It does not mean the mesh is complete - a partial import leaves
    # slots the spec never sees. That is reported, not swallowed.
    result["result"] = "bound" if not mismatches else "failed"
    return result


def main() -> None:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    report = {
        "schema": "humber-cast-rig-bindings.v1",
        "spec": str(SPEC_PATH),
        "characters": {},
        "guardrails": {
            "masters_duplicated": False,
            "slots_outside_spec_touched": False,
            "instances_created_only_when_declared": True,
        },
    }
    try:
        for name, entry in spec["characters"].items():
            unreal.log_warning("cast bindings: %s" % name)
            report["characters"][name] = bind_character(name, entry, spec)
    except Exception as exc:
        report["result"] = "failed"
        report["error"] = str(exc)
        report["traceback"] = traceback.format_exc()
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
        raise

    summary = {n: r.get("result") for n, r in report["characters"].items()}
    report["summary"] = summary
    report["result"] = "complete" if all(v in ("bound", "awaiting_import")
                                          for v in summary.values()) else "partial"
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("cast rig bindings written: %s" % REPORT_PATH)
    print("CAST_BINDINGS_JSON " + json.dumps(report))


if __name__ == "__main__":
    main()