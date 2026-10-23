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

cube_mesh = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
mat_wall = unreal.load_asset("/Game/Materials/Instances/UniversalFilm_20261016/MI_Film_Wall")

# Span full header beam from Y = -250 to Y = 950 (length = 1200 cm = 12.0m)
# Center Y = (-250 + 950)/2 = 350.0. Center X = -290.0. Center Z = 320.0 (thickness 0.60m = 60cm, from Z=290 to 350)
for a in eas.get_all_level_actors():
    if a.get_actor_label() in ["Film_Wall_Header_Full", "Film_Wall_Header"]:
        eas.destroy_actor(a)

master_header = eas.spawn_actor_from_class(unreal.StaticMeshActor, to_world(-290.0, 350.0, 320.0), rot_room())
master_header.set_actor_label("Film_Wall_Header_Full")
master_header.set_actor_scale3d(unreal.Vector(0.30, 12.00, 0.60)) # Spans Y from -250 to +950, Z from 290 to 350
if hasattr(master_header, "set_folder_path"):
    master_header.set_folder_path("Master_Perimeter_Enclosure")

smc = master_header.get_component_by_class(unreal.StaticMeshComponent)
if smc:
    smc.set_static_mesh(cube_mesh)
    smc.set_material(0, mat_wall)

unreal.EditorLevelLibrary.save_current_level()
print("SUCCESS: Film_Wall_Header_Full scaled to 12.0m, permanently sealing all upper wall gaps along West wall!")
