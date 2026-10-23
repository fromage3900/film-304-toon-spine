import unreal, math

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
yaw_rad = math.radians(-25.0)
cos_y = math.cos(yaw_rad)
sin_y = math.sin(yaw_rad)

def to_local(xw, yw, zw):
    xl = xw * cos_y + yw * sin_y
    yl = -xw * sin_y + yw * cos_y
    return (xl, yl, zw)

for a in eas.get_all_level_actors():
    loc = a.get_actor_location()
    xl, yl, zl = to_local(loc.x, loc.y, loc.z)
    if xl < 50.0 and yl < -100.0:
        lbl = a.get_actor_label()
        bounds = a.get_actor_bounds(False)
        print(f"{lbl:35} | L=({xl:6.1f}, {yl:6.1f}, {zl:6.1f}) | top_z={bounds[0].z+bounds[1].z:5.1f} | class={a.get_class().get_name()}")
