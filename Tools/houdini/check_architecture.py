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

actors_to_check = [
    "Film_BackWall",
    "Film_WarmWallPanel",
    "Film_Wall_Right",
    "Film_SouthWall",
    "Film_Wall_Seam_Infill",
    "Film_Breakroom_UpperHeader",
    "Film_NorthEast_UpperHeader",
    "Film_Wall_Header_Full",
    "SM_BreakRoomTogether_ZMJ_FilmStage_20261016",
    "SM_Glass_WindowBay_01",
    "SM_Glass_WindowBay_02",
    "SM_Glass_WindowBay_03",
    "Film_WindowMullion_-90",
    "Film_WindowMullion_140",
    "Film_WindowMullion_370",
    "Film_WindowMullion_600",
    "SM_VenetianBlind_Bay_01",
    "SM_VenetianBlind_Bay_02",
    "SM_VenetianBlind_Bay_03",
    "FG_Architectural_Column",
    "FG_Planter_Box_Edge",
    "Film_Floor",
    "Film_Ceiling_Slab"
]

print("=== ARCHITECTURAL BOUNDS & LOCAL EXTENTS ===")
for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    if lbl in actors_to_check:
        loc = a.get_actor_location()
        xl, yl, zl = to_local(loc.x, loc.y, loc.z)
        bounds = a.get_actor_bounds(False)
        scale = a.get_actor_scale3d()
        rot = a.get_actor_rotation()
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        mats = [smc.get_material(i).get_name() if smc.get_material(i) else "None" for i in range(smc.get_num_materials())] if smc else []
        print(f"{lbl:35} | loc=({xl:6.1f},{yl:6.1f},{zl:6.1f}) | scale=({scale.x:5.2f},{scale.y:5.2f},{scale.z:5.2f}) | rot={rot.yaw:5.1f} | mats={mats}")
