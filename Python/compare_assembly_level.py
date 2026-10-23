import unreal

# We can load the World asset as an object
world_pkg = unreal.load_package("/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office_Assembly_20261018_v02")
if world_pkg:
    print("Loaded package:", world_pkg.get_path_name())
    world_obj = unreal.find_object(world_pkg, "L_Film_Office_Assembly_20261018_v02")
    if world_obj:
        print("World object found:", world_obj.get_class().get_name())
        # Print actors in persistent level of that world
        lvl = world_obj.persistent_level
        if lvl:
            print("Persistent level found! Actors count:", len(lvl.actors))
            actors_assembly = [a.get_actor_label() for a in lvl.actors if a]
            print(f"Sample actors ({len(actors_assembly)}):", actors_assembly[:15])
            
            # Find window shafts, fog, etc.
            shafts = [a for a in actors_assembly if any(k in a.lower() for k in ["shaft", "dust", "god", "ray", "variant", "lvs"])]
            print("Matching lighting/VFX actors in Assembly:", shafts)
