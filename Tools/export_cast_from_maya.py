"""Export one Film 304 cast rig from its Maya source to a deform-only FBX.

Generalised from the proven Dana exporter (Tools/export_dana_film_from_maya.py):
the same visibility / intermediate / skinCluster discipline, the same refusal to
invent weights, and the same "source is opened and never saved" rule. The
per-character configuration lives in specs/cast/cast_rig_sources.v1.json.

Maya's standalone interpreter is single-scene, so this runs one character per
process:

    mayapy Tools/export_cast_from_maya.py Spider

The exporter refuses to write when the rig has no visible bound render geometry
or when the required body mesh is missing or unbound. A report is written for
every run, including refusals, so a blocked rig is evidence rather than silence.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "specs/cast/cast_rig_sources.v1.json"


def load_spec() -> dict:
    return json.loads(SPEC.read_text(encoding="utf-8"))


def export(character: str, spec: dict) -> dict:
    import maya.cmds as cmds
    import maya.mel as mel

    config = spec["characters"].get(character)
    if config is None:
        raise KeyError("character not in %s: %s" % (SPEC.name, character))

    intake = Path(spec["intake_root"])
    source = intake / config["source"]
    output = ROOT / spec["export_root"] / character / config["output"]
    report_path = ROOT / spec["report_root"] / ("export_%s.json" % character.lower())

    if not source.is_file():
        raise FileNotFoundError(str(source))
    if output.exists():
        raise RuntimeError(
            "export already exists, preserved untouched: %s "
            "(choose a new output name for a revision)" % output)

    helper = re.compile(config["helper_regex"], re.I)
    required_body = re.compile(config["required_body_regex"], re.I)
    # A mesh matching this is exported even when the artist left visibility off.
    # This is an explicit, named exception recorded in the report - it is never
    # a blanket "ignore visibility", because a hidden mesh is usually hidden on
    # purpose (an unbound base cage, a work-in-progress toggle).
    include_hidden = re.compile(config.get("include_hidden_regex", r"(?!x)x"), re.I)
    material_roles = config.get("material_roles") or []

    cmds.file(str(source), open=True, force=True, executeScriptNodes=False, ignoreVersion=True)
    scene = source.stem
    min_time = cmds.playbackOptions(query=True, minTime=True)
    max_time = cmds.playbackOptions(query=True, maxTime=True)
    cmds.currentTime(min_time, edit=True)

    def is_visible(node: str) -> bool:
        current = node
        while current:
            if (cmds.attributeQuery("visibility", node=current, exists=True)
                    and not cmds.getAttr(current + ".visibility")):
                return False
            parents = cmds.listRelatives(current, parent=True, fullPath=True) or []
            current = parents[0] if parents else None
        return True

    # Optional: give each mesh a named material so the FBX carries distinct
    # slots. Without this the legacy importer collapses everything into the
    # Maya shading-group names ("blinn2", "blinn4") and separate parts of the
    # character - an eye and a fang - end up sharing one slot.
    #
    # forceElement needs a SET, not a shader: a shadingGroup is created
    # explicitly, named for the role, and driven by a throwaway lambert. The
    # scene is never saved, so the throwaway material disappears with it.
    forced_materials: dict[str, str] = {}
    for role in material_roles:
        shader = cmds.shadingNode("lambert", asShader=True, name=role["material"] + "_lambert")
        group = cmds.sets(renderable=True, noSurfaceShader=True, empty=True,
                          name=role["material"] + "SG")
        cmds.connectAttr(shader + ".outColor", group + ".surfaceShader", force=True)
        forced_materials[re.compile(role["pattern"], re.I)] = group

    def material_for(shape_name: str):
        for pattern, group in forced_materials.items():
            if pattern.search(shape_name):
                return group
        return None

    def _force_visible_chain(transform):
        """Break any driven visibility on this node and its ancestors, then
        show them. Returns the nodes actually changed."""
        changed = []
        node = transform
        while node:
            if cmds.attributeQuery("visibility", node=node, exists=True):
                for plug in (cmds.listConnections(node + ".visibility",
                                                 source=True, destination=False,
                                                 plugs=True) or []):
                    try:
                        cmds.disconnectAttr(plug, node + ".visibility")
                    except Exception:                              # noqa: BLE001
                        pass
                try:
                    if not cmds.getAttr(node + ".visibility"):
                        cmds.setAttr(node + ".visibility", True)
                        changed.append(node.rsplit("|", 1)[-1])
                except Exception:                                  # noqa: BLE001
                    pass
            node = (cmds.listRelatives(node, parent=True, fullPath=True) or [None])[0]
        return changed

    render_meshes = []
    excluded = []
    influences: set[str] = set()
    visibility_overridden = []

    for shape in cmds.ls(type="mesh", long=True) or []:
        parents = cmds.listRelatives(shape, parent=True, fullPath=True) or []
        if not parents:
            continue
        transform = parents[0]
        short = transform.rsplit("|", 1)[-1].rsplit(":", 1)[-1]
        intermediate = bool(cmds.getAttr(shape + ".intermediateObject"))
        visible = is_visible(shape)
        forced_hidden = (not visible) and bool(include_hidden.search(short))

        history = cmds.listHistory(shape, pruneDagObjects=True) or []
        skins = cmds.ls(history, type="skinCluster") or []

        if intermediate or helper.search(short) or (not visible and not forced_hidden):
            excluded.append({
                "mesh": transform, "short": short,
                "reason": ("intermediate" if intermediate
                           else "helper" if helper.search(short) else "hidden"),
            })
            continue
        if not skins:
            excluded.append({"mesh": transform, "short": short, "reason": "unbound_no_skinCluster"})
            continue

        shader = material_for(short)
        if shader is not None:
            # sets() wants the TRANSFORM, not the shape, and forceElement wants
            # the shading group; Maya creates the shadingEngine from it.
            cmds.sets(transform, edit=True, forceElement=shader)
        if forced_hidden:
            # Selecting an invisible node is not enough. The FBX carries the
            # node's Visibility flag, and a downstream reader that honours it
            # (Blender's importer does) drops the mesh entirely - which is how
            # the body vanished from the consolidated file on the first pass.
            #
            # On these rigs the flag is DRIVEN by a rig expression ("hide the
            # body while working on clothes"), so the attribute arrives locked
            # and setAttr raises. The driving connection has to be broken
            # first, on the node and every ancestor that could be hiding it.
            # The scene is never saved, so the rig is untouched on disk.
            _force_visible_chain(transform)
            visibility_overridden.append(short)

        found = {j for skin in skins for j in (cmds.skinCluster(skin, query=True, influence=True) or [])}
        influences |= found
        render_meshes.append({
            "mesh": transform, "short": short,
            "triangles": cmds.polyEvaluate(shape, triangle=True),
            "skin_clusters": skins,
            "influence_count": len(found),
            "forced_material": (shader.split("|")[-1] if shader else None),
            "visibility_overridden": forced_hidden,
            "shading_groups": cmds.listConnections(shape, type="shadingEngine") or [],
        })

    # Include only the deformation hierarchy above the influences. Control and
    # constraint networks are never selected, so the FBX exporter cannot follow
    # them into the file.
    joints = set(influences)
    for joint in list(joints):
        parents = cmds.listRelatives(joint, parent=True, fullPath=True) or []
        while parents and cmds.nodeType(parents[0]) == "joint":
            joints.add(parents[0])
            parents = cmds.listRelatives(parents[0], parent=True, fullPath=True) or []

    # Match on the SHORT name: the spec's patterns are anchored (^...$) so they
    # must not be tested against the full DAG path.
    bodies = [m for m in render_meshes if required_body.search(m["short"])]
    problems = []
    if not render_meshes:
        problems.append("no visible bound render geometry was found in " + scene)
    if not influences or not joints:
        problems.append("no deform joints resolved; the meshes are not skinned to a joint hierarchy")
    if not bodies:
        problems.append(
            "no mesh matched the required body pattern %r; found %d visible bound meshes: %s"
            % (config["required_body_regex"], len(render_meshes),
               sorted(m["short"] for m in render_meshes)[:12]))

    report = {
        "schema": "humber-cast-maya-export.v1",
        "character": character,
        "source": str(source),
        "source_bytes": source.stat().st_size,
        "output": str(output),
        "scene": scene,
        "playback_range": [min_time, max_time],
        "render_meshes": render_meshes,
        "render_mesh_count": len(render_meshes),
        "render_triangle_total": sum(m["triangles"] or 0 for m in render_meshes),
        "excluded": excluded,
        "excluded_count": len(excluded),
        "unique_influences": len(influences),
        "selected_joint_count": len(joints),
        "body_meshes_matched": [m["short"] for m in bodies],
        "visibility_overridden": visibility_overridden,
        "visibility_override_rule": config.get("include_hidden_regex", None),
        "forced_material_roles": [r["material"] for r in material_roles],
        "problems": problems,
        "result": "blocked" if problems else "exported",
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)

    if problems:
        report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        raise RuntimeError("; ".join(problems))

    cmds.loadPlugin("fbxmaya", quiet=True)
    mel.eval("FBXResetExport;")
    for statement in (
        "FBXExportSkins -v true;",
        "FBXExportShapes -v true;",
        "FBXExportConstraints -v false;",
        "FBXExportInputConnections -v false;",
        "FBXExportBakeComplexAnimation -v true;",
        "FBXExportCameras -v false;",
        "FBXExportLights -v false;",
        "FBXExportEmbeddedTextures -v false;",
    ):
        mel.eval(statement)
    mel.eval("FBXExportBakeComplexStart -v %s;" % min_time)
    mel.eval("FBXExportBakeComplexEnd -v %s;" % max_time)

    cmds.select([m["mesh"] for m in render_meshes] + sorted(joints), replace=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    mel.eval('FBXExport -f "%s" -s;' % output.as_posix())

    import hashlib
    digest = hashlib.sha256()
    with output.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    report["result"] = "exported_pending_ue_import"
    report["output_bytes"] = output.stat().st_size
    report["output_sha256"] = digest.hexdigest()
    report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print("EXPORT_JSON" + json.dumps(report, default=str))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: mayapy Tools/export_cast_from_maya.py <Character>")
    import maya.standalone
    maya.standalone.initialize(name="python")
    try:
        export(sys.argv[1], load_spec())
    finally:
        maya.standalone.uninitialize()