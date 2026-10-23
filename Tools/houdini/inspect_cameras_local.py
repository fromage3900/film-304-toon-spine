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
    if isinstance(a, unreal.CineCameraActor):
        loc = a.get_actor_location()
        rot = a.get_actor_rotation()
        xl, yl, zl = to_local(loc.x, loc.y, loc.z)
        rel_yaw = rot.yaw - (-25.0)
        print(f"CAMERA: {a.get_actor_label():30} | local_loc=({xl:6.1f},{yl:6.1f},{zl:6.1f}) | rot=(P:{rot.pitch:5.1f}, Y:{rel_yaw:5.1f}, R:{rot.roll:5.1f})")
