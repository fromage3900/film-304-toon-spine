import unreal
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
unreal.log(f"[CurrentMap] Active map is: {w.get_path_name() if w else None}")
