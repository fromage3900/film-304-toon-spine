"""Reconcile the two morning maps in memory, keeping the original Office active."""
import json
from pathlib import Path
import unreal

import film304_fog

def main():
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert world.get_path_name()=='/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office.L_Film_Office'
    assert not unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem).is_rendering()
    subsystem=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    by={a.get_actor_label():a for a in subsystem.get_all_level_actors()}
    copies=[];source=None
    for suffix in ['v01','v02']:
        path='/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office_Assembly_20261018_'+suffix
        copyworld=unreal.load_asset(path);assert copyworld
        actors=unreal.GameplayStatics.get_all_actors_of_class(copyworld,unreal.Actor)
        copies.append({'map':path,'actors':len(actors),'relevant':[a.get_actor_label() for a in actors if any(k in a.get_actor_label() for k in ['Closeout','Dust','Shaft','LoopPlayback'])]})
        if suffix=='v02':source={a.get_actor_label():a for a in actors}
    source_dust=source['Film_WindowDust_Subtle'].get_component_by_class(unreal.NiagaraComponent)
    dust=by.get('Film_WindowDust_Subtle')
    assert dust,'Existing convergence must have created exactly one dust actor'
    c=dust.get_component_by_class(unreal.NiagaraComponent)
    c.set_asset(source_dust.get_asset())
    values={}
    for p in ['User.Spawn Rate','User.CPU Spawn Rate','User.Sprite Scale','User.Sprite Alpha','User.Max Lifetime','User.Spawn Box Height','User.Max Spawn Distance','User.Camera Forward Offset','User.Spawn Distance Distribution','User.Custom Time Dilation','User.Wind Velocity Scale','User.Twirl Velocity','User.Ambient Intensity','User.Fog Particle Percentage']:
        value,valid=source_dust.get_variable_float(p)
        if valid:values[p]=value;c.set_variable_float(p,value)
    c.set_variable_bool('User.Override Camera Transform',True)
    c.set_variable_bool('User.Particle Collision Enabled',False)
    position,valid=source_dust.get_variable_position('User.Custom Camera Position');assert valid
    c.set_variable_position('User.Custom Camera Position',position)
    forward,valid=source_dust.get_variable_vec3('User.Custom Camera Forward');assert valid
    c.set_variable_vec3('User.Custom Camera Forward',forward)
    c.set_variable_material('User.Dust Sprite Material',unreal.load_asset('/Game/VFX/Film304Closeout_20261018/M_Film_WindowDust_SoftLoop_v01'))
    c.reinitialize_system();c.activate(True)
    legacy=by.get('VFX_DustMotes_WindowRays')
    if legacy:
        lc=legacy.get_component_by_class(unreal.NiagaraComponent);lc.deactivate();lc.set_editor_property('auto_activate',False)
    # This is the supported hook used successfully in the morning copy.
    sky=by['Film_UDS_Daylight'];fog=by['EST_Fog_E1']
    fog_before={'custom_actor':str(sky.get_editor_property('Custom Height Fog Actor')),'density':fog.component.fog_density,'maximum_opacity':fog.component.fog_max_opacity}
    film304_fog.assert_single_owner(actors)
    sky.set_editor_property('Custom Height Fog Actor',fog)
    sky.set_editor_property('Animate Time of Day',False)
    for fc in sky.get_components_by_class(unreal.ExponentialHeightFogComponent):fc.set_visibility(False)
    fog.component.set_visibility(True)
    # Routed through film304_fog so the morning values carry an explicit intent and a
    # before/after receipt instead of being a silent overwrite of the shared actor.
    film304_fog.apply({'fog_density':.0018,'fog_max_opacity':.65},film304_fog.INTENT_SHOT_LOOK,actors=subsystem)
    # Fix the copy's concrete/glazing slot mismatch by semantic material-slot names.
    concrete=unreal.load_asset('/Game/Materials/Instances/Film304/Scene/MI_Film304_EnvE1_Concrete')
    asphalt=unreal.load_asset('/Game/Materials/Instances/Film304/Scene/MI_Film304_EnvE1_Asphalt')
    placements={
        'SM_Ext_Mid_SlenderTower':((-9000,6500,-2400),-25),
        'SM_Ext_FG_BarbicanScale':((-13500,1800,-2500),15),
        'SM_Ext_Sky_KMZ_TowerCluster':((-26000,22000,-8000),-15),
        'EST_EstablishingE1_04_SM_CITY_TowerCluster':((-18000,13000,-5500),25),
        'EST_EstablishingE1_05_SM_KMZ_TowerCluster':((-35000,5000,-6500),-10),
        'EST_EstablishingE1_06_SM_KMZ_TowerCluster':((-24000,32000,-7000),65),
    }
    before=[]
    labels=list(placements)+['EST_HorizonBody','EST_HorizonWindows','EST_HorizonBody2','EST_HorizonWindows2']
    for label in labels:
        a=by.get(label)
        if not a:continue
        sm=a.get_component_by_class(unreal.StaticMeshComponent)
        before.append({'actor':label,'transform':a.get_actor_transform().export_text(),'hidden':a.get_editor_property('hidden'),'materials':[m.get_path_name() if m else None for m in sm.get_materials()]})
        if label in placements:
            position,yaw=placements[label]
            a.set_actor_location(unreal.Vector(*position),False,False);a.set_actor_rotation(unreal.Rotator(pitch=0,yaw=yaw,roll=0),False)
            for i,slot in enumerate(sm.static_mesh.get_editor_property('static_materials')):
                name=str(slot.material_slot_name).lower()
                if 'concrete' in name:sm.set_material(i,concrete)
                elif 'asphalt' in name:sm.set_material(i,asphalt)
        elif label.endswith('2'):
            a.set_actor_hidden_in_game(True);a.set_is_temporarily_hidden_in_editor(True)
        else:
            a.set_actor_location(unreal.Vector(0,0,-18000 if label=='EST_HorizonBody' else -18000.012622),False,False)
            a.set_actor_rotation(unreal.Rotator(pitch=0,yaw=54,roll=0),False)
    counts={label:sum(a.get_actor_label()==label for a in subsystem.get_all_level_actors()) for label in ['Film_Closeout_Ceiling_Concrete','Film_Closeout_Ceiling_Metal','Film_WindowDust_Subtle','Film_WindowShaft_01','Film_WindowShaft_02','Film_WindowShaft_03']}
    assert all(v==1 for v in counts.values()),counts
    assert unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()==world
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    report={'world':world.get_path_name(),'copies_read_without_switching_active_map':copies,'dust_values_copied_from_v02':values,'unique_actor_counts':counts,'fog_before':fog_before,'skyline_before':before,'ceiling':'Keep corrected main-room-fit v05 instead of regressing to the copy v03 mesh','lighting':'Main-only composed Neutral/Warm/Cool sequences supersede the old camera-copy bindings; no variant controller with stale copy references was promoted','skin':'Frozen by owner; not modified','visual_gate':'pending skyline and hand renders'}
    (Path(unreal.Paths.project_dir())/'Saved/Audit/Closeout_20261018/morning_copies_converged_into_main.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({'copies':[c['actors'] for c in copies],'dust':values,'counts':counts,'active_map':world.get_path_name()}))

if __name__=='__main__':main()
