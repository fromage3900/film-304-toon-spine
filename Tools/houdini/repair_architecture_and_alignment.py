"""CAD Architectural Repair & Enclosure for L_Film_Office.

Solves:
1. Missing North Wall: creates full-height Film_NorthWall_Full (Y_local = 830, X_local = -290..950, Z = 0..350).
2. Missing East Wall: creates full-height Film_EastWall_Full (X_local = 1150, Y_local = -340..830, Z = 0..350).
3. West Corner Return: creates Film_West_NorthReturnWall (X_local = -290, Y_local = 600..830, Z = 0..350).
4. Destroys all duplicate rogue actors (Wall_Right2, BackWall2, WarmWallPanel2, etc., and orphan glass bays).
5. Fixes SM_Glass_WindowBay_01 scale (0.04, 2.26, 3.00) and alignment.
6. Fixes untextured WorldGridMaterial on Film_WindowMullion_600 and troffers.
7. Aligns SM_BreakRoomTogether neatly in the northwest niche.
"""
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
mat_frame = unreal.load_asset("/Game/Materials/Instances/Film304/Scene/MI_Film304_Frame")
mat_metal = unreal.load_asset("/Game/Materials/Instances/Film304/Scene/MI_Film304_Prop_Metal")
mat_troffer = unreal.load_asset("/Game/Materials/Instances/MI_Toon_Office_Troffer")
mat_glass = unreal.load_asset("/Game/Materials/Instances/MI_Toon_Glass")

print("--- 1. DESTROYING ROGUE DUPLICATES & OBSOLETE HEADER FRAGMENTS ---")
rogue_labels = [
    "Film_Wall_Right2",
    "Film_Wall_Header_Full2",
    "Film_BackWall2",
    "Film_WarmWallPanel2",
    "Film_Wall_Seam_Infill2",
    "SM_Glass_WindowBay_2",
    "SM_Glass_WindowBay_3",
    "SM_Glass_WindowBay_4",
    "Film_Breakroom_UpperHeader",
    "Film_NorthEast_UpperHeader",
    "Film_Wall_Right",
    "Film_DeskReturn"
]

for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if lbl in rogue_labels:
        print(f"  Destroying rogue/obsolete actor: {lbl}")
        eas.destroy_actor(a)

print("--- 2. CREATING SOLID NORTH DEMISING WALL (Y_local = 830.0 cm) ---")
# Span from X_local = -290 to +950 (length = 1240 cm = 12.4m)
# Center X = (-290 + 950) / 2 = 330.0 cm. Center Y = 830.0 cm. Center Z = 175.0 cm (height = 350.0 cm)
# Thickness in Y = 25 cm (scale Y = 0.25). Scale X = 12.40. Scale Z = 3.50.
north_wall = None
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_NorthWall_Full":
        north_wall = a
        break

if not north_wall:
    north_wall = eas.spawn_actor_from_class(unreal.StaticMeshActor, to_world(330.0, 830.0, 175.0), rot_room())
    north_wall.set_actor_label("Film_NorthWall_Full")

north_wall.set_actor_location(to_world(330.0, 830.0, 175.0), False, False)
north_wall.set_actor_rotation(rot_room(), False)
north_wall.set_actor_scale3d(unreal.Vector(12.40, 0.25, 3.50))
smc = north_wall.get_component_by_class(unreal.StaticMeshComponent)
if smc:
    smc.set_static_mesh(cube_mesh)
    smc.set_material(0, mat_wall)
if hasattr(north_wall, "set_folder_path"):
    north_wall.set_folder_path("Master_Perimeter_Enclosure")
print("  Spawned & configured Film_NorthWall_Full")

print("--- 3. CREATING SOLID EAST CORRIDOR WALL (X_local = 1150.0 cm) ---")
# Span Y_local from -340 to +830 (length = 1170 cm = 11.7m)
# Center X = 1150.0 cm. Center Y = (-340 + 830) / 2 = 245.0 cm. Center Z = 175.0 cm.
# Thickness in X = 25 cm (scale X = 0.25). Scale Y = 11.70. Scale Z = 3.50.
east_wall = None
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_EastWall_Full":
        east_wall = a
        break

if not east_wall:
    east_wall = eas.spawn_actor_from_class(unreal.StaticMeshActor, to_world(1150.0, 245.0, 175.0), rot_room())
    east_wall.set_actor_label("Film_EastWall_Full")

east_wall.set_actor_location(to_world(1150.0, 245.0, 175.0), False, False)
east_wall.set_actor_rotation(rot_room(), False)
east_wall.set_actor_scale3d(unreal.Vector(0.25, 11.70, 3.50))
smc = east_wall.get_component_by_class(unreal.StaticMeshComponent)
if smc:
    smc.set_static_mesh(cube_mesh)
    smc.set_material(0, mat_wall)
if hasattr(east_wall, "set_folder_path"):
    east_wall.set_folder_path("Master_Perimeter_Enclosure")
print("  Spawned & configured Film_EastWall_Full")

print("--- 4. CREATING WEST CORNER RETURN WALL (Connecting Window Bay 3 to North Wall) ---")
# Window Mullion 600 is at Y_local = 600. North Wall is at Y_local = 830.
# Length = 230 cm = 2.30m.
# Center X = -290.0 cm. Center Y = (600 + 830) / 2 = 715.0 cm. Center Z = 175.0 cm.
# Thickness in X = 20 cm (scale X = 0.20). Scale Y = 2.30. Scale Z = 3.50.
west_return = None
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_West_NorthReturnWall":
        west_return = a
        break

if not west_return:
    west_return = eas.spawn_actor_from_class(unreal.StaticMeshActor, to_world(-290.0, 715.0, 175.0), rot_room())
    west_return.set_actor_label("Film_West_NorthReturnWall")

west_return.set_actor_location(to_world(-290.0, 715.0, 175.0), False, False)
west_return.set_actor_rotation(rot_room(), False)
west_return.set_actor_scale3d(unreal.Vector(0.20, 2.30, 3.50))
smc = west_return.get_component_by_class(unreal.StaticMeshComponent)
if smc:
    smc.set_static_mesh(cube_mesh)
    smc.set_material(0, mat_wall)
if hasattr(west_return, "set_folder_path"):
    west_return.set_folder_path("Master_Perimeter_Enclosure")
print("  Spawned & configured Film_West_NorthReturnWall")

print("--- 5. UPDATING FULL UPPER HEADER BEAM ALONG WEST WALL ---")
# Span Y_local from -340 to +830 (length = 1170 cm = 11.7m)
# Center X = -290.0 cm. Center Y = 245.0 cm. Center Z = 320.0 cm.
# Thickness X = 30 cm (scale 0.30). Scale Y = 11.70. Height Z = 60 cm (scale 0.60, from 290 to 350).
header = None
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_Wall_Header_Full":
        header = a
        break

if not header:
    header = eas.spawn_actor_from_class(unreal.StaticMeshActor, to_world(-290.0, 245.0, 320.0), rot_room())
    header.set_actor_label("Film_Wall_Header_Full")

header.set_actor_location(to_world(-290.0, 245.0, 320.0), False, False)
header.set_actor_rotation(rot_room(), False)
header.set_actor_scale3d(unreal.Vector(0.30, 11.70, 0.60))
smc = header.get_component_by_class(unreal.StaticMeshComponent)
if smc:
    smc.set_static_mesh(cube_mesh)
    smc.set_material(0, mat_wall)
print("  Updated Film_Wall_Header_Full to seamlessly span Y = -340 to +830")

print("--- 6. REPAIRING SM_Glass_WindowBay_01 ALIGNMENT & SCALE ---")
# Bay 01 spans Y_local from -90 to +140.
# Center Y = (-90 + 140) / 2 = 25.0 cm. Center X = -290.0 cm. Center Z = 145.5 cm.
# Scale: X = 0.04 (thickness), Y = 2.26 (bay width), Z = 3.00 (height).
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "SM_Glass_WindowBay_01":
        a.set_actor_location(to_world(-290.0, 25.0, 145.5), False, False)
        a.set_actor_rotation(rot_room(), False)
        a.set_actor_scale3d(unreal.Vector(0.04, 2.26, 3.00))
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        if smc:
            smc.set_material(0, mat_glass)
        print("  Repaired SM_Glass_WindowBay_01: scale=(0.04, 2.26, 3.00) at Y_local = 25.0")

print("--- 7. ASSIGNING MATERIAL TO Film_WindowMullion_600 ---")
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_WindowMullion_600":
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        if smc:
            smc.set_material(0, mat_frame)
            print("  Assigned MI_Film304_Frame to Film_WindowMullion_600")

print("--- 8. CLEANING UP CHECKERBOARDS ON Film_Troffer_1..6 HOUSINGS & PANELS ---")
for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if "Troffer" in lbl and "Housing" in lbl:
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        if smc:
            smc.set_material(0, mat_metal)
            print(f"  Assigned MI_Film304_Prop_Metal to {lbl}")
    elif "Troffer" in lbl and "Panel" in lbl:
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        if smc:
            smc.set_material(0, mat_troffer)
            print(f"  Assigned MI_Toon_Office_Troffer to {lbl}")

print("--- 9. NEATLY TUCKING SM_BreakRoomTogether IN NORTHWEST CORNER ---")
# Put breakroom counter/cabinets cleanly against the north and west return walls
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "SM_BreakRoomTogether_ZMJ_FilmStage_20261016":
        # Keep its native rotation yaw = 155.0 (which is rot_room + 180)
        # Position at X_local = -200.0, Y_local = 720.0, Z = 0.0
        a.set_actor_location(to_world(-200.0, 720.0, 0.0), False, False)
        print("  Re-aligned SM_BreakRoomTogether in northwest niche")

unreal.EditorLevelLibrary.save_current_level()
print("SUCCESS: Architectural repair & alignment completed and saved!")
