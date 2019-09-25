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
  """
  a gene complex (or gene product complex, or enzyme complex) in a network
    
  :param gene: initialize this complex with a first gene
  :type gene: :class:`.gene.Gene`
  """
  def __init__(self, gene = None):
    self.genes = set ()
    self.reactions = []
    self.links = {"g":set (), "gc":set()}
    self.identifier = None
    if gene is not None:
      self.genes.add (gene)
    
  def add_gene (self, gene):
    """
    add another gene to this complex
    
    :param gene: the gene to add to this complex
    :type gene: :class:`.gene.Gene`
    """
    self.genes.add (gene)
    
  def add_genes (self, gene_complex):
    """
    add all genes of another complex to this complex
    
    will iterate the genes in the other gene_complex, to add each of them to this complex
    
    :param gene_complex: the gene complex to copy the genes from
    :type gene_complex: :class:`GeneComplex`
    """
    for g in gene_complex.genes:
      self.genes.add (g)
      
  def get_id (self):
    """
    get the identifier of this complex
    
    will calculate the id using :func:`calc_id`, if the id is not yet calculated
    
    .. warning::
        the id can only be calculated once! so please only calculate it when the complex contains all genes
    
    :return: the identifier of this complex
    :rtype: str
    """
    
    if self.identifier is None:
      self.calc_id ()
    return self.identifier
  
  def contains_one_of (self, genes = []):
    """
    check if this complex contains one of the genes of a given list
    
    :param genes: the list of gene identifiers
    :type genes: list of str
    
    :return: True if any of the genes in this complex is found in the genes list, otherwise False
    :rtype: bool
    """
    for g in self.genes:
      if g.identifier in genes:
        return True
    return False
  
  def calc_id (self):
    """
    calculate the identifier of this complex
    
    .. warning::
        please note that this can only be calculated once!
        so only calculate it when the complex contains all genes
    
    
    :raises RuntimeError: if the identifier was already calculated before
    """
    if self.identifier is not None:
      raise RuntimeError ("cannot overwrite the id of a gene complex")
  
    gl = []
    for g in self.genes:
      gl.append (g.identifier)
    self.identifier = " + ".join (sorted (gl))
      
  def to_sbml_string (self):
    """
    serialize this complex to a valid SBML infix string
    
    will join the list of genes using 'and', and cares about brackets...
    
    :return: the SBML infix expression
    :rtype: str
    """
    gs = []
    for g in self.genes:
      gs.append (g.identifier)
    return "(" + (" and ".join (sorted (gs))) + ")"
    
  def to_string (self):
    """
    serialise this complex into a string
    
    mainly for debugging purposes
    
    :return: the string representation of this complex
    :rtype: str
    """
    gs = ""
    for g in self.genes:
      gs += g.identifier + "+"
    return "GeneComplex["+gs+"]"
    
  def serialize (self, gene_mapper):
    """
    serialize to a JSON-dumpable object
    
    will calculate the id using :func:`calc_id`, if the id is not yet calculated
    
    .. warning::
        the id can only be calculated once! so please only calculate it when the complex contains all genes
    
    the object will contain the following information:
    - id: the complex' identifier
    - enzs: list of enzymes that part of this complex - as list of integers pointing into the serialized enzymes
    - reactions: which reactions does the complex catalyze?
    
    :param gene_mapper: dict that maps a gene id to an integer, which corresponds to the entry in the serialized genes list
    :type gene_mapper: dict
    
    :return: JSON-dumpable object
    :rtype: dict
    
    
    """
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
