# Reusable per-rig skin wiring (2026-10-17).
# Enables VT on freshly re-imported single-tile skin textures and rebinds that
# rig's skin instance to them. Driven by a small JSON request file so the same
# tool serves David, Sam and any later cast member.
#
# Request:  Saved/Audit/MasterConvergence_20261017/_wire_request.json
#           {"tiles": ["T_DavidSkin_Tile1", ...],
#            "instance": "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_David_Skin_20261016",
#            "tex_dir": "/Game/Materials/Textures/OneDriveRigs_20261016/",
#            "param_names": ["BaseColorTile1001", "BaseColorTile1002", "BaseColorTile1003"]}

import json
import os
import unreal

REQ = unreal.Paths.project_dir() + "Saved/Audit/MasterConvergence_20261017/_wire_request.json"
OUT = unreal.Paths.project_dir() + "Saved/Audit/MasterConvergence_20261017/"


def log(m):
    unreal.log("[WireSkin] " + str(m))


def main():
    with open(REQ, encoding="utf-8-sig") as f:
        req = json.load(f)
    tex_dir = req.get("tex_dir", "/Game/Materials/Textures/OneDriveRigs_20261016/")
    tiles = req["tiles"]
    params = req.get("param_names") or ["BaseColorTile1001", "BaseColorTile1002", "BaseColorTile1003"]
    instance = req["instance"]

    # 1. VT on, save, and verify by re-reading
    vt_results = []
    for t in tiles:
        tex = unreal.load_asset(tex_dir + t)
        if tex is None:
            vt_results.append({"tile": t, "error": "missing"})
            continue
        tex.set_editor_property("virtual_texture_streaming", True)
        saved = unreal.EditorAssetLibrary.save_asset(tex_dir + t)
        check = unreal.load_asset(tex_dir + t)
        vt_results.append({
            "tile": t,
            "vt": check.get_editor_property("virtual_texture_streaming"),
            "saved": bool(saved),
        })
        log("%s vt=%s saved=%s" % (t, vt_results[-1]["vt"], saved))

    # 2. rebind the instance and save immediately (an unsaved reparent is
    #    silently reverted by the next package reload)
    inst = unreal.load_asset(instance)
    if inst is None:
        raise RuntimeError("cannot load instance " + instance)
    overrides = []
    lib = unreal.MaterialEditingLibrary
    for pname, tile in zip(params, tiles):
        tex = unreal.load_asset(tex_dir + tile)
        if tex is None:
            log("missing texture for %s" % pname)
            continue
        try:
            lib.set_material_instance_texture_parameter_value(inst, pname, tex)
            overrides.append(pname)
        except Exception as exc:                             # noqa: BLE001
            log("bind %s failed: %s" % (pname, exc))
    saved = unreal.EditorAssetLibrary.save_asset(instance)

    # 3. read back
    check = unreal.load_asset(instance)
    readback = []
    for pname in params:
        cur = lib.get_material_instance_texture_parameter_value(check, pname)
        readback.append("%s = %s" % (pname, cur.get_name() if cur else "None"))

    record = {"instance": instance, "vt": vt_results, "bound": overrides,
              "saved": bool(saved), "readback": [str(r) for r in readback]}
    path = os.path.join(OUT, "_wire_result.json")
    with open(path, "w") as f:
        json.dump(record, f, indent=1)
    for r in readback:
        log("readback %s" % r)
    log("wrote %s" % path)


main()
