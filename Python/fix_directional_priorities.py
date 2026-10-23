import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# Assign strictly distinct forward_shading_priority to each DirectionalLight
prio_map = {
    "Light_Cinematic_SunBeam": 5,
    "Film_UDS_Daylight": 4, # for Sun, or component
    "EST_Fill_E1": 2,
    "Cast_RimKicker_Light": 1,
}

dir_lights = []
for a in eas.get_all_level_actors():
    for c in a.get_components_by_class(unreal.DirectionalLightComponent):
        dir_lights.append((a.get_actor_label(), c))

print(f"Found {len(dir_lights)} DirectionalLightComponents:")
prio = 1
for label, c in sorted(dir_lights, key=lambda x: x[0]):
    old_prio = c.get_editor_property("forward_shading_priority")
    new_prio = prio_map.get(label, prio)
    if label == "Film_UDS_Daylight":
        if "Moon" in c.get_name():
            new_prio = 3
        else:
            new_prio = 4
    c.set_editor_property("forward_shading_priority", new_prio)
    print(f"  {label} ({c.get_name()}): prio {old_prio} -> {new_prio}, intensity={c.intensity}")
    prio += 1

print("Distinct forward shading priorities applied successfully.")
