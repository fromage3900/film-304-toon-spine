import unreal

LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
loaded = LES.load_level("/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office")
print(f"Loaded L_Film_Office: {loaded}")
