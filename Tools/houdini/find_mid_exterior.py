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

print("=== ALL ACTORS BETWEEN X_local = -5000 and -290 ===")
for a in eas.get_all_level_actors():
    loc = a.get_actor_location()
    xl, yl, zl = to_local(loc.x, loc.y, loc.z)
    bounds = a.get_actor_bounds(False)
    if -8000 < xl < -280 and -2000 < yl < 2000:
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        mesh_name = smc.static_mesh.get_name() if smc and smc.static_mesh else "None"
        mats = [smc.get_material(i).get_name() if smc.get_material(i) else "None" for i in range(smc.get_num_materials())] if smc else []
        print(f"{a.get_actor_label():35} | local_loc=({xl:6.1f},{yl:6.1f},{zl:6.1f}) | mesh={mesh_name:25} | mats={mats}")
