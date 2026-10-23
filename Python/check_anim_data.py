import unreal

dana_actor = None
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_Subject_Dana_v08_CleanSkin":
        dana_actor = a
        break

skc = dana_actor.get_component_by_class(unreal.SkeletalMeshComponent)
anim_data = skc.get_editor_property("animation_data")
print("anim_data attrs:", [p for p in dir(anim_data) if not p.startswith("_")])
