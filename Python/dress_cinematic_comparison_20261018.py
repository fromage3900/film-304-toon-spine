"""Scoped contact, stencil, instance, lighting and Niagara improvements."""
from pathlib import Path
import unreal,json

def main():
    root=Path(unreal.Paths.project_dir());audit=root/'Saved/Audit/Closeout_20261018/cinematic_dressing_applied.json'
    assert not audit.exists(),'Review existing receipt; do not repeat offsets'
    ed=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);actors=ed.get_all_level_actors();by={a.get_actor_label():a for a in actors}
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert world.get_path_name().startswith('/Game/Maps/Lookdev/UniversalFilm_20261016/L_Film_Office.')
    assert not unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem).is_rendering()
    report={'contacts':[],'stencils':[],'material_instances':[],'new_lights':[],'niagara':[]}
    # Contact correction uses only the named supporting table, never the floor or adjacent clutter.
    tokens=('Mug','Mouse','Sticky','File','Cactus','CoffeeBag','CoffeeTin','Pastry','Dome')
    for a in actors:
        name=a.get_actor_label();support=None
        if not isinstance(a,unreal.StaticMeshActor):continue
        if name.startswith('Workstation_Row_') and any(t in name for t in tokens):
            digits=[s for s in name.split('_') if s.isdigit()]
            if digits:support=by.get('Workstation_Row_Desk_'+digits[-1])
        elif name.startswith('Breakroom_Table_') and any(t in name for t in tokens):support=by.get('Breakroom_Table')
        if not support:continue
        before=a.get_actor_transform().export_text();oldrot=a.get_actor_rotation()
        # These imported ZMJ mugs share a native X-up mesh; the two breakroom copies were sideways.
        if name.startswith('Breakroom_Table_Mug_'):
            a.modify();a.set_actor_rotation(unreal.Rotator(-90,oldrot.yaw,-90),False)
        center,extent=a.get_actor_bounds(False);support_center,support_extent=support.get_actor_bounds(False)
        top=support_center.z+support_extent.z
        hits=unreal.SystemLibrary.line_trace_multi(world,unreal.Vector(center.x,center.y,top+35),unreal.Vector(center.x,center.y,top-60),unreal.TraceTypeQuery.ECC_VISIBILITY,True,[x for x in actors if x!=support],unreal.DrawDebugTrace.NONE)
        hit=next((h.to_dict() for h in (hits or []) if h.to_dict().get('hit_actor')==support and h.to_dict()['normal'].z>.9),None)
        if not hit:
            if name.startswith('Breakroom_Table_Mug_'):a.set_actor_rotation(oldrot,False)
            report['contacts'].append({'actor':name,'status':'skipped_no_support_hit'});continue
        delta=hit['impact_point'].z+.06-(center.z-extent.z)
        if abs(delta)>30:
            a.set_actor_rotation(oldrot,False);report['contacts'].append({'actor':name,'status':'skipped_offset_over_30cm','delta':delta});continue
        a.modify();p=a.get_actor_location();a.set_actor_location(unreal.Vector(p.x,p.y,p.z+delta),False,False)
        c,e=a.get_actor_bounds(False)
        report['contacts'].append({'actor':name,'support':support.get_actor_label(),'before':before,'after':a.get_actor_transform().export_text(),'offset_z_cm':delta,'contact_clearance_cm':c.z-e.z-hit['impact_point'].z,'raycast_verified':True})
    # Semantic custom-stencil categories. Camera look controls remain separate from material graphs.
    unreal.SystemLibrary.execute_console_command(world,'r.CustomDepth 3')
    for a in actors:
        name=a.get_actor_label()
        for c in a.get_components_by_class(unreal.MeshComponent):
            if not isinstance(c,(unreal.StaticMeshComponent,unreal.SkeletalMeshComponent)):continue
            if isinstance(c,unreal.SkeletalMeshComponent):category=1
            elif any(x in name for x in ['Skyline','CITY','KMZ','Horizon','Glass','Floor']):continue
            elif any(x in name for x in ['Wall','Ceiling','Troffer','WindowBay']):category=3
            else:category=2
            a.modify();c.modify();c.set_render_custom_depth(True);c.set_custom_depth_stencil_value(category)
            report['stencils'].append({'actor':name,'component':c.get_name(),'category':category})
    source=unreal.load_asset('/Game/Materials/Instances/Film304/PostProcess/Outline/MI_Outline_Storybook')
    dest='/Game/Materials/Recovery_Office_20261018/Comparisons';name='MI_Outline_StencilThin_v01'
    thin=unreal.load_asset(dest+'/'+name) if unreal.EditorAssetLibrary.does_asset_exist(dest+'/'+name) else unreal.AssetToolsHelpers.get_asset_tools().duplicate_asset(name,dest,source);assert thin
    for k,v in {'OutlineWidth':.72,'MinWidthPx':.35,'MaxWidthPx':1.15,'EdgeStrength':.62,'CreaseThreshold':.72,'StencilCharacterWeight':.6,'StencilPropWeight':.22,'StencilFoliageWeight':.12,'InkBlurStrength':.05,'HalftoneAmount':.035}.items():
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(thin,k,v)
    for k in ['OutlineColor','CreaseColor']:unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(thin,k,unreal.LinearColor(.009,.008,.011,1))
    unreal.EditorAssetLibrary.save_loaded_asset(thin,False)
    volume=by['Film_Compare_B_SoftClean'];volume.modify();s=volume.settings;blend=s.weighted_blendables
    weights=list(blend.array);weights[0]=unreal.WeightedBlendable(weight=1,object=thin)
    if len(weights)>1:weights[1].weight=.2
    s.weighted_blendables=unreal.WeightedBlendables(array=weights);volume.settings=s
    report['thin_outline']=thin.get_path_name()
    # Isolated tint/roughness variations use the already working toon instance chain.
    working=unreal.load_asset('/Game/Materials/Recovery_Office_20261018/DanaParts/MI_Dana_Hair_StageRestored_v01')
    def instance(name,folder,tint,rough):
        m=unreal.load_asset(folder+'/'+name) if unreal.EditorAssetLibrary.does_asset_exist(folder+'/'+name) else unreal.AssetToolsHelpers.get_asset_tools().duplicate_asset(name,folder,working);assert m
        unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(m,'BaseTint',unreal.LinearColor(*tint,1))
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(m,'Roughness',rough)
        unreal.EditorAssetLibrary.save_loaded_asset(m,False);return m
    for actor,tint in [('Workstation_Row_Mug_01',(.025,.085,.095)),('Breakroom_Table_Mug_01',(.20,.16,.105)),('Breakroom_Table_Mug_02',(.035,.055,.09)),('Breakroom_Table_CoffeeTin',(.16,.07,.025))]:
        a=by[actor];c=a.static_mesh_component;m=instance('MI_'+actor+'_Accent_v01','/Game/Materials/Recovery_Office_20261018/PropVariations',tint,.72)
        a.modify();c.modify();before=c.get_material(0).get_path_name();c.set_material(0,m)
        report['material_instances'].append({'actor':actor,'before':before,'after':m.get_path_name()})
    for key,tint in [('Warm',(.16,.145,.125)),('Cool',(.125,.135,.14))]:instance('MI_FloorTile_'+key+'_v01','/Game/Materials/Recovery_Office_20261018/Floor',tint,.86)
    # Broad motivation from the existing ceiling fixtures; keep the breakroom readable.
    for label,pos,target,value,temp,width,height in [('Film_Compare_BreakroomFill',(560,350,270),(350,580,110),45,4800,240,160),('Film_Compare_CoffeePool',(420,525,240),(370,510,85),12,3300,120,90)]:
        a=by.get(label) or ed.spawn_actor_from_class(unreal.RectLight,unreal.Vector(*pos));a.set_actor_label(label);a.modify()
        a.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*pos),unreal.Vector(*target)),False)
        c=a.get_component_by_class(unreal.RectLightComponent);c.modify();c.set_mobility(unreal.ComponentMobility.MOVABLE)
        for prop,val in {'intensity_units':unreal.LightUnits.CANDELAS,'intensity':value,'use_temperature':True,'temperature':temp,'source_width':width,'source_height':height,'attenuation_radius':700,'cast_shadows':True}.items():c.set_editor_property(prop,val)
        report['new_lights'].append({'actor':label,'candela':value,'kelvin':temp})
    system=unreal.load_asset('/Game/VFX/Film304Closeout_20261018/NS_Film_WindowDust_v01')
    for label,pos in [('Film_Dust_Aisle',(180,180,180)),('Film_Dust_Coffee',(380,520,165))]:
        a=ed.spawn_actor_from_class(unreal.NiagaraActor,unreal.Vector(*pos));a.set_actor_label(label);a.modify()
        c=a.get_component_by_class(unreal.NiagaraComponent);c.modify();c.set_asset(system)
        for k,v in {'User.SpawnRate':9.,'User.CPUSpawnRate':9.,'User.SpriteScale':.006,'User.Alpha':.22}.items():c.set_variable_float(k,v)
        c.set_variable_position('User.PositionOverride',unreal.Vector(*pos));c.activate(True)
        report['niagara'].append({'actor':label,'system':system.get_path_name(),'sprite_scale':.006,'spawn_rate':9})
    task=unreal.AssetImportTask();task.filename=str(root/'Tools/houdini/Published/Film304Closeout_20261018/Floor/Film304_MeasuredFloor_v01.hda');task.destination_path='/Game/Houdini/Film304Closeout_20261018';task.automated=True;task.save=True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);hda=task.get_objects()[0]
    unreal._film_floor_live=unreal.HoudiniPublicAPIBlueprintLib.get_api().instantiate_asset(hda,unreal.Transform(),enable_auto_cook=True,enable_auto_bake=False)
    unreal._film_floor_live.get_houdini_asset_actor().set_actor_label('Film_Live_MeasuredFloor_v01')
    unreal._film_floor_live.process_component_synchronous();report['live_floor_outputs']=unreal._film_floor_live.get_num_outputs()
    assert report['live_floor_outputs']>0
    assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    audit.write_text(json.dumps(report,indent=2));print(json.dumps({k:len(v) if isinstance(v,list) else v for k,v in report.items()}))

if __name__=='__main__':main()
