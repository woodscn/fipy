#!/usr/bin/env python

## -*-Pyth-*-
 # ########################################################################
 # FiPy - a finite volume PDE solver in Python
 # 
 # FILE: "uniformGrid3D.py"
 #
 #  Author: Jonathan Guyer <guyer@nist.gov>
 #  Author: Daniel Wheeler <daniel.wheeler@nist.gov>
 #  Author: James Warren   <jwarren@nist.gov>
 #   mail: NIST
 #    www: <http://www.ctcms.nist.gov/fipy/>
 #  
 # ========================================================================
 # This software was developed at the National Institute of Standards
 # and Technology by employees of the Federal Government in the course
 # of their official duties.  Pursuant to title 17 Section 105 of the
 # United States Code this software is not subject to copyright
 # protection and is in the public domain.  FiPy is an experimental
 # system.  NIST assumes no responsibility whatsoever for its use by
 # other parties, and makes no guarantees, expressed or implied, about
 # its quality, reliability, or any other characteristic.  We would
 # appreciate acknowledgement if the software is used.
 # 
 # This software can be redistributed and/or modified freely
 # provided that any derivative works bear some notice that they are 
 # derived from it, and any modified versions bear some notice that
 # they have been modified.
 # ========================================================================
 # 
 # ########################################################################
 ##

from fipy.tools.numerix import MA

from fipy.meshes.numMesh.grid3D import Grid3D
from fipy.tools import numerix
from fipy.tools.dimensions.physicalField import PhysicalField

from fipy.variables.cellVariable import CellVariable
from fipy.variables.faceVariable import FaceVariable
from fipy.variables.vertexVariable import _VertexVariable

class UniformGrid3D(Grid3D):
    """
    3D rectangular-prism Mesh with uniform grid spacing in each dimension.

    X axis runs from left to right.
    Y axis runs from bottom to top.
    Z axis runs from front to back.

    Numbering System:

    Vertices: Numbered in the usual way. X coordinate changes most quickly, then Y, then Z.
    
    *** arrays are arranged Z, Y, X because in numerix, the final index is the one that changes the most quickly ***

    Cells: Same numbering system as vertices.

    Faces: XY faces numbered first, then XZ faces, then YZ faces. Within each subcategory, it is numbered in the usual way.
    """
    def __init__(self, dx = 1., dy = 1., dz = 1., nx = 1, ny = 1, nz = 1, origin = [[0], [0], [0]]):
        self.dim = 3
        
        self.dx = PhysicalField(value = dx)
        scale = PhysicalField(value = 1, unit = self.dx.getUnit())
        self.dx /= scale
        
        self.nx = nx
        
        self.dy = PhysicalField(value = dy)
        if self.dy.getUnit().isDimensionless():
            self.dy = dy
        else:
            self.dy /= scale
            
        self.ny = ny
        
        self.dz = PhysicalField(value = dy)
        if self.dz.getUnit().isDimensionless():
            self.dz = dz
        else:
            self.dz /= scale
            
        self.nz = nz
        
        self.origin = PhysicalField(value = origin)
        self.origin /= scale

        self.numberOfVertices = (self.nx + 1) * (self.ny + 1) * (self.nz + 1)
        self.numberOfXYFaces = self.nx * self.ny * (self.nz + 1)
        self.numberOfXZFaces = self.nx * (self.ny + 1) * self.nz
        self.numberOfYZFaces = (self.nx + 1) * self.ny * self.nz
        self.numberOfFaces = self.numberOfXYFaces + self.numberOfXZFaces + self.numberOfYZFaces
        self.numberOfCells = self.nx * self.ny * self.nz
        
        
        self.scale = {
            'length': 1.,
            'area': 1.,
            'volume': 1.
        }

        self.setScale(value = scale)
        
    def _translate(self, vector):
        return UniformGrid3D(dx = self.dx, nx = self.nx, 
                             dy = self.dy, ny = self.ny, 
                             dz = self.dz, nz = self.nz, 
                             origin = self.origin + vector)

    def __mul__(self, factor):
        return UniformGrid3D(dx = self.dx * factor, nx = self.nx, 
                             dy = self.dy * factor, ny = self.ny, 
                             dz = self.dz * factor, nz = self.nz, 
                             origin = self.origin * factor)

    def _getConcatenableMesh(self):
        from fipy.meshes.numMesh.mesh import Mesh
        return Mesh(vertexCoords = self.getVertexCoords(), 
                    faceVertexIDs = self._createFaces(), 
                    cellFaceIDs = self._createCells())
                      
    def _concatenate(self, other, smallNumber):
        return self._getConcatenableMesh()._concatenate(other = other, smallNumber = smallNumber)
        
##     get topology methods

##         from common/mesh
        
    def _getCellFaceIDs(self):
        return CellVariable(mesh=self, value=self._createCells())
        
    def _getXYFaceIDs(self):
        ids = numerix.arange(0, self.numberOfXYFaces)
        return ids.reshape((self.nz + 1, self.ny, self.nx)).swapaxes(0,2)

    def _getXZFaceIDs(self):
        ids = numerix.arange(self.numberOfXYFaces, self.numberOfXYFaces + self.numberOfXZFaces)
        return ids.reshape((self.nz, self.ny + 1, self.nx)).swapaxes(0,2)

    def _getYZFaceIDs(self):
        ids = numerix.arange(self.numberOfXYFaces + self.numberOfXZFaces, self.numberOfFaces)
        return ids.reshape((self.nz, self.ny, self.nx + 1)).swapaxes(0,2)

    def getExteriorFaces(self):
        """
        Return only the faces that have one neighboring cell.
        """
        XYids = self._getXYFaceIDs()
        XZids = self._getXZFaceIDs()
        YZids = self._getYZFaceIDs()
        
        exteriorIDs = numerix.concatenate((numerix.ravel(XYids[...,      0].swapaxes(0,1)), 
                                           numerix.ravel(XYids[...,     -1].swapaxes(0,1)),
                                           numerix.ravel(XZids[...,  0,...]), 
                                           numerix.ravel(XZids[..., -1,...]),
                                           numerix.ravel(YZids[ 0,     ...]), 
                                           numerix.ravel(YZids[-1,     ...])))
                                                     
        from fipy.variables.faceVariable import FaceVariable
        exteriorFaces = FaceVariable(mesh=self, value=False)
        exteriorFaces[exteriorIDs] = True
        return exteriorFaces
        
    def getInteriorFaces(self):
        """
        Return only the faces that have two neighboring cells
        """
        XYids = self._getXYFaceIDs()
        XZids = self._getXZFaceIDs()
        YZids = self._getYZFaceIDs()
        
        interiorIDs = numerix.concatenate((numerix.ravel(XYids[ ...     ,1:-1]),
                                           numerix.ravel(XZids[ ...,1:-1, ...]),
                                           numerix.ravel(YZids[1:-1,      ...].swapaxes(0,1))))
                                                     
        from fipy.variables.faceVariable import FaceVariable
        interiorFaces = FaceVariable(mesh=self, value=False)
        interiorFaces[interiorIDs] = True
        return interiorFaces

    def _getCellFaceOrientations(self):
        tmp = numerix.take(self.getFaceCellIDs()[0], self._getCellFaceIDs(), axis=-1)
        return (tmp == MA.indices(tmp.shape)[-1]) * 2 - 1

    def _getAdjacentCellIDs(self):
        faceCellIDs = self.getFaceCellIDs()
        mask = faceCellIDs.getMask()
        faceCellIDs = faceCellIDs.filled()
        return ((mask[0] * faceCellIDs[1] + ~mask[0] * faceCellIDs[0]),
                (mask[1] * faceCellIDs[0] + ~mask[1] * faceCellIDs[1]))

    def _getCellToCellIDs(self):
        ids = MA.zeros((6, self.nx, self.ny, self.nz), 'l')
        indices = numerix.indices((self.nx, self.ny, self.nz))
        ids[0] = indices[0] + (indices[1] + indices[2] * self.ny) * self.nx - 1
        ids[1] = indices[0] + (indices[1] + indices[2] * self.ny) * self.nx + 1
        ids[2] = indices[0] + (indices[1] + indices[2] * self.ny - self.nz) * self.nx
        ids[3] = indices[0] + (indices[1] + indices[2] * self.ny + self.nz) * self.nx
        ids[4] = indices[0] + (indices[1] + (indices[2] - 1) * self.ny) * self.nx
        ids[5] = indices[0] + (indices[1] + (indices[2] + 1) * self.ny) * self.nx
        
        ids[0, 0,    ...] = MA.masked
        ids[1,-1,    ...] = MA.masked
        ids[2,..., 0,...] = MA.masked
        ids[3,...,-1,...] = MA.masked
        ids[4,...,     0] = MA.masked
        ids[5,...,    -1] = MA.masked

        return CellVariable(mesh=self, 
                            value=MA.reshape(ids.swapaxes(1,3), (6, self.numberOfCells)))
        
    def _getCellToCellIDsFilled(self):
        N = self.getNumberOfCells()
        M = self._getMaxFacesPerCell()
        cellIDs = CellVariable(mesh=self, value=numerix.repeat(numerix.arange(N)[numerix.newaxis, ...], M, axis=0))
        cellToCellIDs = self._getCellToCellIDs()
        mask = cellToCellIDs.getMask()
        return mask * cellIDs + ~mask * cellToCellIDs.filled()
        
    def _getMaxFacesPerCell(self):
        return 6
        
##         from numMesh/mesh

    def getVertexCoords(self):
        return _VertexVariable(mesh=self,
                               value=self._createVertices() + self.origin,
                               _bootstrap=True)
                               
    def getFaceCellIDs(self):
        XYids = MA.zeros((2, self.nx, self.ny, self.nz + 1), 'l')
        indices = numerix.indices((self.nx, self.ny, self.nz + 1))
        XYids[1] = indices[0] + (indices[1] + indices[2] * self.ny) * self.nx
        XYids[0] = XYids[1] - self.nx * self.ny
        XYids[0,..., 0] = XYids[1,..., 0]
        XYids[1,..., 0] = MA.masked
        XYids[1,...,-1] = MA.masked
        
        XZids = MA.zeros((2, self.nx, self.ny + 1, self.nz), 'l')
        indices = numerix.indices((self.nx, self.ny + 1, self.nz))
        XZids[1] = indices[0] + (indices[1] + indices[2] * self.ny) * self.nx
        XZids[0] = XZids[1] - self.nx
        XZids[0,..., 0,...] = XZids[1,..., 0,...]
        XZids[1,..., 0,...] = MA.masked
        XZids[1,...,-1,...] = MA.masked

        YZids = MA.zeros((2, self.nx + 1, self.ny, self.nz), 'l')
        indices = numerix.indices((self.nx + 1, self.ny, self.nz))
        YZids[1] = indices[0] + (indices[1] + indices[2] * self.ny) * self.nx
        YZids[0] = YZids[1] - 1
        YZids[0, 0] = YZids[1, 0]
        YZids[1, 0] = MA.masked
        YZids[1,-1] = MA.masked

        return FaceVariable(mesh=self,
                            value=MA.concatenate((XYids.swapaxes(1,3).reshape((2, self.numberOfXYFaces)), 
                                                  XZids.swapaxes(1,3).reshape((2, self.numberOfXZFaces)), 
                                                  YZids.swapaxes(1,3).reshape((2, self.numberOfYZFaces))), axis=1))

##     get geometry methods
        
##         from common/mesh
        
    def _getFaceAreas(self):
        return FaceVariable(mesh=self, 
                            value=numerix.concatenate((numerix.repeat((self.dx * self.dy,), self.numberOfXYFaces),
                                                       numerix.repeat((self.dx * self.dz,), self.numberOfXZFaces),
                                                       numerix.repeat((self.dy * self.dz,), self.numberOfYZFaces))))

    def _getFaceNormals(self):
        XYnor = numerix.zeros((3, self.nx, self.ny, self.nz + 1))
        XYnor[0,      ...] =  1
        XYnor[0,  ...,  0] = -1

        XZnor = numerix.zeros((3, self.nx, self.ny + 1, self.nz))
        XZnor[1,      ...] =  1
        XZnor[1,...,0,...] = -1

        YZnor = numerix.zeros((3, self.nx + 1, self.ny, self.nz))
        YZnor[2,      ...] =  1
        YZnor[2, 0,   ...] = -1
        
        return FaceVariable(mesh=self,
                            value=numerix.concatenate((numerix.reshape(XYnor[::-1].swapaxes(1,3), (3, self.numberOfXYFaces)), 
                                                       numerix.reshape(XZnor[::-1].swapaxes(1,3), (3, self.numberOfXZFaces)), 
                                                       numerix.reshape(YZnor[::-1].swapaxes(1,3), (3, self.numberOfYZFaces))), axis=1))

    def _getFaceCellToCellNormals(self):
        return self._getFaceNormals()
        
    def getCellVolumes(self):
        return CellVariable(mesh=self, value=self.dx * self.dy * self.dz)

    def getCellCenters(self):
        centers = numerix.zeros((3, self.nx, self.ny, self.nz), 'd')
        indices = numerix.indices((self.nx, self.ny, self.nz))
        centers[0] = (indices[0] + 0.5) * self.dx
        centers[1] = (indices[1] + 0.5) * self.dy
        centers[2] = (indices[2] + 0.5) * self.dz
        return CellVariable(mesh=self,
                            value=numerix.reshape(centers.swapaxes(1,3), (3, self.numberOfCells)) + self.origin)

    def _getCellDistances(self):
        XYdis = numerix.zeros((self.nz + 1, self.ny, self.nx),'d')
        XYdis[:] = self.dz
        XYdis[ 0,...] = self.dz / 2.
        XYdis[-1,...] = self.dz / 2.
        
        XZdis = numerix.zeros((self.nz, self.ny + 1, self.nx),'d')
        XZdis[:] = self.dy
        XZdis[..., 0,...] = self.dy / 2.
        XZdis[...,-1,...] = self.dy / 2.

        YZdis = numerix.zeros((self.nz, self.ny, self.nx + 1),'d')
        YZdis[:] = self.dx
        YZdis[..., 0] = self.dx / 2.
        YZdis[...,-1] = self.dx / 2.

        return FaceVariable(mesh=self, 
                            value=numerix.concatenate((numerix.ravel(XYdis),
                                                       numerix.ravel(XZdis),
                                                       numerix.ravel(YZdis))))

    def _getFaceToCellDistanceRatio(self):
        XYdis = numerix.zeros((self.nx, self.ny, self.nz + 1),'d')
        XYdis[:] = 0.5
        XYdis[..., 0] = 1
        XYdis[...,-1] = 1
        
        XZdis = numerix.zeros((self.nx, self.ny + 1, self.nz),'d')
        XZdis[:] = 0.5
        XZdis[..., 0,...] = 1
        XZdis[...,-1,...] = 1
        
        YZdis = numerix.zeros((self.nx + 1, self.ny, self.nz),'d')
        YZdis[:] = 0.5
        YZdis[ 0,...] = 1
        YZdis[-1,...] = 1
        
        return FaceVariable(mesh=self, 
                            value=numerix.concatenate((numerix.ravel(XYdis.swapaxes(0,2)),
                                                       numerix.ravel(XZdis.swapaxes(0,2)),
                                                       numerix.ravel(YZdis.swapaxes(0,2))), axis=1))
                                    
    def _getOrientedAreaProjections(self):
        return self._getAreaProjections()

    def _getAreaProjections(self):
        return self._getFaceNormals() * self._getFaceAreas()

    def _getOrientedFaceNormals(self):
        return self._getFaceNormals()

    def _getFaceTangents1(self):
        XYtan = numerix.zeros((3, self.nx, self.ny, self.nz + 1))
        XYtan[2,      ...] =  1
        
        XZtan = numerix.zeros((3, self.nx, self.ny + 1, self.nz))
        XZtan[2,      ...] =  1
        
        YZtan = numerix.zeros((3, self.nx + 1, self.ny, self.nz))
        YZtan[1,      ...] =  1
        
        return FaceVariable(mesh=self, 
                            value=numerix.concatenate((numerix.reshape(XYtan[::-1].swapaxes(1,3), (3, self.numberOfXYFaces)), 
                                                       numerix.reshape(XZtan[::-1].swapaxes(1,3), (3, self.numberOfXZFaces)), 
                                                       numerix.reshape(YZtan[::-1].swapaxes(1,3), (3, self.numberOfYZFaces))), axis=1))
        
    def _getFaceTangents2(self):
        XYtan = numerix.zeros((3, self.nx, self.ny, self.nz + 1))
        XYtan[1,      ...] =  1
        
        XZtan = numerix.zeros((3, self.nx, self.ny + 1, self.nz))
        XZtan[0,      ...] =  1
        
        YZtan = numerix.zeros((3, self.nx + 1, self.ny, self.nz))
        YZtan[0,      ...] =  1
        
        return FaceVariable(mesh=self, 
                            value=numerix.concatenate((numerix.reshape(XYtan[::-1].swapaxes(1,3), (3, self.numberOfXYFaces)), 
                                                       numerix.reshape(XZtan[::-1].swapaxes(1,3), (3, self.numberOfXZFaces)), 
                                                       numerix.reshape(YZtan[::-1].swapaxes(1,3), (3, self.numberOfYZFaces))), axis=1))
        
    def _getFaceAspectRatios(self):
        return self._getFaceAreas() / self._getCellDistances()
    
    def _getCellToCellDistances(self):
        distances = numerix.zeros((6, self.nx, self.ny, self.nz), 'd')
        distances[0] = self.dx
        distances[1] = self.dx
        distances[2] = self.dy
        distances[3] = self.dy
        distances[4] = self.dz
        distances[5] = self.dz
        
        distances[0,  0,...    ] = self.dx / 2.
        distances[1, -1,...    ] = self.dx / 2.
        distances[2,...,  0,...] = self.dy / 2.
        distances[3,..., -1,...] = self.dy / 2.
        distances[4,...,      0] = self.dz / 2.
        distances[5,...,     -1] = self.dz / 2.

        return CellVariable(mesh=self, 
                            value=numerix.reshape(distances.swapaxes(1,3), (self.numberOfCells, 6)),
                            elementshape=(6,))
        
    def _getCellNormals(self):
        normals = CellVariable(mesh=self, value=0., elementshape=(3,6))
        normals[...,0,...] = [[-1], [ 0], [ 0]]
        normals[...,1,...] = [[ 1], [ 0], [ 0]]
        normals[...,2,...] = [[ 0], [-1], [ 0]]
        normals[...,3,...] = [[ 0], [ 1], [ 0]]
        normals[...,4,...] = [[ 0], [ 0], [-1]]
        normals[...,5,...] = [[ 0], [ 0], [ 1]]

        return normals
        
    def _getCellAreas(self):
        areas = CellVariable(mesh=self, value=0., elementshape=(6,))
        areas[0] = self.dy * self.dz
        areas[1] = self.dy * self.dz
        areas[2] = self.dx * self.dz
        areas[3] = self.dx * self.dz
        areas[4] = self.dx * self.dy
        areas[5] = self.dx * self.dy
        return areas

    def _getCellAreaProjections(self):
        return self._getCellAreas() * self._getCellNormals()

##         from numMesh/mesh

    def getFaceCenters(self):
        XYcen = numerix.zeros((3, self.nx, self.ny, self.nz + 1), 'd')
        indices = numerix.indices((self.nx, self.ny, self.nz + 1))
        XYcen[0] = (indices[0] + 0.5) * self.dx
        XYcen[1] = (indices[1] + 0.5) * self.dy
        XYcen[2] = indices[2] * self.dz

        XZcen = numerix.zeros((3, self.nx, self.ny + 1, self.nz), 'd')
        indices = numerix.indices((self.nx, self.ny + 1, self.nz))
        XZcen[0] = (indices[0] + 0.5) * self.dx
        XZcen[1] = indices[1] * self.dy
        XZcen[2] = (indices[2] + 0.5) * self.dz
        
        YZcen = numerix.zeros((3, self.nx + 1, self.ny, self.nz), 'd')
        indices = numerix.indices((self.nx + 1, self.ny, self.nz))
        YZcen[0] = indices[0] * self.dx
        YZcen[1] = (indices[1] + 0.5) * self.dy
        YZcen[2] = (indices[2] + 0.5) * self.dz

        return FaceVariable(mesh=self,
                            value=numerix.concatenate((numerix.reshape(XYcen.swapaxes(1,3), (3, self.numberOfXYFaces)), 
                                                       numerix.reshape(XZcen.swapaxes(1,3), (3, self.numberOfXZFaces)),
                                                       numerix.reshape(YZcen.swapaxes(1,3), (3, self.numberOfYZFaces))), axis=1),
                            rank=1)
                                    
    def _getCellVertexIDs(self):
        ids = numerix.zeros((8, self.nx, self.ny, self.nz))
        indices = numerix.indices((self.nx, self.ny, self.nz))
        ids[1] = indices[0] + (indices[1] + (indices[2] + 1) * (self.ny + 1) + 1) * (self.nx + 1)
        ids[0] = ids[1] + 1
        ids[3] = indices[0] + (indices[1] + (indices[2] + 1) * (self.ny + 1)) * (self.nx + 1)
        ids[2] = ids[3] + 1
        ids[5] = indices[0] + (indices[1] + indices[2] * (self.ny + 1) + 1) * (self.nx + 1)
        ids[4] = ids[5] + 1
        ids[7] = indices[0] + (indices[1] + indices[2] * (self.ny + 1)) * (self.nx + 1)
        ids[6] = ids[7] + 1
        
        return CellVariable(mesh=self, 
                            value=numerix.reshape(ids.swapaxes(1,3), (8, self.numberOfCells)),
                            elementshape=(8,))
        
    def _getFaceVertexIDs(self):
        return FaceVariable(mesh=self,
                            value=self._createFaces())
                                    
    def _getOrderedCellVertexIDs(self):
        """Correct ordering for VTK_VOXEL"""
        return self._getCellVertexIDs()     
        
##     scaling
    
    def _calcScaledGeometry(self):
        pass
    
    def _getNearestCellID(self, points):
        x0, y0, z0 = self.getCellCenters()[...,0]        
        xi, yi, zi = points
        nx, ny, nz = self.getShape()
        dx, dy, dz = self.dx, self.dy, self.dz
        
        i = numerix.array(numerix.rint(((xi - x0) / dx)), 'l')
        i[i < 0] = 0
        i[i > nx - 1] = nx - 1

        j = numerix.array(numerix.rint(((yi - y0) / dy)), 'l')
        j[j < 0] = 0
        j[j > ny - 1]  = ny - 1

        k = numerix.array(numerix.rint(((zi - z0) / dz)), 'l')
        k[k < 0] = 0
        k[k > nz - 1]  = nz - 1
        
        return k * ny * nx + j * nx + i
        
    def _test(self):
        """
        These tests are not useful as documentation, but are here to ensure
        everything works as expected.
        
            >>> dx = 0.5
            >>> dy = 2.
            >>> dz = 4.
            >>> nx = 3
            >>> ny = 2
            >>> nz = 1
            
            >>> mesh = UniformGrid3D(nx=nx, ny=ny, nz=nz, dx=dx, dy=dy, dz=dz)
            
            >>> print mesh._getXYFaceIDs()
            [[[ 0  6]
              [ 3  9]]
            <BLANKLINE>
             [[ 1  7]
              [ 4 10]]
            <BLANKLINE>
             [[ 2  8]
              [ 5 11]]]
              
            >>> print mesh._getXZFaceIDs()
            [[[12]
              [15]
              [18]]
            <BLANKLINE>
             [[13]
              [16]
              [19]]
            <BLANKLINE>
             [[14]
              [17]
              [20]]]
              
            >>> print mesh._getYZFaceIDs()
            [[[21]
              [25]]
            <BLANKLINE>
             [[22]
              [26]]
            <BLANKLINE>
             [[23]
              [27]]
            <BLANKLINE>
             [[24]
              [28]]]

            >>> print mesh._getAdjacentCellIDs()[0]
            [0 1 2 3 4 5 0 1 2 3 4 5 0 1 2 0 1 2 3 4 5 0 0 1 2 3 3 4 5]
            >>> print mesh._getAdjacentCellIDs()[1]
            [0 1 2 3 4 5 0 1 2 3 4 5 0 1 2 3 4 5 3 4 5 0 1 2 2 3 4 5 5]

            >>> vertices = numerix.array(((0., 1., 2., 3., 0., 1., 2., 3., 0., 1., 2., 3., 0., 1., 2., 3., 0., 1., 2., 3., 0., 1., 2., 3.),
            ...                           (0., 0., 0., 0., 1., 1., 1., 1., 2., 2., 2., 2., 0., 0., 0., 0., 1., 1., 1., 1., 2., 2., 2., 2.),
            ...                           (0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.)))
            >>> vertices *= numerix.array([[dx], [dy], [dz]])
            
            >>> numerix.allequal(vertices, mesh._createVertices())
            1
        
            >>> faces = numerix.array((( 0,  1,  2,  4,  5,  6, 12, 13, 14, 16, 17, 18,  0,  1,  2,  4,  5,  6,  8,  9, 10,  0,  1,  2,  3,  4,  5,  6,  7),
            ...                        ( 1,  2,  3,  5,  6,  7, 13, 14, 15, 17, 18, 19,  1,  2,  3,  5,  6,  7,  9, 10, 11,  4,  5,  6,  7,  8,  9, 10, 11),
            ...                        ( 5,  6,  7,  9, 10, 11, 17, 18, 19, 21, 22, 23, 13, 14, 15, 17, 18, 19, 21, 22, 23, 16, 17, 18, 19, 20, 21, 22, 23),
            ...                        ( 4,  5,  6,  8,  9, 10, 16, 17, 18, 20, 21, 22, 12, 13, 14, 16, 17, 18, 20, 21, 22, 12, 13, 14, 15, 16, 17, 18, 19))) 
            >>> numerix.allequal(faces, mesh._createFaces())
            1

            >>> cells = numerix.array(((21, 22, 23, 25, 26, 27),
            ...                        (22, 23, 24, 26, 27, 28),
            ...                        (12, 13, 14, 15, 16, 17),
            ...                        (15, 16, 17, 18, 19, 20),
            ...                        ( 0,  1,  2,  3,  4,  5),
            ...                        ( 6,  7,  8,  9, 10, 11)))
            >>> numerix.allequal(cells, mesh._createCells())
            1

            >>> externalFaces = numerix.array((0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 18, 19, 20, 21, 24, 25, 28))
            >>> print numerix.allequal(externalFaces, 
            ...                        numerix.nonzero(mesh.getExteriorFaces()))
            1

            >>> internalFaces = numerix.array((15, 16, 17, 22, 23, 26, 27))
            >>> print numerix.allequal(internalFaces, 
            ...                        numerix.nonzero(mesh.getInteriorFaces()))
            1

            >>> from fipy.tools.numerix import MA
            >>> faceCellIds = MA.masked_values((( 0, 1, 2, 3, 4, 5, 0, 1, 2, 3, 4, 5, 0, 1, 2, 0, 1, 2, 3, 4, 5, 0, 0, 1, 2, 3, 3, 4, 5),
            ...                                 (-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1, 3, 4, 5,-1,-1,-1,-1, 1, 2,-1,-1, 4, 5,-1)), -1) 
            >>> print numerix.allequal(faceCellIds, mesh.getFaceCellIDs())
            1
            
            >>> xy = dx * dy
            >>> xz = dx * dz
            >>> yz = dy * dz
            >>> faceAreas = numerix.array((xy, xy, xy, xy, xy, xy, xy, xy, xy, xy, xy, xy,
            ...                            xz, xz, xz, xz, xz, xz, xz, xz, xz,
            ...                            yz, yz, yz, yz, yz, yz, yz, yz))
            >>> print numerix.allclose(faceAreas, mesh._getFaceAreas(), 
            ...                        atol = 1e-10, rtol = 1e-10)
            1
            
            >>> faceCoords = numerix.take(vertices, faces, axis=1)
            >>> faceCenters = (faceCoords[...,0,:] + faceCoords[...,1,:] + faceCoords[...,2,:] + faceCoords[...,3,:]) / 4.
            >>> print numerix.allclose(faceCenters, mesh.getFaceCenters(), 
            ...                        atol = 1e-10, rtol = 1e-10)
            1

            >>> faceNormals = numerix.array((( 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,-1, 1, 1, 1,-1, 1, 1, 1),
            ...                              ( 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,-1,-1,-1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0),
            ...                              (-1,-1,-1,-1,-1,-1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)))
            >>> print numerix.allclose(faceNormals, mesh._getFaceNormals(), 
            ...                        atol = 1e-10, rtol = 1e-10)
            1

            >>> cellToFaceOrientations = numerix.array((( 1,-1,-1, 1,-1,-1),
            ...                                         ( 1, 1, 1, 1, 1, 1),
            ...                                         ( 1, 1, 1,-1,-1,-1),
            ...                                         ( 1, 1, 1, 1, 1, 1),
            ...                                         ( 1, 1, 1, 1, 1, 1),
            ...                                         ( 1, 1, 1, 1, 1, 1)))
            >>> print numerix.allequal(cellToFaceOrientations, 
            ...                        mesh._getCellFaceOrientations())
            1
                                             
            >>> cellVolumes = numerix.array((dx*dy*dz, dx*dy*dz, dx*dy*dz, dx*dy*dz, dx*dy*dz, dx*dy*dz))
            >>> print numerix.allclose(cellVolumes, mesh.getCellVolumes(), 
            ...                        atol = 1e-10, rtol = 1e-10)
            1

            >>> cellCenters = numerix.array(((   dx/2., 3.*dx/2., 5.*dx/2.,   dx/2., 3.*dx/2., 5.*dx/2.),
            ...                              (   dy/2.,    dy/2.,    dy/2.,3.*dy/2., 3.*dy/2., 3.*dy/2.),
            ...                              (   dz/2.,    dz/2.,    dz/2.,   dz/2.,    dz/2.,    dz/2.)))
            >>> print numerix.allclose(cellCenters, mesh.getCellCenters(), 
            ...                        atol = 1e-10, rtol = 1e-10)
            1
                                              
            >>> cellDistances = numerix.array((dz/2, dz/2, dz/2, dz/2, dz/2, dz/2, dz/2, dz/2, dz/2, dz/2, dz/2, dz/2,
            ...                                dy/2, dy/2, dy/2, dy, dy, dy, dy/2, dy/2, dy/2,
            ...                                dx/2, dx, dx, dx/2, dx/2, dx, dx, dx/2))
            >>> print numerix.allclose(cellDistances, mesh._getCellDistances(), 
            ...                        atol = 1e-10, rtol = 1e-10)
            1
            
            >>> faceToCellDistances = MA.masked_values(((dz/2, dz/2, dz/2, dz/2, dz/2, dz/2, dz/2, dz/2, dz/2, dz/2, dz/2, dz/2, dy/2, dy/2, dy/2, dy/2, dy/2, dy/2, dy/2, dy/2, dy/2, dx/2, dx/2, dx/2, dx/2, dx/2, dx/2, dx/2, dx/2),
            ...                                         (  -1,   -1,   -1,   -1,   -1,   -1,   -1,   -1,   -1,   -1,   -1,   -1,   -1,   -1,   -1, dy/2, dy/2, dy/2,   -1,   -1,   -1,   -1, dx/2, dx/2,   -1,   -1, dx/2, dx/2,   -1)), -1)
            >>> faceToCellDistanceRatios = faceToCellDistances[0] / cellDistances
            >>> print numerix.allclose(faceToCellDistanceRatios, 
            ...                        mesh._getFaceToCellDistanceRatio(), 
            ...                        atol = 1e-10, rtol = 1e-10)
            1

            >>> areaProjections = faceNormals * faceAreas
            >>> print numerix.allclose(areaProjections, 
            ...                        mesh._getAreaProjections(), 
            ...                        atol = 1e-10, rtol = 1e-10)
            1

            >>> tangents1 = numerix.array(((1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0),
            ...                            (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1),
            ...                            (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)))
            >>> print numerix.allclose(tangents1, mesh._getFaceTangents1(), 
            ...                        atol = 1e-10, rtol = 1e-10)
            1

            >>> tangents2 = numerix.array(((0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
            ...                            (1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
            ...                            (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1)))
            >>> print numerix.allclose(tangents2, mesh._getFaceTangents2(), 
            ...                        atol = 1e-10, rtol = 1e-10)
            1

            >>> print mesh._getCellToCellIDs()
            [[-- 0 1 -- 3 4]
             [1 2 -- 4 5 --]
             [-- -- -- 0 1 2]
             [3 4 5 -- -- --]
             [-- -- -- -- -- --]
             [-- -- -- -- -- --]]

            >>> print mesh._getCellToCellIDsFilled()
            [[0 0 1 3 3 4]
             [1 2 2 4 5 5]
             [0 1 2 0 1 2]
             [3 4 5 3 4 5]
             [0 1 2 3 4 5]
             [0 1 2 3 4 5]]
              
            >>> cellToCellDistances = numerix.take(cellDistances, cells, axis=-1)
            >>> print numerix.allclose(cellToCellDistances, 
            ...                        mesh._getCellToCellDistances(), 
            ...                        atol = 1e-10, rtol = 1e-10)
            1

            >>> cellNormals = numerix.array((((-1, -1, -1, -1, -1, -1),
            ...                               ( 1,  1,  1,  1,  1,  1),
            ...                               ( 0,  0,  0,  0,  0,  0),
            ...                               ( 0,  0,  0,  0,  0,  0),
            ...                               ( 0,  0,  0,  0,  0,  0),
            ...                               ( 0,  0,  0,  0,  0,  0)),
            ...                              (( 0,  0,  0,  0,  0,  0),
            ...                               ( 0,  0,  0,  0,  0,  0),
            ...                               (-1, -1, -1, -1, -1, -1),
            ...                               ( 1,  1,  1,  1,  1,  1),
            ...                               ( 0,  0,  0,  0,  0,  0),
            ...                               ( 0,  0,  0,  0,  0,  0)),
            ...                              (( 0,  0,  0,  0,  0,  0),
            ...                               ( 0,  0,  0,  0,  0,  0),
            ...                               ( 0,  0,  0,  0,  0,  0),
            ...                               ( 0,  0,  0,  0,  0,  0),
            ...                               (-1, -1, -1, -1, -1, -1),
            ...                               ( 1,  1,  1,  1,  1,  1))))
            >>> print numerix.allclose(cellNormals, mesh._getCellNormals(), 
            ...                        atol = 1e-10, rtol = 1e-10)
            1

            >>> cellAreaProjections = numerix.array((((-yz,-yz,-yz,-yz,-yz,-yz),
            ...                                       ( yz, yz, yz, yz, yz, yz),
            ...                                       (  0,  0,  0,  0,  0,  0),
            ...                                       (  0,  0,  0,  0,  0,  0),
            ...                                       (  0,  0,  0,  0,  0,  0),
            ...                                       (  0,  0,  0,  0,  0,  0)),
            ...                                      ((  0,  0,  0,  0,  0,  0),
            ...                                       (  0,  0,  0,  0,  0,  0),
            ...                                       (-xz,-xz,-xz,-xz,-xz,-xz),
            ...                                       ( xz, xz, xz, xz, xz, xz),
            ...                                       (  0,  0,  0,  0,  0,  0),
            ...                                       (  0,  0,  0,  0,  0,  0)),
            ...                                      ((  0,  0,  0,  0,  0,  0),
            ...                                       (  0,  0,  0,  0,  0,  0),
            ...                                       (  0,  0,  0,  0,  0,  0),
            ...                                       (  0,  0,  0,  0,  0,  0),
            ...                                       (-xy,-xy,-xy,-xy,-xy,-xy),
            ...                                       ( xy, xy, xy, xy, xy, xy))))
            >>> print numerix.allclose(cellAreaProjections, 
            ...                        mesh._getCellAreaProjections(), 
            ...                        atol = 1e-10, rtol = 1e-10)
            1

            >>> cellVertexIDs = numerix.array((17, 16, 13, 12, 5, 4, 1, 0))
            >>> cellVertexIDs = numerix.array((cellVertexIDs, cellVertexIDs + 1, cellVertexIDs + 2,
            ...                                cellVertexIDs + 4, cellVertexIDs + 5, cellVertexIDs + 6))
            >>> cellVertexIDs = cellVertexIDs.swapaxes(0,1)
            >>> print numerix.allclose(mesh._getCellVertexIDs(), cellVertexIDs)
            1


            >>> from fipy.tools import dump            
            >>> (f, filename) = dump.write(mesh, extension = '.gz')            
            >>> unpickledMesh = dump.read(filename, f)

            >>> print numerix.allequal(mesh.getCellCenters(), 
            ...                        unpickledMesh.getCellCenters())
            1
            
            # Bug #130 & #135 are because we only checked a mesh with nz of 1
            
            >>> nx = 1
            >>> ny = 2
            >>> nz = 3
            
            >>> mesh = UniformGrid3D(nx=nx, ny=ny, nz=nz, dx=dx, dy=dy, dz=dz)

            >>> cellVertexIDs = numerix.array((9, 8, 7, 6, 3, 2, 1, 0))
            >>> cellVertexIDs = numerix.array((cellVertexIDs, cellVertexIDs + 2, cellVertexIDs + 6,
            ...                                cellVertexIDs + 8, cellVertexIDs + 12, cellVertexIDs + 14))
            >>> cellVertexIDs = cellVertexIDs.swapaxes(0,1)
            >>> print numerix.allclose(mesh._getCellVertexIDs(), cellVertexIDs)
            1
            
            >>> nx = 3
            >>> ny = 1
            >>> nz = 2
            
            >>> mesh = UniformGrid3D(nx=nx, ny=ny, nz=nz, dx=dx, dy=dy, dz=dz)

            >>> cellVertexIDs = numerix.array((13, 12, 9, 8, 5, 4, 1, 0))
            >>> cellVertexIDs = numerix.array((cellVertexIDs, cellVertexIDs + 1, cellVertexIDs + 2,
            ...                                cellVertexIDs + 8, cellVertexIDs + 9, cellVertexIDs + 10))
            >>> cellVertexIDs = cellVertexIDs.swapaxes(0,1)
            >>> print numerix.allclose(mesh._getCellVertexIDs(), cellVertexIDs)
            1

        """

def _test():
    import doctest
    return doctest.testmod()

if __name__ == "__main__":
    _test()
