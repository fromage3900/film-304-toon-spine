import unreal
import math

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

yaw_rad = math.radians(-25.0)
cos_y = math.cos(yaw_rad)
sin_y = math.sin(yaw_rad)

def to_local(wx, wy, wz):
    xl = wx * cos_y + wy * sin_y
    yl = -wx * sin_y + wy * cos_y
    return xl, yl, wz

print("=== ALL DESKS, CHAIRS, WORKSTATIONS, PARTITIONS ===")
for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if any(k in lbl.lower() for k in ["desk", "chair", "cubicle", "table", "breakroom", "partition", "workstation"]):
        loc = a.get_actor_location()
        xl, yl, zl = to_local(loc.x, loc.y, loc.z)
        bounds = a.get_actor_bounds(False)
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        mesh_name = smc.static_mesh.get_name() if smc and smc.static_mesh else "None"
        print(f"{lbl:35} | mesh={mesh_name:25} | local_loc=({xl:6.1f},{yl:6.1f},{zl:6.1f})")
