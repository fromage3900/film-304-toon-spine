import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

print("=== DUST, GODRAYS, SUNBEAMS, NIAGARA ===")
for a in eas.get_all_level_actors():
    lbl = a.get_actor_label()
    cname = a.get_class().get_name()
    if any(k in lbl.lower() for k in ["dust", "shaft", "god", "ray", "sun", "beam", "vfx", "mote", "volumetric", "light"]):
        loc = a.get_actor_location()
        vis = a.is_hidden_ed() if hasattr(a, "is_hidden_ed") else False
        extra = ""
        c = a.get_component_by_class(unreal.LightComponentBase)
        if c:
            extra = f" | Light: {c.get_class().get_name()}, Intensity={c.get_editor_property('intensity')}, VolumetricScattering={c.get_editor_property('volumetric_scattering_intensity') if hasattr(c, 'volumetric_scattering_intensity') else 'N/A'}"
        nc = a.get_component_by_class(unreal.NiagaraComponent)
        if nc:
            extra = f" | Niagara: Asset={nc.get_asset().get_name() if nc.get_asset() else 'None'}, Active={nc.is_active()}"
        print(f"Actor: {lbl} ({cname}) | Loc: ({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f}) | HiddenEd: {vis}{extra}")
