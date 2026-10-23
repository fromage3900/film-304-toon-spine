"""Prepare cast retarget assets on the existing Humber editor; no scene changes.

Uses the existing Sparrow IK definition as donor. This prepares mappings only:
alignment, foot contact, facial animation and film-quality motion remain gates.
Never overwrites existing assets, source meshes, skeletons or the old retargeter.
"""
import json
import time
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
DEST = '/Game/Retarget/Film304Idle_20261017'
OUT = ROOT / 'Saved/Audit/Film304Idle_20261017'
CAST = {
    'Dana': '/Game/Staging/Film304Repaired_20261017/Dana/SK_Dana_Film304_v10e',
    'David': '/Game/Staging/Film304Repaired_20261017/David/SK_David_Film304_v01',
    'Sam': '/Game/Staging/Film304Repaired_20261017/Sam/SK_Sam_Film304_v01',
    'Spider': '/Game/Staging/CastRigs_20261016/Spider/Spider_Deform_v2',
}


def human_chains():
    rows = [('Spine', 'Spine1_M', 'Chest_M'),
            ('Neck', 'Neck_M', 'NeckPart2_M'), ('Head', 'Head_M', 'Head_M')]
    for side, label in [('L', 'Left'), ('R', 'Right')]:
        for chain, start, end in [('Leg', 'Hip', 'Ankle'), ('Foot', 'Toes', 'Toes'),
                                  ('Clavicle', 'Scapula', 'Scapula'),
                                  ('Arm', 'Shoulder', 'Wrist')]:
            rows.append((label+chain, start+'_'+side, end+'_'+side))
        for finger in ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']:
            rows.append((label+finger, finger+'Finger1_'+side, finger+'Finger3_'+side))
    return rows


def spider_chains():
    rows = [('Body', 'wolfSpider_Torso', 'wolfSpider_Torso'),
            ('Head', 'wolfSpider_Head', 'wolfSpider_Head'),
            ('Abdomen', 'wolfSpider_Thorax', 'wolfSpider_ThoraxTip')]
    for side in ['L', 'R']:
        for leg in 'ABCD':
            prefix = 'wolfSpider_Leg'+leg+'_'+side
            rows.append(('Leg'+leg+'_'+side, prefix+'_a', prefix+'_tip'))
        rows.append(('Fang_'+side, 'wolfSpider_fangA_'+side+'_a', 'wolfSpider_fangA_'+side+'_c'))
    return rows


def rig_readback(rig):
    c = unreal.IKRigController.get_controller(rig)
    return [{'name': str(x.chain_name),
             'start': str(c.get_retarget_chain_start_bone(x.chain_name)),
             'end': str(c.get_retarget_chain_end_bone(x.chain_name))}
            for x in c.get_retarget_chains()]


def main(apply=False, allow_user_dirty=False):
    assert unreal.Paths.get_project_file_path().endswith('HumberToonShader.uproject')
    lease_path = ROOT / 'Saved/Coord/editor_lease.json'
    if lease_path.exists():
        lease = json.loads(lease_path.read_text(encoding='utf-8-sig'))
        assert float(lease.get('expires_epoch') or 0) < time.time(), 'Active editor lease'
    OUT.mkdir(parents=True, exist_ok=True)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    donor = unreal.load_asset('/Game/Retarget/IKRig_Sparrow')
    assert donor
    report = {'status': 'preparing', 'scene_modified': False, 'rigs': {},
              'retargeters': {}, 'animation_exported': False,
              'visual_gate': False, 'loop_gate': False,
              'donor_rig': donor.get_path_name(),
              'qualification': 'Explicit chain preparation only; no film-quality or loop claim.'}
    # Preflight every character before creating anything.
    preflight = {}
    for character, path in CAST.items():
        mesh = unreal.load_asset(path)
        assert mesh, path
        modifier = unreal.SkeletonModifier()
        assert modifier.set_skeletal_mesh(mesh)
        names = {str(n) for n in modifier.get_all_bone_names()}
        chains = spider_chains() if character == 'Spider' else human_chains()
        for _, start, end in chains:
            assert start in names and end in names, (character, start, end)
            ancestor = end
            while ancestor != start and ancestor not in ['', 'None']:
                ancestor = str(modifier.get_parent_name(ancestor))
            assert ancestor == start, ('Non-contiguous deform chain', character, start, end)
        preflight[character] = {'mesh': path, 'bone_count': len(names),
                                'validated_chains': len(chains)}
    (OUT/'cast_chain_preflight.json').write_text(json.dumps(preflight, indent=2))
    if not apply:
        print(json.dumps({'mode': 'read_only_preflight', 'cast': preflight,
                          'assets_created': False}))
        return
    if not allow_user_dirty:
        assert not unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages(), 'Dirty assets: recheck ownership'
    for character, path in CAST.items():
        mesh = unreal.load_asset(path)
        name = 'IKR_'+character+'_FilmIdle_v01'
        rig = unreal.load_asset(DEST+'/'+name)
        chains = spider_chains() if character == 'Spider' else human_chains()
        if not rig:
            rig = tools.create_asset(name, DEST, unreal.IKRigDefinition, unreal.IKRigDefinitionFactory())
            c = unreal.IKRigController.get_controller(rig)
            assert c.set_skeletal_mesh(mesh)
            assert c.set_retarget_root('wolfSpider_Root' if character == 'Spider' else 'Root_M')
            for chain, start, end in chains:
                assert str(c.add_retarget_chain(chain, start, end, '')) == chain
            assert unreal.EditorAssetLibrary.save_loaded_asset(rig)
        actual = rig_readback(rig)
        assert {(r['name'], r['start'], r['end']) for r in actual} == set(chains)
        report['rigs'][character] = {'asset': rig.get_path_name(), 'mesh': path, 'chains': actual}
        if character == 'Spider':
            report['rigs'][character]['blocker'] = 'No compatible eight-leg donor identified. Humanoid mapping is invalid; native idle authoring required.'
            continue
        name = 'RTG_SparrowTo'+character+'_FilmIdle_v01'
        retargeter = unreal.load_asset(DEST+'/'+name)
        if not retargeter:
            retargeter = tools.create_asset(name, DEST, unreal.IKRetargeter, unreal.IKRetargetFactory())
            c = unreal.IKRetargeterController.get_controller(retargeter)
            c.set_ik_rig(unreal.RetargetSourceOrTarget.SOURCE, donor)
            c.set_ik_rig(unreal.RetargetSourceOrTarget.TARGET, rig)
            c.add_default_ops()
            for chain, _, _ in chains:
                assert c.set_source_chain(chain, chain), chain
            assert unreal.EditorAssetLibrary.save_loaded_asset(retargeter)
        c = unreal.IKRetargeterController.get_controller(retargeter)
        assert c.get_num_retarget_ops() > 0
        mappings = {chain: str(c.get_source_chain(chain)) for chain, _, _ in chains}
        assert all(k == v for k, v in mappings.items()), mappings
        report['retargeters'][character] = {'asset': retargeter.get_path_name(),
            'operations': c.get_num_retarget_ops(), 'mapping': mappings,
            'alignment_tested': False, 'contact_tested': False,
            'note': 'Sparrow donor setup; UAL and Melusina source skeletons require their own source IK definition.'}
        (OUT/'retarget_preparation.json').write_text(json.dumps(report, indent=2))
    report['status'] = 'rig_and_mapping_preparation_verified_motion_pending'
    (OUT/'retarget_preparation.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report))


if __name__ == '__main__':
    main()
