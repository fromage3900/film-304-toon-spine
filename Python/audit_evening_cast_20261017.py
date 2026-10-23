"""Read-only live cast baseline. Writes evidence only; never changes UE assets."""
import json
from pathlib import Path
from datetime import datetime, timezone
import unreal

ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / 'Saved/Audit/EveningExecution_20261017/live_cast_baseline.json'

def path(value):
    return value.get_path_name() if value else None

def vector(value):
    return [value.x, value.y, value.z]

def prop(value, name, default=None):
    try:
        return value.get_editor_property(name)
    except Exception:
        return default

def main():
    spec = json.loads((ROOT / 'specs/cast/cast_rigs.v1.json').read_text())
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    rows = []
    for actor in actors:
        comp = actor.get_component_by_class(unreal.SkeletalMeshComponent)
        if not comp:
            continue
        mesh = prop(comp, 'skeletal_mesh_asset')
        origin, extent = actor.get_actor_bounds(False)
        slots = []
        for index, slot in enumerate(prop(mesh, 'materials', [])):
            material = comp.get_material(index)
            textures = []
            for param in prop(material, 'texture_parameter_values', []):
                info = prop(param, 'parameter_info')
                tex = prop(param, 'parameter_value')
                textures.append({'parameter': str(prop(info, 'name')),
                                 'texture': path(tex),
                                 'virtual_texture': prop(tex, 'virtual_texture_streaming')})
            slots.append({'index': index, 'slot': str(prop(slot, 'material_slot_name')),
                          'mesh_default': path(prop(slot, 'material_interface')),
                          'effective_material': path(material),
                          'parent': path(prop(material, 'parent')), 'texture_overrides': textures})
        rows.append({'actor': actor.get_actor_label(), 'mesh': path(mesh),
                     'skeleton': path(prop(mesh, 'skeleton')),
                     'location': vector(actor.get_actor_location()),
                     'scale': vector(actor.get_actor_scale3d()),
                     'bounds_origin': vector(origin), 'bounds_extent': vector(extent),
                     'height_cm': extent.z * 2, 'bottom_z': origin.z - extent.z,
                     'animation_mode': str(prop(comp, 'animation_mode')),
                     'slots': slots})
    report = {'time_utc': datetime.now(timezone.utc).isoformat(),
              'project': str(ROOT),
              'world': path(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()),
              'spec_cast': list(spec['characters']), 'skeletal_actors': rows,
              'proof': 'live editor readback only; no visual or fresh-open certification'}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'report': str(OUT), 'cast': [
        {'actor': row['actor'], 'height_cm': row['height_cm'],
         'mesh': row['mesh'], 'slots': len(row['slots'])} for row in rows]}, indent=2))

if __name__ == '__main__':
    main()
