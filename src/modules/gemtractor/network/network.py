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

import logging
import re

from .gene import Gene
from .genecomplex import GeneComplex
from .reaction import Reaction
from .species import Species
from ..utils import Utils

from libsbml import LIBSBML_OPERATION_SUCCESS, SBMLDocument, SBMLWriter


class Network:
  """
  a class representing a network
  """
  def __init__ (self):
    self.__logger = logging.getLogger(__name__)
    self.species = {}
    self.reactions = {}
    self.genes = {}
    self.gene_complexes = {}
    self.have_gene_net = False
    self.have_reaction_net = False
    self.__annotation_about_pattern = re.compile (r"<rdf:Description rdf:about=['\"]#[^'\"]+['\"]>", re.IGNORECASE)
    
  def add_species (self, identifier, name):
    """
    adds a species to the network
    
    if there is not yet a species with that identifier, it will
    create a new species and add it to the internal structure
    
    eventually, the species with the corresponding identifier is returned (may be an already existing species, though)
    
    :param identifier: the id of the species
    :param name: the name of the species
    :type identifier: str
    :type name: str
    
    :return: the species with id 'identifier'
    :rtype: :class:`.species.Species`
    """
    if identifier not in self.species:
      self.species[identifier] = Species (identifier, name)
    return self.species[identifier]

  def add_reaction (self, identifier, name):
    """
    adds a reaction to the network
    
    if there is not yet a reaction with that identifier, it will
    create a new reaction and add it to the internal structure
    
    eventually, the reaction with the corresponding identifier is returned (may be an already existing reaction, though)
    
    :param identifier: the id of the reaction
    :param name: the name of the reaction
    :type identifier: str
    :type name: str
    
    :return: the reaction with id 'identifier'
    :rtype: :class:`.reaction.Reaction`
    """
    if identifier not in self.reactions:
      self.reactions[identifier] = Reaction (identifier, name)
    return self.reactions[identifier]
  
  def add_gene (self, gene):
    """
    adds a gene/gene-product/enzyme to the network
    
    if there is not yet a gene with that identifier, it will
    create a new gene and add it to the internal structure
    
    eventually, the gene with the corresponding identifier is returned (may be an already existing gene, though)
    
    :param identifier: the id of the gene
    :param name: the name of the gene
    :type identifier: str
    :type name: str
    
    :return: the gene with id 'identifier'
    :rtype: :class:`.gene.Gene`
    """
    if gene.identifier not in self.genes:
      self.genes[gene.identifier] = Gene (gene.identifier)
    return self.genes[gene.identifier]

  def add_genes (self, reaction, gene_complexes):
    """
    adds multiple genes to this network and to a reaction
    
    iterates all genes and complexes from 'gene_complexes' in 'gene_complexes' and
    - creates new genes if necessary (using :func:`add_gene`)
    - creates new gene complexes and their genes if necessary (using :func:`add_gene`)
    - links the gene and the reaction
    
    
    
    :param reaction: the reaction that is catalyzed by gene_complexes
    :param gene_complexes: list of (mixed) genes and gene complexes that catalyze the reaction
    :type reaction: :class:`.reaction.Reaction`
    :type gene_complexes: list of :class:`.gene.Gene` and :class:`.genecomplex.GeneComplex`
    """
    for gc in gene_complexes:
      if type (gc) is Gene:
        g = self.add_gene (gc)
        reaction.genes.append (g.identifier)
        g.reactions.append (reaction.identifier)
      elif type (gc) is GeneComplex:
        if len (gc.genes) == 1:
          g = self.add_gene (next(iter(gc.genes)))
          reaction.genes.append (g.identifier)
          g.reactions.append (reaction.identifier)
        else:
          gcomplex = GeneComplex ()
          for g in gc.genes:
            gcomplex.add_gene (self.add_gene (g))
          gcomplex.calc_id ()
          reaction.genec.append (gcomplex.identifier)
          gcomplex.reactions.append (reaction.identifier)
          self.gene_complexes[gcomplex.identifier] = (gcomplex)
      else:
        raise RuntimeError ("unexpected gene type: " + type (gc))

  def serialize (self):
    """
    serialize to a JSON-dumpable object
    
    the object will contain the following information:
    
    - species: array of :class:`.species.Species` in the network
    - reactions: array of :class:`.reaction.Reaction` in the network
    - enzs: array of :class:`.gene.Gene` in the network
    - enzc: array of :class:`.genecomplex.GeneComplex` in the network
    
    :return: JSON-dumpable object
    :rtype: dict
    """
    self.__logger.debug ("serialising the network")
    json = {
      "species": [],
      "reactions": [],
      "enzs": [],
      "enzc": [],
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
    
    for identifier, gene in self.genes.items ():
      self.__logger.debug ("serialising gene " + identifier)
      g_ser = gene.serialize ()
      gene_mapper[identifier] = len (json["enzs"])
      json["enzs"].append (g_ser)
    
    for identifier, gene_complex in self.gene_complexes.items ():
      self.__logger.debug ("serialising gene complex " + identifier)
      g_ser = gene_complex.serialize (gene_mapper)
      gene_complex_mapper[identifier] = len (json["enzc"])
      json["enzc"].append (g_ser)
      # add gene-genecomplex information
      for g in gene_complex.genes:
        json["enzs"][gene_mapper[g.identifier]]["cplx"].append (gene_complex_mapper[identifier])
    
    
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
    for g in json["enzs"]:
      o = []
      for occ in g["reactions"]:
        o.append (reaction_mapper[occ])
      g["reactions"] = o
    for g in json["enzc"]:
      o = []
      for occ in g["reactions"]:
        o.append (reaction_mapper[occ])
      g["reactions"] = o
      
    return json
    
    
  def calc_reaction_net (self):
    """
    Calculate the reaction-centric network
    
    Let's say you have this network:
    
    - A -r-> B (reaction r turns A into B)
    - B -s-> C (reaction s turns B into C)
    
    then the reaction-centric network will be:
    
    - r -> s (r links to s)
    
    """
    self.__logger.info ("calc reaction net")
    
    num = 0
    for identifier, reaction in self.reactions.items ():
      num += 1
      if num % 100 == 0:
        self.__logger.info ("calc reaction net " + str (num))
      self.__logger.debug ("calc reaction net " + reaction.identifier)
      
      for species in reaction.consumed:
        self.species[species]._consumption["r"].add (identifier)
        if reaction.reversible:
          self.species[species]._production["r"].add (identifier)
      for species in reaction.produced:
        self.species[species]._production["r"].add (identifier)
        if reaction.reversible:
          self.species[species]._consumption["r"].add (identifier)
      
      
    for identifier, species in self.species.items ():
      for consumption in species._consumption["r"]:
        reaction = self.reactions[consumption]
        for production in species._production["r"]:
          reaction.links.add (self.reactions[production])

    self.have_reaction_net = True

  def calc_genenet (self):
    """
    Calculate the enzyme-centric network
    
    Let's say you have this network:
    
    - A -r-> B (reaction r turns A into B)
    - B -s-> C (reaction s turns B into C)
    
    and let's assume the reactions are catalyzed by the following enzymes:
    
    - r: V or W
    - s: X and (Y or Z) 
    
    then the enzyme-centric network will be:
    
    - V -> X+Y  (V links to X+Y)
    - V -> X+Z  (V links to X+Z)
    - W -> X+Y  (W links to X+Y)
    - W -> X+Z  (W links to X+Z)
    
    """
    self.__logger.info ("calc gene net")
    
    num = 0
    for identifier, reaction in self.reactions.items ():
      num += 1
      if num % 100 == 0:
        self.__logger.info ("calc gene associations for reaction " + str (num))
      self.__logger.debug ("calc gene associations for reaction " + reaction.identifier)
      
      for gene in reaction.genes:
        self.__logger.debug ("processing gene " + gene)
        for species in reaction.consumed:
          s = self.species[species]
          s._consumption["g"].add (gene)
          if reaction.reversible:
            s._production["g"].add (gene)
        for species in reaction.produced:
          s = self.species[species]
          s._production["g"].add (gene)
          if reaction.reversible:
            s._consumption["g"].add (gene)
      
      for gene in reaction.genec:
        self.__logger.debug ("processing gene complex " + gene)
        for species in reaction.consumed:
          s = self.species[species]
          s._consumption["gc"].add (gene)
          if reaction.reversible:
            s._production["gc"].add (gene)
        for species in reaction.produced:
          s = self.species[species]
          s._production["gc"].add (gene)
          if reaction.reversible:
            s._consumption["gc"].add (gene)
    
    self.__logger.info ("got gene associations")
    for identifier, species in self.species.items ():
      for consumption in species._consumption["g"]:
        for production in species._production["g"]:
          self.genes[production].links["g"].add (self.genes[consumption])
        for production in species._production["gc"]:
          self.gene_complexes[production].links["g"].add (self.genes[consumption])
      
      for consumption in species._consumption["gc"]:
        for production in species._production["g"]:
          self.genes[production].links["gc"].add (self.gene_complexes[consumption])
        for production in species._production["gc"]:
          self.gene_complexes[production].links["gc"].add (self.gene_complexes[consumption])
          # ~ self.genenet[production]["links"].add (consumption)
          
    self.__logger.info ("got gene net")
    self.have_gene_net = True
    
    
  def export_mn_dot (self, file_path):
    """
    export the metabolite-reaction network in DOT format
    
    :param file_path: where to store the exported format?
    :type file_path: str
    """
    nodemap = {}
    with open(file_path, 'w') as f:
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
      
  
  
  def export_rn_dot (self, file_path):
    """
    export the reaction-centric network in DOT format
    
    :param file_path: where to store the exported format?
    :type file_path: str
    """
    if not self.have_reaction_net:
      self.calc_reaction_net ()
    with open(file_path, 'w') as f:
      f.write ("digraph GEMtractor {\n")
      
      for identifier, reaction in self.reactions.items ():
        f.write ("\t" + identifier + " [label=\""+reaction.name+"\"];\n")
        
      for identifier, reaction in self.reactions.items ():
        for r in reaction.links:
          f.write ("\t" + identifier + " -> " + r.identifier + ";\n")
      f.write ("}\n")
      
  def export_en_dot (self, file_path):
    """
    export the enzyme-centric network in DOT format
    
    :param file_path: where to store the exported format?
    :type file_path: str
    """
    if not self.have_gene_net:
      self.calc_genenet ()
    nodemap = {}
    with open(file_path, 'w') as f:
      f.write ("digraph GEMtractor {\n")
      #TODO comment incl time and version?
      num = 0
      for gene in self.genes:
          num = num + 1
          nodemap[gene] = 'g' + str(num)
          f.write ("\t" + nodemap[gene] + " [label=\""+gene+"\"];\n")
      for gene in self.gene_complexes:
          num = num + 1
          nodemap[gene] = 'gc' + str(num)
          f.write ("\t" + nodemap[gene] + " [label=\""+gene+"\"];\n")
      
      for gene in self.genes:
          for associated in self.genes[gene].links["g"]:
              f.write ("\t" + nodemap[gene] + " -> " + nodemap[associated.identifier] + ";\n")
          for associated in self.genes[gene].links["gc"]:
              f.write ("\t" + nodemap[gene] + " -> " + nodemap[associated.identifier] + ";\n")
      for gene in self.gene_complexes:
          for associated in self.gene_complexes[gene].links["g"]:
              f.write ("\t" + nodemap[gene] + " -> " + nodemap[associated.identifier] + ";\n")
          for associated in self.gene_complexes[gene].links["gc"]:
              f.write ("\t" + nodemap[gene] + " -> " + nodemap[associated.identifier] + ";\n")
      f.write ("}\n")
      
      
  def export_mn_gml (self, file_path):
    """
    export the metabolite-reaction network in GML format
    
    :param file_path: where to store the exported format?
    :type file_path: str
    """
    nodemap = {}
    with open(file_path, 'w') as f:
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
  
  
  def export_rn_gml (self, file_path):
    """
    export the reaction-centric network in GMl format
    
    :param file_path: where to store the exported format?
    :type file_path: str
    """
    if not self.have_reaction_net:
      self.calc_reaction_net ()
    with open(file_path, 'w') as f:
      f.write (Network.create_gml_prefix ())
      
      nodemap = {}
      num = 0
      for identifier, reaction in self.reactions.items ():
        num += 1
        nodemap[identifier] = str (num)
        f.write (Network.create_gml_node (nodemap[identifier], "reaction", "ellipse", reaction.name))
        
      for identifier, reaction in self.reactions.items ():
        for r in reaction.links:
          f.write (Network.create_gml_edge (nodemap[identifier], nodemap[r.identifier]))
      f.write ("]\n")
      
      
  def export_en_gml (self, file_path):
    """
    export the enzyme-centric network in GML format
    
    :param file_path: where to store the exported format?
    :type file_path: str
    """
    if not self.have_gene_net:
      self.calc_genenet ()
    nodemap = {}
    with open(file_path, 'w') as f:
      f.write (Network.create_gml_prefix ())
      #TODO comment incl time and version?
      num = 0
      for gene in self.genes:
        num += 1
        nodemap[gene] = str (num)
        f.write (Network.create_gml_node (nodemap[gene], "enzyme", "ellipse", gene))
      for gene in self.gene_complexes:
        num += 1
        nodemap[gene] = str (num)
        f.write (Network.create_gml_node (nodemap[gene], "enzyme_complex", "ellipse", gene))
        
        
      for gene in self.genes:
          for associated in self.genes[gene].links["g"]:
              f.write (Network.create_gml_edge (nodemap[gene], nodemap[associated.identifier]))
          for associated in self.genes[gene].links["gc"]:
              f.write (Network.create_gml_edge (nodemap[gene], nodemap[associated.identifier]))
      for gene in self.gene_complexes:
          for associated in self.gene_complexes[gene].links["g"]:
              f.write (Network.create_gml_edge (nodemap[gene], nodemap[associated.identifier]))
          for associated in self.gene_complexes[gene].links["gc"]:
              f.write (Network.create_gml_edge (nodemap[gene], nodemap[associated.identifier]))
      f.write ("]\n")
      
  @staticmethod
  def create_gml_prefix ():
    """
    create the prefix for a GML file
    
    :return: the preamble string for GML files
    :rtype: str
    
    """
    n =     "graph [\n"
    #TODO time and version?
    n = n + "\tcomment \"generated using the GEMtractor\"\n"
    n = n + "\tdirected 1\n"
    return n
  @staticmethod
  def create_gml_node (nid, ntype, nshape, nlabel):
    """
    create a GML node
    
    :param nid: the identifier of the node in the network
    :param ntype: the node's type
    :param nshape: the node's shape
    :param nlabel: the node's label
    :type nid: str
    :type ntype: str
    :type nshape: str
    :type nlabel: str
    
    :return: the GML representation of the network node
    :rtype: str
    
    """
    n =     "\tnode [\n"
    n = n + "\t\tid " + nid + "\n"
    n = n + "\t\tlabel \""+nlabel+"\"\n"
    n = n + "\t]\n"
    return n
  @staticmethod
  def create_gml_edge (source, target):
    """
    create a GML edge
    
    :param source: the identifier of the source node in the network
    :param target: the identifier of the target node in the network
    :type source: str
    :type target: str
    
    :return: the GML representation of the edge
    :rtype: str
    
    """
    n =     "\tedge [\n"
    n = n + "\t\tsource "+source+"\n"
    n = n + "\t\ttarget "+target+"\n"
    n = n + "\t]\n"
    return n
      
  def export_mn_graphml (self, file_path):
    """
    export the metabolite-reaction network in GraphML format
    
    :param file_path: where to store the exported format?
    :type file_path: str
    """
    nodemap = {}
    with open(file_path, 'w') as f:
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
  
  
  def export_rn_graphml (self, file_path):
    """
    export the reaction-centric network in GraphML format
    
    :param file_path: where to store the exported format?
    :type file_path: str
    """
    if not self.have_reaction_net:
      self.calc_reaction_net ()
    with open(file_path, 'w') as f:
      f.write (Network.create_graphml_prefix ())
      for identifier, reaction in self.reactions.items ():
        f.write (Network.create_graphml_node (identifier, "reaction", "ellipse", reaction.name))
        
      num = 0
      for identifier, reaction in self.reactions.items ():
        for r in reaction.links:
          num = num + 1
          f.write ("\t\t<edge id=\"e" + str(num) + "\" source=\"" + identifier + "\" target=\"" + r.identifier + "\"/>\n")
      
      f.write ("\t</graph>\n</graphml>\n")
      
      
  def export_en_graphml (self, file_path):
    """
    export the enzyme-centric network in GraphML format
    
    :param file_path: where to store the exported format?
    :type file_path: str
    """
    if not self.have_gene_net:
      self.calc_genenet ()
    nodemap = {}
    with open(file_path, 'w') as f:
      f.write (Network.create_graphml_prefix ())
      #TODO comment incl time and version?
      num = 0
      for gene in self.genes:
        num += 1
        nodemap[gene] = 'g' + str (num)
        f.write (Network.create_graphml_node (nodemap[gene], "enzyme", "ellipse", gene))
      for gene in self.gene_complexes:
        num += 1
        nodemap[gene] = 'gc' + str (num)
        f.write (Network.create_graphml_node (nodemap[gene], "enzyme_complex", "ellipse", gene))
      num = 0
      for gene in self.genes:
          for associated in self.genes[gene].links["g"]:
              num += 1
              f.write ("\t\t<edge id=\"e" + str(num) + "\" source=\"" + nodemap[gene] + "\" target=\"" + nodemap[associated.identifier] + "\"/>\n")
          for associated in self.genes[gene].links["gc"]:
              num += 1
              f.write ("\t\t<edge id=\"e" + str(num) + "\" source=\"" + nodemap[gene] + "\" target=\"" + nodemap[associated.identifier] + "\"/>\n")
      for gene in self.gene_complexes:
          for associated in self.gene_complexes[gene].links["g"]:
              num += 1
              f.write ("\t\t<edge id=\"e" + str(num) + "\" source=\"" + nodemap[gene] + "\" target=\"" + nodemap[associated.identifier] + "\"/>\n")
          for associated in self.gene_complexes[gene].links["gc"]:
              num += 1
              f.write ("\t\t<edge id=\"e" + str(num) + "\" source=\"" + nodemap[gene] + "\" target=\"" + nodemap[associated.identifier] + "\"/>\n")
      
      f.write ("\t</graph>\n</graphml>\n")
  
  @staticmethod
  def create_graphml_prefix ():
    """
    create the prefix for a GraphML file
    
    :return: the preamble string for GraphML files
    :rtype: str
    
    """
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
    """
    create a GraphML node
    
    :param nid: the identifier of the node in the network
    :param ntype: the node's type
    :param nshape: the node's shape
    :param nlabel: the node's label
    :type nid: str
    :type ntype: str
    :type nshape: str
    :type nlabel: str
    
    :return: the GraphML representation of the network node
    :rtype: str
    
    """
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
      
  def export_rn_sbml (self, file_path, gemtractor, model_id, model_name = None, filter_species = None, filter_reactions = None, filter_genes = None, filter_gene_complexes = None, remove_reaction_enzymes_removed = True, remove_ghost_species = False, discard_fake_enzymes = False, remove_reaction_missing_species = False, removing_enzyme_removes_complex = True):
    """
    export the reaction-centric network in SBML format
    
    will attach the trimming-settings as SBML note
    
    writes the document using the `libsbml:SBMLWriter <http://sbml.org/Special/Software/libSBML/docs/python-api/class_s_b_m_l_writer.html>` -- returns the result of `libsbml:SBMLWriter.writeSBML <http://sbml.org/Special/Software/libSBML/docs/python-api/class_s_b_m_l_writer.html#a02d1998aee7656d7b9c3ac69d62bb66f>`_
    
    :param file_path: where to store the exported format?
    :param model_id: the model's identifier, will be postfixed with a greeting from us
    :param model_name: the model's name, will be prefixed with a greeting from us
    :param filter_species: species identifiers to get rid of
    :param filter_reactions: reaction identifiers to get rid of
    :param filter_genes: enzyme identifiers to get rid of
    :param filter_gene_complexes: enzyme-complex identifiers to get rid of, every list-item should be of format: 'A + B + gene42'
    :param remove_reaction_enzymes_removed: should we remove a reaction if all it's genes were removed?
    :param remove_ghost_species: should species be removed, that do not participate in any reaction anymore - even though they might be required in other entities?
    :param discard_fake_enzymes: should fake enzymes (implicitly assumes enzymes, if no enzymes are annotated to a reaction) be removed?
    :param remove_reaction_missing_species: remove a reaction if one of the participating genes was removed?
    :param removing_enzyme_removes_complex: if an enzyme is removed, should also all enzyme complexes be removed in which it participates?
    
    :type file_path: str
    :type model_id: str
    :type model_name: str
    :type filter_species: list of str
    :type filter_reactions: list of str
    :type filter_genes: list of str
    :type filter_gene_complexes: list of str
    :type remove_reaction_enzymes_removed: bool
    :type remove_ghost_species: bool
    :type discard_fake_enzymes: bool
    :type remove_reaction_missing_species: bool
    :type removing_enzyme_removes_complex: bool
    
    :return: true on success, otherwise false
    :rtype: bool
    """
    if not self.have_reaction_net:
      self.calc_reaction_net ()
    
    
    sbml = SBMLDocument ()
    model = sbml.createModel ()
    #TODO dc modified?
    if model is None:
      self.__logger.error ("could not create model...")
      return False
    model.setId (model_id + "_GEMtracted_ReactionNetwork")
    if model_name is None:
      model_name = model_id
    model.setName ("GEMtracted ReactionNetwork of " + model_name)
    
    Utils.add_model_note (model, filter_species, filter_reactions, filter_genes, filter_gene_complexes, remove_reaction_enzymes_removed, remove_ghost_species, discard_fake_enzymes, remove_reaction_missing_species, removing_enzyme_removes_complex)
    
    compartment = model.createCompartment()
    compartment.setId('compartment')
    compartment.setConstant(True)
    
    nodemap = {}
    for identifier, reaction in self.reactions.items ():
      nodemap[identifier] = self.__create_sbml_reaction_species (model, identifier, reaction.name, compartment, gemtractor)
    
    num = 0
    for identifier, reaction in self.reactions.items ():
      for r in reaction.links:
        num += 1
        Network.create_sbml_reaction (model, 'r' + str (num), nodemap[identifier], nodemap[r.identifier])
  
    return SBMLWriter().writeSBML (sbml, file_path)
  
  def __create_sbml_reaction_species (self, model, identifier, name, compartment, gemtractor):
    """
    create an SBML reaction species for the Reaction-centric network
    
    
    :param model: the SBML model
    :param identifier: the identifier of the reaction
    :param name: the reaction's name
    :param compartment: the compartment in which the reaction will appear
    :param gemtractor: the GEMtractor
    :type model: `libsbml:Model <http://sbml.org/Special/Software/libSBML/docs/python-api/classlibsbml_1_1_model.html>`_
    :type identifier: str
    :type name: str
    :type compartment: `libsbml:Compartment <sbml.org/Software/libSBML/docs/python-api/classlibsbml_1_1_compartment.html>`_
    :type gemtractor: :class:`.gemtractor.GEMtractor`
    
    :return: the SBML species representing a reaction
    :rtype: `libsbml:Species <http://sbml.org/Special/Software/libSBML/docs/python-api/classlibsbml_1_1_species.html>`_
    """
    g = model.createSpecies ()
    g.setId (identifier)
    g.setMetaId (identifier)
    g.setName (name)
    g.setCompartment(compartment.getId())
    g.setHasOnlySubstanceUnits(False)
    g.setBoundaryCondition(False)
    g.setConstant(False)
    
    annotations = gemtractor.get_reaction_annotations (identifier)
    if annotations is not None:
      annotations = self.__annotation_about_pattern.sub('<rdf:Description rdf:about="#'+identifier+'">', annotations)
      if g.setAnnotation (annotations) != LIBSBML_OPERATION_SUCCESS:
        self.__logger.error ("unable to add annotation to reaction " + identifier)
        self.__logger.debug ("annotation was: " + annotations)
    
    return g
      
  def export_en_sbml (self, file_path, gemtractor, model_id, model_name = None, filter_species = None, filter_reactions = None, filter_genes = None, filter_gene_complexes = None, remove_reaction_enzymes_removed = True, remove_ghost_species = False, discard_fake_enzymes = False, remove_reaction_missing_species = False, removing_enzyme_removes_complex = True):
    """
    export the enzyme-centric network in SBML format
    
    will attach the trimming-settings as SBML note
    
    writes the document using the `libsbml:SBMLWriter <http://sbml.org/Special/Software/libSBML/docs/python-api/class_s_b_m_l_writer.html>` -- returns the result of `libsbml:SBMLWriter.writeSBML <http://sbml.org/Special/Software/libSBML/docs/python-api/class_s_b_m_l_writer.html#a02d1998aee7656d7b9c3ac69d62bb66f>`_
    
    :param file_path: where to store the exported format?
    :param model_id: the model's identifier, will be postfixed with a greeting from us
    :param model_name: the model's name, will be prefixed with a greeting from us
    :param filter_species: species identifiers to get rid of
    :param filter_reactions: reaction identifiers to get rid of
    :param filter_genes: enzyme identifiers to get rid of
    :param filter_gene_complexes: enzyme-complex identifiers to get rid of, every list-item should be of format: 'A + B + gene42'
    :param remove_reaction_enzymes_removed: should we remove a reaction if all it's genes were removed?
    :param remove_ghost_species: should species be removed, that do not participate in any reaction anymore - even though they might be required in other entities?
    :param discard_fake_enzymes: should fake enzymes (implicitly assumes enzymes, if no enzymes are annotated to a reaction) be removed?
    :param remove_reaction_missing_species: remove a reaction if one of the participating genes was removed?
    :param removing_enzyme_removes_complex: if an enzyme is removed, should also all enzyme complexes be removed in which it participates?
    
    :type file_path: str
    :type model_id: str
    :type model_name: str
    :type filter_species: list of str
    :type filter_reactions: list of str
    :type filter_genes: list of str
    :type filter_gene_complexes: list of str
    :type remove_reaction_enzymes_removed: bool
    :type remove_ghost_species: bool
    :type discard_fake_enzymes: bool
    :type remove_reaction_missing_species: bool
    :type removing_enzyme_removes_complex: bool
    
    :return: true on success, otherwise false
    :rtype: bool
    """
    if not self.have_gene_net:
      self.calc_genenet ()
    
    sbml = SBMLDocument ()
    model = sbml.createModel ()
    #TODO dc modified?
    if model is None:
      self.__logger.error ("could not create model...")
      return False
    model.setId (model_id + "_GEMtracted_EnzymeNetwork")
    if model_name is None:
      model_name = model_id
    model.setName ("GEMtracted EnzymeNetwork of " + model_name)
    
    # print ("adding note to en sbml")
    Utils.add_model_note (model, filter_species, filter_reactions, filter_genes, filter_gene_complexes, remove_reaction_enzymes_removed, remove_ghost_species, discard_fake_enzymes, remove_reaction_missing_species, removing_enzyme_removes_complex)
    
    nodemap = {}
    
    compartment = model.createCompartment()
    compartment.setId('compartment')
    compartment.setConstant(True)
    
    num = 0
    for gene in self.genes:
      num += 1
      nodemap[gene] = self.__create_sbml_gene (model, 'g' + str (num), gene, compartment, gemtractor)
      # TODO: add other information if available
    
    for gene in self.gene_complexes:
      num += 1
      nodemap[gene] = self.__create_sbml_gene_complex (model, 'gc' + str (num), gene, compartment, gemtractor, self.gene_complexes[gene].genes, nodemap)
      # TODO: add other information if available
    
    num = 0
    for gene in self.genes:
      for associated in self.genes[gene].links["g"]:
        num += 1
        Network.create_sbml_reaction (model, 'r' + str (num), nodemap[gene], nodemap[associated.identifier])
      for associated in self.genes[gene].links["gc"]:
        num += 1
        Network.create_sbml_reaction (model, 'r' + str (num), nodemap[gene], nodemap[associated.identifier])
    for gene in self.gene_complexes:
      for associated in self.gene_complexes[gene].links["g"]:
        num += 1
        Network.create_sbml_reaction (model, 'r' + str (num), nodemap[gene], nodemap[associated.identifier])
      for associated in self.gene_complexes[gene].links["gc"]:
        num += 1
        Network.create_sbml_reaction (model, 'r' + str (num), nodemap[gene], nodemap[associated.identifier])
    
    return SBMLWriter().writeSBML (sbml, file_path)

  
  def __create_sbml_gene_complex (self, model, identifier, name, compartment, gemtractor, genes, nodemap):
    """
    create an SBML gene-complex species for the Enzyme-centric network
    
    
    :param model: the SBML model
    :param identifier: the identifier of the gene complex
    :param name: the gene complex' name
    :param compartment: the compartment in which the gene complex will appear
    :param gemtractor: the GEMtractor
    :param genes: the genes, which are part of this complex
    :param nodemap: mapper to map gene identifiers to corresponding SBML species
    :type model: `libsbml:Model <http://sbml.org/Special/Software/libSBML/docs/python-api/classlibsbml_1_1_model.html>`_
    :type identifier: str
    :type name: str
    :type compartment: `libsbml:Compartment <sbml.org/Software/libSBML/docs/python-api/classlibsbml_1_1_compartment.html>`_
    :type gemtractor: :class:`.gemtractor.GEMtractor`
    :type genes: list of :class:`.gene.Gene`
    :type nodemap: dict
    
    :return: the SBML species representing a gene complex
    :rtype: `libsbml:Species <http://sbml.org/Special/Software/libSBML/docs/python-api/classlibsbml_1_1_species.html>`_
    """
    g = model.createSpecies ()
    g.setId (identifier)
    g.setMetaId (identifier)
    g.setName (name)
    g.setCompartment(compartment.getId())
    g.setHasOnlySubstanceUnits(False)
    g.setBoundaryCondition(False)
    g.setConstant(False)
    
    annotations = ""
    
    for gene in genes:
      annotations += '<rdf:li rdf:resource="#' + nodemap[gene.identifier].getMetaId () + '" />'
    
    if len (annotations) > 0:
      annotations = """
        <annotation>
         <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:bqbiol="http://biomodels.net/biology-qualifiers/">
          <rdf:Description rdf:about="#""" + identifier + """">
            <bqbiol:hasPart>
              <rdf:Bag>""" + annotations + """</rdf:Bag>
            </bqbiol:hasPart>
          </rdf:Description>
         </rdf:RDF>
        </annotation>"""
      if g.setAnnotation (annotations) != LIBSBML_OPERATION_SUCCESS:
        self.__logger.error ("unable to add annotation to gene " + identifier)
        self.__logger.debug ("annotation was: " + annotations)
    else:
      self.__logger.warn ("gene complex has no genes: " + identifier)
    
    return g
  
  def __create_sbml_gene (self, model, identifier, name, compartment, gemtractor):
    """
    create an SBML gene species for the Enzyme-centric network
    
    
    :param model: the SBML model
    :param identifier: the identifier of the gene
    :param name: the gene's name
    :param compartment: the compartment in which the gene will appear
    :param gemtractor: the GEMtractor
    :type model: `libsbml:Model <http://sbml.org/Special/Software/libSBML/docs/python-api/classlibsbml_1_1_model.html>`_
    :type identifier: str
    :type name: str
    :type compartment: `libsbml:Compartment <sbml.org/Software/libSBML/docs/python-api/classlibsbml_1_1_compartment.html>`_
    :type gemtractor: :class:`.gemtractor.GEMtractor`
    
    :return: the SBML species representing a gene
    :rtype: `libsbml:Species <http://sbml.org/Special/Software/libSBML/docs/python-api/classlibsbml_1_1_species.html>`_
    """
    g = model.createSpecies ()
    g.setId (identifier)
    g.setMetaId (identifier)
    g.setName (name)
    g.setCompartment(compartment.getId())
    g.setHasOnlySubstanceUnits(False)
    g.setBoundaryCondition(False)
    g.setConstant(False)
    
    annotations = gemtractor.get_gene_product_annotations (name)
    if annotations is not None:
      annotations = self.__annotation_about_pattern.sub('<rdf:Description rdf:about="#'+identifier+'">', annotations)
      if g.setAnnotation (annotations) != LIBSBML_OPERATION_SUCCESS:
        self.__logger.error ("unable to add annotation to gene " + identifier)
        self.__logger.debug ("annotation was: " + annotations)
    
    return g

  @staticmethod
  def create_sbml_reaction (model, identifier, reactant, product):
    """
    create an SBML reaction for the Enzyme-centric or Reaction-centric network
    
    the reaction will consume and produce exactly one species
    
    :param model: the SBML model
    :param identifier: the identifier of the reaction
    :param reactant: the reactant consumed by the reaction
    :param product: the product produced by the reaction
    :type model: `libsbml:Model <http://sbml.org/Special/Software/libSBML/docs/python-api/classlibsbml_1_1_model.html>`_
    :type identifier: str
    :type reactant: `libsbml:Species <http://sbml.org/Special/Software/libSBML/docs/python-api/classlibsbml_1_1_species.html>`_
    :type product: `libsbml:Species <http://sbml.org/Special/Software/libSBML/docs/python-api/classlibsbml_1_1_species.html>`_
    
    :return: the SBML reaction
    :rtype: `libsbml:Reaction <http://sbml.org/Special/Software/libSBML/docs/python-api/classlibsbml_1_1_reaction.html>`_
    """
    r= model.createReaction ()
    r.setId (identifier)
    r.setFast(False)
    r.setReversible(False)
    r.addReactant (reactant)
    r.addProduct (product)
    return r
    
  
  
  def export_mn_csv (self, file_path):
    """
    export the metabolite-reaction network in CSV format
    
    :param file_path: where to store the exported format?
    :type file_path: str
    """
    with open(file_path, 'w') as f:
      f.write ('"source","target"\n')
      for identifier, reaction in self.reactions.items ():
        rid = 'r' + identifier
        for s in reaction.consumed:
          f.write ('"s' + s + '","' + rid + '"\n')
        for s in reaction.produced:
          f.write ('"' + rid + '","s' + s + '"\n')
    
  
  
  def export_rn_csv (self, file_path):
    """
    export the reaction-centric network in CSV format
    
    :param file_path: where to store the exported format?
    :type file_path: str
    """
    if not self.have_reaction_net:
      self.calc_reaction_net ()
    with open(file_path, 'w') as f:
      f.write ('"source","target"\n')
      for identifier, reaction in self.reactions.items ():
        for r in reaction.links:
          f.write ('"' + identifier + '","' + r.identifier + '"\n')
      
      
  def export_en_csv (self, file_path):
    """
    export the enzyme-centric network in CSV format
    
    :param file_path: where to store the exported format?
    :type file_path: str
    """
    if not self.have_gene_net:
      self.calc_genenet ()
    with open(file_path, 'w') as f:
      f.write ('"source","target"\n')
      for gene in self.genes:
          for associated in self.genes[gene].links["g"]:
            f.write ('"' + gene + '","' + associated.identifier + '"\n')
          for associated in self.genes[gene].links["gc"]:
            f.write ('"' + gene + '","' + associated.identifier + '"\n')
      for gene in self.gene_complexes:
          for associated in self.gene_complexes[gene].links["g"]:
            f.write ('"' + gene + '","' + associated.identifier + '"\n')
          for associated in self.gene_complexes[gene].links["gc"]:
            f.write ('"' + gene + '","' + associated.identifier + '"\n')
