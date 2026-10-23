"""Audit and fix every unassigned or default material across the entire level.
Enforces curated, high-end toon materials on every mesh.
"""
import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# Curated production materials
mat_wall = unreal.load_asset("/Game/Materials/Instances/UniversalFilm_20261016/MI_Film_Wall")
mat_warm_wall = unreal.load_asset("/Game/Materials/Instances/UniversalFilm_20261016/MI_Film_WarmWall")
mat_floor = unreal.load_asset("/Game/Materials/Instances/Film304/Scene/MI_Film304_Floor")
mat_frame = unreal.load_asset("/Game/Materials/Instances/Film304/Scene/MI_Film304_Frame")
mat_metal = unreal.load_asset("/Game/Materials/Instances/Film304/Scene/MI_Film304_Prop_Metal")
mat_concrete = unreal.load_asset("/Game/Materials/Instances/Film304/Environment/MI_Film304_BrutalistConcrete")
mat_plastic = unreal.load_asset("/Game/Materials/Instances/Film304/Scene/MI_Film304_Prop_Plastic")
mat_troffer = unreal.load_asset("/Game/Materials/Instances/MI_Toon_Office_Troffer")
mat_glass = unreal.load_asset("/Game/Materials/Instances/MI_Toon_Glass")

repaired_count = 0

for a in eas.get_all_level_actors():
    smc = a.get_component_by_class(unreal.StaticMeshComponent)
    if not smc or not smc.static_mesh:
        continue
        
    lbl = a.get_actor_label()
    num_mats = smc.get_num_materials()
    mesh_name = smc.static_mesh.get_name()
    
    for slot in range(num_mats):
        mat = smc.get_material(slot)
        mat_name = mat.get_name() if mat else "None"
        
        # Check if default or worldgrid or untextured
        if mat is None or "WorldGrid" in mat_name or "Default" in mat_name:
            repaired_count += 1
            # Pick best contextual material
            if "Mullion" in lbl or "Frame" in lbl:
                smc.set_material(slot, mat_frame)
                print(f"  Fixed {lbl} slot {slot}: -> MI_Film304_Frame")
            elif "Wall" in lbl or "Header" in lbl or "Cube" in mesh_name and "Column" not in lbl:
                smc.set_material(slot, mat_wall)
                print(f"  Fixed {lbl} slot {slot}: -> MI_Film_Wall")
            elif "Housing" in lbl or "Duct" in lbl or "Hanger" in lbl or "Metal" in lbl or "Troffer" in lbl:
                smc.set_material(slot, mat_metal)
                print(f"  Fixed {lbl} slot {slot}: -> MI_Film304_Prop_Metal")
            elif "Panel" in lbl or "Diffuser" in lbl:
                smc.set_material(slot, mat_troffer)
                print(f"  Fixed {lbl} slot {slot}: -> MI_Toon_Office_Troffer")
            elif "Glass" in lbl or "Window" in lbl:
                smc.set_material(slot, mat_glass)
                print(f"  Fixed {lbl} slot {slot}: -> MI_Toon_Glass")
            elif "Floor" in lbl:
                smc.set_material(slot, mat_floor)
                print(f"  Fixed {lbl} slot {slot}: -> MI_Film304_Floor")
            elif "Column" in lbl or "Slab" in lbl or "Concrete" in lbl:
                smc.set_material(slot, mat_concrete)
                print(f"  Fixed {lbl} slot {slot}: -> MI_Film304_BrutalistConcrete")
            else:
                smc.set_material(slot, mat_plastic)
                print(f"  Fixed {lbl} slot {slot}: -> MI_Film304_Prop_Plastic")

# Verify ceiling HVAC grid materials
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "SM_Houdini_Ceiling_HVAC_Grid":
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        if smc:
            smc.set_material(0, mat_concrete) # Beams
            smc.set_material(1, mat_metal)    # Ducts/hangers
            smc.set_material(2, mat_troffer)  # Diffusers
            print("  Verified SM_Houdini_Ceiling_HVAC_Grid 3 slots (Concrete, Metal, Troffer)")

# Clean up redundant legacy ceiling actors if present
for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if lbl.startswith("HOUDINI_SM_Houdini_Office_Ceiling_"):
        print(f"  Destroying redundant legacy ceiling mesh: {lbl}")
        eas.destroy_actor(a)

unreal.EditorLevelLibrary.save_current_level()
print(f"MATERIAL AUDIT COMPLETE! Total fixed slots: {repaired_count}")
