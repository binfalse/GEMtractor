# This file is part of the GEMtractor
# Copyright (C) 2019 Martin Scharm <https://binfalse.de>
# 
# The GEMtractor is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# The GEMtractor is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

class InvalidBiggId (Exception):
  """
  signals that the user supplied an invalid bigg id
  """
  pass
class InvalidBiomodelsId (Exception):
  """
  signals that the user supplied an invalid biomodels id
  """
  pass
class UnableToRetrieveBiomodel (Exception):
  """
  signals that there was an error retrieving a model from biomodles
  """
  pass
class BreakLoops (Exception):
  """
  just to skip multiple loops...
  """
  pass
class NotYetImplemented (Exception):
  """
  this is not implemented yet..
  """
  pass
class InvalidGeneExpression (Exception):
  """
  signals that the model uses a gene expression that the GEMtractor doesn't understand
  """
  pass
class InvalidGeneComplexExpression (Exception):
  """
  signals that the user supplied a gene-complex expression that the GEMtractor doesn't understand
  """
  pass
class TooBigForBrowser (Exception):
  """
  signals that the model is too big for the browser
  """
  pass
