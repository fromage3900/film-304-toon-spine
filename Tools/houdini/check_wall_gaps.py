import math
import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
yaw_rad = math.radians(-25.0)
cos_y = math.cos(yaw_rad)
sin_y = math.sin(yaw_rad)

def to_world(xl, yl, zl):
    return unreal.Vector(xl * cos_y - yl * sin_y, xl * sin_y + yl * cos_y, zl)

def rot_room(pitch=0.0, yaw_offset=0.0, roll=0.0):
    return unreal.Rotator(pitch=pitch, yaw=-25.0 + yaw_offset, roll=roll)

# 1. Investigate the wall gap on the left of shot 1
print("All walls in level:")
for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if any(k in lbl for k in ["Wall", "Header", "Seam", "Panel"]):
        loc = a.get_actor_location()
        xl = loc.x * cos_y + loc.y * sin_y
        yl = -loc.x * sin_y + loc.y * cos_y
        bounds = a.get_actor_bounds(False)
        print(f"  {lbl:30} | L=({xl:6.1f}, {yl:6.1f}, {loc.z:6.1f}) | box_ext=({bounds[1].x:5.1f}, {bounds[1].y:5.1f}, {bounds[1].z:5.1f})")
