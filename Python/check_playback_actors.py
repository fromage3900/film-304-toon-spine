import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if isinstance(a, unreal.LevelSequenceActor) or "playback" in a.get_actor_label().lower() or "loop" in a.get_actor_label().lower():
        seq = a.get_sequence()
        settings = a.get_editor_property("playback_settings")
        print(f"Sequence Actor: {a.get_actor_label()} Seq: {seq.get_path_name() if seq else 'None'} AutoPlay: {settings.auto_play if settings else 'N/A'}")
