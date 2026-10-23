import unreal

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# Let's check all actors with location X < -300 and Y between 200 and 2000
actors = eas.get_all_level_actors()
print("Actors behind the window wall (X < -300, Y > 0):")
for a in actors:
    loc = a.get_actor_location()
    if loc.x < -300 and loc.y > 0 and abs(loc.z) < 5000:
        print(f"Actor: {a.get_actor_label()} Class: {a.get_class().get_name()} Loc: ({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f})")

# Also check Ultra Dynamic Sky / SkyAtmosphere / ExponentialHeightFog / Sun
print("\nSky / Atmosphere / Lighting actors:")
for a in actors:
    cls = a.get_class().get_name()
    lbl = a.get_actor_label()
    if any(k in cls.lower() or k in lbl.lower() for k in ["sky", "atmosphere", "fog", "sun", "light"]):
        if not any(k in lbl.lower() for k in ["troffer", "dressing", "phone", "sticky"]):
            print(f"Actor: {lbl} ({cls}) Loc: ({a.get_actor_location().x:.1f}, {a.get_actor_location().y:.1f}, {a.get_actor_location().z:.1f})")
