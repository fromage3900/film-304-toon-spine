import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "SM_Ext_Bay3_Barbican":
        print("Live SM_Ext_Bay3_Barbican loc:", a.get_actor_location())
    if a.get_actor_label() == "Film_Cast_Sam":
        skc = a.get_component_by_class(unreal.SkeletalMeshComponent)
        print("Live Sam anim:", skc.get_editor_property("animation_data").anim_to_play.get_name())
