import unreal

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

cleaned = 0
for a in EAS.get_all_level_actors():
    lbl = a.get_actor_label()
    if "_instancer_" in lbl:
        EAS.destroy_actor(a)
        cleaned += 1

print(f"Cleaned {cleaned} test instancer actors.")
LES.save_current_level()
