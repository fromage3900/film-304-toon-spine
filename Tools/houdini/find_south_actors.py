import math
import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
yaw_rad = math.radians(-25.0)
cos_y = math.cos(yaw_rad)
sin_y = math.sin(yaw_rad)

print("Actors with Y_local < -250:")
for a in eas.get_all_level_actors():
    loc = a.get_actor_location()
    xl = loc.x * cos_y + loc.y * sin_y
    yl = -loc.x * sin_y + loc.y * cos_y
    if yl < -250.0 and abs(xl) < 1500.0:
        lbl = a.get_actor_label()
        print(f"  {lbl:35} | L=({xl:6.1f}, {yl:6.1f}, {loc.z:6.1f}) | class={a.get_class().get_name()}")
