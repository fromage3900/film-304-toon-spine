"""READ-ONLY audit of the live Film 304 render level.

Enumerates every mesh material slot, its instance parent chain and overrides,
plus the VFX / post-process / light stack. Writes a JSON report and a short
human summary. Changes no asset and saves no map.

Run inside the open editor:
    powershell -File Tools/mcp_exec.ps1 -Path Python/audit_film304_render_20261018.py
"""
import json
from pathlib import Path

import unreal

OUT = Path(unreal.Paths.project_dir()) / 'Saved/Audit/Film304_Finish_20261018'
OUT.mkdir(parents=True, exist_ok=True)

MEL = unreal.MaterialEditingLibrary


def walk_chain(mat):
    chain = []
    seen = set()
    cur = mat
    while cur is not None and cur.get_path_name() not in seen:
        seen.add(cur.get_path_name())
        chain.append(cur.get_path_name())
        try:
            cur = cur.get_editor_property('parent')
        except Exception:
            cur = None
    return chain


def instance_overrides(mi):
    """Read overrides from the instance's own parameter arrays.

    UE 5.8's MaterialEditingLibrary has no get_material_instance_*_values
    enumeration (the singular get_..._value(name) works); the arrays on
    UMaterialInstanceConstant are the supported read path.
    """
    out = {'scalars': {}, 'vectors': {}, 'textures': {}, 'switches': {}}
    if not isinstance(mi, unreal.MaterialInstanceConstant):
        return out
    try:
        for v in mi.get_editor_property('scalar_parameter_values') or []:
            out['scalars'][str(v.get_editor_property('parameter_info').get_editor_property('name'))] = \
                float(v.get_editor_property('parameter_value'))
    except Exception as exc:
        out['scalars']['__error__'] = str(exc)[:120]
    try:
        for v in mi.get_editor_property('vector_parameter_values') or []:
            c = v.get_editor_property('parameter_value')
            out['vectors'][str(v.get_editor_property('parameter_info').get_editor_property('name'))] = [
                round(c.r, 4), round(c.g, 4), round(c.b, 4), round(c.a, 4)]
    except Exception as exc:
        out['vectors']['__error__'] = str(exc)[:120]
    try:
        for v in mi.get_editor_property('texture_parameter_values') or []:
            t = v.get_editor_property('parameter_value')
            out['textures'][str(v.get_editor_property('parameter_info').get_editor_property('name'))] = \
                t.get_path_name() if t else None
    except Exception as exc:
        out['textures']['__error__'] = str(exc)[:120]
    try:
        for v in mi.get_editor_property('static_parameters') or []:
            out['switches'][str(v.get_editor_property('parameter_info').get_editor_property('name'))] = \
                bool(v.get_editor_property('value'))
    except Exception as exc:
        out['switches']['__error__'] = str(exc)[:120]
    return out


def component_slots(comp):
    rows = []
    try:
        mats = comp.get_materials()
    except Exception:
        return rows
    for i, m in enumerate(mats or []):
        if m is None:
            rows.append({'slot': i, 'material': None, 'chain': [], 'overrides': {}})
            continue
        rows.append({
            'slot': i,
            'material': m.get_path_name(),
            'chain': walk_chain(m),
            'overrides': instance_overrides(m),
        })
    return rows



def record_light(a, label, cls, folder):
    comp = None
    for attr in ('light_component', 'directional_light_component', 'point_light_component',
                 'spot_light_component', 'rect_light_component', 'sky_light_component'):
        try:
            comp = a.get_editor_property(attr)
            if comp:
                break
        except Exception:
            pass
    rec = {'label': label, 'class': cls, 'folder': folder,
           'location': [round(v, 2) for v in a.get_actor_location().to_tuple()]}
    if comp:
        for prop in ('intensity', 'light_color', 'attenuation_radius', 'source_radius',
                     'volumetric_scattering_intensity', 'mobility'):
            try:
                v = comp.get_editor_property(prop)
                if hasattr(v, 'to_tuple'):
                    v = [round(x, 4) for x in v.to_tuple()]
                elif not isinstance(v, (int, float, str, bool)):
                    v = str(v)
                rec[prop] = v
            except Exception:
                pass
    return rec


def main():
    world = unreal.EditorLevelLibrary.get_editor_world()
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    report = {
        'world': world.get_path_name() if world else None,
        'actor_count': len(actors),
        'mesh_slots': [],
        'non_mesh_actors': [],
        'vfx': [],
        'lights': [],
        'post_process': [],
        'summary': {},
    }

    for a in actors:
        try:
            label = a.get_actor_label()
            cls = a.get_class().get_name()
            folder = str(a.get_folder_path())
        except Exception:
            continue

        if isinstance(a, unreal.NiagaraActor):
            sys_path = None
            try:
                sys_path = a.get_editor_property('niagara_component').get_editor_property('asset').get_path_name()
            except Exception:
                pass
            report['vfx'].append({'label': label, 'class': cls, 'folder': folder,
                                  'system': sys_path,
                                  'location': [round(v, 2) for v in a.get_actor_location().to_tuple()]})
            continue

        if isinstance(a, unreal.PostProcessVolume):
            s = a.get_editor_property('settings')
            report['post_process'].append({
                'label': label, 'folder': folder,
                'enabled': bool(a.get_editor_property('enabled')),
                'unbound': bool(a.get_editor_property('unbound')),
                'blend_weight': float(a.get_editor_property('blend_weight')),
                'priority': float(a.get_editor_property('priority')),
                'bloom': float(s.get_editor_property('bloom_intensity')),
                'vignette': float(s.get_editor_property('vignette_intensity')),
                'grain': float(s.get_editor_property('film_grain_intensity')),
                'fringe': float(s.get_editor_property('scene_fringe_intensity')),
                'exposure_method': str(s.get_editor_property('auto_exposure_method')),
                'exposure_bias': float(s.get_editor_property('auto_exposure_bias')),
            })
            continue

        if isinstance(a, unreal.Light):
            report['lights'].append(record_light(a, label, cls, folder))
            continue

        try:
            comps = a.get_components_by_class(unreal.MeshComponent) or []
        except Exception:
            comps = []
        for comp in comps:
            slots = component_slots(comp)
            if slots:
                report['mesh_slots'].append({
                    'actor': label, 'class': cls, 'folder': folder,
                    'component': comp.get_name(), 'slots': slots,
                })
        if not comps:
            report['non_mesh_actors'].append({'label': label, 'class': cls, 'folder': folder})

    unique_mats = {}
    for rec in report['mesh_slots']:
        for s in rec['slots']:
            if s['material']:
                unique_mats[s['material']] = unique_mats.get(s['material'], 0) + 1
    report['summary']['unique_materials'] = len(unique_mats)
    report['summary']['material_use'] = dict(sorted(unique_mats.items(), key=lambda kv: -kv[1]))
    report['summary']['legacy_materials'] = sorted(
        m for m in unique_mats
        if ('OneDriveRigs' in m or '/Instances/MI_Toon_' in m or 'UniversalFilm_20261016' in m
            or '/Melodia/' in m))
    report['summary']['textured_instances'] = sorted({
        s['material'] for rec in report['mesh_slots'] for s in rec['slots']
        if s.get('overrides', {}).get('textures')
        and '__error__' not in s['overrides']['textures']})
    report['summary']['texture_weight_nonzero'] = sorted({
        s['material'] for rec in report['mesh_slots'] for s in rec['slots']
        if abs(s.get('overrides', {}).get('scalars', {}).get('TextureWeight', 0.0)) > 0.001})
    report['summary']['worldgrid_slots'] = [
        {'actor': rec['actor'], 'component': rec['component'], 'slot': s['slot']}
        for rec in report['mesh_slots'] for s in rec['slots']
        if s['material'] and s['material'].endswith('WorldGridMaterial.WorldGridMaterial')]

    path = OUT / 'level_material_vfx_audit.json'
    path.write_text(json.dumps(report, indent=2), encoding='utf-8')

    print('AUDIT_OK world=%s actors=%d material_records=%d unique_materials=%d'
          % (report['world'], report['actor_count'], len(report['mesh_slots']),
             report['summary']['unique_materials']))
    print('LEGACY=%d' % len(report['summary']['legacy_materials']))
    for m in report['summary']['legacy_materials'][:60]:
        print('  LEGACY ' + m)
    print('TEXTURED=%d TEXTURE_WEIGHT_NONZERO=%d'
          % (len(report['summary']['textured_instances']),
             len(report['summary']['texture_weight_nonzero'])))
    print('VFX=%d LIGHTS=%d PPV=%d' % (len(report['vfx']), len(report['lights']), len(report['post_process'])))
    for v in report['vfx']:
        print('  VFX %s -> %s' % (v['label'], v['system']))
    for p in report['post_process']:
        print('  PPV %s enabled=%s unbound=%s weight=%.2f prio=%.1f bloom=%.2f vig=%.2f grain=%.3f fringe=%.2f bias=%.2f'
              % (p['label'], p['enabled'], p['unbound'], p['blend_weight'], p['priority'],
                 p['bloom'], p['vignette'], p['grain'], p['fringe'], p['exposure_bias']))
    print('WORLDGRID=%d' % len(report['summary']['worldgrid_slots']))
    for w in report['summary']['worldgrid_slots']:
        print('  WORLDGRID %s | %s | slot %d' % (w['actor'], w['component'], w['slot']))
    print('REPORT ' + str(path))


main()

