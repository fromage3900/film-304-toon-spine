"""Align the existing six fixtures to the verified ceiling in the assembly copy."""
import json
from pathlib import Path
import unreal

def main():
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert 'L_Film_Office_Assembly_20261018_v01.' in world.get_path_name()
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    bylabel={a.get_actor_label():a for a in actors.get_all_level_actors()}
    report=[]
    for index in range(1,7):
        panel=bylabel['Film_Troffer_%d_Panel'%index]
        housing=bylabel['Film_Troffer_%d_Housing'%index]
        light=bylabel['Film_Troffer_%d_Light'%index]
        location=panel.get_actor_location()
        previous={a.get_actor_label():{'position':list(a.get_actor_location().to_tuple()),
                                      'rotation':[a.get_actor_rotation().pitch,a.get_actor_rotation().yaw,a.get_actor_rotation().roll]}
                  for a in [panel,housing,light]}
        # The source room yaw is -25 degrees; previous fixtures accidentally used pitch.
        for actor,z in [(panel,333.2),(housing,335.7),(light,331.5)]:
            actor.modify();actor.set_actor_location(unreal.Vector(location.x,location.y,z),False,False)
            actor.set_actor_rotation(unreal.Rotator(pitch=-90 if actor==light else 0,
                                      yaw=65 if actor==light else -25,roll=0),False)
        comp=light.get_component_by_class(unreal.RectLightComponent)
        comp.set_source_width(110);comp.set_source_height(50)
        # Keep existing intensity/temperature for the controlled baseline.
        pb=panel.get_actor_bounds(False);hb=housing.get_actor_bounds(False)
        assert abs(hb[0].z+hb[1].z-336.7)<.02
        assert abs(pb[0].z+pb[1].z-(hb[0].z-hb[1].z))<.02
        assert light.get_actor_forward_vector().z<-.999
        report.append({'fixture':index,'previous':previous,'panel_top_cm':pb[0].z+pb[1].z,
                       'housing_top_cm':hb[0].z+hb[1].z,'tile_underside_cm':336.7,
                       'light_forward':list(light.get_actor_forward_vector().to_tuple()),
                       'light_intensity':comp.intensity,'intensity_units':str(comp.intensity_units)})
    # Dedicated review camera leaves every owner camera untouched.
    camera=actors.spawn_actor_from_class(unreal.CineCameraActor,unreal.Vector(-150,-450,180))
    camera.set_actor_label('Film_Cam_Closeout_CeilingReview')
    camera.set_folder_path('Film304/FinalAssembly/Cameras')
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(),
                              unreal.Vector(250,300,325)),False)
    cine=camera.get_cine_camera_component();cine.current_focal_length=24;cine.current_aperture=8
    focus=cine.focus_settings;focus.focus_method=unreal.CameraFocusMethod.DISABLE;cine.focus_settings=focus
    out=Path(unreal.Paths.project_dir())/'Saved/Audit/Closeout_20261018/troffer_alignment.json'
    out.write_text(json.dumps({'fixtures':report,'count':6,'added_duplicate_fixtures':0,
                              'world':world.get_path_name(),'review_camera':camera.get_actor_label()},indent=2))
    print('TROFFER_ALIGNMENT count=6 flush_contacts=True all_lights_down=True')

if __name__=='__main__':main()
