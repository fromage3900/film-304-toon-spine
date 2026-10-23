import unreal

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

cam_loc = unreal.Vector(240.0, -220.0, 115.0)
target = unreal.Vector(-176.8, 562.1, 150.0)
ray_dir = (target - cam_loc).normal()

hit = unreal.SystemLibrary.line_trace_single(
    world, cam_loc, cam_loc + ray_dir * 50000.0, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
    False, [], unreal.DrawDebugTrace.NONE, True
)
print("Hit properties:", [p for p in dir(hit) if not p.startswith("_")])

print("\nActors with X < 0 and Y > 500:")
for a in eas.get_all_level_actors():
    loc = a.get_actor_location()
    if loc.x < 0 and loc.y > 500 and abs(loc.z) < 10000:
        print(f"  {a.get_actor_label()} ({a.get_class().get_name()}): Loc={loc}")
