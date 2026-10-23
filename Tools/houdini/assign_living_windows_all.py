"""Assigns warm amber and cool fluorescent living-window emissive materials to exterior skyline towers."""
import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

mi_warm = unreal.load_asset("/Game/Materials/Instances/Film304/Environment/MI_Film304_Glazing_WarmOffice")
mi_cool = unreal.load_asset("/Game/Materials/Instances/Film304/Environment/MI_Film304_Glazing_CoolOffice")

assigned = 0
for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    smc = a.get_component_by_class(unreal.StaticMeshComponent)
    if not smc:
        continue
    if any(k in lbl for k in ["Tower", "Barbican", "Superblock"]):
        num = smc.get_num_materials()
        if num > 1:
            target_mat = mi_warm if ("Hero" in lbl or "Mid" in lbl or "Barbican" in lbl) else mi_cool
            smc.set_material(1, target_mat)
            assigned += 1
            print(f"  Assigned {target_mat.get_name()} to {lbl} (slot 1)")

unreal.EditorLevelLibrary.save_current_level()
print(f"SUCCESS: Assigned living windows to {assigned} skyline towers!")
