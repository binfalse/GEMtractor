# This file is part of the enalyzer
# Copyright (C) 2019 Martin Scharm <https://binfalse.de>
# 
# The enalyzer is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# The enalyzer is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import logging
from libsbml import SBMLDocument, SBMLWriter
from .utils import Utils

# TODO: logging
class Species:
  def __init__ (self, identifier, name):
    self.__logger = logging.getLogger(__name__)
    self.name = name
    self.identifier = identifier
    self.genes_for_consumption = set ()
    self.genes_for_production = set ()
    self.occurence = []
    
  def serialize (self):
    return {
      "id" : self.identifier,
      "name" : self.name,
      "occ" : self.occurence
      }
    

class Reaction:

  def __init__(self, identifier, name, reversible = False):
    self.identifier = identifier
    self.name = name
    self.reversible = reversible
    self.consumed = []
    self.produced = []
    self.genes = []


  def add_input (self, species):
    species.occurence.append (self.identifier)
    self.consumed.append (species.identifier)

  def add_output (self, species):
    species.occurence.append (self.identifier)
    self.produced.append (species.identifier)
      
  def serialize (self, species_mapper, gene_mapper, gene_complex_mapper):
    ret =  {
      "id" : self.identifier,
      "name" : self.name,
      "rev" : self.reversible,
      "cons" : [],
      "prod" : [],
      "genes" : [],
      "genec" : []
      }
    for s in self.consumed:
      ret["cons"].append (species_mapper[s])
    for s in self.produced:
      ret["prod"].append (species_mapper[s])
    for g in self.genes:
      if g in gene_mapper:
        ret["genes"].append (gene_mapper[g])
      else:
        ret["genec"].append (gene_complex_mapper[g])
    return ret

class Gene:
  def __init__(self, identifier):
    self.identifier = identifier
    self.reactions = []
    self.links = []
      
  def serialize (self):
    return {
      "id" : self.identifier,
      "reactions": self.reactions,
      "cplx": []
      }

class GeneComplex:
  def __init__(self, gene = None):
    self.genes = set ()
    self.reactions = []
    self.links = []
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
  
  def calc_id (self):
    if self.identifier is not None:
      raise RuntimeError ("cannot overwrite the id of a gene complex")
  
    gl = []
    for g in self.genes:
      gl.append (g.identifier)
    self.identifier = " + ".join (sorted (gl))
      
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
      "genes" : [],
      "reactions": self.reactions
      }
    for g in self.genes:
      ret["genes"].append (gene_mapper[g.identifier])
    return ret
    
  

class Network:

  def __init__ (self):
    self.__logger = logging.getLogger(__name__)
    self.species = {}
    self.reactions = {}
    self.genes = {}
    self.gene_complexes = {}
    self.genenet = {}
    
  def add_species (self, identifier, name):
    if identifier not in self.species:
      self.species[identifier] = Species (identifier, name)
    return self.species[identifier]

  def add_reaction (self, identifier, name):
    if identifier not in self.reactions:
      self.reactions[identifier] = Reaction (identifier, name)
    return self.reactions[identifier]
  
  def add_gene (self, identifier):
    if identifier not in self.genes:
      self.genes[identifier] = Gene (identifier)
    return self.genes[identifier]

  def add_genes (self, reaction, gene_complexes):
    # ~ logc = []
    for gc in gene_complexes:
      # ~ log = []
      if len (gc.genes) == 1:
        g = self.add_gene (next(iter(gc.genes)).identifier)
        reaction.genes.append (g.identifier)
        g.reactions.append (reaction.identifier)
      else:
        gcomplex = GeneComplex ()
        for g in gc.genes:
          gcomplex.add_gene (self.add_gene (g.identifier))
        gcomplex.calc_id ()
        reaction.genes.append (gcomplex.identifier)
        gcomplex.reactions.append (reaction.identifier)
        self.gene_complexes[gcomplex.identifier] = (gcomplex)
    
    # ~ if identifier not in self.genes:
      # ~ self.genes[identifier] = Gene (identifier)
    # ~ return self.genes[identifier]

  def serialize (self):
    self.__logger.debug ("serialising the network")
    json = {
      "species": [],
      "reactions": [],
      "genes": [],
      "genec": [],
      }
      
    species_mapper = {}
    reaction_mapper = {}
    gene_mapper = {}
    gene_complex_mapper = {}
    
    for identifier, species in self.species.items ():
      self.__logger.debug ("serialising species " + identifier)
      s_ser = species.serialize ()
      species_mapper[identifier] = len (json["species"])
      json["species"].append (s_ser)
    
    print (self.genes)
    for identifier, gene in self.genes.items ():
      self.__logger.debug ("serialising gene " + identifier)
      g_ser = gene.serialize ()
      gene_mapper[identifier] = len (json["genes"])
      json["genes"].append (g_ser)
    
    for identifier, gene_complex in self.gene_complexes.items ():
      self.__logger.debug ("serialising gene complex " + identifier)
      g_ser = gene_complex.serialize (gene_mapper)
      gene_complex_mapper[identifier] = len (json["genec"])
      json["genec"].append (g_ser)
      # add gene-genecomplex information
      for g in gene_complex.genes:
        json["genes"][gene_mapper[g.identifier]]["cplx"].append (gene_complex_mapper[identifier])
    
    
    for identifier, reaction in self.reactions.items ():
      self.__logger.debug ("serialising reaction " + identifier)
      # json["reactions"][reaction.num] = reaction.serialize ()
      r_ser = reaction.serialize (species_mapper, gene_mapper, gene_complex_mapper)
      reaction_mapper[identifier] = len (json["reactions"])
      json["reactions"].append (r_ser)
    
    
    # further reduce return size: replace reaction ids in species occurrences
    for s in json["species"]:
      o = []
      for occ in s["occ"]:
        o.append (reaction_mapper[occ])
      s["occ"] = o
    
    # further reduce return size: replace reaction ids in gene occurrences
    for g in json["genes"]:
      o = []
      for occ in g["reactions"]:
        o.append (reaction_mapper[occ])
      g["reactions"] = o
    for g in json["genec"]:
      o = []
      for occ in g["reactions"]:
        o.append (reaction_mapper[occ])
      g["reactions"] = o
    
    
    # ~ for gene in self.genenet:
      # ~ json["genenet"][gene] = {"links": [], "reactions": []}
      # ~ for associated in self.genenet[gene]["links"]:
        # ~ json["genenet"][gene]["links"].append (associated)
      # ~ for reaction in self.genenet[gene]["reactions"]:
        # ~ json["genenet"][gene]["reactions"].append (reaction)
      
    return json


  # ~ def calc_genenet (self):
    # ~ self.__logger.info ("calc gene net")
    # ~ self.genenet = {}
    
    # ~ num = 0
    # ~ for identifier, reaction in self.reactions.items ():
      # ~ num += 1
      # ~ if num % 100 == 0:
        # ~ self.__logger.info ("calc gene associations for reaction " + str (num))
      # ~ self.__logger.debug ("calc gene associations for reaction " + reaction.identifier)
      # ~ for gene in reaction.genes:
        # ~ self.__logger.debug ("processing gene " + gene)
        # ~ if gene not in self.genenet:
          # ~ self.genenet[gene] = {"links": set (), "reactions": [identifier]}
        # ~ else:
          # ~ self.genenet[gene]["reactions"].append (identifier)
        
        # ~ for species in reaction.consumed:
          # ~ s = self.species[species]
          # ~ #if gene not in s.genes_for_consumption:
          # ~ s.genes_for_consumption.add (gene)
          # ~ if reaction.reversible:
            # ~ # and gene not in s.genes_for_production:
            # ~ s.genes_for_production.add (gene)
        # ~ for species in reaction.produced:
          # ~ s = self.species[species]
          # ~ # if gene not in s.genes_for_production:
          # ~ s.genes_for_production.add (gene)
          # ~ if reaction.reversible:
            # ~ # and gene not in s.genes_for_consumption:
            # ~ s.genes_for_consumption.add (gene)
    
    # ~ self.__logger.info ("got gene associations")
    # ~ for identifier, species in self.species.items ():
      # ~ for consumption in species.genes_for_consumption:
        # ~ for production in species.genes_for_production:
          # ~ self.genenet[production]["links"].add (consumption)
    # ~ self.__logger.info ("got gene net")
    
    
  def export_rn_dot (self, filename):
    """ export the chemical reaction network in DOT format """
    nodemap = {}
    with open(filename, 'w') as f:
      f.write ("digraph GEMtractor {\n")
      #TODO comment incl time and version?
      for identifier, species in self.species.items ():
          nodemap[identifier] = 's' + identifier
          f.write ("\t" + nodemap[identifier] + " [label=\""+identifier+"\"];\n")
      for identifier, reaction in self.reactions.items ():
        rid = 'r' + identifier
        f.write ("\t" + rid + " [label=\""+identifier+"\" shape=box];\n")
        for s in reaction.consumed:
          f.write ("\t" + nodemap[s] + " -> " + rid + ";\n")
        for s in reaction.produced:
          f.write ("\t" + rid + " -> " + nodemap[s] + ";\n")
      f.write ("}\n")
      
      
  def export_en_dot (self, filename):
    """ export the enzyme network in DOT format """
    if not self.genenet:
      self.calc_genenet ()
    nodemap = {}
    with open(filename, 'w') as f:
      f.write ("digraph GEMtractor {\n")
      #TODO comment incl time and version?
      num = 0
      for gene in self.genenet:
          num = num + 1
          nodemap[gene] = 'g' + str(num)
          f.write ("\t" + nodemap[gene] + " [label=\""+gene+"\"];\n")
      for gene in self.genenet:
          for associated in self.genenet[gene]['links']:
              f.write ("\t" + nodemap[gene] + " -> " + nodemap[associated] + ";\n")
      f.write ("}\n")
      
      
  def export_rn_gml (self, filename):
      nodemap = {}
      with open(filename, 'w') as f:
        f.write (Network.create_gml_prefix ())
        #TODO comment incl time and version?
        
        num = 0
        for identifier, species in self.species.items ():
          num += 1
          nodemap[identifier] = str (num)
          f.write (Network.create_gml_node (nodemap[identifier], "species", "ellipse", identifier))
        
        for identifier, reaction in self.reactions.items ():
          num += 1
          rid = str (num)
          f.write (Network.create_gml_node (rid, "reaction", "rectangle", identifier))
          for s in reaction.consumed:
            f.write (Network.create_gml_edge (nodemap[s], rid))
          for s in reaction.produced:
            f.write (Network.create_gml_edge (rid, nodemap[s]))
          
        f.write ("]\n")
      
      
  def export_en_gml (self, filename):
      nodemap = {}
      with open(filename, 'w') as f:
        f.write (Network.create_gml_prefix ())
        #TODO comment incl time and version?
        num = 0
        for gene in self.genenet:
          num += 1
          nodemap[gene] = str (num)
          f.write (Network.create_gml_node (nodemap[gene], "gene", "ellipse", gene))
        for gene in self.genenet:
            for associated in self.genenet[gene]['links']:
                f.write (Network.create_gml_edge (nodemap[gene], nodemap[associated]))
        f.write ("]\n")
      
  @staticmethod
  def create_gml_prefix ():
    n =     "graph [\n"
    #TODO time and version?
    n = n + "\tcomment \"generated using the GEMtractor\"\n"
    n = n + "\tdirected 1\n"
    return n
  @staticmethod
  def create_gml_node (nid, ntype, nshape, nlabel):
    n =     "\tnode [\n"
    n = n + "\t\tid " + nid + "\n"
    n = n + "\t\tlabel \""+nlabel+"\"\n"
    n = n + "\t]\n"
    return n
  @staticmethod
  def create_gml_edge (source, target):
    n =     "\tedge [\n"
    n = n + "\t\tsource "+source+"\n"
    n = n + "\t\ttarget "+target+"\n"
    n = n + "\t]\n"
    return n
      
  def export_rn_graphml (self, filename):
      nodemap = {}
      with open(filename, 'w') as f:
        f.write (Network.create_graphml_prefix ())
        #TODO comment incl time and version?
        
        for identifier, species in self.species.items ():
          nodemap[identifier] = 's' + identifier
          f.write (Network.create_graphml_node (nodemap[identifier], "species", "ellipse", identifier))
        
        num = 0
        for identifier, reaction in self.reactions.items ():
          rid = 'r' + identifier
          f.write (Network.create_graphml_node (rid, "reaction", "rectangle", identifier))
          for s in reaction.consumed:
            num = num + 1
            f.write ("\t\t<edge id=\"e" + str(num) + "\" source=\"" + nodemap[s] + "\" target=\"" + rid + "\"/>\n")
          for s in reaction.produced:
            num = num + 1
            f.write ("\t\t<edge id=\"e" + str(num) + "\" source=\"" + rid + "\" target=\"" + nodemap[s] + "\"/>\n")
          
        f.write ("\t</graph>\n</graphml>\n")
      
      
  def export_en_graphml (self, filename):
      nodemap = {}
      with open(filename, 'w') as f:
        f.write (Network.create_graphml_prefix ())
        #TODO comment incl time and version?
        num = 0
        for gene in self.genenet:
          num += 1
          nodemap[gene] = 'g' + str (num)
          f.write (Network.create_graphml_node (nodemap[gene], "gene", "ellipse", gene))
        num = 0
        for gene in self.genenet:
            for associated in self.genenet[gene]['links']:
                num += 1
                f.write ("\t\t<edge id=\"e" + str(num) + "\" source=\"" + nodemap[gene] + "\" target=\"" + nodemap[associated] + "\"/>\n")
        f.write ("\t</graph>\n</graphml>\n")
  
  @staticmethod
  def create_graphml_prefix ():
    #TODO time and version?
    n =     "<graphml xmlns=\"http://graphml.graphdrawing.org/xmlns\"\n"
    n = n + "\txmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"\n"
    n = n + "\txsi:schemaLocation=\"http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd\"\n"
    n = n + "\txmlns:y=\"http://www.yworks.com/xml/graphml\">\n\n"
    n = n + "\t<key for=\"node\" id=\"layout\" yfiles.type=\"nodegraphics\"/>\n"
    n = n + "\t<key for=\"node\" id=\"type\" attr.type=\"string\"><default>species</default></key>\n"
    n = n + "\t<graph id=\"GEMtractor\" edgedefault=\"directed\">\n"
    return n
  @staticmethod
  def create_graphml_node (nid, ntype, nshape, nlabel):
    n =     "\t\t<node id=\"" + nid + "\">\n"
    n = n + "\t\t\t<data key=\"type\">"+ntype+"</data>\n"
    n = n + "\t\t\t<data key=\"layout\">\n"
    n = n + "\t\t\t\t<y:ShapeNode>\n"
    n = n + "\t\t\t\t\t<y:Shape type=\""+nshape+"\"/>\n"
    n = n + "\t\t\t\t\t<y:NodeLabel>"+nlabel+"</y:NodeLabel>\n"
    n = n + "\t\t\t\t</y:ShapeNode>\n"
    n = n + "\t\t\t</data>\n"
    n = n + "\t\t</node>\n"
    return n
      
      
  def export_en_sbml (self, filename, model_id, model_name = None, filter_species = None, filter_reactions = None, filter_genes = None, remove_reaction_genes_removed = True, remove_reaction_missing_species = False):
    sbml = SBMLDocument ()
    model = sbml.createModel ()
    #TODO dc modified?
    if model is None:
      return False
    model.setId (model_id + "_GEMtracted_EnzymeNetwork")
    if model_name is None:
      model_name = model_id
    model.setName ("GEMtracted EnzymeNetwork of " + model_name)
    
    # print ("adding note to en sbml")
    Utils.add_model_note (model, filter_species, filter_reactions, filter_genes, remove_reaction_genes_removed, remove_reaction_missing_species)
    
    nodemap = {}
    
    compartment = model.createCompartment()
    compartment.setId('compartment')
    compartment.setConstant(True)
    
    num = 0
    for gene in self.genenet:
      num += 1
      g = model.createSpecies ()
      g.setId ('g' + str (num))
      g.setName (gene)
      g.setCompartment(compartment.getId())
      g.setHasOnlySubstanceUnits(False)
      g.setBoundaryCondition(False)
      g.setConstant(False)
      nodemap[gene] = g
      # TODO: add other information if available
    
    num = 0
    for gene in self.genenet:
      for associated in self.genenet[gene]['links']:
        num += 1
        r= model.createReaction ()
        r.setId ('r' + str (num))
        r.setFast(False)
        r.setReversible(False)
        r.addReactant (nodemap[gene])
        r.addProduct (nodemap[associated])
    
    return SBMLWriter().writeSBML (sbml, filename)
