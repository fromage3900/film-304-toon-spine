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

# North Wall spans from West (-290.0) to East Wall (+1160.0)
# Center X = 435.0 cm. Center Y = 830.0 cm. Center Z = 175.0 cm.
# Length = 14.50m (scale X = 14.50).
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_NorthWall_Full":
        a.set_actor_location(to_world(435.0, 830.0, 175.0), False, False)
        a.set_actor_rotation(rot_room(), False)
        a.set_actor_scale3d(unreal.Vector(14.50, 0.25, 3.50))
        print("Film_NorthWall_Full extended to 14.5m, seamlessly sealing North-East corner!")

unreal.EditorLevelLibrary.save_current_level()
