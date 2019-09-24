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

class GeneComplex:
  def __init__(self, gene = None):
    self.genes = set ()
    self.reactions = []
    self.links = {"g":set (), "gc":set()}
    self.identifier = None
    if gene is not None:
      self.genes.add (gene)
    
  def add_gene (self, gene):
    self.genes.add (gene)
    
  def add_genes (self, gene_complex):
    for g in gene_complex.genes:
      self.genes.add (g)
      
  def get_id (self):
    if self.identifier is None:
      self.calc_id ()
    return self.identifier
  
  def contains_one_of (self, genes = []):
    for g in self.genes:
      if g.identifier in genes:
        return True
    return False
  
  def calc_id (self):
    if self.identifier is not None:
      raise RuntimeError ("cannot overwrite the id of a gene complex")
  
    gl = []
    for g in self.genes:
      gl.append (g.identifier)
    self.identifier = " + ".join (sorted (gl))
      
  def to_sbml_string (self):
    gs = []
    for g in self.genes:
      gs.append (g.identifier)
    return "(" + (" and ".join (sorted (gs))) + ")"
    
  def to_string (self):
    gs = ""
    for g in self.genes:
      gs += g.identifier + "+"
    return "GeneComplex["+gs+"]"
    
  def serialize (self, gene_mapper):
    if self.identifier is None:
      self.calc_id ()
    
    ret = {
      "id": self.identifier,
      "enzs" : [],
      "reactions": self.reactions
      }
    for g in self.genes:
      ret["enzs"].append (gene_mapper[g.identifier])
    return ret
