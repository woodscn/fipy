#!/usr/bin/env python

## -*-Pyth-*-
 # ###################################################################
 #  PFM - Python-based phase field solver
 # 
 #  FILE: "poissonEquation.py"
 #                                    created: 11/12/03 {10:39:23 AM} 
 #                                last update: 1/16/04 {8:57:33 AM} 
 #  Author: Jonathan Guyer
 #  E-mail: guyer@nist.gov
 #  Author: Daniel Wheeler
 #  E-mail: daniel.wheeler@nist.gov
 #    mail: NIST
 #     www: http://ctcms.nist.gov
 #  
 # ========================================================================
 # This software was developed at the National Institute of Standards
 # and Technology by employees of the Federal Government in the course
 # of their official duties.  Pursuant to title 17 Section 105 of the
 # United States Code this software is not subject to copyright
 # protection and is in the public domain.  PFM is an experimental
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
 #  2003-11-12 JEG 1.0 original
 # ###################################################################
 ##


import Numeric

from equations.matrixEquation import MatrixEquation
from terms.transientTerm import TransientTerm
from substitutionalSumVariable import SubstitutionalSumVariable
from terms.implicitDiffusionTerm import ImplicitDiffusionTerm
from terms.scSourceTerm import ScSourceTerm
from terms.spSourceTerm import SpSourceTerm

from tools.dimensions import physicalField

class PoissonEquation(MatrixEquation):
    def __init__(self,
                 potential,
		 parameters,
		 fields = {},
                 solver='default_solver',
		 solutionTolerance = 1e-10,
                 boundaryConditions=()):
		     
        mesh = potential.getMesh()
	
	dielectric = physicalField.Scale(parameters['dielectric'], "eps0") 
	dielectric *= physicalField.PhysicalField(value = "eps0 / (Faraday**2 * LENGTH**2 / (ENERGY * MOLARVOLUME))")
	
	diffusionTerm = ImplicitDiffusionTerm(
	    diffCoeff = dielectric,
	    mesh = mesh,
	    boundaryConditions = boundaryConditions)
	    
	fields['charge'] = fields['solvent'].getValence()
	for component in list(fields['interstitials']) + list(fields['substitutionals']):
	    fields['charge'] = fields['charge'] + component * component.getValence() #.getOld()
	    
## 	charge = charge * "1 Faraday/MOLARVOLUME"
	
	self.scTerm = ScSourceTerm(
	    sourceCoeff = fields['charge'],
	    mesh = mesh)
	    
	terms = (
	    diffusionTerm,
	    self.scTerm
            )
	    
	MatrixEquation.__init__(
            self,
            var = potential,
            terms = terms,
            solver = solver,
            solutionTolerance = solutionTolerance)

