"""Rebuild each Dusk camera cut with the engine-resolved binding ID."""
import unreal

SEQ_DIR = '/Game/Sequences/Film304Dusk_20261018'
EAL = unreal.EditorAssetLibrary

for name in ('LS_DUSK01_Medium', 'LS_DUSK02_Window', 'LS_DUSK03_DeskLineup'):
    seq = unreal.load_asset(SEQ_DIR + '/' + name)
    if seq is None:
        print('MISSING ' + name)
        continue
    cam_binding = None
    for b in seq.get_bindings():
        bn = b.get_name()
        if bn.startswith('CineCam') or bn.startswith('Film_Cam'):
            cam_binding = b
            break
    if cam_binding is None:
        print('NO CAMERA BINDING ' + name)
        continue
    bid = seq.get_binding_id(cam_binding)
    print('%s camera=%s bid=%s' % (name, cam_binding.get_name(), bid))
    for track in seq.get_tracks():
        for s in track.get_sections():
            try:
                s.set_camera_binding_id(bid)
                s.set_range_seconds(0.0, 2.0)
                print('  set cut %s range=%.3f-%.3f' % (
                    s.get_class().get_name(), s.get_start_frame_seconds(),
                    s.get_end_frame_seconds()))
            except Exception as exc:
                print('  SET ERR %s' % str(exc)[:100])
    EAL.save_loaded_asset(seq, False)
    print('SAVED ' + name)
