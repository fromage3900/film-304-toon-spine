import unreal

# Inspect actors in L_Film_Office_Assembly_20261018_v02
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world_sub = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)

print("Current open world:", world_sub.get_editor_world().get_path_name())

# Let's check what LVS asset exists
lvs = unreal.load_asset('/Game/Variants/Film304Closeout_20261018/LVS_Office_LightingCloseout_v01')
if lvs:
    print(f"Loaded LVS: {lvs.get_path_name()}, num variant sets: {lvs.get_num_variant_sets()}")
    for i in range(lvs.get_num_variant_sets()):
        vs = lvs.get_variant_set(i)
        print(f"  Variant Set {i}: {vs.get_display_text()}, num variants: {vs.get_num_variants()}")
        for j in range(vs.get_num_variants()):
            v = vs.get_variant(j)
            print(f"    Variant {j}: {v.get_display_text()}")
else:
    print("LVS not found")
