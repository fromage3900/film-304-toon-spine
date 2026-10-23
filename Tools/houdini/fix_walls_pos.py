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

print("Target world locs:")
print("North Wall:", to_world(330.0, 830.0, 175.0))
print("East Wall:", to_world(1150.0, 245.0, 175.0))

for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if lbl == "Film_NorthWall_Full":
        a.set_actor_location(to_world(330.0, 830.0, 175.0), False, False)
        a.set_actor_rotation(rot_room(), False)
        print("Set Film_NorthWall_Full to", a.get_actor_location())
    elif lbl == "Film_EastWall_Full":
        a.set_actor_location(to_world(1150.0, 245.0, 175.0), False, False)
        a.set_actor_rotation(rot_room(), False)
        print("Set Film_EastWall_Full to", a.get_actor_location())

unreal.EditorLevelLibrary.save_current_level()
