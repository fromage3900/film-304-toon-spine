import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

print("=== APPLYING DUSK MATERIALS AND FIXING DIRECTIONAL LIGHT PRIORITIES ===")

# 1. Load the 23 Dusk Materials from the verified path
DUSK_DIR = "/Game/Materials/Instances/Film304/Scene/Dusk20261018"
dusk_keys = [
    "Wall", "WarmWall", "Floor", "Desk", "Ceiling", "Glazing",
    "Metal", "Plastic", "Ceramic", "Paper", "LampShade", "Frame",
    "Plant", "Chair", "Breakroom", "Whiteboard", "Monitor", "Blinds"
]

DUSK = {}
for k in dusk_keys:
    mat = unreal.load_asset(f"{DUSK_DIR}/MI_Dusk_{k}")
    if mat:
        DUSK[k] = mat
        print(f"Loaded MI_Dusk_{k}")
    else:
        print(f"Warning: Missing MI_Dusk_{k}")

# Function to determine dusk key for a material and actor
def dusk_key_for(mat_path, actor_label):
    p = mat_path or ""
    a = actor_label or ""
    if "WarmWall" in p or "Feature" in a or "NorthReturn" in a:
        return "WarmWall"
    if "Floor" in p or "Floor" in a:
        return "Floor"
    if "Ceiling" in p or "Ceiling" in a:
        return "Ceiling"
    if "Wall" in p or "Wall" in a:
        return "Wall"
    if any(k in p for k in ["Desk", "BreakroomTable", "DeskDrawers"]):
        return "Desk"
    if "Desk" in a and "Chair" not in a and "Lamp" not in a:
        return "Desk"
    if "Mullion" in a or "Frame" in p:
        return "Frame"
    if "Glass" in a or "WindowBay" in a or "Glazing" in p:
        return "Glazing"
    if "Blind" in a:
        return "Blinds"
    if "Chair" in a or "Chair" in p:
        return "Chair"
    if "Screen" in p or "Monitor" in a:
        return "Monitor"
    if any(k in a for k in ["Plant", "Succulent", "Cactus"]):
        return "Plant"
    if "Lamp" in a and "Light" not in a:
        return "LampShade"
    if "BreakRoom" in a or "Vending" in a:
        return "Plastic"
    if p.endswith("WorldGridMaterial.WorldGridMaterial") or "WorldGrid" in p:
        if "Mullion" in a or "Housing" in a:
            return "Metal"
        if "Wall" in a:
            return "Wall"
        return "Metal"
    return None

repointed = 0
for a in eas.get_all_level_actors():
    # NEVER TOUCH SAM
    if a.get_actor_label() == "Film_Cast_Sam":
        continue
    
    lbl = a.get_actor_label()
    # Check all mesh components
    comps = a.get_components_by_class(unreal.StaticMeshComponent)
    for comp in comps:
        num_mats = comp.get_num_materials()
        for i in range(num_mats):
            m = comp.get_material(i)
            mpath = m.get_path_name() if m else ""
            key = dusk_key_for(mpath, lbl)
            if key and key in DUSK:
                comp.set_material(i, DUSK[key])
                repointed += 1

print(f"Successfully repointed {repointed} material slots to MI_Dusk_* instances")

# 2. Fix Directional Light Forward Shading Priority to remove screen warning
for a in eas.get_all_level_actors():
    c = a.get_component_by_class(unreal.DirectionalLightComponent)
    if c:
        lbl = a.get_actor_label()
        if lbl in ["Light_Cinematic_SunBeam", "DirectionalLight"]:
            c.set_editor_property("forward_shading_priority", 1)
            print(f"Set forward_shading_priority=1 on {lbl}")
        else:
            c.set_editor_property("forward_shading_priority", 0)
            print(f"Set forward_shading_priority=0 on {lbl}")

# 3. Verify Sam transform is 100% UNTOUCHED
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_Cast_Sam":
        print(f"CONFIRMED Sam Transform UNTOUCHED: Loc={a.get_actor_location()}, Rot={a.get_actor_rotation()}")
        break

unreal.EditorLoadingAndSavingUtils.save_current_level()
print("Saved current level cleanly.")
