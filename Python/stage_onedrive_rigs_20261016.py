"""Stage the 2026-10-16 film asset intake in a reversible Humber lane.

This builder imports the supplied color maps and 3D model FBXs, creates a
small Substrate Toon material set, and assigns instances to the static mesh
imports. Character rig sources are inventoried and their instances are
prepared, but no character FBX is imported until Dana's body/face/eye export
passes the isolated roundtrip gate. All imported source assets stay local to
this uncommitted staging folder; this does not package or redistribute rig
files.
"""
from __future__ import annotations

import hashlib
import json
import re
import traceback
from pathlib import Path

import unreal


REPO = Path(__file__).resolve().parents[1]
SOURCE = Path(r"G:\Film304_AssetIntake_20261016_Source")
STATIC_SOURCE = SOURCE / "3rd Year Film" / "3D Models" / "FBX Files"
MASTER_DIR = "/Game/Materials/Masters/OneDriveRigs_20261016"
INSTANCE_DIR = "/Game/Materials/Instances/OneDriveRigs_20261016"
TEXTURE_DIR = "/Game/Materials/Textures/OneDriveRigs_20261016"
STATIC_DIR = "/Game/Staging/OneDriveRigs_20261016/Environment"
REPORT_PATH = REPO / "Saved" / "Audit" / "OneDriveRigs_20261016" / "intake.json"

PROFILE_ENV = "/Game/Materials/ToonProfiles/TP_Environment"
PROFILE_CHARACTER = "/Game/Materials/ToonProfiles/TP_DanaFilm_Clean"
PROFILE_EYE = "/Game/Materials/ToonProfiles/TP_DanaFilm_Eye"
CORNEA_PARENT = "/Game/Materials/Masters/DanaFilm/M_DanaFilm_CorneaClear"

CHARACTERS = {
    "Dana": {
        "rig": SOURCE / "3rd Year Film" / "Rigs" / "Temp" / "Dana_Rig_v1.5" / "Dana_Rig_v1.5.mb",
        "texture_root": SOURCE / "3rd Year Film" / "Rigs" / "Temp" / "Dana_Rig_v1.5" / "TexturesDana",
        "tiles_folder": "Dana_Skin_Texture",
        "skin_prefix": "Dana_Diffuse",
        "shoes": "DanaShoes_Texture.png",
        "hair": (0.055, 0.025, 0.018, 1.0),
        "shirt": (0.035, 0.24, 0.27, 1.0),
        "cloth": (0.22, 0.10, 0.32, 1.0),
        "detail": (0.30, 0.16, 0.055, 1.0),
    },
    "David": {
        "rig": SOURCE / "3rd Year Film" / "Rigs" / "Temp" / "David_Rig_v1.51" / "David_Rig_v1.51.mb",
        "texture_root": SOURCE / "3rd Year Film" / "Rigs" / "Temp" / "David_Rig_v1.51" / "Textures",
        "tiles_folder": "David_Skin_Texture",
        "skin_prefix": "David_Diffuse",
        "shoes": "DavidShoes_Texture.png",
        "hair": (0.025, 0.018, 0.016, 1.0),
        "shirt": (0.18, 0.22, 0.24, 1.0),
        "cloth": (0.075, 0.09, 0.13, 1.0),
        "detail": (0.34, 0.35, 0.34, 1.0),
    },
    "Sam": {
        "rig": SOURCE / "3rd Year Film" / "Rigs" / "Guy" / "Sam Rig" / "C_Guy.mb",
        "texture_root": SOURCE / "3rd Year Film" / "Rigs" / "Guy" / "Sam Rig" / "Textures",
        "tiles_folder": "Sam_Skin_Texture",
        "skin_prefix": "Sam_Diffuse",
        "shoes": "Sam_Shoes_Diffuse.png",
        "hair": (0.045, 0.028, 0.020, 1.0),
        "shirt": (0.20, 0.10, 0.13, 1.0),
        "cloth": (0.09, 0.10, 0.12, 1.0),
        "detail": (0.34, 0.27, 0.14, 1.0),
    },
}

EAL = unreal.EditorAssetLibrary
ME = unreal.MaterialEditingLibrary
ASSET_TOOLS = unreal.AssetToolsHelpers.get_asset_tools()


def asset_exists(path: str) -> bool:
    return bool(EAL.does_asset_exist(path))


def ensure_dir(path: str) -> None:
    if not EAL.does_directory_exist(path):
        EAL.make_directory(path)


def save(asset) -> None:
    if not EAL.save_loaded_asset(asset, only_if_is_dirty=False):
        raise RuntimeError("save failed: " + asset.get_path_name())


def source_record(path: Path) -> dict:
    if not path.is_file():
        return {"path": str(path), "exists": False}
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    stat = path.stat()
    return {
        "path": str(path),
        "exists": True,
        "bytes": stat.st_size,
        "sha256": digest.hexdigest(),
        "mtime_utc": __import__("datetime").datetime.fromtimestamp(
            stat.st_mtime, __import__("datetime").timezone.utc
        ).isoformat(),
    }


def write_report(report: dict) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")


def new_expr(material, cls, x: int, y: int):
    return ME.create_material_expression(material, cls, x, y)


def connect(source, output: str, target, input_name: str) -> None:
    ok = ME.connect_material_expressions(source, output, target, input_name)
    if ok is False:
        raise RuntimeError("wire failed: %s.%s -> %s.%s" % (
            source.get_name(), output, target.get_name(), input_name))


def set_desc(node, description: str) -> None:
    for name in ("description", "desc"):
        try:
            node.set_editor_property(name, description)
            return
        except Exception:
            continue


def scalar_parameter(material, name: str, default: float, x: int, y: int,
                     minimum: float, maximum: float, description: str):
    node = new_expr(material, unreal.MaterialExpressionScalarParameter, x, y)
    node.set_editor_property("parameter_name", name)
    node.set_editor_property("group", "Film Surface")
    node.set_editor_property("default_value", float(default))
    node.set_editor_property("slider_min", float(minimum))
    node.set_editor_property("slider_max", float(maximum))
    set_desc(node, description)
    return node


def vector_parameter(material, name: str, default, x: int, y: int,
                     description: str):
    node = new_expr(material, unreal.MaterialExpressionVectorParameter, x, y)
    node.set_editor_property("parameter_name", name)
    node.set_editor_property("group", "Film Surface")
    node.set_editor_property("default_value", unreal.LinearColor(*default))
    set_desc(node, description)
    return node


def texture_parameter(material, name: str, x: int, y: int, description: str):
    node = new_expr(material, unreal.MaterialExpressionTextureSampleParameter2D, x, y)
    node.set_editor_property("parameter_name", name)
    node.set_editor_property("group", "Film Color")
    set_desc(node, description)
    return node


def color_graph(material, texture_kind: str):
    tint = vector_parameter(
        material, "BaseTint", (1.0, 1.0, 1.0, 1.0), -820, 20,
        "Neutral multiplier. Leave at white to preserve the supplied diffuse map.")
    if texture_kind == "tint":
        base_color = tint
        texture_params = []
    elif texture_kind == "single":
        uv = new_expr(material, unreal.MaterialExpressionTextureCoordinate, -820, -180)
        sample = texture_parameter(
            material, "BaseColorMap", -600, -160,
            "Color texture for a single 0-1 UV set.")
        connect(uv, "", sample, "UVs")
        multiply = new_expr(material, unreal.MaterialExpressionMultiply, -320, 10)
        connect(sample, "RGB", multiply, "A")
        connect(tint, "", multiply, "B")
        base_color = multiply
        texture_params = ["BaseColorMap"]
    elif texture_kind == "udim3":
        uv = new_expr(material, unreal.MaterialExpressionTextureCoordinate, -1120, -260)
        uv.set_editor_property("coordinate_index", 0)
        tile_uv = new_expr(material, unreal.MaterialExpressionFrac, -900, -240)
        connect(uv, "", tile_uv, "")
        u_only = new_expr(material, unreal.MaterialExpressionComponentMask, -900, -480)
        u_only.set_editor_properties({"r": True, "g": False, "b": False, "a": False})
        connect(uv, "", u_only, "")
        tile_floor = new_expr(material, unreal.MaterialExpressionFloor, -700, -460)
        connect(u_only, "", tile_floor, "")
        half = new_expr(material, unreal.MaterialExpressionConstant, -700, -640)
        half.set_editor_property("r", 0.5)
        one_half = new_expr(material, unreal.MaterialExpressionConstant, -470, -640)
        one_half.set_editor_property("r", 1.5)

        samples = []
        names = ("BaseColorTile1001", "BaseColorTile1002", "BaseColorTile1003")
        for idx, name in enumerate(names):
            sample = texture_parameter(
                material, name, -650, -160 + idx * 165,
                "UDIM diffuse tile %s; source UV U spans 0, 1, 2." % name[-4:])
            connect(tile_uv, "", sample, "UVs")
            samples.append(sample)

        choose_23 = new_expr(material, unreal.MaterialExpressionIf, -180, -40)
        connect(tile_floor, "", choose_23, "A")
        connect(one_half, "", choose_23, "B")
        connect(samples[2], "RGB", choose_23, "A > B")
        connect(samples[1], "RGB", choose_23, "A == B")
        connect(samples[1], "RGB", choose_23, "A < B")

        choose_1_23 = new_expr(material, unreal.MaterialExpressionIf, 60, -40)
        connect(tile_floor, "", choose_1_23, "A")
        connect(half, "", choose_1_23, "B")
        connect(choose_23, "", choose_1_23, "A > B")
        connect(samples[0], "RGB", choose_1_23, "A == B")
        connect(samples[0], "RGB", choose_1_23, "A < B")

        multiply = new_expr(material, unreal.MaterialExpressionMultiply, 340, 20)
        connect(choose_1_23, "", multiply, "A")
        connect(tint, "", multiply, "B")
        base_color = multiply
        texture_params = list(names)
    else:
        raise ValueError("unknown texture graph: " + texture_kind)

    roughness = scalar_parameter(
        material, "Roughness", 0.72, -560, 260, 0.05, 1.0,
        "Surface roughness; 0 is sharp, 1 is fully matte.")
    specular = scalar_parameter(
        material, "Specular", 0.18, -560, 390, 0.0, 0.8,
        "Subtle specular response for a film surface.")
    return base_color, roughness, specular, texture_params


def create_toon_master(name: str, profile_path: str, texture_kind: str,
                       skeletal: bool) -> dict:
    asset_path = MASTER_DIR + "/" + name
    existed = asset_exists(asset_path)
    if existed:
        material = EAL.load_asset(asset_path)
        if material is None:
            raise RuntimeError("existing staged master could not be loaded: " + asset_path)
    else:
        ensure_dir(MASTER_DIR)
        material = ASSET_TOOLS.create_asset(
            name, MASTER_DIR, unreal.Material, unreal.MaterialFactoryNew())
        if material is None:
            raise RuntimeError("could not create material " + asset_path)

    profile = EAL.load_asset(profile_path)
    if profile is None:
        raise RuntimeError("missing Toon Profile " + profile_path)
    existing_nodes = [n for n in ME.get_material_expressions(material) or []
                      if type(n).__name__ == "MaterialExpressionSubstrateToonBSDF"]
    if existed:
        bound = (existing_nodes[0].get_editor_property("toon_profile")
                 if len(existing_nodes) == 1 else None)
        if bound is not None and bound.get_path_name() == profile.get_path_name():
            before = len(ME.get_material_expressions(material) or [])
            ME.delete_unused_expressions(material)
            after = len(ME.get_material_expressions(material) or [])
            expected_counts = {"tint": 4, "single": 7, "udim3": 16}
            if after == expected_counts[texture_kind]:
                if after < before:
                    ME.recompile_material(material)
                toon_nodes = [n for n in ME.get_material_expressions(material) or []
                              if type(n).__name__ == "MaterialExpressionSubstrateToonBSDF"]
                if len(toon_nodes) != 1:
                    raise RuntimeError("expected one Toon BSDF after island cleanup: " + asset_path)
                toon_nodes[0].modify()
                toon_nodes[0].set_editor_property("toon_profile", profile)
                if toon_nodes[0].get_editor_property("toon_profile") != profile:
                    raise RuntimeError("Toon Profile did not persist after island cleanup: " + asset_path)
                save(material)
            return {
                "path": asset_path,
                "profile": profile.get_path_name(),
                "graph": texture_kind,
                "expression_count": after,
                "toon_bsdf_count": 1,
                "texture_parameters": {
                    "tint": [],
                    "single": ["BaseColorMap"],
                    "udim3": ["BaseColorTile1001", "BaseColorTile1002", "BaseColorTile1003"],
                }[texture_kind],
                "iridescence_parameters": [],
                "compiled": True,
                "reused_existing": True,
                "orphan_expressions_removed": before - after,
            }
        # This path is exclusively generated by this builder. A partial graph
        # or residual island is rebuilt from the source script.
        material.modify()
        ME.delete_all_material_expressions(material)

    material.set_editor_property("material_domain", unreal.MaterialDomain.MD_SURFACE)
    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    if skeletal:
        material.set_editor_property("used_with_skeletal_mesh", True)
    material.set_editor_property("two_sided", False)
    try:
        material.set_editor_property("bUsesSubstrate", True)
    except Exception:
        pass

    base_color, roughness, specular, texture_params = color_graph(material, texture_kind)
    toon = new_expr(material, unreal.MaterialExpressionSubstrateToonBSDF, 720, 80)
    connect(base_color, "", toon, "BaseColor")
    connect(roughness, "", toon, "Roughness")
    connect(specular, "", toon, "Specular")
    if ME.connect_material_property(
            toon, "", unreal.MaterialProperty.MP_FRONT_MATERIAL) is False:
        raise RuntimeError("could not connect the Substrate Toon output on " + asset_path)
    # A previous interrupted generation can leave unconnected nodes in the
    # isolated staging asset. Remove only expressions that do not reach output.
    ME.delete_unused_expressions(material)
    ME.recompile_material(material)

    toon_nodes = [n for n in ME.get_material_expressions(material)
                  if type(n).__name__ == "MaterialExpressionSubstrateToonBSDF"]
    if len(toon_nodes) != 1:
        raise RuntimeError("expected one Substrate Toon BSDF in " + asset_path)
    toon_nodes[0].modify()
    toon_nodes[0].set_editor_property("toon_profile", profile)
    if toon_nodes[0].get_editor_property("toon_profile") != profile:
        raise RuntimeError("Toon Profile did not persist on " + asset_path)
    save(material)
    return {
        "path": asset_path,
        "profile": profile.get_path_name(),
        "graph": texture_kind,
        "expression_count": len(ME.get_material_expressions(material) or []),
        "toon_bsdf_count": len(toon_nodes),
        "texture_parameters": texture_params,
        "iridescence_parameters": [],
        "compiled": True,
        "reused_existing": existed,
    }


def import_texture(source_path: Path, asset_name: str, report: dict) -> str:
    asset_path = TEXTURE_DIR + "/" + asset_name
    source_path = source_path.resolve()
    if not source_path.is_file():
        raise FileNotFoundError(str(source_path))
    if not asset_exists(asset_path):
        ensure_dir(TEXTURE_DIR)
        task = unreal.AssetImportTask()
        task.set_editor_properties({
            "filename": str(source_path),
            "destination_path": TEXTURE_DIR,
            "destination_name": asset_name,
            "automated": True,
            "replace_existing": False,
            "save": True,
        })
        ASSET_TOOLS.import_asset_tasks([task])
        paths = [str(p) for p in task.get_editor_property("imported_object_paths")]
        if not paths:
            raise RuntimeError("texture import returned no assets: " + str(source_path))
    texture = EAL.load_asset(asset_path)
    if texture is None:
        raise RuntimeError("imported texture not found at " + asset_path)
    try:
        texture.set_editor_property("srgb", True)
    except Exception:
        pass
    save(texture)
    report.setdefault("textures", []).append({
        **source_record(source_path),
        "asset": asset_path,
        "srgb": True,
    })
    return asset_path


def create_instance(name: str, parent_path: str, overrides: dict) -> dict:
    asset_path = INSTANCE_DIR + "/" + name
    ensure_dir(INSTANCE_DIR)
    parent = EAL.load_asset(parent_path)
    if parent is None:
        raise RuntimeError("missing material parent " + parent_path)
    if asset_exists(asset_path):
        instance = EAL.load_asset(asset_path)
        if instance is None:
            raise RuntimeError("existing staged instance could not be loaded: " + asset_path)
        current_parent = instance.get_editor_property("parent")
        if current_parent is not None and current_parent.get_path_name() != parent.get_path_name():
            raise RuntimeError("refusing to change unexpected parent on " + asset_path)
    else:
        instance = ASSET_TOOLS.create_asset(
            name, INSTANCE_DIR, unreal.MaterialInstanceConstant,
            unreal.MaterialInstanceConstantFactoryNew())
        if instance is None:
            raise RuntimeError("could not create instance " + asset_path)
    if ME.set_material_instance_parent(instance, parent) is False:
        raise RuntimeError("could not set parent on " + asset_path)

    for key, value in overrides.items():
        if isinstance(value, str):
            texture = EAL.load_asset(value)
            if texture is None:
                raise RuntimeError("missing texture %s for %s" % (value, asset_path))
            ME.set_material_instance_texture_parameter_value(instance, key, texture)
        elif isinstance(value, (tuple, list)):
            ME.set_material_instance_vector_parameter_value(
                instance, key, unreal.LinearColor(*value))
        else:
            ME.set_material_instance_scalar_parameter_value(instance, key, float(value))
    save(instance)

    parent_read = instance.get_editor_property("parent")
    if parent_read is None or parent_read.get_path_name() != parent.get_path_name():
        raise RuntimeError("parent readback mismatch: " + asset_path)
    values = {}
    for key, wanted in overrides.items():
        if isinstance(wanted, str):
            actual = ME.get_material_instance_texture_parameter_value(instance, key)
            actual_path = actual.get_path_name().split(".")[0] if actual is not None else None
            if actual_path != wanted:
                raise RuntimeError("texture readback mismatch for %s.%s" % (asset_path, key))
            values[key] = actual_path
        elif isinstance(wanted, (tuple, list)):
            actual = ME.get_material_instance_vector_parameter_value(instance, key)
            got = tuple(round(float(x), 4) for x in
                        (actual.r, actual.g, actual.b, actual.a))
            expected = tuple(round(float(x), 4) for x in wanted)
            if got != expected:
                raise RuntimeError("vector readback mismatch for %s.%s" % (asset_path, key))
            values[key] = list(got)
        else:
            actual = ME.get_material_instance_scalar_parameter_value(instance, key)
            if round(float(actual), 4) != round(float(wanted), 4):
                raise RuntimeError("scalar readback mismatch for %s.%s" % (asset_path, key))
            values[key] = round(float(actual), 4)
    return {"path": asset_path, "parent": parent.get_path_name(), "values": values}


def rig_material_instances(report: dict, textures: dict) -> dict:
    result = {}
    char_parent = MASTER_DIR + "/M_OneDriveRigs_FilmToon_Character_20261016"
    eye_parent = MASTER_DIR + "/M_OneDriveRigs_FilmToon_Eyes_20261016"
    udim_parent = MASTER_DIR + "/M_OneDriveRigs_FilmToon_UDIM_20261016"
    single_parent = MASTER_DIR + "/M_OneDriveRigs_FilmToon_Albedo_20261016"
    for character, spec in CHARACTERS.items():
        prefix = "MI_OneDriveRigs_%s_" % character
        skin_overrides = {
            "BaseTint": (1.0, 1.0, 1.0, 1.0),
            "Roughness": 0.72,
            "Specular": 0.18,
        }
        for tile in (1001, 1002, 1003):
            skin_overrides["BaseColorTile%d" % tile] = textures[character]["tiles"][tile]
        rows = {
            "Skin": create_instance(prefix + "Skin_20261016", udim_parent, skin_overrides),
            "Shoes": create_instance(prefix + "Shoes_20261016", single_parent, {
                "BaseTint": (1.0, 1.0, 1.0, 1.0),
                "Roughness": 0.66,
                "Specular": 0.16,
                "BaseColorMap": textures[character]["shoes"],
            }),
            "Hair": create_instance(prefix + "Hair_20261016", char_parent, {
                "BaseTint": spec["hair"], "Roughness": 0.64, "Specular": 0.16,
            }),
            "EyeWhite": create_instance(prefix + "EyeWhite_20261016", eye_parent, {
                "BaseTint": (0.72, 0.66, 0.58, 1.0), "Roughness": 0.50, "Specular": 0.20,
            }),
            "Iris": create_instance(prefix + "Iris_20261016", eye_parent, {
                "BaseTint": (0.20, 0.075, 0.035, 1.0), "Roughness": 0.30, "Specular": 0.18,
            }),
            "EyeInterior": create_instance(prefix + "EyeInterior_20261016", eye_parent, {
                "BaseTint": (0.025, 0.018, 0.020, 1.0), "Roughness": 0.55, "Specular": 0.08,
            }),
            "Cloth": create_instance(prefix + "Cloth_20261016", char_parent, {
                "BaseTint": spec["cloth"], "Roughness": 0.82, "Specular": 0.12,
            }),
            "Shirt": create_instance(prefix + "Shirt_20261016", char_parent, {
                "BaseTint": spec["shirt"], "Roughness": 0.80, "Specular": 0.12,
            }),
            "Detail": create_instance(prefix + "Detail_20261016", char_parent, {
                "BaseTint": spec["detail"], "Roughness": 0.38, "Specular": 0.26,
            }),
            "Cornea": create_instance(prefix + "Cornea_20261016", CORNEA_PARENT, {
                "CorneaTint": (0.76, 0.84, 0.88, 1.0), "Coverage": 0.12,
                "Roughness": 0.08, "Specular": 0.18,
            }),
        }
        result[character] = rows
        report.setdefault("rigs", {})[character] = {
            "source": source_record(spec["rig"]),
            "texture_instances": rows,
            "mesh_imported": False,
            "material_assignment": "pending validated Dana body/face/eye export gate",
        }
    spider_rig = SOURCE / "3rd Year Film" / "Rigs" / "Spider" / "C_Spider.ma"
    result["Spider"] = {
        "Body": create_instance("MI_OneDriveRigs_Spider_Body_20261016", char_parent, {
            "BaseTint": (0.12, 0.105, 0.095, 1.0), "Roughness": 0.68, "Specular": 0.18,
        }),
        "Eye": create_instance("MI_OneDriveRigs_Spider_Eye_20261016", eye_parent, {
            "BaseTint": (0.22, 0.16, 0.10, 1.0), "Roughness": 0.36, "Specular": 0.18,
        }),
    }
    report.setdefault("rigs", {})["Spider"] = {
        "source": source_record(spider_rig),
        "texture_instances": result["Spider"],
        "mesh_imported": False,
        "material_assignment": "pending Maya-to-FBX export; no texture maps shipped",
    }
    return result


def import_static_models(report: dict, environment_parent: str) -> list:
    files = sorted(STATIC_SOURCE.glob("*.fbx"), key=lambda p: p.name.casefold())
    if not files:
        raise RuntimeError("no static FBX source files under " + str(STATIC_SOURCE))
    ensure_dir(STATIC_DIR)
    tasks = []
    records = []
    for src in files:
        stem = re.sub(r"[^A-Za-z0-9_]+", "_", src.stem).strip("_")
        if not stem.startswith("SM_"):
            stem = "SM_" + stem
        asset_name = stem + "_FilmStage_20261016"
        asset_path = STATIC_DIR + "/" + asset_name
        if asset_exists(asset_path):
            records.append({"source": str(src), "asset": asset_path, "status": "already_present"})
            continue
        options = unreal.FbxImportUI()
        options.set_editor_properties({
            "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
            "import_as_skeletal": False,
            "import_mesh": True,
            "import_animations": False,
            "import_materials": False,
            "import_textures": False,
        })
        static_data = options.get_editor_property("static_mesh_import_data")
        static_data.set_editor_properties({
            "combine_meshes": True,
            "auto_generate_collision": False,
        })
        task = unreal.AssetImportTask()
        task.set_editor_properties({
            "filename": str(src.resolve()),
            "destination_path": STATIC_DIR,
            "destination_name": asset_name,
            "automated": True,
            "replace_existing": False,
            "save": True,
            "options": options,
        })
        tasks.append(task)
        records.append({"source": str(src), "asset": asset_path, "task": task})

    if tasks:
        ASSET_TOOLS.import_asset_tasks(tasks)

    for row in records:
        task = row.pop("task", None)
        asset_path = row["asset"]
        mesh = EAL.load_asset(asset_path)
        if mesh is None and task is not None:
            imported = [str(p).split(".")[0] for p in task.get_editor_property("imported_object_paths")]
            mesh_path = next((p for p in imported if EAL.load_asset(p) is not None), None)
            if mesh_path:
                mesh = EAL.load_asset(mesh_path)
                row["asset"] = mesh_path
                asset_path = mesh_path
        if mesh is None:
            row["status"] = "import_failed"
            report.setdefault("static_assets", []).append({**row, **source_record(Path(row["source"]))})
            continue

        mi_name = "MI_OneDriveRigs_Env_" + asset_path.rsplit("/", 1)[-1]
        mi_path = INSTANCE_DIR + "/" + mi_name
        create_instance(mi_name, environment_parent, {
            "BaseTint": (0.4, 0.4, 0.4, 1.0),
            "Roughness": 0.55,
            "Specular": 0.22,
        })
        instance = EAL.load_asset(mi_path)
        slots = list(mesh.get_editor_property("static_materials") or [])
        if not slots:
            slot = unreal.StaticMaterial()
            slot.set_editor_property("material_slot_name", "FilmSurface")
            slot.set_editor_property("material_interface", instance)
            slots = [slot]
        else:
            for slot in slots:
                slot.set_editor_property("material_interface", instance)
        mesh.modify()
        mesh.set_editor_property("static_materials", slots)
        save(mesh)
        verify = list(mesh.get_editor_property("static_materials") or [])
        valid = bool(verify) and all(
            s.get_editor_property("material_interface") is not None and
            s.get_editor_property("material_interface").get_path_name().split(".")[0] == mi_path
            for s in verify)
        if not valid:
            raise RuntimeError("static mesh MI assignment readback failed: " + asset_path)
        row.update({"status": "staged_and_assigned", "mi": mi_path, "slot_count": len(verify)})
        report.setdefault("static_assets", []).append({**row, **source_record(Path(row["source"]))})
    return records


def main() -> None:
    report = {
        "schema": "humber-onedrive-rig-intake.v1",
        "project": "HumberToonShader",
        "material_role": "intake_preview",
        "approved_universal_toon_parent": "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal",
        "source_root": str(SOURCE),
        "output_paths": {
            "masters": MASTER_DIR,
            "instances": INSTANCE_DIR,
            "textures": TEXTURE_DIR,
            "static_meshes": STATIC_DIR,
        },
        "guardrails": {
            "melodia_assets_modified": False,
            "approved_universal_toon_master_modified": False,
            "staging_materials_are_intake_previews": True,
            "iridescence_or_sparkle_used": False,
            "character_meshes_imported": False,
            "character_source_files_copied_into_repo": False,
            "scene_or_camera_assets_created": False,
        },
        "materials": [],
        "textures": [],
        "rigs": {},
        "static_assets": [],
    }
    try:
        if not SOURCE.is_dir():
            raise FileNotFoundError("asset intake missing: " + str(SOURCE))
        if not asset_exists(PROFILE_ENV) or not asset_exists(PROFILE_CHARACTER) or not asset_exists(PROFILE_EYE):
            raise RuntimeError("one or more required film Toon Profiles are missing")

        masters = [
            create_toon_master("M_OneDriveRigs_FilmToon_Environment_20261016",
                              PROFILE_ENV, "tint", False),
            create_toon_master("M_OneDriveRigs_FilmToon_Character_20261016",
                              PROFILE_CHARACTER, "tint", True),
            create_toon_master("M_OneDriveRigs_FilmToon_Eyes_20261016",
                              PROFILE_EYE, "tint", True),
            create_toon_master("M_OneDriveRigs_FilmToon_Albedo_20261016",
                              PROFILE_CHARACTER, "single", True),
            create_toon_master("M_OneDriveRigs_FilmToon_UDIM_20261016",
                              PROFILE_CHARACTER, "udim3", True),
        ]
        for row in masters:
            row["role"] = "intake_preview"
        report["materials"].extend(masters)

        imported_textures = {}
        for name, spec in CHARACTERS.items():
            tiles = {}
            for tile in (1001, 1002, 1003):
                source = spec["texture_root"] / spec["tiles_folder"] / (spec["skin_prefix"] + ".%d.png" % tile)
                asset_name = "T_%s_Skin_D_%d_20261016" % (name, tile)
                tiles[tile] = import_texture(source, asset_name, report)
            shoes_source = spec["texture_root"] / spec["shoes"]
            shoes_asset = "T_%s_Shoes_D_20261016" % name
            imported_textures[name] = {
                "tiles": tiles,
                "shoes": import_texture(shoes_source, shoes_asset, report),
            }
        report["texture_instances"] = rig_material_instances(report, imported_textures)

        environment_parent = MASTER_DIR + "/M_OneDriveRigs_FilmToon_Environment_20261016"
        import_static_models(report, environment_parent)
        report["status"] = "staged"
        report["notes"] = [
            "OneDriveRigs FilmToon parents and instances are intake previews, not replacements for or approval of Melodia's delivered Universal Toon master.",
            "The approved Universal Toon parent remains unchanged; test any UDIM adaptation against that parent as a separate integration gate.",
            "Static FBXs receive one neutral film-environment instance per imported mesh.",
            "Dana, David, and Sam source textures are imported and assigned to prepared character MIs.",
            "Character skeletal meshes remain unimported pending Dana body/face/eye FBX roundtrip proof.",
            "Source rig licenses are single-user; keep imported rig derivatives local and uncommitted.",
        ]
    except Exception as exc:
        report["status"] = "failed"
        report["error"] = str(exc)
        report["traceback"] = traceback.format_exc()
        write_report(report)
        raise
    write_report(report)
    unreal.log("OneDrive rig intake staged: %s" % str(REPORT_PATH))


main()
