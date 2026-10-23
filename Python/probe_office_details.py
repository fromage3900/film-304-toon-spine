import unreal

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = eas.get_all_level_actors()

print(f"Total actors in {world.get_path_name()}: {len(actors)}")

print("\n--- CAMERAS ---")
for a in actors:
    if isinstance(a, unreal.CineCameraActor) or "Cam" in a.get_actor_label():
        loc = a.get_actor_location()
        rot = a.get_actor_rotation()
        print(f"Cam: {a.get_actor_label()} Class: {a.get_class().get_name()} Loc: ({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f}) Rot: (pitch={rot.pitch:.1f}, yaw={rot.yaw:.1f}, roll={rot.roll:.1f})")

print("\n--- SKELETAL MESH CHARACTERS ---")
for a in actors:
    if isinstance(a, unreal.SkeletalMeshActor) or any(name in a.get_actor_label().lower() for name in ["dana", "sam", "david", "spider", "cast", "subject"]):
        loc = a.get_actor_location()
        rot = a.get_actor_rotation()
        skc = a.get_component_by_class(unreal.SkeletalMeshComponent)
        sk_mesh = skc.skeletal_mesh_asset if skc else None
        anim_mode = skc.get_editor_property("animation_mode") if skc else None
        anim_data = skc.get_editor_property("animation_data") if skc else None
        anim_to_play = anim_data.anim_to_play if anim_data else None
        print(f"Char: {a.get_actor_label()} Mesh: {sk_mesh.get_name() if sk_mesh else 'None'} Loc: ({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f}) Rot: (pitch={rot.pitch:.1f}, yaw={rot.yaw:.1f}, roll={rot.roll:.1f}) Anim: {anim_to_play.get_name() if anim_to_play else 'None'}")

print("\n--- WINDOW / EXTERIOR / SKY / LIGHTS ---")
for a in actors:
    lbl = a.get_actor_label().lower()
    if any(k in lbl for k in ["window", "sky", "sun", "exterior", "building", "tower", "city", "louver", "blind", "wall", "floor", "troffer"]):
        loc = a.get_actor_location()
        cls_name = a.get_class().get_name()
        print(f"Env/Light: {a.get_actor_label()} ({cls_name}) Loc: ({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f})")

