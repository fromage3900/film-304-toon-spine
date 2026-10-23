import math
import unreal

world = unreal.EditorLevelLibrary.get_editor_world()
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

yaw_rad = math.radians(-25.0)
cos_y = math.cos(yaw_rad)
sin_y = math.sin(yaw_rad)

def to_world(xl, yl, zl):
    return unreal.Vector(xl * cos_y - yl * sin_y, xl * sin_y + yl * cos_y, zl)

# Spawn a high-altitude overhead camera looking straight down
# Center of office is roughly X_local = 250, Y_local = 250
cam_loc = to_world(250.0, 250.0, 345.0)
cam_rot = unreal.Rotator(pitch=-89.9, yaw=-25.0, roll=0.0)

rt = unreal.RenderingLibrary.create_render_target2d(world, 1920, 1080, format=unreal.TextureRenderTargetFormat.RTF_RGBA8)
cap = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SceneCapture2D, cam_loc, cam_rot)
comp = cap.get_component_by_class(unreal.SceneCaptureComponent2D)
comp.texture_target = rt
comp.capture_source = unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR
comp.fov_angle = 110.0

# Hide the ceiling slab temporarily for this top-down shot so we see the entire floor plan!
ceiling_actors = []
for a in eas.get_all_level_actors():
    if any(k in a.get_actor_label() for k in ["Ceiling", "HVAC", "Troffer"]):
        a.set_actor_hidden_in_game(True)
        ceiling_actors.append(a)

comp.capture_scene()

for a in ceiling_actors:
    a.set_actor_hidden_in_game(False)

out_dir = "C:/Users/froma/.gemini/antigravity-ide/brain/10d93b13-68af-4057-ae2d-343574ed43dd"
unreal.RenderingLibrary.export_render_target(world, rt, out_dir, "floorplan_diagnostic_topdown.png")
eas.destroy_actor(cap)

print("Exported floorplan_diagnostic_topdown.png!")
