import unreal
w = unreal.EditorLevelLibrary.get_editor_world()
print("world:", w.get_name() if w else None)
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    lbl = a.get_actor_label()
    if lbl.startswith("Cam_") or lbl in ("BR_Counter", "BR_Shell", "BR_Shelf", "LGT_Sun", "LGT_Sky"):
        loc = a.get_actor_location()
        fwd = a.get_actor_forward_vector()
        print("%-20s %-18s loc=(%7.1f,%7.1f,%7.1f) fwd=(%5.2f,%5.2f,%5.2f)"
              % (lbl, a.get_class().get_name(), loc.x, loc.y, loc.z, fwd.x, fwd.y, fwd.z))
        try:
            o, e = a.get_actor_bounds(False)
            print("      bounds origin=(%7.1f,%7.1f,%7.1f) extent=(%6.1f,%6.1f,%6.1f)"
                  % (o.x, o.y, o.z, e.x, e.y, e.z))
        except Exception as ex:
            print("      bounds n/a:", ex)
print("LAYOUT_OK")
