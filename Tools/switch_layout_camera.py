"""One-click layout camera switcher. Run in Maya's script editor."""
import maya.cmds as cmds
SHOTS = {'62': 'Cam_Shot62', '63A': 'Cam_Shot63A1', '63B': 'Cam_Shot63B1', '64A': 'Cam_Shot64A1', '64B': 'Cam_Shot64B1', '65': 'Cam_Shot65', '66A': 'Cam_Shot66A1', '66B': 'Cam_Shot66B1'}
def go(shot):
    cam = SHOTS[shot]
    if cmds.objExists(cam):
        cmds.lookThru(cam)
        cmds.select(cam, replace=True)
        print('Layout camera:', shot, cam)
if __name__ == '__main__':
    import sys
    go(sys.argv[1] if len(sys.argv) > 1 else '62')
