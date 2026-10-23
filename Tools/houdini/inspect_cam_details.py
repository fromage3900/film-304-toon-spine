import unreal

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

print("=== ALL CAMERAS IN LEVEL ===")
for a in EAS.get_all_level_actors():
    lbl = a.get_actor_label()
    if isinstance(a, (unreal.CineCameraActor, unreal.CameraActor)) or "cam" in lbl.lower():
        loc = a.get_actor_location()
        rot = a.get_actor_rotation()
        folder = str(a.get_folder_path()) if hasattr(a, "get_folder_path") else ""
        print(f"Camera: {lbl:35s} | Folder: {folder:30s} | Loc: ({loc.x:7.1f}, {loc.y:7.1f}, {loc.z:7.1f}) | Rot: (P={rot.pitch:5.1f}, Y={rot.yaw:6.1f})")

print("\n=== HDA_Cubicle_Hive DETAILED BOUNDS ===")
for a in EAS.get_all_level_actors():
    if a.get_actor_label() == "HDA_Cubicle_Hive":
        loc = a.get_actor_location()
        print(f"HDA_Cubicle_Hive Actor Loc: {loc}")
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            sm = c.get_editor_property("static_mesh")
            cnt = c.get_instance_count()
            print(f"  Component: {sm.get_name() if sm else 'None'} ({cnt} instances)")
            for i in range(min(cnt, 2)):
                t = c.get_instance_transform(i, True) # world transform
                print(f"    - inst {i} World Loc: ({t.translation.x:.1f}, {t.translation.y:.1f}, {t.translation.z:.1f})")
