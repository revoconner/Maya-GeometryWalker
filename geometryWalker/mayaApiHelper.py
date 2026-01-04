import maya.OpenMaya as om

class mayaApiHelper(object):
    VTX = 0
    POLY = 1
    EDGE = 2

    def __init__(self, objPath=''):
        self._objPath = objPath
        self._dagPath = ''
        self._polygonIt = ''
        self._vtxIt = ''
        self._edgeIt = ''
        self._mesh = ''
        self._dummyF = om.MScriptUtil()
        self._dummyV = om.MScriptUtil()
        self._dummyE = om.MScriptUtil()
        self.edgeIndex = 0

    def initObject(self):
        if self._dagPath == '':
            self._dagPath = self.dagPath
        if self._mesh == '':
            self._mesh = self.mesh

    def setIndex(self, fNumber, componentType):
        if componentType == self.POLY:
            if self._polygonIt == '':
                self._polygonIt = self.polygonIt
            self._polygonIt.setIndex(fNumber, self._dummyF.asIntPtr())
        if componentType == self.VTX:
            if self._vtxIt == '':
                self._vtxIt = self.vtxIt
            self._vtxIt.setIndex(fNumber, self._dummyV.asIntPtr())
        if componentType == self.EDGE:
            if self._edgeIt == '':
                self._edgeIt = self.edgeIt
            self._edgeIt.setIndex(fNumber, self._dummyE.asIntPtr())
            self._edgeIndex = fNumber

    def getConnectedComponent(self, fromComponent, toComponent):
        if fromComponent == self.POLY:
            if toComponent == self.EDGE:
                connectedEdges = om.MIntArray()
                self._polygonIt.getConnectedEdges(connectedEdges)
                return connectedEdges
            if toComponent == self.VTX:
                connectedVtx = om.MIntArray()
                self._polygonIt.getConnectedVertices(connectedVtx)
                return connectedVtx
            if toComponent == self.POLY:
                connectedPolys = om.MIntArray()
                self._polygonIt.getConnectedFaces(connectedPolys)
                return connectedPolys
        if fromComponent == self.VTX:
            if toComponent == self.VTX:
                connectedVtx = om.MIntArray()
                self._vtxIt.getConnectedVertices(connectedVtx)
                return connectedVtx
            if toComponent == self.EDGE:
                connectedEDGE = om.MIntArray()
                self._vtxIt.getConnectedEdges(connectedEDGE)
                return connectedEDGE
        if fromComponent == self.EDGE:
            if toComponent == self.POLY:
                connectedPolys = om.MIntArray()
                self._edgeIt.getConnectedFaces(connectedPolys)
                return connectedPolys

    def getComponent(self, fromComponent, toComponent):
        if fromComponent == self.POLY:
            if toComponent == self.EDGE:
                connectedEdges = om.MIntArray()
                self._polygonIt.getEdges(connectedEdges)
                return connectedEdges
            if toComponent == self.VTX:
                connectedVtx = om.MIntArray()
                self._polygonIt.getVertices(connectedVtx)
                return connectedVtx
        if fromComponent == self.EDGE:
            if toComponent == self.VTX:
                pArray = [
                 0, 0]
                x = om.MScriptUtil()
                x.createFromList(pArray, 2)
                y = x.asInt2Ptr()
                self._mesh.getEdgeVertices(self._edgeIndex, y)
                return [
                 x.getInt2ArrayItem(y, 0, 0), x.getInt2ArrayItem(y, 0, 1)]

    @property
    def mesh(self):
        self._mesh = om.MFnMesh(self._dagPath)
        return self._mesh

    @mesh.setter
    def mesh(self, value):
        self._mesh = value

    @property
    def dagPath(self):
        sel = om.MSelectionList()
        sel.add(self._objPath)
        dagPath = om.MDagPath()
        component = om.MObject()
        sel.getDagPath(0, dagPath, component)
        self._dagPath = dagPath
        return self._dagPath

    @dagPath.setter
    def dagPath(self, value):
        self._dagPath = value

    @property
    def polygonIt(self):
        self._polygonIt = om.MItMeshPolygon(self._dagPath)
        return self._polygonIt

    @property
    def vtxIt(self):
        self._vtxIt = om.MItMeshVertex(self._dagPath)
        return self._vtxIt

    @property
    def edgeIt(self):
        self._edgeIt = om.MItMeshEdge(self._dagPath)
        return self._edgeIt

    @property
    def objPath(self):
        return self._objPath

    @objPath.setter
    def objPath(self, value):
        self._objPath = value