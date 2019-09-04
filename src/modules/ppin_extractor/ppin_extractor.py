# PPIN Extractor
# Copyright (C) 2019 Martin Scharm <https://binfalse.de>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from libsbml import *
import re
import pyparsing as pp
import sys
import logging
import hashlib
from .network import Network, Reaction, Species
import math
from modules.enalyzer_utils.utils import BreakLoops, InvalidGeneExpression, Utils

# assumptions:
# * gene logic is stored per reaction in reaction->notes->html as "<p>GENE_ASSOCIATION: ....</p>"
# * GENE_ASSOCIATION to lower _only_ changes char cases (not logic) -aka- gene names are basically case insensitive
# * AND has priority over OR -> a or b and c == a or (b and c) -> better use parentheses to make sure!
# * you know that ((a and b) and c) is the same as (a and (b and c)) etc... we don't care about the ordering, if you care you need to post process the results
# * there is no list of modifiers

class PpinExtractor:
    """class to extract protein-protein-interaction-networks from chemical reaction networks"""

    
    
    def __init__(self):
        self.__GENE_PATTERN = re.compile(r".*GENE_ASSOCIATION: *([^<]+)<.*", re.DOTALL)
        self.__EXPRESSION_PARSER = self.__get_expression_parser ()
        self.__logger = logging.getLogger('PpinExtractor')
        # TODO: fix
        # self.__logger.setLevel(logging.DEBUG)
    
    def __get_expression_parser (self):
        variables = pp.Word(pp.alphanums, pp.alphanums + "_-.") 
        condition = pp.Group(variables)
        return pp.infixNotation(condition,[("and", 2, pp.opAssoc.LEFT, ),("or", 2, pp.opAssoc.LEFT, ),])


    def _parse_expression (self, expression):
        # print ("parsing expression: " + expression)
        try:
            return self.__EXPRESSION_PARSER.parseString(expression.lower (), True)
        except pp.ParseException as e:
            raise InvalidGeneExpression ("cannot parse expression: >>" + expression + "<< -- " + getattr(e, 'message', repr(e)))

    def _unfold_complex_expression (self, parseresult):
        #print ("current: " + str(parseresult))
        if isinstance(parseresult, pp.ParseResults):
            
            if len(parseresult) == 1:
                return self._unfold_complex_expression (parseresult[0])
            
            if len(parseresult) > 2 and len(parseresult) % 2 == 1:
                # this is a chain of ANDs/ORs
                # make sure it's only ANDs or only ORs
                for i in range (0, math.floor (len(parseresult) / 2) - 1):
                  if parseresult[2*i+1] != parseresult[2*i+3]:
                    # if it's mixed we'll raise an error
                    self.__logger.critical('and/or mixed in expression: ' + str(parseresult[1]))
                    raise NotImplementedError ('and/or mixed in expression: ' + str(parseresult[1]))
                
                logic = None
                if parseresult[1] == "and":
                    logic = True
                elif parseresult[1] == "or":
                    logig = False
                else:
                    self.__logger.critical('neither and nor or -> do not understand: ' + str(parseresult[1]))
                    raise NotImplementedError ('neither and nor or -> do not understand: ' + str(parseresult[1]))
                
                # parse the first subterm
                term_combination = self._unfold_complex_expression (parseresult[0])
                
                # from the second subterm, it depends on the logic-connection on how to combine subterms
                for i in range(2, len(parseresult), 2):
                    if logic:
                        # it's ANDed -> so every previous item needs to be connected to every next item
                        newterms = self._unfold_complex_expression (parseresult[i])
                        tmp = []
                        for a in term_combination:
                            for b in newterms:
                                tmp.append ("("+str(a)+" and "+str (b)+")")
                        term_combination = tmp
                    else:
                        # just add them to the list as alternatives
                        term_combination += self._unfold_complex_expression (parseresult[i])
                
                return term_combination
            
            else:
                self.__logger.critical('unexpected expression: ' + str(parseresult))
                raise NotImplementedError ('unexpected expression: ' + str(parseresult))
                
        else:
            return [parseresult]


    def _extract_genes_from_sbml_notes (self, annotation, default):
        m = re.match (self.__GENE_PATTERN, annotation)
        if m:
            return m.group (1)
        return default
    
    def _overwrite_genes_in_sbml_notes (self, original_genes, new_genes, reaction):
        m = re.match (self.__GENE_PATTERN, reaction.getNotesString())
        if m:
          reaction.setNotes (reaction.getNotesString().replace (original_genes, new_genes))
        else:
          # TODO
          raise IOError ("not yet implemented")
          # return
          
      
    
    def get_sbml (self, sbml_file, filter_species = None, filter_reactions = None, filter_genes = None, remove_reaction_genes_removed = True, remove_reaction_missing_species = False):
      """ Get a filtered SBML document from a file
      
      Parameters:
      -----------
      
      sbml_file: path to the SBML file
      filter_species:
      filter_reactions:
      filter_genes:
      remove_reaction_genes_removed: should we remove a reaction if all it's genes were removed?
      remove_reaction_missing_species: remove a reaction if one of the participating genes was removed?
      """
      sbml = SBMLReader().readSBML(sbml_file)
      if sbml.getNumErrors() > 0:
        raise IOError ("model seems to be invalid")
      model = sbml.getModel()
      name = model.getName ()
      if name is None:
          name = model.getId()
      model.setId (model.getId() + "_enalyzed_ReactionNetwork")
      model.setName ("enalyzed ReactionNetwork of " + name)
      
      Utils.add_model_note (model, filter_species, filter_reactions, filter_genes, remove_reaction_genes_removed, remove_reaction_missing_species)
      
      
      if filter_species is not None or filter_reactions is not None or filter_genes is not None:
        try:
          for n in range (model.getNumReactions () - 1, -1, -1):
            reaction = model.getReaction (n)
            if filter_reactions is not None and reaction.getId () in filter_reactions:
              model.removeReaction (n)
              continue
            
            if filter_species is not None:
              for sn in range (reaction.getNumReactants() -1, -1, -1):
                  s = reaction.getReactant(sn).getSpecies()
                  if s in filter_species:
                    if remove_reaction_missing_species:
                      model.removeReaction (n)
                      raise BreakLoops
                    reaction.removeReactant (sn)
                  
              for sn in range (reaction.getNumProducts() -1, -1, -1):
                  s = reaction.getProduct(sn).getSpecies()
                  if s in filter_species:
                    if remove_reaction_missing_species:
                      model.removeReaction (n)
                      raise BreakLoops
                    reaction.removeProduct (sn)
                  
              for sn in range (reaction.getNumModifiers() -1, -1, -1):
                  s = reaction.getModifier(sn).getSpecies()
                  if s in filter_species:
                    if remove_reaction_missing_species:
                      model.removeReaction (n)
                      raise BreakLoops
                    reaction.removeModifier (sn)
            
            if filter_genes is not None:
              genes = self._get_genes (reaction)
              self.__logger.critical("current genes string: " + genes + " - reaction: " + reaction.getId ())
              #self._extract_genes_from_sbml_notes (reaction.getNotesString(), reaction.getId ())
              current_genes = self._unfold_complex_expression(self._parse_expression(genes))
              if len(current_genes) < 1:
                self.__logger.critical("did not find genes in reaction " + reaction.getId ())
                raise NotImplementedError ("did not find genes in reaction " + reaction.getId ())
              
              # if len(current_genes) == 1 and current_genes[0] == reaction.getId ():
              
              final_genes = []
              for g in current_genes:
                if g not in filter_genes:
                  final_genes.append (g)
              
              if (remove_reaction_genes_removed and len (final_genes) < 1):
                model.removeReaction (n)
                continue
              
              if (len (final_genes) != len (current_genes)):
                self._overwrite_genes_in_sbml_notes (genes, "(" + ("".join (final_genes)) + ")", reaction)
                #self.__logger.debug ("reaction " + reaction.getId() + " found gene " + g)
                # if g not in r.genes:
                  # r.genes.append (g)
            
            if reaction.getNumReactants() + reaction.getNumModifiers() + reaction.getNumProducts() == 0:
              model.removeReaction (n)
        except BreakLoops:
          pass
      
      # self.__logger.critical('filter species:')
      # self.__logger.critical(filter_species)
      # if filter_species is not None:
        # self.__logger.critical('filter species!')
        # for n in range (model.getNumSpecies() - 1, -1, -1):
          # s = model.getSpecies (n)
          # self.__logger.critical('remove species? ' +  s.getId ())
          # if s.getId () in filter_species:
            # self.__logger.critical('remove species ' +  s.getId ())
            # self.__logger.critical(model.removeSpecies (s.getId ()))
      
      return sbml
      
    def _get_genes (self, reaction):
        rfbc = reaction.getPlugin ("fbc")
        if rfbc is not None:
            gpa = rfbc.getGeneProductAssociation()
            if gpa is not None:
                return gpa.getAssociation().toInfix()
            else:
                self.__logger.debug('no association: ' + reaction.getId ())
        else:
            self.__logger.debug('no fbc: ' + reaction.getId ())
        
        return self._extract_genes_from_sbml_notes (reaction.getNotesString(), reaction.getId ())
        
        
    
    def extract_network_from_sbml (self, sbml):
      """Extract the Network from an SBML model
      
      Parameters:
      -----------
      
      sbml_file: path to the SBML file
      """
      if sbml.getNumErrors() > 0:
        raise IOError ("model seems to be invalid")
      model = sbml.getModel()
      
      network = Network ()
      species = {}
      
      for n in range (0, model.getNumSpecies()):
        s = model.getSpecies (n)
        species[s.getId ()] = Species (s.getName (), s.getId ())
        network.add_species (species[s.getId ()])
        
      for n in range (0, model.getNumReactions()):
        reaction = model.getReaction(n)
        # TODO: reversible?
        r = Reaction (reaction.getId (), reaction.getName ())
        genes = self._get_genes (reaction)
        self.__logger.debug("current genes string: " + genes + " - reaction: " + reaction.getId ())
        current_genes = self._unfold_complex_expression(self._parse_expression(self._get_genes (reaction)))
      
        if len(current_genes) < 1:
          self.__logger.debug("did not find genes in reaction " + reaction.getId ())
          raise NotImplementedError ("did not find genes in reaction " + reaction.getId ())
    
        for g in current_genes:
          #self.__logger.debug ("reaction " + reaction.getId() + " found gene " + g)
          if g not in r.genes:
            r.genes.append (g)
            
        for sn in range (0, reaction.getNumReactants()):
          s = reaction.getReactant(sn).getSpecies()
          r.add_input (species[s])
            
        for sn in range (0, reaction.getNumProducts()):
          s = reaction.getProduct(sn).getSpecies()
          r.add_output (species[s])
        
        network.add_reaction (r)
        
      return network


