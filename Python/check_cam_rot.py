import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_Cam_Showcase_Ensemble_v01":
        print("Camera loc:", a.get_actor_location())
        print("Camera rot:", a.get_actor_rotation())
