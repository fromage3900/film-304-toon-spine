import unreal

al = unreal.AnimationLibrary
print("AnimationLibrary bone pose functions:")
for m in dir(al):
    if any(k in m.lower() for k in ["bone", "pose", "track", "key", "curve"]):
        print(" ", m)
