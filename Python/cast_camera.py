# Spawn a session camera framing the whole cast line, for verification shots.
# Session-only: spawned and left alive for the session, never saved into a map.

import unreal

LABEL = "SESSION_CAM_Cast"
CENTER = unreal.Vector(-60.0, -63.10, 90.0)
DIST = -170.0


def log(m):
    unreal.log("[CastCam] " + str(m))


def find_by_label(prefix):
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        if a.get_actor_label() == prefix:
            return a
    return None


def main():
    cam = find_by_label(LABEL)
    if cam is None:
        loc = unreal.Vector(CENTER.x, CENTER.y + DIST, CENTER.z + 45.0)
        cam = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.CineCameraActor, loc, unreal.Rotator(-8.0, 90.0, 0.0))
        if cam is None:
            raise RuntimeError("camera spawn failed")
        cam.set_actor_label(LABEL)
        cam.set_folder_path("FilmCast")
    else:
        cam.set_actor_location(unreal.Vector(CENTER.x, CENTER.y + DIST, CENTER.z + 45.0),
                               False, False)
        cam.set_actor_rotation(unreal.Rotator(-8.0, 90.0, 0.0), False)

    comp = cam.get_component_by_class(unreal.CineCameraComponent)
    if comp is not None:
        comp.set_editor_property("current_focal_length", 24.0)
    log("camera ready: %s at %s" % (LABEL, [round(v, 1) for v in (
        cam.get_actor_location().x, cam.get_actor_location().y, cam.get_actor_location().z)]))

    # how far apart the cast actually is, for framing sanity
    xs = []
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        if a.get_actor_label().startswith(("Film_Subject_Dana", "Film_Cast_")):
            xs.append(a.get_actor_location().x)
    log("cast x-range: %.1f .. %.1f (%d actors)" % (min(xs), max(xs), len(xs)) if xs else "no cast")


main()
