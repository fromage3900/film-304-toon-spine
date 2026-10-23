import unreal
import math

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

print("=== CAMERA SIGHTLINE & INTERSECTION AUDIT ===")

cams = []
for a in EAS.get_all_level_actors():
    if isinstance(a, (unreal.CineCameraActor, unreal.CameraActor)) or "cam" in a.get_actor_label().lower():
        loc = a.get_actor_location()
        rot = a.get_actor_rotation()
        lbl = a.get_actor_label()
        folder = str(a.get_folder_path()) if hasattr(a, "get_folder_path") else ""
        cams.append((lbl, loc, rot, folder, a))

print(f"\nFound {len(cams)} cameras:")
for lbl, loc, rot, folder, a in cams:
    print(f"  Camera: {lbl:35s} | Loc: ({loc.x:7.1f}, {loc.y:7.1f}, {loc.z:7.1f}) | Rot: (P={rot.pitch:5.1f}, Y={rot.yaw:6.1f}) | Folder: {folder}")

print("\n--- MAJOR BOUNDS OF STAGED OBJECTS ---")
for a in EAS.get_all_level_actors():
    lbl = a.get_actor_label()
    if any(k in lbl for k in ["HDA", "Houdini", "Ceiling", "Troffer", "Whiteboard", "Desk", "Cubicle"]):
        origin, extent = a.get_actor_bounds(False)
        print(f"  Object: {lbl:35s} | Origin: ({origin.x:7.1f}, {origin.y:7.1f}, {origin.z:7.1f}) | Extent: ({extent.x:6.1f}, {extent.y:6.1f}, {extent.z:6.1f})")
        print(f"          X-range: [{origin.x - extent.x:7.1f} .. {origin.x + extent.x:7.1f}] | Y-range: [{origin.y - extent.y:7.1f} .. {origin.y + extent.y:7.1f}]")
