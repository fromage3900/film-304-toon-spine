import unreal

print("=== CHECKING ALL LIGHTS IN THE LEVEL ===")
actors = unreal.EditorLevelLibrary.get_all_level_actors()
for a in actors:
    lbl = a.get_actor_label()
    for lc in a.get_components_by_class(unreal.LightComponent):
        intens = lc.get_editor_property("intensity")
        col = lc.get_editor_property("light_color")
        loc = a.get_actor_location()
        rot = a.get_actor_rotation()
        print(f"Actor: {lbl:35s} | Class: {lc.get_class().get_name():22s} | Int: {intens:8.2f} | Loc: ({loc.x:7.1f},{loc.y:7.1f},{loc.z:7.1f}) | Rot: ({rot.pitch:5.1f},{rot.yaw:5.1f},{rot.roll:5.1f})")
