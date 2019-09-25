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

class Gene:
  """
  a gene (or gene product, or enzyme) in a network
  """
  def __init__(self, identifier):
    """
    :param identifier: the gene's id
    """
    self.identifier = identifier
    self.reactions = []
    self.links = {"g":set (), "gc":set()}
      
  def contains_one_of (self, genes = []):
    """
    is this one of the genes?
    
    basically just to be compliant with the gene-complex
    
    :param genes: list of genes to test
    :type genes: list of str
    
    :return: true, if this identifier in in genes-list
    :rtype: bool
    """
    return self.identifier in genes
  
  def to_sbml_string (self):
    """
    serialize this to an SBML compatible notes' string
    
    
    :return: the notes string
    :rtype: str
    """
    return "(" + self.identifier + ")"
      
  def to_string (self):
    """
    return this as a string
    
    basically for debugging
    
    :return: this object as a string
    :rtype: string
    """
    return self.identifier + "[#reactions="+str (len (self.reactions))+" #links="+str (len (self.links))+"]"
    
  def serialize (self):
    """
    serialize to a JSON-dumpable object
    """
    return {
      "id" : self.identifier,
      "reactions": self.reactions,
      "cplx": []
      }
