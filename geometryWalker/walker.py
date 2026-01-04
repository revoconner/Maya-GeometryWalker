import maya.OpenMaya as om
import maya.mel as ml
import maya.cmds as cmds
from . import mayaApiHelper
import time
from queue import Queue
from threading import Thread

class walker(object):
    vtxListA = []
    edgeListA = []
    queueA = []

    def __init__(self, meshA, meshB='', coordSys=0, copyPos=True, copyColor=False, copyUV=False):
        self._meshA = meshA
        self._meshB = meshB
        self._copyPos = copyPos
        self._copyColor = copyColor
        self._copyUV = copyUV
        if coordSys == 1:
            self._coordSys = om.MSpace.kObject
        elif coordSys == 2:
            self._coordSys = om.MSpace.kWorld

    def getNextVtx(self, mApi, faceID, vtxID):
        mApi.setIndex(vtxID[1], mApi.VTX)
        mApi.setIndex(faceID, mApi.POLY)
        connectedEdges = mApi.getConnectedComponent(mApi.VTX, mApi.EDGE)
        faceVertices = mApi.getComponent(mApi.POLY, mApi.VTX)
        for edge in connectedEdges:
            mApi.setIndex(edge, mApi.EDGE)
            edgeVertices = mApi.getComponent(mApi.EDGE, mApi.VTX)
            for vtx in edgeVertices:
                if vtx not in vtxID and vtx in faceVertices:
                    return (edge, vtx)

    def walkFace(self, mApi, faceID, vtxID):
        seenVtx = []
        queueItem = []
        while True:
            if vtxID[1] in seenVtx:
                break
            nEdge, nVtx = self.getNextVtx(mApi, faceID, vtxID)
            vtxID[0] = vtxID[1]
            vtxID[1] = nVtx
            seenVtx.append(vtxID[0])
            queueItem.append([faceID, nEdge, [vtxID[0], vtxID[1]]])

        del mApi
        del faceID
        del vtxID
        del nEdge
        del seenVtx
        del queueItem
        return queueItem

    def walkFaceDouble(self, mApiA, faceIDA, vtxIDA, mApiB, faceIDB, vtxIDB):
        seenVtxA = []
        seenVtxB = []
        queueItem = []
        while True:
            if vtxIDA[1] in seenVtxA:
                if vtxIDB[1] not in seenVtxB:
                    cmds.error('FACE MISTMATCHE FOUNDED!')
                break
            if vtxIDB[1] in seenVtxB and vtxIDA[1] not in seenVtxA:
                cmds.error('FACE MISTMATCHE FOUNDED!')
            nEdgeA, nVtxA = self.getNextVtx(mApiA, faceIDA, vtxIDA)
            vtxIDA[0] = vtxIDA[1]
            vtxIDA[1] = nVtxA
            nEdgeB, nVtxB = self.getNextVtx(mApiB, faceIDB, vtxIDB)
            vtxIDB[0] = vtxIDB[1]
            vtxIDB[1] = nVtxB
            seenVtxA.append(vtxIDA[0])
            seenVtxB.append(vtxIDB[0])
            queueItem.append([mApiA,
             faceIDA,
             nEdgeA,
             [
              vtxIDA[0], vtxIDA[1]],
             mApiB,
             faceIDB,
             nEdgeB,
             [
              vtxIDB[0], vtxIDB[1]]])

        del seenVtxA
        del seenVtxB
        del nEdgeA
        del nVtxA
        del mApiA
        del faceIDA
        del nEdgeB
        del nVtxB
        del mApiB
        del faceIDB
        return queueItem

    def getOppositeFace(self, mApi, faceId, edgeId):
        mApi.setIndex(edgeId, mApi.EDGE)
        faces = mApi.getConnectedComponent(mApi.EDGE, mApi.POLY)
        for face in faces:
            if face != faceId:
                return face

    def _getLocalVtxIndex(self, mesh, faceId, globalVtxId):
        verts = om.MIntArray()
        mesh.getPolygonVertices(faceId, verts)
        for i in range(verts.length()):
            if verts[i] == globalVtxId:
                return i
        return -1

    def _copyVertexData(self, meshA, meshB, faceA, faceB, vtxA, vtxB):
        if self._copyPos:
            pt = om.MPoint()
            meshA.getPoint(vtxA, pt, self._coordSys)
            meshB.setPoint(vtxB, pt, self._coordSys)

        if self._copyColor:
            localA = self._getLocalVtxIndex(meshA, faceA, vtxA)
            localB = self._getLocalVtxIndex(meshB, faceB, vtxB)
            if localA >= 0 and localB >= 0:
                color = om.MColor()
                colorIdxUtil = om.MScriptUtil()
                colorIdxPtr = colorIdxUtil.asIntPtr()
                try:
                    meshA.getFaceVertexColorIndex(faceA, localA, colorIdxPtr)
                    colorIdx = colorIdxUtil.getInt(colorIdxPtr)
                    meshA.getColor(colorIdx, color)
                    meshB.setVertexColor(color, vtxB)
                except:
                    pass

        if self._copyUV:
            localA = self._getLocalVtxIndex(meshA, faceA, vtxA)
            localB = self._getLocalVtxIndex(meshB, faceB, vtxB)
            if localA >= 0 and localB >= 0:
                uUtil = om.MScriptUtil()
                vUtil = om.MScriptUtil()
                uPtr = uUtil.asFloatPtr()
                vPtr = vUtil.asFloatPtr()
                try:
                    meshA.getPolygonUV(faceA, localA, uPtr, vPtr)
                    u = uUtil.getFloat(uPtr)
                    v = vUtil.getFloat(vPtr)
                except:
                    return
                uvIdUtil = om.MScriptUtil()
                uvIdPtr = uvIdUtil.asIntPtr()
                try:
                    meshB.getPolygonUVid(faceB, localB, uvIdPtr)
                    uvId = uvIdUtil.getInt(uvIdPtr)
                    meshB.setUV(uvId, u, v)
                except:
                    pass

    def pickWalkTwoMesh(self, f1, f2, vtxA, vtxB):
        mA = mayaApiHelper.mayaApiHelper(self._meshA)
        mB = mayaApiHelper.mayaApiHelper(self._meshB)
        mA.initObject()
        mB.initObject()
        seenEdges = []
        benchmarkStart = time.time()
        numEdges = mA.mesh.numEdges()
        queues = self.walkFaceDouble(mA, f1, vtxA, mB, f2, vtxB)
        gMainProgressBar = ml.eval('$tmp = $gMainProgressBar')
        cmds.progressBar(gMainProgressBar, edit=True, beginProgress=True, isInterruptable=True, status='"Pick Walking Mesh ...', maxValue=numEdges)
        while True:
            if cmds.progressBar(gMainProgressBar, query=1, isCancelled=1):
                break
            if queues == []:
                break
            for queue in queues:
                mApiA, faceIDA, edgeIDA, vtxIDA, mApiB, faceIDB, edgeIDB, vtxIDB = queue
                if edgeIDA not in seenEdges:
                    seenEdges.append(edgeIDA)
                    nFaceA = self.getOppositeFace(mApiA, faceIDA, edgeIDA)
                    nFaceB = self.getOppositeFace(mApiB, faceIDB, edgeIDB)
                    self._copyVertexData(mApiA.mesh, mApiB.mesh, faceIDA, faceIDB, vtxIDA[1], vtxIDB[1])
                    self._copyVertexData(mApiA.mesh, mApiB.mesh, faceIDA, faceIDB, vtxIDA[0], vtxIDB[0])
                    if nFaceA and nFaceB:
                        queues = queues + self.walkFaceDouble(mApiA, nFaceA, vtxIDA, mApiB, nFaceB, vtxIDB)
                        cmds.progressBar(gMainProgressBar, edit=True, step=1)
                del mApiA
                del faceIDA
                del edgeIDA
                del vtxIDA
                del mApiB
                del faceIDB
                del edgeIDB
                del vtxIDB
                queues.remove(queue)

        del queues
        cmds.progressBar(gMainProgressBar, edit=True, endProgress=1)
        print('DONE! Thank mapping succesfull! Done in: %s Seconds' % (time.time() - benchmarkStart))
        print('DONE! Thank mapping succesfull! Done in: %s Minutes' % ((time.time() - benchmarkStart) / 60))
        cmds.displaySmoothness(self._meshB, du=0, dv=0, pointsWire=4, pointsShaded=1, polygonObject=1)
        cmds.refresh()