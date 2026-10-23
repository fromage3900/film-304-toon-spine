import unreal

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

for a in EAS.get_all_level_actors():
    lbl = a.get_actor_label()
    if lbl in ["HDA_Cubicle_Hive", "HDA_Breakroom_Sanctuary", "Houdini_Ceiling_HVAC_Grid"]:
        loc = a.get_actor_location()
        rot = a.get_actor_rotation()
        root = a.get_editor_property("root_component")
        print(f"\n{lbl}:")
        print(f"  Actor Loc: ({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f})")
        print(f"  Actor Rot: ({rot.pitch:.1f}, {rot.yaw:.1f}, {rot.roll:.1f})")
        if root:
            rloc = root.get_editor_property("relative_location")
            rrot = root.get_editor_property("relative_rotation")
            print(f"  Root Rel Loc: ({rloc.x:.1f}, {rloc.y:.1f}, {rloc.z:.1f})")
            print(f"  Root Rel Rot: ({rrot.pitch:.1f}, {rrot.yaw:.1f}, {rrot.roll:.1f})")
            
        # Check components
        for c in a.get_components_by_class(unreal.SceneComponent):
            if c != root:
                cloc = c.get_editor_property("relative_location")
                crot = c.get_editor_property("relative_rotation")
                print(f"    Child Comp {c.get_name()}: RelLoc=({cloc.x:.1f}, {cloc.y:.1f}, {cloc.z:.1f}) RelRot=({crot.pitch:.1f}, {crot.yaw:.1f}, {crot.roll:.1f})")
