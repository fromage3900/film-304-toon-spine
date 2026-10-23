# Pull the cast into a tight group right beside Dana so the known-good
# authored camera (Film_Cam_OfficeMedium) actually frames them.

import unreal

TARGETS = {
    "Film_Cast_David":  70.0,
    "Film_Cast_Sam":    -80.0,
    "Film_Cast_Spider": -160.0,
}
DANA = "Film_Subject_Dana"


def log(m):
    unreal.log("[CastTighten] " + str(m))


def find(prefix):
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        if a.get_actor_label().startswith(prefix):
            return a
    return None


dana = find(DANA)
if dana is None:
    raise RuntimeError("no Dana in level")
dloc = dana.get_actor_location()
dyaw = dana.get_actor_rotation().yaw
log("dana loc=[%.1f %.1f %.1f] yaw=%.1f" % (dloc.x, dloc.y, dloc.z, dyaw))

for a in unreal.EditorLevelLibrary.get_all_level_actors():
    lbl = a.get_actor_label()
    if lbl in TARGETS:
        loc = a.get_actor_location()
        a.set_actor_location(unreal.Vector(dloc.x + TARGETS[lbl], dloc.y, dloc.z), False, False)
        a.set_actor_rotation(unreal.Rotator(0, dyaw, 0), False)
        log("%s -> x=%.1f yaw=%.1f" % (lbl, dloc.x + TARGETS[lbl], dyaw))
