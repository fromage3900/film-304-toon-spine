import unreal

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

print("=== CURRENT LEVEL ACTOR CENSUS (POST-CLEANUP) ===")
folders = {}
for a in EAS.get_all_level_actors():
    f = str(a.get_folder_path()) if hasattr(a, "get_folder_path") else "None"
    folders.setdefault(f, []).append(a.get_actor_label())

for f, alist in sorted(folders.items()):
    print(f"[{f}]: {len(alist)} actors")
    if len(alist) <= 5:
        for name in alist:
            print(f"    - {name}")

print("\n--- HERO CAMERAS STATUS ---")
for a in EAS.get_all_level_actors():
    lbl = a.get_actor_label()
    if lbl in ["SESSION_CAM_Cast", "Film_Cam_OfficeWide", "Film_Cam_OfficeMedium", "Film_Cam_David_DeskSleep", "CineCam_Hero_WindowEstablishing"]:
        loc = a.get_actor_location()
        rot = a.get_actor_rotation()
        print(f"  {lbl:35s} | Loc: ({loc.x:7.1f}, {loc.y:7.1f}, {loc.z:7.1f}) | Rot: (P={rot.pitch:5.1f}, Y={rot.yaw:6.1f})")
