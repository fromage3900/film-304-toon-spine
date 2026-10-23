import unreal

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

print("=== EXTERIOR BUILDINGS & HORIZON OBJECTS ===")
for a in EAS.get_all_level_actors():
    lbl = a.get_actor_label()
    if any(k in lbl.lower() for k in ["tower", "estate", "barbican", "sprawl", "horizon", "skyline", "exterior", "building"]):
        loc = a.get_actor_location()
        origin, extent = a.get_actor_bounds(False)
        print(f"  {lbl:45s} | Loc: ({loc.x:8.1f}, {loc.y:8.1f}, {loc.z:8.1f}) | Bounds Origin: ({origin.x:8.1f}, {origin.y:8.1f}, {origin.z:8.1f}) | Extent: ({extent.x:7.1f}, {extent.y:7.1f}, {extent.z:7.1f})")

print("\n=== WINDOW GLASS & BACKWALL ===")
for a in EAS.get_all_level_actors():
    lbl = a.get_actor_label()
    if any(k in lbl.lower() for k in ["glass", "window", "backwall", "wallpanel"]):
        loc = a.get_actor_location()
        print(f"  {lbl:35s} | Loc: ({loc.x:7.1f}, {loc.y:7.1f}, {loc.z:7.1f})")
