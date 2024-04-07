"""
Camera Shaker v1.0 by Will Marciano
"""
import maya.cmds as cmds
import maya.mel as mel
import shutil
import sys
import os

def onMayaDroppedPythonFile(*args):

    prefs_dir = os.path.dirname(cmds.about(preferences=True))
    scripts_dir = os.path.normpath(os.path.join(prefs_dir, "scripts"))
    shutil.copy(__file__, scripts_dir)

    current_shelf = mel.eval("string $currentShelf = `tabLayout -query -selectTab $gShelfTopLevel`;")
    cmds.setParent(current_shelf)
    cmds.shelfButton(command="import camShaker; camShaker.execute()", ann="Add Camera Shake",
                     label="camShake", image="move_M.png", sourceType="python", iol="camShake")

    cmds.confirmDialog(message="Script successfully installed! Access it from the new button in the shelf ^",
                       title="CamShaker v1.0 by Will Marciano")

def addCamShake(cams):
    if cmds.nodeType(cams[0]) == 'camera':
        cams = cmds.listRelatives(allCams, parent=True)
    for i, cam in enumerate(cams):
        camShape = cmds.listRelatives(cam, shapes=True)[0]
        if cmds.nodeType(camShape) != 'camera':
            sys.exit("Can't find a camera.\n")
        if cmds.attributeQuery('camShake_strength', node=cam, exists=True):
            cmds.warning("This camera already has shake attributes!\n")
            oldExpressions = cmds.ls("*camShake_expr*")
            cmds.delete(oldExpressions)
        else:
            cmds.addAttr(cam, longName='camShake_strength', niceName='Shake Strength', attributeType='float', defaultValue=1,
                         hasMinValue=True, keyable=True, minValue=0, readable=True, softMaxValue=1)
            cmds.addAttr(cam, longName='camShake_freqHoriz', niceName='Horizontal Freq', attributeType='float', defaultValue=0.5,
                         hasMinValue=True, keyable=True, minValue=0, readable=True, softMaxValue=1)
            cmds.addAttr(cam, longName='camShake_strHoriz', niceName='Horizontal Amnt', attributeType='float', defaultValue=1,
                         hasMinValue=True, keyable=True, minValue=0, readable=True, softMaxValue=1)
            cmds.addAttr(cam, longName='camShake_freqVert', niceName='Vertical Freq', attributeType='float', defaultValue=0.25,
                         hasMinValue=True, keyable=True, minValue=0, readable=True, softMaxValue=1)
            cmds.addAttr(cam, longName='camShake_strVert', niceName='Vertical Amnt', attributeType='float', defaultValue=1,
                         hasMinValue=True, keyable=True, minValue=0, readable=True, softMaxValue=1)
            #cmds.setAttr(sel[x] + '.camShake_strength', 1)
            #cmds.setAttr(sel[x] + '.camShake_freqHoriz', 2)
            #cmds.setAttr(sel[x] + '.camShake_strHoriz', 1)
        cmds.setAttr(camShape + '.shakeEnabled', 1)
        expre1 = cmds.expression(string=f"float $strength = `getAttr {cam}.camShake_strength`;\n" +
                                        f"float $freqHoriz = `getAttr {cam}.camShake_freqHoriz`;\n" +
                                        f"float $strHoriz = `getAttr {cam}.camShake_strHoriz`;\n" +
                                        f"{camShape}.horizontalShake = noise(frame*$freqHoriz/10)/100 * $strHoriz * $strength;",
                                 object=cam, ae=True, unitConversion='all')
        expre2 = cmds.expression(string=f"float $strength = `getAttr {cam}.camShake_strength`;\n" +
                                        f"float $freqVert = `getAttr {cam}.camShake_freqVert`;\n" +
                                        f"float $strVert = `getAttr {cam}.camShake_strVert`;\n" +
                                        f"{camShape}.verticalShake = noise((50+frame)*$freqVert/10)/100 * $strVert * $strength;",
                                 object=cam, ae=True, unitConversion='all')
        cmds.rename(expre1, 'camShake_exprHorizontal')
        cmds.rename(expre2, 'camShake_exprVertical')

    sys.stdout.write(f'Successfully added cameraShake to {cams}\n')


def execute():
    camList = []
    selected = cmds.ls(sl=True)
    allCams = cmds.listRelatives(cmds.ls(type="camera"), parent=True)
    selectedCams = [cam for cam in allCams if cam in selected]
    if len(selectedCams) == 0:
        activeCam = 'persp'
        for panel in cmds.getPanel(type="modelPanel"):
            activeCam = cmds.modelEditor(panel, q=1, av=1, cam=1)
        dialog = cmds.confirmDialog(t='Add Camera Shake',
                                    m=f'No camera selected! Would you like to add it to your active camera, {activeCam}?',
                                    button=['Yes', 'Different Camera', 'Cancel'],
                                    db='Yes',
                                    cb='Cancel',
                                    ds='Cancel')
        if dialog == "Cancel":
            sys.exit()
        elif dialog == "Different Camera":
            options = allCams
            options.append("Cancel")
            dialog2 = cmds.confirmDialog(t='Add Camera Shake',
                                        m=f'Add shake to which camera?',
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
    addCamShake(camList)
