"""Stretch all sequence sections to the full 48-frame range in ticks.

The sequence display rate is 24 fps but its tick resolution is 24000; a
section range of 48 therefore covers 48 ticks (0.002 s), not 48 frames.
MRQ at frame 18 (tick 18000) found no camera and fell back to a default view.
"""
import unreal

SEQ_DIR = '/Game/Sequences/Film304Dusk_20261018'
EAL = unreal.EditorAssetLibrary
FULL_TICKS = 48000  # 48 frames at 24 fps, tick resolution 24000

for name in ('LS_DUSK01_Medium', 'LS_DUSK02_Window', 'LS_DUSK03_DeskLineup'):
    path = SEQ_DIR + '/' + name
    seq = unreal.load_asset(path)
    if seq is None:
        print('MISSING ' + path)
        continue
    seq.set_playback_start(0)
    seq.set_playback_end(48)
    n = 0
    for track in seq.get_tracks():
        for s in track.get_sections():
            try:
                s.set_range(0, FULL_TICKS)
                n += 1
            except Exception as exc:
                print('  RANGE ERR %s %s: %s' % (name, s.get_class().get_name(), str(exc)[:90]))
    EAL.save_loaded_asset(seq, False)
    print('FIXED %s sections=%d tracks=%d' % (name, n, len(seq.get_tracks())))
