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
    smc = a.get_component_by_class(unreal.StaticMeshComponent)
    if smc and smc.static_mesh:
        loc = a.get_actor_location()
        xl, yl, zl = to_local(loc.x, loc.y, loc.z)
        bounds = a.get_actor_bounds(False)
        # Check actors with Z > 100 or Z near ceiling or on ground
        mats = [smc.get_material(i).get_name() if smc.get_material(i) else "None" for i in range(smc.get_num_materials())]
        if any("WorldGrid" in m or "Default" in m for m in mats):
            print(f"CHECKERBOARD ACTOR: {a.get_actor_label():30} | local_loc=({xl:6.1f},{yl:6.1f},{zl:6.1f}) | mesh={smc.static_mesh.get_name()} | mats={mats}")
