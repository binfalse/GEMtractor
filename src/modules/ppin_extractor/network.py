
import logging
from libsbml import *
from modules.enalyzer_utils.utils import Utils

# TODO: logging
class Species:
  def __init__ (self, name, identifier):
    self.__logger = logging.getLogger('enalyzer.species')
    # TODO: fix
    # self.__logger.setLevel(logging.DEBUG)
    self.name = name
    self.identifier = identifier
    self.genes_for_consumption = []
    self.genes_for_production = []
    self.occurence = []
    
  def serialize (self):
    return {
      "identifier" : self.identifier,
      "name" : self.name,
      "occurence" : self.occurence
      }
    

class Reaction:

  def __init__(self, identifier, name, reversible = False):
    self.__logger = logging.getLogger('enalyzer.reaction')
    # TODO: fix
    # self.__logger.setLevel(logging.DEBUG)
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
      
  def serialize (self):
    return {
      "identifier" : self.identifier,
      "name" : self.name,
      "reversible" : self.reversible,
      "consumed" : self.consumed,
      "produced" : self.produced,
      "genes" : self.genes
      }

class Network:

  def __init__ (self):
    self.__logger = logging.getLogger('enalyzer.network')
    # TODO: fix
    # self.__logger.setLevel(logging.ERROR)
    self.species = {}
    self.reactions = {}
    self.genenet = {}
    
  def add_species (self, species):
    self.species[species.identifier] = species

  def add_reaction (self, reaction):
    self.reactions[reaction.identifier] = reaction
    
  def get_species (self, identifier):
    return self.species[identifier]

  def serialize (self):
    json = {
      "species": {},
      "reactions": {},
      "genenet": self.genenet}
    
    for identifier, species in self.species.items ():
      json["species"][identifier] = species.serialize ()
    for identifier, reaction in self.reactions.items ():
      json["reactions"][identifier] = reaction.serialize ()
    
    return json


  def calc_genenet (self):
    
    self.genenet = {}
    
    for identifier, reaction in self.reactions.items ():
      self.__logger.debug ("calc gene net for reaction " + reaction.identifier)
      for gene in reaction.genes:
        self.__logger.debug ("processing gene " + gene)
        if gene not in self.genenet:
          self.genenet[gene] = {"links": [], "reactions": [identifier]}
        else:
          self.genenet[gene]["reactions"].append (identifier)
        
        for species in reaction.consumed:
          s = self.species[species]
          if gene not in s.genes_for_consumption:
            s.genes_for_consumption.append (gene)
          if reaction.reversible and gene not in s.genes_for_production:
            s.genes_for_production.append (gene)
        for species in reaction.produced:
          s = self.species[species]
          if gene not in s.genes_for_production:
            s.genes_for_production.append (gene)
          if reaction.reversible and gene not in s.genes_for_consumption:
            s.genes_for_consumption.append (gene)
    
    for identifier, species in self.species.items ():
      for consumption in species.genes_for_consumption:
        for production in species.genes_for_production:
          if consumption not in self.genenet[production]["links"]:
            self.genenet[production]["links"].append (consumption)
    
    
  def export_rn_dot (self, filename):
    """ export the chemical reaction network in DOT format """
    nodemap = {}
    with open(filename, 'w') as f:
      f.write ("digraph enalyzer {\n")
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
      f.write ("digraph enalyzer {\n")
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
    n = n + "\tcomment \"generated using ENAlyzer\"\n"
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
    n = n + "\t<graph id=\"enalyzer\" edgedefault=\"directed\">\n"
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
    if model is None:
      return False
    model.setId (model_id + "_enalyzed_EnzymeNetwork")
    if model_name is None:
      model_name = model_id
    model.setName ("enalyzed EnzymeNetwork of " + model_name)
    
    print ("adding note to en sbml")
    Utils.add_model_note (model, filter_species, filter_reactions, filter_genes, remove_reaction_genes_removed, remove_reaction_missing_species)
    
    nodemap = {}
    
    num = 0
    for gene in self.genenet:
      num += 1
      g = model.createSpecies ()
      g.setId ('g' + str (num))
      g.setName (gene)
      nodemap[gene] = g
      # TODO: add other information if available
    
    num = 0
    for gene in self.genenet:
      for associated in self.genenet[gene]['links']:
        num += 1
        r= model.createReaction ()
        r.setId ('r' + str (num))
        r.addReactant (nodemap[gene])
        r.addProduct (nodemap[associated])
    
    return SBMLWriter().writeSBML (sbml, filename)
