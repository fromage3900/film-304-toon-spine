"""Apply a named lighting variant to L_Film_Office. Run inside the editor:

    import apply_office_lighting_variant as v; v.apply("NightOffice")

Also sets the sky's "Time of Day" (authored value was 652.8). Only touches lights it finds by label; does not save anything, spawn anything or move cameras.
Variants: FluorescentDay, WarmAfternoon, NightOffice, SpiderDread.
"""
import unreal

VARIANTS = {
    # troffer: intensity (cd), kelvin, which fixtures are on (1-6); key = SpotLight; fill = PointLight; rim = Cast_RimKicker_Light
    "FluorescentDay": dict(troffer=(3.5, 4300, "123456"), key=(160.0, 6500), fill=(10.6, 6500), rim=0.15, tod=1200.0),
    "WarmAfternoon":  dict(troffer=(0.8, 3000, "123456"), key=(220.0, 3200), fill=(6.0, 7500), rim=0.40, tod=1730.0),
    "NightOffice":    dict(troffer=(1.5, 5000, "123456"), key=(40.0, 4000),  fill=(2.0, 8000), rim=0.05, tod=2300.0),
    "SpiderDread":    dict(troffer=(2.0, 4800, "12"),     key=(20.0, 4000),  fill=(1.0, 9000), rim=0.60, tod=2130.0),
}


def _light_comp(actor):
    comps = actor.get_components_by_class(unreal.LightComponent)
    return comps[0] if comps else None


def apply(name):
    cfg = VARIANTS[name]
    actors = {a.get_actor_label(): a for a in unreal.EditorLevelLibrary.get_all_level_actors()}
    inten, kelvin, on = cfg["troffer"]
    for i in range(1, 7):
        lc = _light_comp(actors.get(f"Film_Troffer_{i}_Light")) if f"Film_Troffer_{i}_Light" in actors else None
        if lc:
            lc.set_editor_property("intensity", inten if str(i) in on else 0.0)
            lc.set_editor_property("use_temperature", True)
            lc.set_editor_property("temperature", float(kelvin))
    for label, (i, k) in (("SpotLight", cfg["key"]), ("PointLight", cfg["fill"])):
        lc = _light_comp(actors[label]) if label in actors else None
        if lc:
            lc.set_editor_property("intensity", i)
            lc.set_editor_property("use_temperature", True)
            lc.set_editor_property("temperature", float(k))
    if "Cast_RimKicker_Light" in actors:
        _light_comp(actors["Cast_RimKicker_Light"]).set_editor_property("intensity", cfg["rim"])
    sky = actors.get("Film_UDS_Daylight")
    if sky is not None and "tod" in cfg:
        import claireon  # in-editor MCP bridge; setting via the bridge re-runs the sky's construction
        claireon.uobject_set_property(object_path=sky.get_path_name(), property_path="Time of Day", value=str(cfg["tod"]))
    return name
