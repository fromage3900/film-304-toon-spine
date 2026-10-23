# Verification camera: park it right in front of one cast member and let the
# caller fire a still. Close enough to judge materials, not a composed shot.

import unreal

LABEL = "SESSION_CAM_Verify"


def log(m):
    unreal.log("[VerifyCam] " + str(m))


def find_by_label(prefix):
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        if a.get_actor_label() == prefix:
            return a
    return None


def main():
    subject = None
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        if a.get_actor_label() == "Film_Cast_David":
            subject = a
    if subject is None:
        raise RuntimeError("no Film_Cast_David in level")
    loc = subject.get_actor_location()
    cam = find_by_label(LABEL)
    spot = unreal.Vector(loc.x, loc.y - 230.0, loc.z + 110.0)
    if cam is None:
        cam = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.CineCameraActor, spot, unreal.Rotator(-6.0, 90.0, 0.0))
        cam.set_actor_label(LABEL)
        cam.set_folder_path("FilmCast")
    else:
        cam.set_actor_location(spot, False, False)
        cam.set_actor_rotation(unreal.Rotator(-6.0, 90.0, 0.0), False)
    comp = cam.get_component_by_class(unreal.CineCameraComponent)
    if comp is not None:
        comp.set_editor_property("current_focal_length", 50.0)
    log("verify cam at %s -> %s" % ([round(v, 1) for v in (spot.x, spot.y, spot.z)],
                                    subject.get_actor_label()))


main()
