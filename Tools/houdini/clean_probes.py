import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if "__probe" in lbl or lbl in ["Film_Wall_Header_Full2", "Film_BackWall2", "Film_Wall_Seam_Infill2"]:
        print(f"Destroying {lbl}")
        eas.destroy_actor(a)
    elif "EastWall" in lbl or "NorthWall" in lbl:
        print(f"{lbl}: world_loc={a.get_actor_location()}, scale={a.get_actor_scale3d()}")

unreal.EditorLevelLibrary.save_current_level()
