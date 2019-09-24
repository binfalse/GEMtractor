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
  def __init__(self, identifier):
    self.identifier = identifier
    self.reactions = []
    self.links = {"g":set (), "gc":set()}
      
  def contains_one_of (self, genes = []):
    return self.identifier in genes
  
  def to_sbml_string (self):
    return "(" + self.identifier + ")"
      
  def to_string (self):
    return self.identifier + "[#reactions="+str (len (self.reactions))+" #links="+str (len (self.links))+"]"
    
  def serialize (self):
    return {
      "id" : self.identifier,
      "reactions": self.reactions,
      "cplx": []
      }
