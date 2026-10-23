import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
sam = None
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Film_Cast_Sam":
        sam = a
        break

skc = sam.get_component_by_class(unreal.SkeletalMeshComponent)
held_pose = unreal.load_asset("/Game/Staging/Film304Repaired_20261017/Sam/Poses/AS_Sam_HeldPose_v02")
print("Playing AS_Sam_HeldPose_v02...")
skc.set_editor_property("animation_mode", unreal.AnimationMode.ANIMATION_SINGLE_NODE)
anim_data = skc.get_editor_property("animation_data")
anim_data.anim_to_play = held_pose
anim_data.saved_looping = True
anim_data.saved_playing = True
skc.set_editor_property("animation_data", anim_data)

# Now check tower cluster for Bay 3
tower_cluster = unreal.load_asset("/Game/Environment/Brutalist/01_CITY_PBR/SM_CITY_TowerCluster")
concrete_mat = unreal.load_asset("/Game/Materials/Instances/Film304/Environment/MI_Film304_BrutalistConcrete")
asphalt_mat = unreal.load_asset("/Game/Materials/Instances/Film304/Environment/MI_Film304_BrutalistAsphalt")

# Also move SM_Ext_Bay3_Barbican to +X
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "SM_Ext_Bay3_Barbican":
        a.set_actor_location(unreal.Vector(400.0, 3600.0, -213.5), False, False)
        a.set_actor_scale3d(unreal.Vector(2.0, 2.0, 1.5))
        print("Shifted SM_Ext_Bay3_Barbican to (400, 3600, -213.5) with scale 2.0")

# Check if TowerCluster is spawned
cluster_actor = None
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "SM_Ext_Bay3_TowerCluster":
        cluster_actor = a
        break

if not cluster_actor and tower_cluster:
    cluster_actor = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(1200.0, 4800.0, -400.0))
    cluster_actor.set_actor_label("SM_Ext_Bay3_TowerCluster")
    cluster_actor.set_folder_path("Film304/Environment/Exterior")
    smc = cluster_actor.get_component_by_class(unreal.StaticMeshComponent)
    smc.set_static_mesh(tower_cluster)
    if concrete_mat:
        smc.set_material(0, concrete_mat)
    if asphalt_mat:
        smc.set_material(1, asphalt_mat)
    cluster_actor.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.2))
    print("Spawned SM_Ext_Bay3_TowerCluster at (1200, 4800, -400)")

