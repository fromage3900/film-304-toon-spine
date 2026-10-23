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

for a in eas.get_all_level_actors():
    loc = a.get_actor_location()
    xl, yl, zl = to_local(loc.x, loc.y, loc.z)
    bounds = a.get_actor_bounds(False)
    # Check if bounds are elongated
    if bounds[1].x > 100 or bounds[1].y > 100 or bounds[1].z > 100:
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        mats = []
        if smc:
            for i in range(smc.get_num_materials()):
                m = smc.get_material(i)
                mats.append(m.get_name() if m else "None")
        print(f"{a.get_actor_label():30} | local_loc=({xl:6.1f},{yl:6.1f},{zl:6.1f}) | ext=({bounds[1].x:6.1f},{bounds[1].y:6.1f},{bounds[1].z:6.1f}) | mats={mats}")
