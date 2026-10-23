import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for a in eas.get_all_level_actors():
    if a.get_actor_label() == "PPV_StorybookOutline":
        s = a.settings
        ppm = s.get_editor_property("weighted_blendables")
        print("Weighted Blendables array:", ppm.array)
        for b in ppm.array:
            w = b.get_editor_property("weight")
            obj = b.get_editor_property("object")
            print(f"  Blendable: {obj.get_name() if obj else 'None'}, Weight: {w}")
