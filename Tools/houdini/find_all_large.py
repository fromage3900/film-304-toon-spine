import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

print("Listing all actors with bounds and class:")
for a in eas.get_all_level_actors():
    bounds = a.get_actor_bounds(False)
    # Check if length/width is substantial (> 100)
    if bounds[1].x > 100 or bounds[1].y > 100:
        loc = a.get_actor_location()
        if -800 < loc.x < 1500 and -800 < loc.y < 1500:
            print(f"{a.get_actor_label():35} | class={a.get_class().get_name():25} | loc=({loc.x:6.1f},{loc.y:6.1f},{loc.z:6.1f}) | ext=({bounds[1].x:6.1f},{bounds[1].y:6.1f},{bounds[1].z:6.1f})")
