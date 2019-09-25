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

class Reaction:
  """
  a reaction in a network
    
  :param identifier: the reaction's identifier
  :param name: the reaction's name
  :param reversible: is the reaction reversible?
  :type identifier: str
  :type name: str
  :type reversible: bool
  """

  def __init__(self, identifier, name, reversible = True):
    self.identifier = identifier
    self.name = name
    self.reversible = reversible
    self.consumed = []
    self.produced = []
    self.genes = []
    self.genec = []
    self.links = set ()


  def add_input (self, species):
    """
    adds a species that is consumed by this reaction
    
    :param species: the consumed species
    :type species: :class:`.species.Species`
    """
    species.occurence.append (self.identifier)
    self.consumed.append (species.identifier)

  def add_output (self, species):
    """
    adds a species that is produced by this reaction
    
    :param species: the produced species
    :type species: :class:`.species.Species`
    """
    species.occurence.append (self.identifier)
    self.produced.append (species.identifier)
      
  def serialize (self, species_mapper, gene_mapper, gene_complex_mapper):
    """
    serialize to a JSON-dumpable object
    """
    ret =  {
      "id" : self.identifier,
      "name" : self.name,
      "rev" : self.reversible,
      "cons" : [],
      "prod" : [],
      "enzs" : [],
      "enzc" : []
      }
    for s in self.consumed:
      ret["cons"].append (species_mapper[s])
    for s in self.produced:
      ret["prod"].append (species_mapper[s])
    for g in self.genes:
      ret["enzs"].append (gene_mapper[g])
    for g in self.genec:
      ret["enzc"].append (gene_complex_mapper[g])
    return ret
