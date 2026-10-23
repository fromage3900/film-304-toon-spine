"""Compose the final task1_face_eyes.json from the measured artifacts (no new claims)."""
import json, hashlib, datetime
from pathlib import Path

BASE = Path('G:/film-304-toon-spine/Saved/OfflineIntake/20261017/task1_face_eyes')
REP = BASE / 'report'
SOURCE = BASE / 'scratch' / 'Dana_Rig_v1.5.mb'

census = json.loads((REP / 'inspection_face_eyes.json').read_text())
export = json.loads((REP / 'v09_export_report.json').read_text())
gate = json.loads((REP / 'v09_fbx_gate.json').read_text())
raw = json.loads((REP / 'v09_fbx_materials_morphs.json').read_text())
eye_bones = json.loads((REP / 'v09_eye_bones.json').read_text())
houdini = json.loads((REP / 'v09_houdini_verification.json').read_text())
preview = json.loads((REP / 'v09_preview_report.json').read_text())

asface = next((b for b in census['blendshapes'] if b['short'] == 'asFaceBS'), {})
face_channels = sorted(asface.get('aliases', {}).values())
sdk = census.get('sdk_ctrl_driven', [])
def drv_map(attr_sub):
    return [{'driver': row['driver'], 'driven': row['driven']} for row in sdk
            if any(attr_sub in d for d in row['driven'])]

V08_SLOTS = ['danaskin_mat', 'danahair_mat', 'danaeye_mat', 'danacornea_mat', 'danaeyeint_mat',
             'danapants_mat', 'danashirt_mat', 'danashoes_mat', 'danagum_mat', 'danatongue_mat']

out = {
  'task': 'task1_face_eyes',
  'composed_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'source_scene': {
    'path': str(SOURCE),
    'sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'source_unchanged_by_all_runs': bool(census.get('source_unchanged') and export.get('source_unchanged')),
    'original_intake_untouched': True,
    'maya_version': census.get('maya_version'),
    'joints_in_native_scene': census.get('joints_total'),
  },
  'face_animation': {
    'verdict': ('HYBRID: the rig has BOTH authored blendShape channels and joint/SDK-driven '
                'face deformation. 17 blendShape nodes exist; the face expression set lives on '
                'asFaceBS (49 channels on Dana_Body_GEO). Eyelids and jaw are joint+SDK driven; '
                'the region channels are plumbing. Eyelash squint channels exist separately.'),
    'blendshape_node_count': census.get('blendshape_count'),
    'blendshape_nodes': [{'node': b['short'], 'base': b['base_meshes'], 'channels': sorted(b.get('aliases', {}).values())}
                         for b in census['blendshapes']],
    'asFaceBS_channels_all': face_channels,
    'asFaceBS_expression_channels': [c for c in face_channels if 'Region' not in c and c not in ('bodyBreath_GEO',)],
    'sdk_wiring_examples': {
      'brow': drv_map('brow_'),
      'mouth_smile_frown_wide_narrow': drv_map('mouth_'),
      'cheek_nose_squint': drv_map('cheek_') + drv_map('nose_') + drv_map('eye_squint'),
      'eye_iris_pupil_lattices': drv_map('FfdLattice')[:6],
      'blink_lid': drv_map('.blink_L') + drv_map('.blink_R'),
      'jaw': drv_map('FKSDK1Jaw_M'),
    },
    'sdk_face_related_curve_count': census.get('sdk_face_related_count'),
    'sdk_ctrl_driven_curve_count': census.get('sdk_ctrl_driven_count'),
    'joint_systems': {
      'eyelids': 'upperLidMain0-12 / lowerLidMain0-14 per side under faceLid (LidSetup_L/R); eyelash meshes skinned to 13 lid joints each',
      'lips': 'upper/lower lip translate, rotate and scale joints (0-8 per side) under FaceMotionSystem|LipSetup',
      'jaw': 'Jaw_M under faceHeadJoint, SDK-driven from ctrlMouth_M.translateY (measured open extreme -10.0)',
      'eyelash_squint_blendshapes': ['Eyelash_L_blendshapes', 'Eyelash_R_blendshapes'],
      'breath': 'Breath_Deform (bodyBreath_GEO / shirtBreath_GEO) driven from RootX_M per rig ReadMe v1.5',
    },
  },
  'eye_setup': {
    'iris_separate_geometry': False,
    'iris_is': ('per-face material split on the eyeball meshes Dana_Eye_Lf_GEO / Dana_Eye_Rt_GEO: '
                'danaIris_mat on faces f[0:63] and f[992:1119] (front+back caps), danaEye_mat on f[64:991] (sclera)'),
    'measured_native_assignments': [row for row in census['material_inventory'] if 'Eye' in row['shape']],
    'eye_meshes': {
      'eyeball': 'Dana_Eye_Lf/Rt_GEO (1121 verts) - danaEye_mat + danaIris_mat per-face',
      'cornea': 'Dana_Cornea_Lf/Rt_GEO (161 verts) - danaCornea_mat (blinn)',
      'eye_interior': 'Dana_EyeInt_Lf/Rt_GEO (51 verts) - danaEyeInt_mat (surfaceShader)',
      'eyelashes': 'Dana_Eyelashes_Lf/Rt_GEO (39 verts each) - danaHair_mat',
      'eyebrows': 'Dana_Eyebrows_GEO (178 verts) - danaHair_mat (no skin cluster; rigid to Head_M)',
    },
    'eye_look_mechanism': ('bone-driven, NOT a morph: Eye_L/R + Iris_L/R + Pupil_L/R joints are '
                           'skinned to the eyeball/cornea/eyeint meshes (skinCluster108-111, 98-100); '
                           'ctrlEye_*.translate drives the eye joints. The exported FBX skeleton '
                           'carries these bones, so UE can aim the eyes by rotating the Eye bones.'),
    'iris_pupil_dilation': ('ctrlEye_*.iris and .pupil drive FFD lattices (CorneaFfdLattice, '
                            'IrisFfdLattice, EyeIntFfdLattice, PupilFfdLattice) - lattice deformation, '
                            'not transported by this export chain'),
  },
  'what_the_v08_10slot_mapping_lost': {
    'v08_fbx_materials_measured': [
      'danaCornea_mat', 'danaEyeInt_mat', 'danaEye_mat', 'danaGum_mat', 'danaHair_mat',
      'danaPants_mat', 'danaShirt_mat', 'danaShoes_mat', 'danaSkin_mat', 'danaTongue_mat'],
    'mechanism': ('the v08 chain assigned each duplicated mesh entirely to its FIRST shading '
                  'engine (cmds.sets forceElement sgs[0]); every per-face split was flattened'),
    'lost': [
      {'slot': 'danaIris_mat', 'consequence': 'iris faces render with the sclera material; eyes read as blank spheres; the UE-side MI_DanaFilm_Iris has nothing to bind to'},
      {'slot': 'danaTeeth_mat', 'consequence': 'teeth faces render with the gum material (danagum_mat survives; danateeth_mat does not appear in UE)'},
    ],
    'cornea_hidden_helper': ('the cornea slot maps to M_ImportHelpersHidden on the UE side; the FBX '
                             'carries danaCornea_mat correctly (measured), so the substitution happens '
                             'in the UE import/mapping layer, not in the FBX'),
  },
  'v09_export': {
    'file': str(BASE / 'fbx' / 'Dana_CleanSkin_v09.fbx'),
    'bytes': export.get('candidate_bytes'),
    'chain': ('extends Tools/export_dana_clean_skin_v08.py (same 19-mesh contract, exact native '
              'skin weight copy + bounded transport cleanup, same FBX export settings, source never '
              'saved) as Tools/export_dana_clean_skin_v09_face_morphs.py'),
    'morphs_baked': export.get('morph_bakes'),
    'morph_channels_in_fbx': raw['blendshapes'].get('FilmExport:FaceMorphs'),
    'morph_deltas_on_fbx_import_cm': gate['morph_check']['deltas_cm'],
    'requested_but_missing': [
      {'name': 'Mouth_Open', 'reason': 'no authored lip-curl open channel; mouth opening is the jaw SDK (baked as Jaw_Open). Add only if a separate lip pose is wanted.'},
      {'name': 'Eye_Look_L', 'reason': 'eye look is bone-driven (Eye/Iris/Pupil joints exported and skinned); not an authored morph. In UE, rotate the Eye bones instead.'},
      {'name': 'Eye_Look_R', 'reason': 'same as Eye_Look_L'},
      {'name': 'Eye_Look_Up', 'reason': 'same as Eye_Look_L'},
      {'name': 'Eye_Look_Down', 'reason': 'same as Eye_Look_L'},
    ],
    'also_available_not_in_requested_set': [
      'brow_outerRaiser_L/R, brow_innerRaiser_L/R (baked INTO Brow_Up), brow_innerLowerer_L/R (baked into Brow_Down), brow_squeeze_L/R',
      'mouth_smile_C/L/R (baked into Smile), mouth_narrow_C/L/R, cheek_raiser/puff/suck_L/R',
      'nose_wrinkler/dilator/compressor_L/R, eye_squint_L/R, Eyelash_squint_L/R (native channels on the eyelash meshes)',
    ],
    'topology_preserved': {
      'triangles_houdini_total': houdini.get('total_triangles'),
      'ue_v08_reference_triangles': 46041,
      'triangles_match': houdini.get('total_triangles') == 46041,
      'fbx_bone_models': raw.get('bone_models'),
      'v08_fbx_bone_models': 1231,
      'bones_match': raw.get('bone_models') == 1231,
      'render_mesh_count': 19,
      'skeleton_regression_vs_v08_houdini': houdini.get('skeleton_regression_pass'),
    },
    'slot_mapping_delta_from_v08': {
      'v08_10_slots': V08_SLOTS,
      'v09_materials_measured': raw.get('materials'),
      'delta': ('the 10 v08 slot names are all present and unchanged; v09 ADDS the two restored '
                'source splits (danaIris_mat on the eyeball caps, danaTeeth_mat on teeth) so the '
                'UE section count goes 10 -> 12. Triangle count and bone count are identical to v08. '
                'This is the fix for the blank-eyes defect; flip PRESERVE via the export script '
                '(revert the per-face replication to sgs[0]) if the strict 10-slot contract must hold.'),
    },
  },
  'verification': {
    'maya_fbx_gate': {
      'tool': 'Tools/gate_dana_v09_fbx.py (opens only the exported FBX)',
      'mesh_vertex_pass': gate.get('mesh_vertex_pass'),
      'mesh_skin_pass': gate.get('mesh_skin_pass'),
      'mesh_material_pass': gate.get('mesh_material_pass'),
      'morph_pass': gate.get('morph_pass'),
      'joint_count_imported': gate.get('joint_count'),
      'gate_pass': gate.get('gate_pass'),
      'fk_head15_copy_track_max_error_cm': export.get('fk_head15_max_error_cm'),
    },
    'houdini_independent_readback': {
      'tool': 'Tools/verify_dana_v09_houdini.py (hython, kinefx fbxcharacterimport)',
      'profile_pass_19_meshes': houdini.get('profile_pass'),
      'morph_pass': houdini.get('morph_pass'),
      'total_triangles': houdini.get('total_triangles'),
      'total_polygons': houdini.get('total_polygons'),
      'capture_skeleton': houdini.get('capture_skeleton'),
      'animated_hierarchy': houdini.get('animated_hierarchy'),
      'import_errors': houdini.get('import_errors'),
      'gate_pass': houdini.get('gate_pass'),
    },
    'blender_raw_fbx_audit': {
      'tool': 'Tools/audit_dana_fbx_materials_morphs.py (io_scene_fbx.parse_fbx, no DCC import)',
      'materials': raw.get('materials'),
      'material_count': raw.get('material_count'),
      'bone_models': raw.get('bone_models'),
      'blendshape_channels': raw.get('blendshapes'),
      'morph_shape_geometries': raw.get('morph_shape_geometries'),
    },
  },
  'preview': {
    'renders_from_exported_fbx': {k: v['files'] for k, v in preview.get('shots', {}).items()},
    'body_delta_per_shot_cm': {k: v['body_delta_cm'] for k, v in preview.get('shots', {}).items()},
    'required_shot': 'face_blink_L_browUp_jawOpen.png = Blink_L + Brow_Up + Jaw_Open all at weight 1.0',
    'camera': preview.get('camera'),
    'note': ('flat presentation colors were assigned in the scratch session (native texture paths '
             'do not resolve offline); the cornea is rendered transparent so the restored iris reads'),
  },
  'not_verified': [
    'Unreal import behaviour of v09 (slot count after UE import, whether UE binds MI_DanaFilm_Iris to the restored danaIris_mat section, and whether UE exposes the 8 morph targets) - no UE access from this offline agent',
    'per-channel morph-target geometry deltas inside Houdini (packed-primitive content not readable there; the same deltas were measured on the FBX import in Maya instead: 0.62-1.66 cm per channel)',
    'eye aim quality (the rig aims eyes via ctrlEye translate driving eye joints; not exercised in the preview renders)',
    'the cornea slot mapping to M_ImportHelpersHidden is a UE-side substitution; only its absence from the FBX could be ruled out here (FBX carries danaCornea_mat)',
    'native texture paths were not exercised in renders (black-skin failure observed with textured shaders in the scratch scene, worked around with flat presentation colors)',
  ],
  'artifacts': {
    'fbx': str(BASE / 'fbx' / 'Dana_CleanSkin_v09.fbx'),
    'report_jsons': [str(p) for p in sorted(REP.glob('*.json'))],
    'preview': [str(p) for p in sorted((BASE / 'preview').rglob('*.png'))],
    'logs': [str(p) for p in sorted((BASE / 'log').glob('*'))],
    'scratch_copy': str(SOURCE),
  },
}

(REP / 'task1_face_eyes.json').write_text(json.dumps(out, indent=2, default=str))
print(json.dumps({'written': str(REP / 'task1_face_eyes.json'),
                  'face_channels': len(face_channels),
                  'morph_channels_in_fbx': out['v09_export']['morph_channels_in_fbx'],
                  'triangles_match': out['v09_export']['topology_preserved']['triangles_match'],
                  'bones_match': out['v09_export']['topology_preserved']['bones_match'],
                  'maya_gate_pass': out['verification']['maya_fbx_gate']['gate_pass'],
                  'houdini_gate_pass': out['verification']['houdini_independent_readback']['gate_pass']}))
