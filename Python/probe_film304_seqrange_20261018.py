"""Inspect sequence rates and camera-cut section ranges."""
import unreal

for path in ('/Game/Sequences/Film304Dusk_20261018/LS_DUSK02_Window',
             '/Game/Sequences/Film304Hero_20261018/LS_HERO02_DeskInsert'):
    seq = unreal.load_asset(path)
    print('SEQ %s %s' % (path, 'MISSING' if not seq else ''))
    if not seq:
        continue
    print('  display=%s tick=%s playback=%s-%s' % (
        seq.get_display_rate(), seq.get_tick_resolution(),
        seq.get_playback_start(), seq.get_playback_end()))
    for track in seq.get_tracks():
        name = track.get_class().get_name()
        if 'CameraCut' in name:
            for s in track.get_sections():
                r = s.get_range()
                print('  CUTCUT %s range=%s methods=%s' % (
                    name, r, [m for m in dir(s) if 'range' in m.lower()]))
