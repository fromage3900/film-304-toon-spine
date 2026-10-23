import json
import unreal

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
print("WORLD:", world.get_name())

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
all_actors = eas.get_all_level_actors()

lights = []
ppvs = []
cameras = []

for a in all_actors:
    label = a.get_actor_label()
    cls_name = a.get_class().get_name()
    
    if "light" in cls_name.lower() or "sky" in cls_name.lower():
        lights.append({
            "label": label,
            "class": cls_name,
            "loc": [round(x, 1) for x in [a.get_actor_location().x, a.get_actor_location().y, a.get_actor_location().z]],
            "rot": [round(x, 1) for x in [a.get_actor_rotation().pitch, a.get_actor_rotation().yaw, a.get_actor_rotation().roll]],
        })
    elif "postprocess" in cls_name.lower():
        ppvs.append({
            "label": label,
            "class": cls_name,
            "loc": [round(x, 1) for x in [a.get_actor_location().x, a.get_actor_location().y, a.get_actor_location().z]],
            "enabled": getattr(a, "enabled", True),
            "unbound": getattr(a, "unbound", False) if hasattr(a, "unbound") else None,
            "priority": getattr(a, "priority", 0) if hasattr(a, "priority") else None,
        })
    elif "camera" in cls_name.lower():
        cameras.append({
            "label": label,
            "class": cls_name,
            "loc": [round(x, 1) for x in [a.get_actor_location().x, a.get_actor_location().y, a.get_actor_location().z]],
            "rot": [round(x, 1) for x in [a.get_actor_rotation().pitch, a.get_actor_rotation().yaw, a.get_actor_rotation().roll]],
        })

print(f"LIGHTS ({len(lights)}):")
for l in lights:
    print(f"  - {l['label']} ({l['class']}) at {l['loc']}")

print(f"\nPPVS ({len(ppvs)}):")
for p in ppvs:
    print(f"  - {p['label']} ({p['class']}) unbound={p['unbound']} prio={p['priority']}")

print(f"\nCAMERAS ({len(cameras)}):")
for c in cameras:
    print(f"  - {c['label']} ({c['class']}) at {c['loc']}")
