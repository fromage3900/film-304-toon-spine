import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
sam = None
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_Cast_Sam":
        sam = a
        break

if sam:
    skc = sam.get_component_by_class(unreal.SkeletalMeshComponent)
    mode = skc.get_editor_property("animation_mode")
    data = skc.get_editor_property("animation_data")
    anim = data.anim_to_play if data else None
    print(f"Sam: mode={mode} anim={anim.get_name() if anim else 'None'} playing={data.saved_playing if data else 'N/A'}")
