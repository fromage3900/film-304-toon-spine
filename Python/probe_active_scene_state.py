import unreal

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
print("CURRENT_WORLD:", world.get_path_name())

eal = unreal.EditorAssetLibrary
maps = eal.list_assets("/Game/Maps", recursive=True, include_folder=False)
for m in maps:
    if any(k in m for k in ["Office", "Assembly", "Universal", "Film"]):
        print("FOUND_MAP:", m)
