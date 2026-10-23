import unreal

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
cam_loc = unreal.Vector(240.0, -220.0, 115.0)
cam_rot = unreal.Rotator(pitch=-2.27, yaw=142.52, roll=0.0)
forward = cam_rot.get_forward_vector()

print("Cam Loc:", cam_loc, "Forward:", forward)
hits = unreal.SystemLibrary.line_trace_multi(
    world, cam_loc, cam_loc + forward * 2000.0,
    unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
    False, [], unreal.DrawDebugTrace.NONE, True
)
print("Hits in front of camera (within 20m):", len(hits))
for h in hits:
    d = h.to_dict()
    a = d.get("actor")
    print(f"  Hit dist={d.get('distance'):.1f}: {a.get_actor_label() if a else 'None'}")
