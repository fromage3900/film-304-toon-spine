import math
import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
yaw_rad = math.radians(-25.0)
cos_y = math.cos(yaw_rad)
sin_y = math.sin(yaw_rad)

def to_local(xw, yw, zw):
    return (xw * cos_y + yw * sin_y, -xw * sin_y + yw * cos_y, zw)

print("=== AUDIT OF LEVEL ACTORS & MISPLACED MESHES ===")
misplaced = []
world_grid_mats = []

for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    loc = a.get_actor_location()
    xl, yl, zl = to_local(loc.x, loc.y, loc.z)
    
    # Check for WorldGridMaterial
    smc = a.get_component_by_class(unreal.StaticMeshComponent)
    if smc:
        for i in range(smc.get_num_materials()):
            m = smc.get_material(i)
            if m and "WorldGridMaterial" in m.get_name():
                world_grid_mats.append((lbl, i, m.get_name()))
                
    # Check for duplicate/rogue glass
    if "Glass" in lbl and ("Bay_2" in lbl or "Bay_3" in lbl or "Bay_4" in lbl):
        misplaced.append((lbl, (xl, yl, zl), "Rogue duplicate glass pane"))
        
    # Check for actors far out of room bounds that aren't exterior skyline
    is_ext = any(k in lbl for k in ["SM_Ext", "EST_", "Cam_E1", "Light_Aviation", "Light_Cinematic"])
    if not is_ext:
        if abs(xl) > 1500 or abs(yl) > 1500 or loc.z < -200 or loc.z > 600:
            misplaced.append((lbl, (xl, yl, zl), "Actor outside room bounds"))

print(f"\nActors with WorldGridMaterial ({len(world_grid_mats)}):")
for lbl, slot, m_name in world_grid_mats:
    print(f"  {lbl} [slot {slot}]: {m_name}")

print(f"\nMisplaced / Rogue Actors ({len(misplaced)}):")
for lbl, loc, reason in misplaced:
    print(f"  {lbl} at L=({loc[0]:.1f}, {loc[1]:.1f}, {loc[2]:.1f}): {reason}")
