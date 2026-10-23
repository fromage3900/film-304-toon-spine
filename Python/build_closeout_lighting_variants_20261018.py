"""Native, reversible light-only variants for the assembled Office map."""
import json
import math
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir());OUT=ROOT/'Saved/Audit/Closeout_20261018'
DEST='/Game/Variants/Film304Closeout_20261018'
NAME='LVS_Office_LightingCloseout_v01'
PROPS={'intensity':'Intensity','light_color':'Light Color','use_temperature':'Use Temperature','temperature':'Temperature'}

def main():
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert 'L_Film_Office_Assembly_20261018_v02.' in world.get_path_name()
    assert not unreal.EditorAssetLibrary.does_asset_exist(DEST+'/'+NAME)
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    # Ceiling wash is a shot light, not emissive material edits or global exposure.
    yaw=math.radians(-25)
    for index,(x,y) in enumerate([(100,100),(250,500),(-100,-100)],1):
        loc=unreal.Vector(x*math.cos(yaw)-y*math.sin(yaw),x*math.sin(yaw)+y*math.cos(yaw),260)
        a=actors.spawn_actor_from_class(unreal.RectLight,loc)
        a.set_actor_label('Film_Closeout_CeilingWash_%02d'%index)
        a.set_folder_path('Film304/FinalAssembly/Lighting')
        a.set_actor_rotation(unreal.Rotator(pitch=90,yaw=-25,roll=0),False)
        c=a.rect_light_component;c.set_intensity(0);c.set_editor_property('intensity_units',unreal.LightUnits.CANDELAS)
        c.set_source_width(180);c.set_source_height(180);c.set_attenuation_radius(600)
    selected={}
    for a in actors.get_all_level_actors():
        c=a.get_component_by_class(unreal.LightComponent)
        if c and isinstance(a,unreal.Light) and a.get_actor_label()!='Light_AviationBeacon_HeroSpire':
            selected[a.get_actor_label()]=(a,c)
    snapshot={}
    for label,(a,c) in selected.items():
        snapshot[label]={'intensity':c.intensity,'light_color':list(c.light_color.to_tuple()),
                         'use_temperature':c.use_temperature,'temperature':c.temperature}
    (OUT/'lighting_original_snapshot.json').write_text(json.dumps(snapshot,indent=2))

    def restore():
        for label,state in snapshot.items():
            c=selected[label][1]
            for prop,value in state.items():c.set_editor_property(prop,unreal.Color(*value) if prop=='light_color' else value)
    def light(label,intensity,kelvin):
        if label not in selected:return
        c=selected[label][1];c.set_intensity(intensity)
        c.set_editor_property('light_color',unreal.Color(255,255,255,255))
        c.set_editor_property('use_temperature',True);c.set_editor_property('temperature',float(kelvin))

    lib=unreal.VariantManagerLibrary
    lvs=lib.create_level_variant_sets_asset(NAME,DEST);assert lvs
    variants=unreal.VariantSet();variants.set_display_text('Office light studies — same sky, grade and camera')
    lib.add_variant_set(lvs,variants)
    records=[]
    settings=[('A_OriginalDusk',None),('B_NeutralOffice',(7,3.5,35,.6,3.5,4500,10,6000)),
              ('C_WarmDesk',(5.5,2.2,28,.5,1.5,3300,6,3800)),
              ('D_LateOffice',(1.5,.9,12,.3,2.5,4800,3,7000))]
    for name,cfg in settings:
        restore()
        if cfg:
            sun,fill,key,rim,troffer,kelvin,wash,washkelvin=cfg
            light('Light_Cinematic_SunBeam',sun,5200 if name=='B_NeutralOffice' else 3300 if name=='C_WarmDesk' else 7500)
            light('EST_Fill_E1',fill,6500 if name!='D_LateOffice' else 8500)
            light('SpotLight',key,kelvin);light('Cast_RimKicker_Light',rim,6500)
            for index in range(1,7):light('Film_Troffer_%d_Light'%index,troffer,kelvin)
            for index in range(1,4):light('Film_Closeout_CeilingWash_%02d'%index,wash,washkelvin)
        variant=unreal.Variant();variant.set_display_text(name);lib.add_variant(variants,variant)
        count=0
        for label,(actor,component) in selected.items():
            lib.add_actor_binding(variant,actor)
            available=lib.get_capturable_properties(actor)
            for prop,display in PROPS.items():
                matches=[p for p in available if p.endswith(' / '+display) and p.count(' / ')==1]
                assert len(matches)==1,(label,prop,matches)
                capture=lib.capture_property(variant,actor,matches[0]);assert capture,(label,prop)
                capture.record();assert capture.has_recorded_data();count+=1
        records.append({'name':name,'actor_bindings':len(selected),'captured_properties':count})
    restore()
    assert unreal.EditorAssetLibrary.save_loaded_asset(lvs)
    controller=lib.create_level_variant_sets_actor(lvs)
    controller.set_actor_label('Film_Office_LightingVariants')
    controller.set_folder_path('Film304/FinalAssembly/Lighting')
    # Frame architectural services without changing any existing shot camera.
    cam=next(a for a in actors.get_all_level_actors() if a.get_actor_label()=='Film_Cam_Closeout_CeilingReview')
    cam.set_actor_location(unreal.Vector(300,-500,160),False,False)
    cam.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(cam.get_actor_location(),unreal.Vector(180,150,325)),False)
    cine=cam.get_cine_camera_component();filmback=cine.filmback;filmback.sensor_width=36;cine.filmback=filmback;cine.current_focal_length=22
    report={'asset':lvs.get_path_name(),'world':world.get_path_name(),'variants':records,
            'sky_time_changed':False,'shared_materials_changed':False,'restored_original_light_values':True,
            'preview_status':'not yet rendered'}
    (OUT/'lighting_variants.json').write_text(json.dumps(report,indent=2))
    unreal._closeout_lvs=lvs
    print(json.dumps(report))

if __name__=='__main__':main()
