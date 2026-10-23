"""Set every Dusk sequence section to a true 2-second range and report it."""
import unreal

SEQ_DIR = '/Game/Sequences/Film304Dusk_20261018'
EAL = unreal.EditorAssetLibrary

for name in ('LS_DUSK01_Medium', 'LS_DUSK02_Window', 'LS_DUSK03_DeskLineup'):
    seq = unreal.load_asset(SEQ_DIR + '/' + name)
    if seq is None:
        print('MISSING ' + name)
        continue
    for track in seq.get_tracks():
        for s in track.get_sections():
            try:
                s.set_range_seconds(0.0, 2.0)
            except Exception as exc:
                print('  SET ERR %s %s' % (name, str(exc)[:90]))
            try:
                print('%s %s start=%s end=%s sec=%.3f-%.3f' % (
                    name, s.get_class().get_name(), s.get_start_frame(), s.get_end_frame(),
                    s.get_start_frame_seconds(), s.get_end_frame_seconds()))
            except Exception as exc:
                print('  READ ERR %s' % str(exc)[:90])
    EAL.save_loaded_asset(seq, False)
    print('SAVED ' + name)
