import unreal
world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PostProcessVolume)
a = actors[0]
print("components:", a.get_components())
print("root:", a.root_component)
print("children:", a.root_component.get_children_components(True))
