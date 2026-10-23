import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

all_comps = []
for a in eas.get_all_level_actors():
    for c in a.get_components_by_class(unreal.DirectionalLightComponent):
        all_comps.append((a.get_actor_label(), c))

# Assign distinct priority 1, 2, 3, 4, 5... with SunBeam highest
all_comps.sort(key=lambda x: (x[0] == "Light_Cinematic_SunBeam", x[1].intensity))

for idx, (label, c) in enumerate(all_comps):
    c.set_editor_property("forward_shading_priority", idx + 1)
    print(f"Assigned priority {idx + 1} to {label} ({c.get_name()}), intensity={c.intensity}")

print("Unique forward shading priorities successfully locked.")
