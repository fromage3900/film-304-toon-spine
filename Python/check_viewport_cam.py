import unreal

loc, rot = unreal.EditorLevelLibrary.get_level_viewport_camera_info()
print("Current viewport camera:", loc, rot)
