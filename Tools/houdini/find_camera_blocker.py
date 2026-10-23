import unreal
import math

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

yaw_rad = math.radians(-25.0)
cos_y = math.cos(yaw_rad)
sin_y = math.sin(yaw_rad)

def to_world(xl, yl, zl):
    return unreal.Vector(xl * cos_y - yl * sin_y, xl * sin_y + yl * cos_y, zl)

cam_loc = to_world(250.0, 250.0, 950.0)

print(f"Checking what is near camera loc: ({cam_loc.x:.1f}, {cam_loc.y:.1f}, {cam_loc.z:.1f})")

for a in eas.get_all_level_actors():
    smc = a.get_component_by_class(unreal.StaticMeshComponent)
    if smc:
        bounds = a.get_actor_bounds(False)
        origin, ext = bounds[0], bounds[1]
        # Check if bounds contain cam_loc or are between cam_loc and ground at X=250, Y=250
        min_x, max_x = origin.x - ext.x, origin.x + ext.x
        min_y, max_y = origin.y - ext.y, origin.y + ext.y
        min_z, max_z = origin.z - ext.z, origin.z + ext.z
        if min_x <= cam_loc.x <= max_x and min_y <= cam_loc.y <= max_y and max_z > 300:
            print(f"Actor intersecting column: {a.get_actor_label():30} | Z range: [{min_z:.1f}, {max_z:.1f}] | mesh={smc.static_mesh.get_name() if smc.static_mesh else 'None'}")
