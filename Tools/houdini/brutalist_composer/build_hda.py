"""Builds and compiles the HDA_Brutalist_ShotComposer digital asset for Houdini Engine.

Run via hython:
    & "C:\\Program Files\\Side Effects Software\\Houdini 22.0.368\\bin\\hython.exe" Tools/houdini/brutalist_composer/build_hda.py
"""
import sys
from pathlib import Path

# Add project root and composer directory to path
REPO = Path(__file__).resolve().parents[3]
COMPOSER_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(COMPOSER_DIR))

import hou

HDA_DIR = REPO / "Content" / "Houdini"
HDA_PATH = HDA_DIR / "HDA_Brutalist_ShotComposer.hda"
AUDIT_LOG = REPO / "Saved" / "Audit" / "HoudiniBrutalist" / "build_hda_report.json"

OPERATOR_NAME = "film304_brutalist_shot_composer"
OPERATOR_LABEL = "Film 304 Brutalist Shot Composer"

def create_hda():
    print(f"[HDA Builder] Target HDA path: {HDA_PATH}")
    HDA_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)

    # 1. Start clean session
    hou.hipFile.clear(suppress_save_prompt=True)
    obj = hou.node("/obj")
    geo = obj.createNode("geo", "brutalist_builder_stage")

    for child in geo.children():
        child.destroy()

    # 2. Create subnetwork that will become the HDA
    subnet = geo.createNode("subnet", "shot_composer_core")

    sub_input = subnet.createNode("null", "IN_CAMERA_REF")
    python_sop = subnet.createNode("python", "build_composition_sop")
    sub_output = subnet.createNode("output", "OUT_INSTANCES")

    python_sop.setInput(0, sub_input)
    sub_output.setInput(0, python_sop)
    sub_output.setDisplayFlag(True)
    sub_output.setRenderFlag(True)

    # Embed python execution script
    sop_code = '''# Embedded Python SOP script for Brutalist Shot Composer
import sys
from pathlib import Path
import math

repo_path = r"''' + str(REPO).replace('\\', '/') + '''"
tools_path = r"''' + str(COMPOSER_DIR).replace('\\', '/') + '''"
if repo_path not in sys.path: sys.path.insert(0, repo_path)
if tools_path not in sys.path: sys.path.insert(0, tools_path)

import hou
import importlib
if 'composer_core' in sys.modules:
    importlib.reload(sys.modules['composer_core'])
from composer_core import UnifiedFilmComposer, CameraFrustum, Vec3, ASSET_CATALOG, MATERIALS

node = hou.pwd()
geo = node.geometry()
geo.clear()

parent = node.parent()

# Parameters
scene_mode = int(parent.evalParm("scene_mode")) # 0: Exterior, 1: Cubicles, 2: Labyrinth, 3: Breakroom, 4: Hero, 5: Hybrid
cam_pos_tuple = parent.evalParmTuple("cam_pos")
cam_x, cam_y, cam_z = cam_pos_tuple[0], cam_pos_tuple[1], cam_pos_tuple[2]

cam_tgt_tuple = parent.evalParmTuple("cam_target")
tgt_x, tgt_y, tgt_z = cam_tgt_tuple[0], cam_tgt_tuple[1], cam_tgt_tuple[2]

focal = parent.evalParm("focal_length")
sensor_w = parent.evalParm("sensor_width")
aspect = parent.evalParm("aspect_ratio")
near_m = parent.evalParm("clip_near")
far_m = parent.evalParm("clip_far")

fg_density = parent.evalParm("density_fg")
mg_density = parent.evalParm("density_mg")
sky_density = parent.evalParm("density_skyline")
neg_space = parent.evalParm("negative_space_radius")
seed = parent.evalParm("seed")
include_roofs = bool(parent.evalParm("include_roofs"))
output_mode = parent.evalParm("output_mode") # 0: Points/Instances, 1: Bounding Proxies, 2: Both

# Construct camera and composer
cam = CameraFrustum(
    pos=Vec3(cam_x, cam_y, cam_z),
    target=Vec3(tgt_x, tgt_y, tgt_z),
    focal_length_mm=focal,
    sensor_w_mm=sensor_w,
    aspect_ratio=aspect,
    near_m=near_m,
    far_m=far_m
)

composer = UnifiedFilmComposer(cam, seed=seed)

if scene_mode == 0:
    elements = composer.build_exterior_brutalist(
        framing_curtain_density=fg_density,
        midground_density=mg_density,
        skyline_density=sky_density,
        negative_space_radius_m=neg_space,
        include_roofs=include_roofs,
        grid_yaw=0.0
    )
elif scene_mode == 1:
    elements = composer.build_interior_cubicle_hive(
        row_count=3,
        pods_per_row=2,
        include_desks=True,
        include_chairs=True
    )
elif scene_mode == 2:
    elements = composer.build_interior_labyrinth()
elif scene_mode == 3:
    elements = composer.build_breakroom_kitchen()
elif scene_mode == 4:
    elements = composer.build_hero_workstation()
elif scene_mode == 5:
    elements = composer.build_hybrid_establishing()
else:
    elements = composer.build_exterior_brutalist()

# Attributes for Houdini Engine for Unreal
s_instance = geo.addAttrib(hou.attribType.Point, "unreal_instance", "")
s_mat_inst = geo.addAttrib(hou.attribType.Point, "unreal_material_instance", "")
s_mat = geo.addAttrib(hou.attribType.Point, "unreal_material", "")
s_mat0 = geo.addAttrib(hou.attribType.Point, "unreal_material_0", "")
s_mat1 = geo.addAttrib(hou.attribType.Point, "unreal_material_1", "")
s_mat2 = geo.addAttrib(hou.attribType.Point, "unreal_material_2", "")
s_mat_inst0 = geo.addAttrib(hou.attribType.Point, "unreal_material_instance_0", "")
s_mat_inst1 = geo.addAttrib(hou.attribType.Point, "unreal_material_instance_1", "")
s_mat_inst2 = geo.addAttrib(hou.attribType.Point, "unreal_material_instance_2", "")

v_orient = geo.addAttrib(hou.attribType.Point, "orient", (0.0, 0.0, 0.0, 1.0))
v_rot = geo.addAttrib(hou.attribType.Point, "rot", (0.0, 0.0, 0.0))
v_scale = geo.addAttrib(hou.attribType.Point, "scale", (1.0, 1.0, 1.0))
s_cat = geo.addAttrib(hou.attribType.Point, "category", "")
s_name = geo.addAttrib(hou.attribType.Point, "asset_name", "")
v_cd = geo.addAttrib(hou.attribType.Point, "Cd", (1.0, 1.0, 1.0))

colors = {
    "foreground": (0.95, 0.45, 0.15),
    "foreground_accent": (0.95, 0.65, 0.20),
    "midground": (0.55, 0.58, 0.62),
    "skyline": (0.22, 0.35, 0.55),
    "cubicle_pod": (0.20, 0.65, 0.85),
    "cubicle_maze": (0.30, 0.50, 0.80),
    "hero_desk": (0.90, 0.75, 0.20),
    "furniture_desk": (0.80, 0.65, 0.30),
    "furniture_chair": (0.25, 0.25, 0.28),
    "zmj_kitchen": (0.85, 0.30, 0.20),
    "zmj_prop": (0.95, 0.85, 0.30),
    "zmj_appliance": (0.75, 0.80, 0.85),
    "zmj_storage": (0.60, 0.45, 0.35)
}

for b in elements:
    # 1. Point / Instance Output
    if output_mode in (0, 2):
        pt = geo.createPoint()
        pt.setPosition(hou.Vector3(b.position_m.x, b.position_m.y, b.position_m.z))
        pt.setAttribValue(s_instance, b.asset_path)

        # Multi-slot vs single-slot material assignment
        if getattr(b, 'is_multi_slot', False):
            mat0 = b.material_slots.get(0, "")
            mat1 = b.material_slots.get(1, "")
            mat2 = b.material_slots.get(2, "")
            if mat0:
                pt.setAttribValue(s_mat0, mat0)
                pt.setAttribValue(s_mat_inst0, mat0)
            if mat1:
                pt.setAttribValue(s_mat1, mat1)
                pt.setAttribValue(s_mat_inst1, mat1)
            if mat2:
                pt.setAttribValue(s_mat2, mat2)
                pt.setAttribValue(s_mat_inst2, mat2)
        else:
            pt.setAttribValue(s_mat_inst, b.material_path)
            pt.setAttribValue(s_mat, b.material_path)
            pt.setAttribValue(s_mat0, b.material_path)
            pt.setAttribValue(s_mat_inst0, b.material_path)

        pt.setAttribValue(s_cat, b.category)
        pt.setAttribValue(s_name, b.asset_name)
        pt.setAttribValue(v_scale, (b.scale.x, b.scale.y, b.scale.z))
        pt.setAttribValue(v_cd, colors.get(b.category, (0.7, 0.7, 0.7)))

        # Direct Euler rotation (rot) and quaternion (orient) around Y
        pt.setAttribValue(v_rot, (0.0, b.rotation_deg_y, 0.0))
        rad = math.radians(b.rotation_deg_y * 0.5)
        orient_quat = (0.0, math.sin(rad), 0.0, math.cos(rad))
        pt.setAttribValue(v_orient, orient_quat)

    # 2. Proxy Bounding Box Geometry Output (for viewport preview / collision hulls)
    if output_mode in (1, 2):
        bx, by, bz = b.bbox_m[0] * b.scale.x, b.bbox_m[1] * b.scale.y, b.bbox_m[2] * b.scale.z
        rad = math.radians(b.rotation_deg_y)
        cos_y = math.cos(rad)
        sin_y = math.sin(rad)

        def rot_p(lx, ly, lz):
            rx = lx * cos_y + lz * sin_y
            rz = -lx * sin_y + lz * cos_y
            return hou.Vector3(b.position_m.x + rx, b.position_m.y + ly, b.position_m.z + rz)

        hx, hy, hz = bx * 0.5, by, bz * 0.5
        c_pts = [
            rot_p(-hx, 0.0, -hz), rot_p(hx, 0.0, -hz),
            rot_p(hx, 0.0, hz), rot_p(-hx, 0.0, hz),
            rot_p(-hx, hy, -hz), rot_p(hx, hy, -hz),
            rot_p(hx, hy, hz), rot_p(-hx, hy, hz)
        ]
        h_pts = [geo.createPoint() for _ in range(8)]
        for i, hp in enumerate(h_pts):
            hp.setPosition(c_pts[i])
            hp.setAttribValue(s_cat, b.category)
            hp.setAttribValue(s_name, b.asset_name)
            hp.setAttribValue(v_cd, colors.get(b.category, (0.7, 0.7, 0.7)))

        faces = [
            (0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4),
            (2, 3, 7, 6), (0, 3, 7, 4), (1, 2, 6, 5)
        ]
        for f in faces:
            poly = geo.createPolygon()
            for v_idx in f:
                poly.addVertex(h_pts[v_idx])
'''
    python_sop.parm("python").set(sop_code)

    # 3. Build HDA Definition
    subnet.layoutChildren()
    hda_node = subnet.createDigitalAsset(
        name=OPERATOR_NAME,
        hda_file_name=str(HDA_PATH),
        description=OPERATOR_LABEL,
        min_num_inputs=0,
        max_num_inputs=1
    )

    ptg = hda_node.parmTemplateGroup()

    # Create Parameter Tabs
    tab_scene = hou.FolderParmTemplate("folder_scene", "Scene & Preset", folder_type=hou.folderType.Tabs)
    tab_cam = hou.FolderParmTemplate("folder_cam", "Camera & Framing", folder_type=hou.folderType.Tabs)
    tab_comp = hou.FolderParmTemplate("folder_comp", "Composition & Density", folder_type=hou.folderType.Tabs)
    tab_out = hou.FolderParmTemplate("folder_out", "Output & Display", folder_type=hou.folderType.Tabs)

    # Scene Preset Menu
    p_scene = hou.MenuParmTemplate("scene_mode", "Scene Mode / Preset",
                                   menu_items=("0", "1", "2", "3", "4", "5"),
                                   menu_labels=(
                                       "Exterior Brutalist Frustum",
                                       "Interior Cubicle Hive",
                                       "Interior Labyrinth Maze",
                                       "Interior ZMJ Break Room (6.0x Architectural Scale)",
                                       "Hero Workstation",
                                       "Hybrid Office Window Establishing (Office + Monoliths)"
                                   ),
                                   default_value=0)
    tab_scene.addParmTemplate(p_scene)

    # Camera Parameters
    p_cam_pos = hou.FloatParmTemplate("cam_pos", "Camera Position", 3, default_value=(-5.0, 2.8, -25.0))
    p_cam_target = hou.FloatParmTemplate("cam_target", "Camera Target", 3, default_value=(0.0, 42.0, 60.0))
    p_focal = hou.FloatParmTemplate("focal_length", "Focal Length (mm)", 1, default_value=(24.0,), min=12.0, max=200.0)
    p_sensor = hou.FloatParmTemplate("sensor_width", "Sensor Width (mm)", 1, default_value=(35.0,))
    p_aspect = hou.FloatParmTemplate("aspect_ratio", "Aspect Ratio", 1, default_value=(16.0 / 9.0,))
    p_near = hou.FloatParmTemplate("clip_near", "Near Distance (m)", 1, default_value=(15.0,))
    p_far = hou.FloatParmTemplate("clip_far", "Far Distance (m)", 1, default_value=(600.0,))

    tab_cam.addParmTemplate(p_cam_pos)
    tab_cam.addParmTemplate(p_cam_target)
    tab_cam.addParmTemplate(p_focal)
    tab_cam.addParmTemplate(p_sensor)
    tab_cam.addParmTemplate(p_aspect)
    tab_cam.addParmTemplate(p_near)
    tab_cam.addParmTemplate(p_far)

    # Composition Parameters
    p_fg_dens = hou.FloatParmTemplate("density_fg", "Foreground Curtain Density", 1, default_value=(1.0,), min=0.0, max=3.0)
    p_mg_dens = hou.FloatParmTemplate("density_mg", "Midground Slab Density", 1, default_value=(1.0,), min=0.0, max=3.0)
    p_sky_dens = hou.FloatParmTemplate("density_skyline", "Skyline Monolith Density", 1, default_value=(1.0,), min=0.0, max=3.0)
    p_neg_space = hou.FloatParmTemplate("negative_space_radius", "Negative Space Radius (m)", 1, default_value=(25.0,), min=5.0, max=100.0)
    p_seed = hou.IntParmTemplate("seed", "Composition Seed", 1, default_value=(42,))
    p_roofs = hou.ToggleParmTemplate("include_roofs", "Include Crowning Roof Forms", default_value=False)

    tab_comp.addParmTemplate(p_fg_dens)
    tab_comp.addParmTemplate(p_mg_dens)
    tab_comp.addParmTemplate(p_sky_dens)
    tab_comp.addParmTemplate(p_neg_space)
    tab_comp.addParmTemplate(p_seed)
    tab_comp.addParmTemplate(p_roofs)

    # Output Parameters
    p_mode = hou.MenuParmTemplate("output_mode", "Output Mode",
                                  menu_items=("0", "1", "2"),
                                  menu_labels=("Unreal Engine Instances (Points)", "Proxy Bounding Boxes", "Both"),
                                  default_value=0)
    tab_out.addParmTemplate(p_mode)

    ptg.append(tab_scene)
    ptg.append(tab_cam)
    ptg.append(tab_comp)
    ptg.append(tab_out)

    definition = hda_node.type().definition()
    definition.setParmTemplateGroup(ptg)
    definition.save(str(HDA_PATH))
    print(f"[HDA Builder] SUCCESS! Saved digital asset to: {HDA_PATH}")

    import json
    report = {
        "status": "success",
        "hda_path": str(HDA_PATH),
        "operator": OPERATOR_NAME,
        "label": OPERATOR_LABEL,
        "parameters": [p.name() for p in ptg.parmTemplates()],
        "houdini_version": hou.applicationVersionString()
    }
    AUDIT_LOG.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[HDA Builder] Audit written to {AUDIT_LOG}")

if __name__ == "__main__":
    create_hda()
