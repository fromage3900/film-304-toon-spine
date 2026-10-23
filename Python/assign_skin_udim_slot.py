# Point the cast mesh's SKIN slot at the 3-tile UDIM skin instance.
# Universal takes one Albedo and Dana's skin is a 3-tile UDIM set (1001 head,
# 1002 arms, 1003 legs, nothing at u>=3), so the skin slot is the one slot that
# cannot be served by a single-texture bind. The intake lane's UDIM master
# already binds all three tiles and drives the film's own ToonProfile.

import unreal

MESH = "/Game/Staging/DanaFilmRuntime_20261016/Dana_CleanSkin_v08"
SKIN_MI = "/Game/Materials/Instances/OneDriveRigs_20261016/MI_OneDriveRigs_Dana_Skin_20261016"


def log(m):
    unreal.log("[SkinSlot] " + str(m))


def prop(o, n):
    try:
        return o.get_editor_property(n)
    except Exception:                                        # noqa: BLE001
        return None


def main():
    mesh = unreal.load_asset(MESH)
    if mesh is None:
        raise RuntimeError("cannot load " + MESH)
    mi = unreal.load_asset(SKIN_MI)
    if mi is None:
        raise RuntimeError("cannot load " + SKIN_MI)

    mats = prop(mesh, "materials") or []
    log("slots=%d" % len(mats))
    target = -1
    for i, sm in enumerate(mats):
        name = str(prop(sm, "material_slot_name") or "")
        cur = prop(sm, "material_interface")
        cur_path = str(cur.get_path_name()) if cur else "None"
        log("slot %d: %s -> %s" % (i, name, cur_path.split("/")[-1]))
        if "skin" in name.lower():
            target = i
    if target < 0:
        raise RuntimeError("no skin slot found")

    new_mats = []
    for i, sm in enumerate(mats):
        if i == target:
            sm.set_editor_property("material_interface", mi)
        new_mats.append(sm)
    mesh.set_editor_property("materials", new_mats)
    saved = unreal.EditorAssetLibrary.save_asset(MESH)
    log("skin slot %d -> %s, saved=%s" % (target, SKIN_MI.split("/")[-1], saved))

    # read back
    check = prop(unreal.load_asset(MESH), "materials") or []
    cur = prop(check[target], "material_interface")
    log("readback slot %d = %s" % (target, str(cur.get_path_name()).split("/")[-1] if cur else "None"))


main()
