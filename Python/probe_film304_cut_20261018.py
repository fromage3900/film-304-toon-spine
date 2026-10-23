"""Inspect camera-cut section properties and binding IDs."""
import unreal

path = '/Game/Sequences/Film304Dusk_20261018/LS_DUSK02_Window'
seq = unreal.load_asset(path)
print('SEQ %s display=%s tick=%s' % (seq.get_path_name(), seq.get_display_rate(),
                                     seq.get_tick_resolution()))
for b in seq.get_bindings():
    try:
        print('BIND %s id=%s' % (b.get_name(), b.get_id()))
    except Exception as exc:
        print('BIND ERR %s' % str(exc)[:80])
for track in seq.get_tracks():
    print('TRACK %s' % track.get_class().get_name())
    for s in track.get_sections():
        print('  SECTION %s' % s.get_class().get_name())
        for prop in ('range', 'start_frame', 'end_frame', 'start_time', 'end_time'):
            try:
                print('    %s = %s' % (prop, s.get_editor_property(prop)))
            except Exception as exc:
                print('    %s ERR %s' % (prop, str(exc)[:60]))
        try:
            bid = s.get_camera_binding_id()
            print('    camera_binding_id=%s' % bid)
            try:
                print('    guid=%s' % bid.get_editor_property('guid'))
            except Exception as exc:
                print('    guid ERR %s' % str(exc)[:60])
        except Exception as exc:
            print('    camera_binding ERR %s' % str(exc)[:60])
        print('    methods=%s' % [m for m in dir(s) if 'range' in m.lower() or 'frame' in m.lower()])
