"""Read the live Film_Floor material and its effective colour parameters."""
import json

import unreal

ME = unreal.MaterialEditingLibrary
world = unreal.EditorLevelLibrary.get_editor_world()
print('WORLD ' + world.get_path_name())

floor = None
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    try:
        if a.get_actor_label() == 'Film_Floor':
            floor = a
            break
    except Exception:
        pass

if floor is None:
    print('NO FLOOR')
else:
    comp = floor.get_components_by_class(unreal.StaticMeshComponent)[0]
    mi = comp.get_material(0)
    print('MATERIAL ' + mi.get_path_name())
    try:
        print('PARENT ' + mi.get_editor_property('parent').get_path_name())
    except Exception:
        pass
    names = ['BaseTint', 'RampLow', 'RampMid', 'RampHigh', 'PaletteRampLow', 'PaletteRampMid',
             'PaletteRampHigh', 'FilmPaperTint', 'FilmInkTint', 'FilmGradeTint']
    for n in names:
        try:
            v = ME.get_material_instance_vector_parameter_value(mi, n)
            print('VEC %s = [%.4f, %.4f, %.4f]' % (n, v.r, v.g, v.b))
        except Exception as exc:
            print('VEC %s ERR %s' % (n, str(exc)[:60]))
    for n in ['RampStrength', 'PaletteRampStrength', 'PaletteRampDriver', 'TextureWeight',
              'UVScale', 'Roughness', 'FilmPaperLift', 'FilmGradeSaturation',
              'FilmGradeShadowLift', 'FilmGradeContrast', 'PastelLift']:
        try:
            print('SCA %s = %.4f' % (n, ME.get_material_instance_scalar_parameter_value(mi, n)))
        except Exception as exc:
            print('SCA %s ERR %s' % (n, str(exc)[:60]))
    try:
        t = ME.get_material_instance_texture_parameter_value(mi, 'Albedo')
        print('TEX Albedo = %s' % (t.get_path_name() if t else None))
    except Exception as exc:
        print('TEX Albedo ERR %s' % str(exc)[:60])
