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
mat_concrete = unreal.load_asset("/Game/Materials/Instances/Film304/Environment/MI_Film304_BrutalistConcrete")

# Spawn or update Film_SouthWall
# Spanning from X_local = -290 to +950 (length 1240 cm = 12.4m, scale_x = 12.4, thickness 0.20, height 3.50m)
# Center X = (-290 + 950) / 2 = 330.0, Y = -340.0, Z = 175.0
wall_actor = None
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_SouthWall":
        wall_actor = a
        break

if not wall_actor:
    wall_actor = EAS.spawn_actor_from_class(unreal.StaticMeshActor, to_world(330.0, -340.0, 175.0), rot_room())
    wall_actor.set_actor_label("Film_SouthWall")

wall_actor.set_actor_location(to_world(330.0, -340.0, 175.0), False, False)
wall_actor.set_actor_rotation(rot_room(), False)
wall_actor.set_actor_scale3d(unreal.Vector(12.40, 0.25, 3.50))
if hasattr(wall_actor, "set_folder_path"):
    wall_actor.set_folder_path("Master_Perimeter_Enclosure")

smc = wall_actor.get_component_by_class(unreal.StaticMeshComponent)
if smc:
    smc.set_static_mesh(cube_mesh)
    smc.set_material(0, mat_wall)

print("SUCCESS: Film_SouthWall staged spanning from X=-290 to X=+950 at Y=-340.0, Z=0..350cm!")
