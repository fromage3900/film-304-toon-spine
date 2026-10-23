import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# Let's inspect the total illumination or test disabling lights
culprits = [
    "Light_Ceiling_Upwash_01",
    "Light_Ceiling_Upwash_02",
    "Light_Ceiling_Upwash_03",
    "SM_Houdini_Ceiling_HVAC_Grid",
    "Film_UDS_Daylight",
    "Light_David_DeskLamp",
    "SpotLight"
]

for name in culprits:
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == name:
            c = a.get_component_by_class(unreal.ActorComponent)
            print(f"{name}: visible={a.is_hidden_ed()}")
