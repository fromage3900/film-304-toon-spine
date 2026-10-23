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

print("=== CHECKING ACTORS OUTSIDE WINDOW BAYS (X_local < -290, Y_local = -200..600) ===")
for a in eas.get_all_level_actors():
    loc = a.get_actor_location()
    xl, yl, zl = to_local(loc.x, loc.y, loc.z)
    bounds = a.get_actor_bounds(False)
    # Check if outside windows and close to office
    if -3000 < xl < -280 and -500 < yl < 1000:
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        mesh_name = smc.static_mesh.get_name() if smc and smc.static_mesh else "None"
        print(f"{a.get_actor_label():35} | local_loc=({xl:6.1f},{yl:6.1f},{zl:6.1f}) | ext=({bounds[1].x:6.1f},{bounds[1].y:6.1f},{bounds[1].z:6.1f}) | mesh={mesh_name}")
