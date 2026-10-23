import unreal

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

print("=== CLEARING ALL OBJECTS COVERING USER CAMERAS ===")

# 1. Delete the 4 spawned cameras that were cluttering the scene
cams_to_remove = [
    "CineCam_Hero_CubicleEstablishing",
    "CineCam_Hero_CubicleTrench",
    "CineCam_Hero_BreakroomEstablishing",
    "CineCam_Hero_CorridorWatercooler"
]
for a in EAS.get_all_level_actors():
    if a.get_actor_label() in cams_to_remove:
        EAS.destroy_actor(a)
        print(f"Removed extra camera: {a.get_actor_label()}")

# 2. Delete corridor props that were blocking David and Dana's views
props_to_remove = [
    "SM_P_Whiteboard_Corridor",
    "SM_P_WallClock_Corridor"
]
for a in EAS.get_all_level_actors():
    if a.get_actor_label() in props_to_remove:
        EAS.destroy_actor(a)
        print(f"Removed blocking prop: {a.get_actor_label()}")

# 3. Destroy HDA_Cubicle_Hive and the ceiling grid that was in the camera path
for a in EAS.get_all_level_actors():
    lbl = a.get_actor_label()
    if lbl in ["HDA_Cubicle_Hive", "Houdini_Ceiling_HVAC_Grid"] or lbl.startswith("Light_Troffer_CAD_"):
        EAS.destroy_actor(a)
        print(f"Removed camera-blocking actor: {lbl}")

# Also check HDA_Breakroom_Sanctuary
for a in EAS.get_all_level_actors():
    if a.get_actor_label() == "HDA_Breakroom_Sanctuary":
        EAS.destroy_actor(a)
        print("Removed HDA_Breakroom_Sanctuary to clear sightlines.")

LES.save_current_level()
print("Saved clean level with completely cleared camera paths.")
