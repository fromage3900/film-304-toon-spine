import unreal
w = unreal.EditorLevelLibrary.get_editor_world()
print("editor_world:", w.get_name() if w else None)
acts = unreal.EditorLevelLibrary.get_all_level_actors()
print("count:", len(acts))
for a in acts:
    lbl = a.get_actor_label()
    if lbl.startswith("Film_") or lbl.startswith("SESSION_") or "Cam" in lbl:
        print("   %-44s %s" % (lbl, a.get_class().get_name()))
print("all labels:", sorted(a.get_actor_label() for a in acts))
print("DIAG_OK")
