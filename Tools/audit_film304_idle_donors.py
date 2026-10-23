"""Blender offline assessment of existing Melodia UAL takes. No source writes."""
import json
import math
from pathlib import Path
import bpy

ROOT = Path('G:/film-304-toon-spine')
SOURCE = Path('C:/EnvironmentPortfolio/BS_GodFile/Imports/Animations/Cascadeur/Inbox/A_CAS_Melusina_Idle_Loop.fbx')
OUT = ROOT / 'Saved/Audit/Film304Idle_20261017'


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(SOURCE), use_anim=True, use_image_search=False)
    arm, = [o for o in bpy.data.objects if o.type == 'ARMATURE']
    scene = bpy.context.scene
    fps = scene.render.fps / scene.render.fps_base
    rows = []
    for take in ['Idle_Loop', 'Idle_Talking_Loop', 'Sitting_Idle_Loop']:
        matches = [a for a in bpy.data.actions if a.name.rsplit('|', 1)[-1] == take]
        assert len(matches) == 1, (take, len(matches))
        action = matches[0]
        arm.animation_data_create()
        arm.animation_data.action = action
        if len(action.slots):
            arm.animation_data.action_slot = action.slots[0]
        start, end = action.frame_range
        samples = []
        # Include one sample before/after the seam for velocity comparison.
        for frame in [start, start+1, end-1, end, (start+end)/2]:
            scene.frame_set(int(frame), subframe=frame-int(frame))
            bpy.context.view_layer.update()
            samples.append({b.name: arm.matrix_world @ b.matrix for b in arm.pose.bones})
        scale_cm = scene.unit_settings.scale_length * 100
        translation_error = 0.0
        rotation_error = 0.0
        velocity_error = 0.0
        mid_motion = 0.0
        for name in samples[0]:
            mats = [s[name] for s in samples]
            translation_error = max(translation_error, (mats[0].translation-mats[3].translation).length*scale_cm)
            rotation_error = max(rotation_error, math.degrees(mats[0].to_quaternion().rotation_difference(mats[3].to_quaternion()).angle))
            vin = mats[3].translation-mats[2].translation
            vout = mats[1].translation-mats[0].translation
            velocity_error = max(velocity_error, (vin-vout).length*scale_cm*fps)
            mid_motion = max(mid_motion, (mats[4].translation-mats[0].translation).length*scale_cm)
        seconds = (end-start)/fps
        rows.append({'take': take, 'action': action.name, 'start': start, 'end': end,
            'stored_samples': int(end-start+1), 'evaluated_fps': fps, 'duration_seconds': seconds,
            'endpoint_max_bone_position_cm': translation_error,
            'endpoint_max_bone_rotation_degrees': rotation_error,
            'endpoint_velocity_difference_cm_s': velocity_error,
            'midpoint_max_motion_cm': mid_motion,
            'proposed_output': {'fps': 24, 'unique_frames': 48, 'endpoint_sample': 48,
                'duration_seconds': 2, 'speed_multiplier_full_cycle': seconds/2},
            'seam_position_rotation_gate': translation_error < 0.05 and rotation_error < 0.1,
            'retarget_contact_and_visual_gate': False})
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'source': str(SOURCE), 'source_modified': False, 'tool': bpy.app.version_string,
        'source_mesh_present': any(o.type == 'MESH' for o in bpy.data.objects),
        'qualification': 'Original donor transforms only; cast deformation, facial expressions, output seam velocity and film quality unverified.',
        'candidates': rows}
    (OUT/'donor_motion_audit.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
