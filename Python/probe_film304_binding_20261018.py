"""Probe sequence binding-ID APIs and rebuild the camera cut binding."""
import unreal

seq = unreal.load_asset('/Game/Sequences/Film304Dusk_20261018/LS_DUSK02_Window')
cam_binding = None
for b in seq.get_bindings():
    print('BIND %s id=%s' % (b.get_name(), b.get_id()))
    if b.get_name().startswith('CineCam'):
        cam_binding = b
print('SEQ METHODS %s' % [m for m in dir(seq) if 'binding' in m.lower() or 'possess' in m.lower()])
print('EXT METHODS %s' % [m for m in dir(unreal.MovieSceneSequenceExtensions)
                          if 'binding' in m.lower() or 'possess' in m.lower()])
print('BINDING METHODS %s' % [m for m in dir(cam_binding) if 'id' in m.lower() or 'guid' in m.lower()])
print('BID METHODS %s' % [m for m in dir(unreal.MovieSceneObjectBindingID)
                          if 'guid' in m.lower() or 'space' in m.lower()
                          or 'sequence' in m.lower()])
