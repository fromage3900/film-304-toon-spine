import math
import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
yaw_rad = math.radians(-25.0)

for a in eas.get_all_level_actors():
    if a.get_actor_label() == "SM_Houdini_Ceiling_HVAC_Grid":
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        if smc:
            smc.set_mobility(unreal.ComponentMobility.MOVABLE)
        a.set_actor_location(unreal.Vector(0.0, 0.0, 0.0), False, False)
        a.set_actor_rotation(unreal.Rotator(pitch=0.0, yaw=-25.0, roll=0.0), False)
        loc = a.get_actor_location()
        bounds = a.get_actor_bounds(False)
        print(f"Set SM_Houdini_Ceiling_HVAC_Grid to Movable & moved to (0,0,0)!")
        print(f"  New loc: {loc}")
        print(f"  New origin: {bounds[0]}")
        print(f"  New extent: {bounds[1]}")
