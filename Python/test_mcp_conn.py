import unreal
print("MCP Connection OK! Active World:", unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name())
