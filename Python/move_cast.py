# Move the cast into a tight row inside the room, beside Dana.

import unreal

TARGETS = {
    "Film_Cast_David":  90.0,
    "Film_Cast_Sam":    -90.0,
    "Film_Cast_Spider": -215.0,
}


def log(m):
    unreal.log("[CastMove] " + str(m))


for a in unreal.EditorLevelLibrary.get_all_level_actors():
    lbl = a.get_actor_label()
    if lbl in TARGETS:
        loc = a.get_actor_location()
        a.set_actor_location(unreal.Vector(TARGETS[lbl], loc.y, loc.z), False, False)
        log("%s -> x=%.1f" % (lbl, TARGETS[lbl]))
    elif lbl.startswith("Film_Subject_Dana"):
        log("dana stays at x=%.1f" % a.get_actor_location().x)
