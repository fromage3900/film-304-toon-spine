# Enable Virtual Texture streaming on the three re-imported single-tile skin
# textures. The UDIM master samples them as SAMPLERTYPE_VirtualColor, so they
# must be virtual textures for the bind to be legal.

import unreal

DIR = "/Game/Materials/Textures/OneDriveRigs_20261016/"
TILES = ["T_DanaSkin_Tile1", "T_DanaSkin_Tile2", "T_DanaSkin_Tile3"]


def log(m):
    unreal.log("[SkinVT] " + str(m))


for t in TILES:
    tex = unreal.load_asset(DIR + t)
    if tex is None:
        log("missing " + t)
        continue
    before = tex.get_editor_property("virtual_texture_streaming")
    tex.set_editor_property("virtual_texture_streaming", True)
    ok = unreal.EditorAssetLibrary.save_asset(DIR + t)
    check = unreal.load_asset(DIR + t)
    log("%s vt %s -> %s (saved=%s)" % (t, before, check.get_editor_property("virtual_texture_streaming"), ok))
