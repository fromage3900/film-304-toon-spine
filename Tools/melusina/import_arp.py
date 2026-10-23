# Tools/melusina/import_arp.py
# Import Melusina's ARP FBX once and save a scratch Maya ASCII file.
import os
import maya.standalone
maya.standalone.initialize(name="python")
from maya import cmds, mel

SRC = r"G:\MelusinaRigFinalSeparate\SK_MelusinaRigARP.fbx"
OUT = r"G:\film-304-toon-spine\Saved\OfflineIntake\20261017\melusina_assignment1\scratch\arp_import.ma"

def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    cmds.file(newFile=True, force=True)
    cmds.currentUnit(linear="cm", time="film", angle="deg")
    cmds.loadPlugin("fbxmaya", quiet=True)
    mel.eval("FBXResetImport")
    mel.eval('FBXImportMode -v "add"')
    mel.eval("FBXImportFillTimeline -v true")
    mel.eval('FBXImport -f "%s"' % SRC.replace("\\", "/"))
    cmds.file(rename=OUT)
    cmds.file(save=True, type="mayaAscii")
    print("IMPORT SAVED %s" % OUT)

main()
