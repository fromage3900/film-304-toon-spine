import unreal
import json

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

print("=== AUDITING FOR WORLDGRIDMATERIAL IN ACTIVE LEVEL ===")

worldgrid_findings = []

for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    # Check all mesh components
    comps = a.get_components_by_class(unreal.MeshComponent)
    for comp in comps:
        num_mats = comp.get_num_materials()
        for i in range(num_mats):
            mat = comp.get_material(i)
            mpath = mat.get_path_name() if mat else "None"
            if "worldgrid" in mpath.lower() or "default" in mpath.lower() or mat is None:
                mesh_name = "None"
                if hasattr(comp, "static_mesh") and comp.static_mesh:
                    mesh_name = comp.static_mesh.get_name()
                elif hasattr(comp, "skeletal_mesh") and comp.skeletal_mesh:
                    mesh_name = comp.skeletal_mesh.get_name()
                
                finding = {
                    "actor": lbl,
                    "component": comp.get_name(),
                    "mesh": mesh_name,
                    "slot": i,
                    "material": mpath
                }
                worldgrid_findings.append(finding)
                print(f"Found: {lbl} -> Comp: {comp.get_name()}, Slot: {i}, Mesh: {mesh_name}, Material: {mpath}")

print(f"\nTotal WorldGrid/Default/None slots found: {len(worldgrid_findings)}")
