#!/usr/bin/env python

## -*-Pyth-*-
 # ###################################################################
 #  FiPy - Python-based finite volume PDE solver
 # 
 #  FILE: "addOverFacesVariable.py"
 #                                    created: 4/30/04 {10:39:23 AM} 
 #                                last update: 1/3/07 {3:26:40 PM}
 #  Author: Jonathan Guyer <guyer@nist.gov>
 #  Author: Daniel Wheeler <daniel.wheeler@nist.gov>
 #  Author: James Warren   <jwarren@nist.gov>
 #    mail: NIST
 #     www: http://www.ctcms.nist.gov/fipy/
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
 #  Description: 
 # 
 #  History
 # 
 #  modified   by  rev reason
 #  ---------- --- --- -----------
 #  2004- 4-30 JEG 1.0 original
 # ###################################################################
 ##

from fipy.tools import numerix

from fipy.tools import numerix
import fipy.tools.inline.inline as inline
from fipy.variables.cellVariable import CellVariable

class _AddOverFacesVariable(CellVariable):
    def __init__(self, faceVariable, mesh = None):
        if not mesh:
            mesh = faceVariable.getMesh()

        CellVariable.__init__(self, mesh, hasOld = 0)
    
        self.faceVariable = self._requires(faceVariable)

    def _calcValuePy(self):
        ids = self.mesh._getCellFaceIDs()
        
        contributions = numerix.take(self.faceVariable, ids.flat)

        NCells = self.mesh.getNumberOfCells()

        contributions = numerix.reshape(contributions,(NCells,-1))
        
        orientations = numerix.reshape(self.mesh._getCellFaceOrientations(),(NCells,-1))

##         orientations = Numeric.array(orientations)
        
        return numerix.sum(contributions * orientations,1) / self.mesh.getCellVolumes()
        
    def _calcValueIn(self):

        NCells = self.mesh.getNumberOfCells()
        ids = self.mesh._getCellFaceIDs()

        val = self._getArray().copy()
        
        inline._runInline("""
        int i;
        
        for(i = 0; i < numberOfCells; i++)
          {
          int j;
          value(i) = 0.;
          for(j = 0; j < numberOfCellFaces; j++)
            {
              value(i) += orientations(i,j) * faceVariable(ids(i,j));
            }
            value(i) = value(i) / cellVolume(i);
          }
        """,
            numberOfCellFaces = self.mesh._getMaxFacesPerCell(),
            numberOfCells = NCells,
            faceVariable = self.faceVariable.getNumericValue(),
            ids = numerix.array(ids),
            value = val,
            orientations = numerix.array(self.mesh._getCellFaceOrientations()),
            cellVolume = numerix.array(self.mesh.getCellVolumes()))
            
        return self._makeValue(value = val)
##         return self._makeValue(value = val, unit = self.getUnit())

    def _calcValue(self):

        return inline._optionalInline(self._calcValueIn, self._calcValuePy)



    


