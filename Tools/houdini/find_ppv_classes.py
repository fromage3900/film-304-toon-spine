import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for a in eas.get_all_level_actors():
    cname = a.get_class().get_name()
    lbl = a.get_actor_label()
    if "Post" in cname or "PPV" in lbl or "Volume" in cname:
        print(f"Actor: {lbl:30} | class={cname}")
