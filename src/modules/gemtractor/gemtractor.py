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
import math
import re

import pyparsing as pp
from libsbml import FbcAssociation_parseFbcInfixAssociation, SBMLReader

from .network.gene import Gene
from .network.genecomplex import GeneComplex
from .network.network import Network
from .utils import Utils
from .exceptions import BreakLoops, InvalidGeneExpression


class GEMtractor:
  """Main class for the GEMtractor
  
  It reads an SBML file, trims entities, and extracts the encoded network.
  
  :param sbml_file: path to the SBML file
  :type sbml_file: str
  """
  
  def __init__(self, sbml_file):
    self.__GENE_ASSOCIATION_PATTERN = re.compile(r".*GENE_ASSOCIATION:([^<]+) *<.*", re.DOTALL)
    self.__GENE_LIST_PATTERN = re.compile(r".*GENE_LIST: *([^ <][^<]*)<.*", re.DOTALL)
    self.__EXPRESSION_PARSER = self.__get_expression_parser ()
    self.__logger = logging.getLogger(__name__)
    self.__reaction_gene_map = {}
    self.__sbml_file = sbml_file
    self.__fbc_plugin = None
    self.__logger.debug("reading sbml file " + self.__sbml_file)
    self.sbml = SBMLReader().readSBML(self.__sbml_file)
    if self.sbml.getNumErrors() > 0:
      e = []
      for i in range (0, self.sbml.getNumErrors()):
        e.append (self.sbml.getError(i).getMessage())
      raise IOError ("model seems to be invalid: " + str (e))
  
  def __get_expression_parser (self):
    """
    get a parser to parse gene-association strings of reactions
    
    :return: the expression parser
    :rtype: `pyparsing:ParserElement <https://pyparsing-docs.readthedocs.io/en/latest/pyparsing.html#pyparsing.ParserElement>`_
    """
    variables = pp.Word(pp.alphanums + "_-.") 
    condition = pp.Group(variables)
    return pp.infixNotation(condition,[("and", 2, pp.opAssoc.LEFT, ),("or", 2, pp.opAssoc.LEFT, ),])


  def _parse_expression (self, expression):
    """
    parse a gene-association expression
    
    uses the expression parser from :func:`_GEMtractor__get_expression_parser`
    
    :param expression: the gene-association expression
    :type expression: str
    
    :return: the parse result
    :rtype: `pyparsing:ParseResults <https://pyparsing-docs.readthedocs.io/en/latest/pyparsing.html#pyparsing.ParseResults>`_
    """
    try:
        return self.__EXPRESSION_PARSER.parseString(expression.lower (), True)
    except pp.ParseException as e:
        raise InvalidGeneExpression ("cannot parse expression: >>" + expression + "<< -- " + getattr(e, 'message', repr(e)))

  def _unfold_complex_expression (self, parseresult):
    """
    unfold a gene-association parse result
    
    takes a parse result and unfolds it to a list of alternative gene complexes, which can catalyze a certain reaction
    
    :param parseresult: the result of the expression parser
    :type parseresult: `pyparsing:ParseResults <https://pyparsing-docs.readthedocs.io/en/latest/pyparsing.html#pyparsing.ParseResults>`_
    
    :return: the list of gene-complexes catalyzing
    :rtype: list of :class:`.network.genecomplex.GeneComplex`
    """
    if isinstance(parseresult, pp.ParseResults):
        
        if len(parseresult) == 1:
            return self._unfold_complex_expression (parseresult[0])
        
        if len(parseresult) > 1 and len(parseresult) % 2 == 1:
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
                logic = False
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
                    # ~ tmp = []
                    for a in term_combination:
                        for b in newterms:
                          a.add_genes (b)
                            # ~ tmp.append (str(a)+" and "+str (b))
                    # ~ term_combination = tmp
                else:
                    # just add them to the list as alternatives
                    term_combination += self._unfold_complex_expression (parseresult[i])
            
            return term_combination
        
        else:
            self.__logger.critical('unexpected expression: ' + str(parseresult))
            raise NotImplementedError ('unexpected expression: ' + str(parseresult))
            
    else:
        return [GeneComplex (Gene (parseresult))]


  def _extract_genes_from_sbml_notes (self, annotation, default):
    """
    extract the genes from a free-text sbml note
    
    expects the gene associations as
    
    .. code-block:: xml
    
       <p>GENE_ASSOCIATION: a and (b or c)</p>
    
    
    :param annotation: the annotation string
    :param default: the default to return if no gene-associations were found
    
    :type annotation: str
    :type default: str
    
    :return: the gene-associations
    :rtype: string
    """
    m = re.match (self.__GENE_ASSOCIATION_PATTERN, annotation)
    if m:
        g = m.group (1).strip()
        if len (g) > 0:
          return g
    return default
  
  def _overwrite_genes_in_sbml_notes (self, new_genes, reaction):
    """
    set the gene-associations for a note in an sbml reaction
    
    overwrites it, if it was set already
    
    :param new_genes: the new gene-associations
    :param reaction: the sbml reaction
    :type new_genes: str
    :type reaction: `libsbml:Reaction <http://sbml.org/Special/Software/libSBML/docs/python-api/classlibsbml_1_1_reaction.html>`_
    """
    m = re.match (self.__GENE_ASSOCIATION_PATTERN, reaction.getNotesString())
    if m:
      reaction.setNotes (reaction.getNotesString().replace (m.group (1), new_genes))
    else:
      self.__logger.debug('no gene notes to update: ' + reaction.getId ())
    
    # TODO
    # also update the GENE_LIST using __GENE_LIST_PATTERN
    # but for this we need the list of genes here (not only the logic expression)
      
  
  def get_gene_product_annotations (self, gene):
    """
    get the annotations of a gene product
    
    if the document is annotated using the `FBC package <http://sbml.org/Documents/Specifications/SBML_Level_3/Packages/fbc>`_ there is good chance we'll find more information about a gene in the gene-product's annotations
    
    :param gene: the label gene product of interest
    :type gene: str
    
    :return: the annotations of the gene-product labeled `gene` or None if there are no such annotations
    :rtype: xml str
    
    """
    if self.__fbc_plugin is not None:
      gp = self.__fbc_plugin.getGeneProductByLabel (gene)
      if gp is not None:
        return self.__fbc_plugin.getGeneProductByLabel (gene).getAnnotationString()
    return None
    
    
  def get_reaction_annotations (self, reactionid):
    """
    get the annotations of an sbml reaction
    
    :param reactionid: the identifier of the reaction in the sbml document
    :type reactionid: str
    
    :return: the annotations of that reaction
    :rtype: xml str
    """
    return self.sbml.getModel().getReaction (reactionid).getAnnotationString ()
    
   
  
  def get_sbml (self, filter_species = [], filter_reactions = [], filter_genes = [], filter_gene_complexes = [], remove_reaction_enzymes_removed = True, remove_ghost_species = False, discard_fake_enzymes = False, remove_reaction_missing_species = False, removing_enzyme_removes_complex = True):
    """ Get a filtered SBML document from the model file
    
    this parses the SBML file, applies the trimming according to the arguments, and returns the trimmed model
    
    :param filter_species: species identifiers to get rid of
    :param filter_reactions: reaction identifiers to get rid of
    :param filter_genes: enzyme identifiers to get rid of
    :param filter_gene_complexes: enzyme-complex identifiers to get rid of, every list-item should be of format: 'A + B + gene42'
    :param remove_reaction_enzymes_removed: should we remove a reaction if all it's genes were removed?
    :param remove_ghost_species: should species be removed, that do not participate in any reaction anymore - even though they might be required in other entities?
    :param discard_fake_enzymes: should fake enzymes (implicitly assumes enzymes, if no enzymes are annotated to a reaction) be removed?
    :param remove_reaction_missing_species: remove a reaction if one of the participating genes was removed?
    :param removing_enzyme_removes_complex: if an enzyme is removed, should also all enzyme complexes be removed in which it participates?
    
    :type filter_species: list of str
    :type filter_reactions: list of str
    :type filter_genes: list of str
    :type filter_gene_complexes: list of str
    :type remove_reaction_enzymes_removed: bool
    :type remove_ghost_species: bool
    :type discard_fake_enzymes: bool
    :type remove_reaction_missing_species: bool
    :type removing_enzyme_removes_complex: bool
    
    :return: the SBML document
    :rtype: `libsbml:SBMLDocument <http://sbml.org/Special/Software/libSBML/docs/python-api/classlibsbml_1_1_s_b_m_l_document.html>`_
    
    """
    self.__logger.debug("processing sbml model from " + self.__sbml_file)
    model = self.sbml.getModel()
    name = model.getName ()
    if name is None or len (name) < 1:
        name = model.getId()
    model.setId (model.getId() + "_gemtracted_ReactionNetwork")
    model.setName ("GEMtracted ReactionNetwork of " + name)
    self.__logger.info("got proper sbml model")
    
    self.__fbc_plugin = model.getPlugin ("fbc")
    
    self.__logger.debug("append a note")
    Utils.add_model_note (model, filter_species, filter_reactions, filter_genes, filter_gene_complexes, remove_reaction_enzymes_removed, remove_ghost_species, discard_fake_enzymes, remove_reaction_missing_species, removing_enzyme_removes_complex)
    
    if filter_species is None:
      filter_species = []
    if filter_reactions is None:
      filter_reactions = []
    if filter_genes is None:
      filter_genes = []
    if filter_gene_complexes is None:
      filter_gene_complexes = []
      
    
    if len(filter_species) > 0 or len(filter_reactions) > 0 or len(filter_genes) > 0 or len(filter_gene_complexes) > 0 or discard_fake_enzymes:
      try:
        #TODO dc modified?
        self.__logger.debug("filtering things")
        for n in range (model.getNumReactions () - 1, -1, -1):
          reaction = model.getReaction (n)
          if filter_reactions is not None and reaction.getId () in filter_reactions:
            model.removeReaction (n)
            continue
          
          if filter_species is not None:
            try:
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
            except BreakLoops:
              continue
          
          if filter_genes is not None:
            current_genes = self._get_genes (reaction)
            self.__logger.debug("current genes: " + self._implode_genes (current_genes) + " - reaction: " + reaction.getId ())
            
            if len(current_genes) < 1:
              self.__logger.info("did not find genes in reaction " + reaction.getId ())
              raise NotImplementedError ("did not find genes in reaction " + reaction.getId ())
            
            self.__logger.info(discard_fake_enzymes)
            if discard_fake_enzymes and len(current_genes) == 1 and "reaction_" in current_genes[0].get_id ():
              model.removeReaction (n)
              continue
            # if len(current_genes) == 1 and current_genes[0] == reaction.getId ():
            
            final_genes = []
            for g in current_genes:
              # ~ print (g.get_id())
              # ~ print (g.genes)
              if g.get_id () not in filter_genes and g.get_id () not in filter_gene_complexes and not (removing_enzyme_removes_complex and g.contains_one_of (filter_genes)):
                # ~ print (g.get_id() + " will be in model")
                final_genes.append (g)
            
            if len (final_genes) < 1:
              if remove_reaction_enzymes_removed:
                model.removeReaction (n)
                continue
              else:
                final_genes = [Gene (reaction.getId ())]
            
            # should we update the genes in the model?
            if (len (final_genes) != len (current_genes)):
              self._set_genes_in_sbml (final_genes, reaction)
            
            self.__reaction_gene_map[reaction.getId ()] = final_genes
          
          if reaction.getNumReactants() + reaction.getNumModifiers() + reaction.getNumProducts() == 0:
            model.removeReaction (n)
        
        if len(filter_species) > 0 and remove_ghost_species:
          for n in range (model.getNumSpecies () - 1, -1, -1):
            species = model.getSpecies (n)
            if species.getId () in filter_species:
              model.removeSpecies (n)
      except BreakLoops:
        pass
    
    return self.sbml
  
  def _set_genes_in_sbml (self, genes, reaction):
    """
    set the genes of a reaction in an sbml model
    
    tries to set the genes using the `FBC package <http://sbml.org/Documents/Specifications/SBML_Level_3/Packages/fbc>`_, if supported, otherwise sets the genes in the reaction's notes.
    if genes already exist the will be overwritten...
    
    :param genes: the new list of gene associations
    :param reaction: the reaction to annotate
    :type genes: list of :class:`.network.genecomplex.GeneComplex`
    :type reaction: `libsbml:Reaction <http://sbml.org/Special/Software/libSBML/docs/python-api/classlibsbml_1_1_reaction.html>`_
    """
    
    rfbc = reaction.getPlugin ("fbc")
    if rfbc is not None:
      gpa = rfbc.getGeneProductAssociation()
      if gpa is not None:
        g = self._implode_genes (genes)
        gpa.setAssociation(FbcAssociation_parseFbcInfixAssociation (g, self.__fbc_plugin))
      else:
        self.__logger.debug('no fbc to update: ' + reaction.getId ())
    
    self._overwrite_genes_in_sbml_notes (self._implode_genes (genes), reaction)
    
  
  def _implode_genes (self, genes):
    """
    implode a list of genes into a proper logical expression

    basically joins the list with `or`, making sure every item is enclosed in brackets
    
    :param genes: the list of optional genes
    :type genes: list of :class:`.network.genecomplex.GeneComplex`
    
    :return: the logical expression (genes joined using 'or')
    :rtype: str
    """
    r = "("
    for g in genes:
      r += str (g.to_sbml_string ()) + " or "
    
    return r[:-4] + ")"
  
  
  def _get_genes (self, reaction):
    """
    get the genes associated to a reaction
    
    Will cache the gene associations. If there is nothing in cache, it will run :func:`_GEMtractor__find_genes`, :func:`_parse_expression`, and  :func:`_unfold_complex_expression` to find them.
    
    :param reaction: the SBML S-Base reaction
    :type reaction: `libsbml:Reaction <http://sbml.org/Special/Software/libSBML/docs/python-api/classlibsbml_1_1_reaction.html>`_
    
    :return: list of GeneComplexes catalyzing the reaction
    :rtype: list of :class:`.network.genecomplex.GeneComplex`
    
    """
    if reaction.getId () not in self.__reaction_gene_map:
      self.__reaction_gene_map[reaction.getId ()] = self._unfold_complex_expression(self._parse_expression(self.__find_genes (reaction)))
    
    return self.__reaction_gene_map[reaction.getId ()]
    
  
  def __find_genes (self, reaction):
    """
    Look for genes associated to a reaction.
    
    Will check if there are annotations using the
    `FBC package <http://sbml.org/Documents/Specifications/SBML_Level_3/Packages/fbc>`_,
    otherwise it will evaluate the reactions' notes.
    If there are still no valid gene associations, the function assumes there is an undocumented catalyst and falls back to a gene with the reaction's identifier (prefixed with 'reaction\_').
    
    :param reaction: the SBML S-Base reaction
    :type reaction: `libsbml:Reaction <http://sbml.org/Special/Software/libSBML/docs/python-api/classlibsbml_1_1_reaction.html>`_
    
    :return: the gene associations
    :rtype: str
    """
    rfbc = reaction.getPlugin ("fbc")
    if rfbc is not None:
        gpa = rfbc.getGeneProductAssociation()
        if gpa is not None:
            return gpa.getAssociation().toInfix()
        else:
            self.__logger.debug('no association: ' + reaction.getId ())
    else:
        self.__logger.debug('no fbc: ' + reaction.getId ())
    
    return self._extract_genes_from_sbml_notes (reaction.getNotesString(), "reaction_" + reaction.getId ())
      
      
  
  def extract_network_from_sbml (self):
    """
    Extract the Network from the SBML model
    
    Will go through the SBML file and convert the (remaining) entities into our own network structure.
    
    :return: the network (after optional trimming)
    :rtype: :class:`.network.network.Network`
    
    """
    if self.sbml.getNumErrors() > 0:
      raise IOError ("model seems to be invalid")
    model = self.sbml.getModel()
    self.__logger.info ("extracting network from " + model.getId ())
    
    network = Network ()
    species = {}
    
    for n in range (0, model.getNumSpecies()):
      s = model.getSpecies (n)
      species[s.getId ()] = network.add_species (s.getId (), s.getName ())
    
    for n in range (0, model.getNumReactions()):
      if n % 100 == 0:
        self.__logger.info ("processing reaction " + str (n))
      reaction = model.getReaction(n)
      # TODO: reversible?
      #r = Reaction (reaction.getId (), reaction.getName ())
      r = network.add_reaction (reaction.getId (), reaction.getName ())
      if reaction.isSetReversible ():
        r.reversible = reaction.getReversible ()
      
      current_genes = self._get_genes (reaction)
      self.__logger.debug("current genes: " + self._implode_genes (current_genes) + " - reaction: " + reaction.getId ())
    
      if len(current_genes) < 1:
        self.__logger.debug("did not find genes in reaction " + reaction.getId ())
        raise NotImplementedError ("did not find genes in reaction " + reaction.getId ())
      
      network.add_genes (r, current_genes)
      
      for sn in range (0, reaction.getNumReactants()):
        s = reaction.getReactant(sn).getSpecies()
        r.add_input (species[s])
          
      for sn in range (0, reaction.getNumProducts()):
        s = reaction.getProduct(sn).getSpecies()
        r.add_output (species[s])
    
      
    self.__logger.info ("extracted network")
    return network
