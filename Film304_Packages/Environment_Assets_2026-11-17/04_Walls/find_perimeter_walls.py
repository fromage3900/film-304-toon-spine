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

print("=== CHECKING PERIMETER WALLS AROUND OFFICE ===")
walls = []
for a in eas.get_all_level_actors():
    smc = a.get_component_by_class(unreal.StaticMeshComponent)
    if smc:
        lbl = a.get_actor_label()
        loc = a.get_actor_location()
        xl, yl, zl = to_local(loc.x, loc.y, loc.z)
        if "Wall" in lbl or "Header" in lbl or "Breakroom" in lbl:
            scale = a.get_actor_scale3d()
            bounds = a.get_actor_bounds(False)
            print(f"{lbl:35} | local_loc=({xl:6.1f},{yl:6.1f},{zl:6.1f}) | scale=({scale.x:5.2f},{scale.y:5.2f},{scale.z:5.2f}) | ext=({bounds[1].x:5.1f},{bounds[1].y:5.1f},{bounds[1].z:5.1f})")
