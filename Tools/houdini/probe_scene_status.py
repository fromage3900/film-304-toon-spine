import unreal

print("=== LIVE SCENE STATUS PROBE ===")
ELL = unreal.EditorLevelLibrary
world = ELL.get_editor_world()
print(f"World: {world.get_path_name() if world else 'None'}")

folders = {}
for a in ELL.get_all_level_actors():
    f = str(a.get_folder_path()) if hasattr(a, 'get_folder_path') else 'None'
    folders.setdefault(f, []).append(a.get_actor_label())

for f, alist in sorted(folders.items()):
    print(f"[{f}]: {len(alist)} actors")

print("\n--- Houdini Engine Actors ---")
for a in ELL.get_all_level_actors():
    if "HDA" in a.get_actor_label() or "Houdini" in a.get_actor_label():
        loc = a.get_actor_location()
        print(f"Actor: {a.get_actor_label()} at ({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f})")
        for c in a.get_components_by_class(unreal.ActorComponent):
            c_name = c.get_class().get_name()
            if "Mesh" in c_name or "Houdini" in c_name:
                mesh_name = "None"
                if hasattr(c, "get_editor_property"):
                    try:
                        m = c.get_editor_property("static_mesh")
                        if m:
                            mesh_name = m.get_name()
                    except Exception:
                        pass
                inst_cnt = c.get_instance_count() if hasattr(c, "get_instance_count") else 1
                print(f"   Component: {c.get_name()} ({c_name}) | Mesh: {mesh_name} | Count: {inst_cnt}")
