"""Remove the rejected stand-in from owned scenes; preserve UDS composition.

No character render is ready until a validated film-cast mesh and a compatible
retargeted animation are supplied. Sparrow is an animation donor only.
"""
import json
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / 'Saved/Audit/UniversalFilm_20261016'
E = unreal.EditorAssetLibrary
A = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
L = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
report = json.loads((AUDIT / 'scenes.json').read_text())
changes = []
for scene in report['scenes']:
    if not L.load_level(scene['map']):
        raise RuntimeError('Cannot load owned scene ' + scene['map'])
    subjects = [actor for actor in A.get_all_level_actors()
                if actor.get_actor_label().startswith('Film_Subject_')]
    if len(subjects) != 1:
        raise RuntimeError('Expected one owned subject in ' + scene['map'])
    actor = subjects[0]
    component = actor.get_component_by_class(unreal.SkeletalMeshComponent)
    component.set_animation(None)
    component.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    dana = E.load_asset('/Game/Meshes/Office/Props/C_DanaRenderTest_OSC')
    component.set_skeletal_mesh_asset(dana)
    profile = json.loads((ROOT / 'specs/humber_toon_spine/universal_film_cast.v1.json').read_text())
    for index, slot in enumerate(dana.materials):
        name = str(slot.material_slot_name).lower()
        part = profile['slots'].get(name)
        if part is None:
            raise RuntimeError('Unknown Dana slot ' + name)
        path = ('/Game/Materials/Masters/UniversalFilm_20261016/M_ImportHelpersHidden'
                if part == 'Hidden' else '/Game/Materials/Instances/UniversalFilm_20261016/MI_Film_' + part)
        component.set_material(index, E.load_asset(path))
    actor.set_actor_label('Film_Subject_Dana_PENDING_VALIDATED_RIG_AND_RETARGET')
    actor.set_actor_hidden_in_game(True)
    actor.set_actor_scale3d(unreal.Vector(1, 1, 1))
    actor.set_actor_location(unreal.Vector(), False, False)
    for job in scene['jobs']:
        sequence = E.load_asset(job['sequence'])
        for binding in list(sequence.get_bindings()):
            if str(binding.get_name()) == 'Sparrow motion stand-in':
                binding.remove()
        if not E.save_loaded_asset(sequence, False):
            raise RuntimeError('Cannot remove rejected animation binding')
        job['render_ready'] = False
        job['blocked_reason'] = 'Film cast must use a validated skinned mesh and retargeted source action; no Sparrow character and no T-pose render'
    if not unreal.EditorLoadingAndSavingUtils.save_current_level():
        raise RuntimeError('Owned scene reconciliation save failed')
    remaining = [a.get_actor_label() for a in A.get_all_level_actors()
                 if 'SPARROW' in a.get_actor_label().upper()]
    if remaining:
        raise RuntimeError('A rejected Sparrow actor remains: ' + str(remaining))
    sky = [a for a in A.get_all_level_actors() if a.get_actor_label() == 'Film_UDS_Daylight']
    if len(sky) != 1:
        raise RuntimeError('Preserve one UDS daylight actor per scene')
    scene['subject'] = 'Dana placeholder hidden from rendering; validated cast rig/action pending'
    scene['pose'] = 'No approved action yet. Sparrow source clip is donor-only.'
    scene['render_ready'] = False
    changes.append({'map': scene['map'], 'sparrow_actors': 0,
                    'subject_hidden_from_render': bool(actor.get_editor_property('hidden')), 'uds_count': len(sky)})
report.pop('motion_job', None)
report['result'] = 'uds_compositions_saved_character_render_blocked_on_cast_rig_and_retarget'
report['animation_source'] = '/Game/ParagonSparrow/Characters/Heroes/Sparrow/Animations/Jog_Fwd'
report['rejected'] = 'Sparrow character stand-in rejected by owner; all source character bindings removed'
(AUDIT / 'scenes.json').write_text(json.dumps(report, indent=2))
(AUDIT / 'cast_reconciliation.json').write_text(json.dumps({'result': 'source_character_removed', 'scenes': changes}, indent=2))
print('FILM_CAST_RECONCILED')
