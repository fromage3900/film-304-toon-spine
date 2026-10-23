import unreal

print("==================================================================")
print("=== DEEP ARCHITECTURAL AUDIT & CAD COORDINATE SURVEY ===")
print("==================================================================")

ELL = unreal.EditorLevelLibrary
world = ELL.get_editor_world()

print("\n--- HERO CAST LOCATIONS ---")
for a in ELL.get_all_level_actors():
    f = str(a.get_folder_path()) if hasattr(a, 'get_folder_path') else ''
    lbl = a.get_actor_label()
    if 'Cast' in f or 'FilmCast' in f or any(name in lbl for name in ['Dana', 'David', 'Sam', 'Spider']):
        loc = a.get_actor_location()
        rot = a.get_actor_rotation()
        print(f"  {lbl:30s} | Loc: ({loc.x:7.1f}, {loc.y:7.1f}, {loc.z:7.1f}) | Yaw: {rot.yaw:6.1f} | Folder: {f}")

print("\n--- ARCHITECTURAL ENVELOPE (Floors, Walls, Windows, Columns) ---")
for a in ELL.get_all_level_actors():
    lbl = a.get_actor_label()
    if any(k in lbl.lower() for k in ['floor', 'wall', 'window', 'ceiling', 'column', 'blind', 'glass', 'room', 'office']):
        loc = a.get_actor_location()
        origin, box_extent = a.get_actor_bounds(False)
        print(f"  {lbl:35s} | Loc: ({loc.x:7.1f}, {loc.y:7.1f}, {loc.z:7.1f}) | Bounds Origin: ({origin.x:7.1f}, {origin.y:7.1f}, {origin.z:7.1f}) | Extent: ({box_extent.x:6.1f}, {box_extent.y:6.1f}, {box_extent.z:6.1f})")

print("\n--- HOUDINI ENGINE PARAMETERS & COOK LOG FOR HDA_Breakroom_Sanctuary ---")
api = unreal.HoudiniPublicAPIBlueprintLib.get_api()
for a in ELL.get_all_level_actors():
    lbl = a.get_actor_label()
    if 'HDA' in lbl:
        loc = a.get_actor_location()
        print(f"\nHDA Actor: {lbl} at ({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f})")
        w = api.get_wrapper_for_actor(a)
        if w:
            print(f"  Asset name: {w.get_asset().get_name() if w.get_asset() else 'None'}")
            print(f"  Cooking status: {w.get_cooking_status()}")
            params = w.get_parameter_names()
            print(f"  Parameters ({len(params)}): {params}")
            for p in params:
                val = w.get_parameter_value(p)
                print(f"    - {p} = {val}")
            last_err = w.get_last_error_message()
            print(f"  Last error message: '{last_err}'")
            comps = a.get_components_by_class(unreal.ActorComponent)
            print(f"  Component count: {len(comps)}")
            for c in comps:
                print(f"    - Component: {c.get_name()} ({c.get_class().get_name()})")
