"""Compare actor vs cine-component transforms for the three hero cameras."""
import unreal

LABELS = ['Film_Cam_OfficeMedium', 'Film_Cam_OfficeWide',
          'CineCam_Hero_WindowEstablishing', 'CineCam_Hero_DeskLineup',
          'CineCam_Hero_LowAngleTension']

for a in unreal.EditorLevelLibrary.get_all_level_actors():
    try:
        label = a.get_actor_label()
    except Exception:
        continue
    if label not in LABELS:
        continue
    loc = a.get_actor_location()
    rot = a.get_actor_rotation()
    print('%s ACTOR loc=(%.1f,%.1f,%.1f) rot=(p%.1f y%.1f r%.1f)'
          % (label, loc.x, loc.y, loc.z, rot.pitch, rot.yaw, rot.roll))
    try:
        cc = a.get_cine_camera_component()
        cl = cc.get_world_location()
        cr = cc.get_world_rotation()
        print('  COMP loc=(%.1f,%.1f,%.1f) rot=(p%.1f y%.1f r%.1f) focal=%.1f' % (
            cl.x, cl.y, cl.z, cr.pitch, cr.yaw, cr.roll,
            cc.get_editor_property('current_focal_length')))
        fb = cc.get_editor_property('filmback')
        print('  FILMBACK %.2f x %.2f' % (fb.sensor_width, fb.sensor_height))
        f = cc.get_editor_property('focus_settings')
        print('  FOCUS method=%s distance=%.1f' % (f.focus_method, f.focus_distance))
    except Exception as exc:
        print('  NO CINE COMPONENT: %s' % str(exc)[:90])
