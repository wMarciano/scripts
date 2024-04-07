"""
Camera Baker v1.1 by Will Marciano
"""
import maya.cmds as cmds
import maya.mel as mel
import shutil
import sys
import os
import urllib
import re
from subprocess import call

VERSION = 1.1
UPDATE_URL = "https://raw.githubusercontent.com/wMarciano/scripts/main/camBaker.py"

def onMayaDroppedPythonFile(*args):
    prefs_dir = os.path.dirname(cmds.about(preferences=True))
    scripts_dir = os.path.normpath(os.path.join(prefs_dir, "scripts"))
    shutil.copy(__file__, scripts_dir)

    current_shelf = mel.eval("string $currentShelf = `tabLayout -query -selectTab $gShelfTopLevel`;")
    cmds.setParent(current_shelf)
    cmds.shelfButton(command="import importlib; import camBaker; importlib.reload(camBaker); camBaker.execute()", ann="Bake Cam (w/ shake!)",
                     label="camBaker", image="exportCache.png", sourceType="python", iol="camBake")

    cmds.messageLine("Script successfully installed! Access it from the new button in the shelf ^")
def bakeCamera(cams):
    if cmds.nodeType(cams[0]) == 'camera':
        cams = cmds.listRelatives(allCams, parent=True)
    for i, cam in enumerate(cams):
        camShape = cmds.listRelatives(cam, shapes=True)[0]
        cam_lrPivot = cmds.xform(cam, query=True, rotatePivot=True, worldSpace=False)

        # create new camera
        bakeCam, bakeCamShape = cmds.camera(name=f"{cam}_bake")
        bakeCam_constraint = cmds.parentConstraint(cam,bakeCam, maintainOffset = 0)
        cmds.setAttr(bakeCam_constraint[0]+'.target[0].targetOffsetTranslateX',cam_lrPivot[0]*-1)
        cmds.setAttr(bakeCam_constraint[0]+'.target[0].targetOffsetTranslateY',cam_lrPivot[1]*-1)
        cmds.setAttr(bakeCam_constraint[0]+'.target[0].targetOffsetTranslateZ',cam_lrPivot[2]*-1)
        # get a list of all camera shape attributes
        camAttr = cmds.listAttr(camShape)
        camAttr += ['translate', 'rotate', 'scale']

        # loop through all attributes and connect them to the new camera
        for attr in camAttr:
            try:
                cmds.connectAttr(camShape+'.'+ attr, bakeCamShape+'.'+ attr, force=True)
            except RuntimeError:
                pass
        dialog = cmds.confirmDialog(t=f'Cam Baker v{VERSION}',
                                    m=f'Which axis is HORIZONTAL for {cam}?',
                                    button=['X', 'Y (Default)', 'Z', 'Cancel'],
                                    db='Y',
                                    cb='Cancel',
                                    ds='Cancel')
        if dialog is 'Cancel':
            return
        else:
            horizontalAxis = dialog.replace(" (Default)","")
        dialog = cmds.confirmDialog(t=f'Cam Baker v{VERSION}',
                                    m=f'Which axis is VERTICAL for {cam}?',
                                    button=['X (Default)', 'Y', 'Z', 'Cancel'],
                                    db='X',
                                    cb='Cancel',
                                    ds='Cancel')
        if dialog is 'Cancel':
            return
        else:
            verticalAxis = dialog.replace(" (Default)","")
        cmds.addAttr(bakeCamShape, longName='camBake_rotHoriz', niceName='RotHoriz', attributeType='float')
        cmds.addAttr(bakeCamShape, longName='camBake_rotVert', niceName='RotVert', attributeType='float')
        cmds.connectAttr(f"{bakeCam_constraint[0]}.constraintRotate{horizontalAxis}", f"{bakeCamShape}.camBake_rotHoriz")
        cmds.connectAttr(f"{bakeCam_constraint[0]}.constraintRotate{verticalAxis}", f"{bakeCamShape}.camBake_rotVert")
        camAttr += ['camBake_rotHoriz', 'camBake_rotVert']
        cmds.bakeResults(bakeCam, attribute=camAttr,simulation=True, disableImplicitControl=True, preserveOutsideKeys=True, time=(cmds.playbackOptions(q=True, min=True), cmds.playbackOptions(q=True, max=True)))
        cmds.delete(bakeCam_constraint)
        horizConnections = cmds.listConnections(f"{bakeCam}.rotate{horizontalAxis}", plugs=True, destination=True) or []
        for con in horizConnections:
            cmds.disconnectAttr(con, f"{bakeCam}.rotate{horizontalAxis}")
        vertConnections = cmds.listConnections(f"{bakeCam}.rotate{verticalAxis}", plugs=True, destination=True) or []
        for con in vertConnections:
            cmds.disconnectAttr(con, f"{bakeCam}.rotate{verticalAxis}")
        expre1 = cmds.expression(string=f"float $originalRotHoriz = `getAttr {bakeCamShape}.camBake_rotHoriz`;\n" +
                                        f"{bakeCam}.rotate{horizontalAxis} = $originalRotHoriz-22.5*`getAttr {bakeCamShape}.horizontalShake`;")
        expre2= cmds.expression(string=f"float $originalRotVert = `getAttr {bakeCamShape}.camBake_rotVert`;\n" +
                                       f"{bakeCam}.rotate{verticalAxis} = $originalRotVert+22.5*`getAttr {bakeCamShape}.verticalShake`;")
        cmds.rename(expre1, 'camBake_exprHorizontal')
        cmds.rename(expre2, 'camBake_exprVertical')
        shakeConnections = cmds.listConnections(f'{bakeCamShape}.shakeEnabled', plugs=True, destination=True) or []
        for con in shakeConnections:
            cmds.disconnectAttr(con, f'{bakeCamShape}.shakeEnabled')
        cmds.setAttr(f'{bakeCamShape}.shakeEnabled', 0)
        cmds.bakeResults(bakeCam, attribute=camAttr, simulation=True, disableImplicitControl=True, preserveOutsideKeys=True,
                         time=(cmds.playbackOptions(q=True, min=True), cmds.playbackOptions(q=True, max=True)))
        #cmds.delete("camBake_exprVertical")
        #cmds.delete("camBake_exprHorizontal")

        # iterate through each attribute and disconnect it
        for attr in camAttr:
            try:
                cmds.disconnectAttr(camShape+'.'+ attr, bakeCamShape+'.'+ attr)
            except RuntimeError:
                pass
            except ValueError:
                pass

def execute():
    update(UPDATE_URL)
    try:
        update(UPDATE_URL)
    except:
        cmds.warning("Couldn't fetch updates...")
    camList = []
    selected = cmds.ls(sl=True)
    allCams = cmds.listRelatives(cmds.ls(type="camera"), parent=True)
    selectedCams = [cam for cam in allCams if cam in selected]
    if len(selectedCams) == 0:
        activeCam = 'persp'
        for panel in cmds.getPanel(type="modelPanel"):
            activeCam = cmds.modelEditor(panel, q=1, av=1, cam=1)
        dialog = cmds.confirmDialog(t='Bake Camera',
                                    m=f'No camera selected! Would you like to bake your active camera, {activeCam}?',
                                    button=['Yes', 'Different Camera', 'Cancel'],
                                    db='Yes',
                                    cb='Cancel',
                                    ds='Cancel')
        if dialog == "Cancel":
            sys.exit()
        elif dialog == "Different Camera":
            options = allCams
            options.append("Cancel")
            dialog2 = cmds.confirmDialog(t='Bake Camera',
                                         m=f'Bake which camera?',
                                         button=options,
                                         db=options[0],
                                         cb='Cancel',
                                         ds='Cancel')
            if dialog2 == "Cancel":
                sys.exit()
            camList.append(dialog2)
        else:
            camList.append(activeCam)
    else:
        camList = selectedCams
    bakeCamera(camList)

def update(dl_url, force_update=False):
    """
Attempts to download the update url in order to find if an update is needed.
If an update is needed, the current script is backed up and the update is
saved in its place.
"""
    def compare_versions(vA, vB):
        """
    Compares two version number strings
    @param vA: first version string to compare
    @param vB: second version string to compare
    @author <a href="http_stream://sebthom.de/136-comparing-version-numbers-in-jython-pytho/">Sebastian Thomschke</a>
    @return negative if vA < vB, zero if vA == vB, positive if vA > vB.
    """
        if vA == vB: return 0

        def num(s):
            if s.isdigit(): return int(s)
            return s

        seqA = map(num, re.findall('\d+|\w+', vA.replace('-SNAPSHOT', '')))
        seqB = map(num, re.findall('\d+|\w+', vB.replace('-SNAPSHOT', '')))

        # this is to ensure that 1.0 == 1.0.0 in cmp(..)
        lenA, lenB = len(list(seqA)), len(list(seqB))
        for i in range(lenA, lenB): seqA += (0,)
        for i in range(lenB, lenA): seqB += (0,)
        import operator
        rc = operator.eq(set(seqA), set(seqB))

        if rc == 0:
            if vA.endswith('-SNAPSHOT'): return -1
            if vB.endswith('-SNAPSHOT'): return 1
        return rc

    import urllib.request
    import os

    #path = os.path.dirname(__file__)
    real_file = os.path.realpath(__file__)
    #print(real_file)

    with urllib.request.urlopen(dl_url) as upd:
        with open(real_file, "wb+") as f:
            update = upd.read().decode('utf-8')
            #print(update)
            pattern = r"(?sm)VERSION = (?:(\d+)\.)?(?:(\d+)\.)?(?:(\d+)\.\d+)"
            version = re.search(pattern, update)[0]
            version = version.replace("VERSION = ", "")
            if compare_versions(version, str(VERSION)):
                dialog= cmds.confirmDialog(t="CamBaker Update Available!",
                    m=f"Version {version} is available. You have version {VERSION}. Update?",
                                   button=['Yes', 'No'],
                                   cb = 'No',
                                   ds = 'No')
                if dialog == "Yes":
                    f.write(update)
            else:
                print(f"Local version {VERSION} is up to date ({version})")
    return
