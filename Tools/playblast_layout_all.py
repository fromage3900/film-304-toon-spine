"""Render layout playblasts for all shots. Run in Maya GUI."""
import maya.cmds as cmds, os
SHOTS = {'62': ('Cam_Shot62', 1, 48), '63A': ('Cam_Shot63A1', 49, 72), '63B': ('Cam_Shot63B1', 73, 120), '64A': ('Cam_Shot64A1', 121, 144), '64B': ('Cam_Shot64B1', 145, 192), '65': ('Cam_Shot65', 193, 216), '66A': ('Cam_Shot66A1', 217, 240), '66B': ('Cam_Shot66B1', 241, 288)}
OUT = r'G:/film-304-toon-spine/Saved/Playblasts/Layout_62-66/v03'
def run(width=640, height=360):
    os.makedirs(OUT, exist_ok=True)
    for label, (cam, start, end) in SHOTS.items():
        if not cmds.objExists(cam):
            continue
        cmds.lookThru(cam)
        path = os.path.join(OUT, 'Shepherd_Brennan_LayoutScene(62-66)_BS_shot' + label + '_v03.mp4')
        cmds.playblast(format='movie', filename=path, startTime=start, endTime=end,
                       widthHeight=(width, height), percent=100, viewer=False,
                       showOrnaments=False, offScreen=True, forceOverwrite=True, compression='H.264')
        print('Playblast:', path)
if __name__ == '__main__':
    run()
