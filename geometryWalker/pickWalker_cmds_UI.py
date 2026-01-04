"""
Created on Dec 1, 2024
Based on original pickWalker by Olygraph
"""

import maya.cmds as cmds
import re
import importlib
from . import walker

class PickWalkerUI(object):
    def __init__(self):
        self.window_name = "pickWalkerWindow"
        self.textVtx = {}

        if cmds.window(self.window_name, exists=True):
            cmds.deleteUI(self.window_name)

        self.window = cmds.window(
            self.window_name,
            title="Pick Walker",
            widthHeight=(420, 420),
            maximizeButton=False
        )

        main_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=8, columnOffset=["both", 8])
        cmds.separator(height=4, style="none", parent=main_layout)

        # Source Mesh
        source_frame = cmds.frameLayout(
            label="Source Mesh",
            collapsable=False,
            marginWidth=8,
            marginHeight=8,
            parent=main_layout
        )
        source_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=4, parent=source_frame)
        self._createFieldRow(source_layout, "0", "Face")
        self._createFieldRow(source_layout, "1", "Vertex 1")
        self._createFieldRow(source_layout, "2", "Vertex 2")

        # Target Mesh
        target_frame = cmds.frameLayout(
            label="Target Mesh",
            collapsable=False,
            marginWidth=8,
            marginHeight=8,
            parent=main_layout
        )
        target_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=4, parent=target_frame)
        self._createFieldRow(target_layout, "3", "Face")
        self._createFieldRow(target_layout, "4", "Vertex 1")
        self._createFieldRow(target_layout, "5", "Vertex 2")

        # Settings
        settings_frame = cmds.frameLayout(
            label="Settings",
            collapsable=False,
            marginWidth=8,
            marginHeight=8,
            parent=main_layout
        )
        settings_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=4, parent=settings_frame)

        self.spaceOption = cmds.radioButtonGrp(
            parent=settings_layout,
            label="Coordinate Space:",
            labelArray2=["Object", "World"],
            numberOfRadioButtons=2,
            select=2,
            columnWidth3=[100, 80, 80]
        )


        # Execute button
        cmds.separator(height=8, style="none", parent=main_layout)
        cmds.button(
            parent=main_layout,
            label="Execute (No Undo)",
            command=lambda x: self._execute(),
            height=32,
            backgroundColor=[0.4, 0.5, 0.6]
        )
        cmds.separator(height=4, style="none", parent=main_layout)

        cmds.showWindow(self.window)

    def _createFieldRow(self, parent, idx, label):
        row = cmds.rowLayout(
            numberOfColumns=3,
            columnWidth3=(70, 260, 40),
            columnAlign3=["right", "left", "center"],
            columnAttach3=["right", "both", "right"],
            adjustableColumn=2,
            parent=parent
        )
        cmds.text(parent=row, label=label, width=70)
        self.textVtx[idx] = cmds.textField(parent=row, editable=False)
        cmds.button(parent=row, label="<<", width=40, command=lambda x, i=idx: self._setFromSelection(i))

    def _setFromSelection(self, idx):
        sel = cmds.ls(sl=True)
        if idx in ("0", "3"):
            fExpend = cmds.filterExpand(ex=True, sm=34)
            itemName = "face"
        else:
            fExpend = cmds.filterExpand(ex=True, sm=31)
            itemName = "vertex"

        if not fExpend:
            cmds.warning(f"Select a {itemName}")
            return
        if len(fExpend) > 1:
            cmds.warning(f"Select only 1 {itemName}")
            return
        cmds.textField(self.textVtx[idx], edit=True, text=sel[0])

    def _execute(self):
        verts = {}
        for i in range(6):
            x = str(i)
            textField = cmds.textField(self.textVtx[x], query=True, text=True)
            if textField != "":
                verts[i] = textField

        coordSys = cmds.radioButtonGrp(self.spaceOption, query=True, select=True)

        faceRegEx = r"^(.*)\.f\[(\d+)\]$"
        vtxRegEx = r"^(.*)\.vtx\[(\d+)\]$"

        try:
            faceIdxA = int(re.match(faceRegEx, verts[0]).group(2))
            faceIdxB = int(re.match(faceRegEx, verts[3]).group(2))
            objA = re.match(faceRegEx, verts[0]).group(1)
            objB = re.match(faceRegEx, verts[3]).group(1)
            v0A = int(re.match(vtxRegEx, verts[1]).group(2))
            v1A = int(re.match(vtxRegEx, verts[2]).group(2))
            v0B = int(re.match(vtxRegEx, verts[4]).group(2))
            v1B = int(re.match(vtxRegEx, verts[5]).group(2))

            importlib.reload(walker)
            myWalker = walker.walker(objA, objB, int(coordSys))
            myWalker.pickWalkTwoMesh(faceIdxA, faceIdxB, [v0A, v1A], [v0B, v1B])

        except (AttributeError, KeyError, IndexError):
            cmds.warning("Fill all fields correctly")

def create():
    return PickWalkerUI()
