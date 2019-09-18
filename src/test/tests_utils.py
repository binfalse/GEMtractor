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


from modules.gemtractor.utils import Utils
from django.test import TestCase
import os
import tempfile
from libsbml import SBMLReader
import re

class UtilsTests (TestCase):
  __regex_species_section_notes = re.compile (r"Filter Species:[^:]*(<ul>[^:]*</ul>)", re.DOTALL)
  __regex_species_notes = re.compile (r"<li>([^<]+)</li>", re.DOTALL)
  
  __regex_reactions_section_notes = re.compile (r"Filter Reactions:[^:]*(<ul>[^:]*</ul>)", re.DOTALL)
  __regex_reactions_notes = re.compile (r"<li>([^<]+)</li>", re.DOTALL)
  
  __regex_genes_section_notes = re.compile (r"Filter Enzymes:[^:]*(<ul>[^:]*</ul>)", re.DOTALL)
  __regex_genes_notes = re.compile (r"<li>([^<]+)</li>", re.DOTALL)
  
  __regex_gene_complexes_section_notes = re.compile (r"Filter Enzyme Complexes:[^:]*(<ul>[^:]*</ul>)", re.DOTALL)
  __regex_gene_complexes_notes = re.compile (r"<li>([^<]+)</li>", re.DOTALL)
  
  __regex_reaction_genes = re.compile (r"enzymes are removed:\\s*(\w)", re.DOTALL)
  __regex_reaction_species = re.compile (r"missing a species:\\s*(\w)", re.DOTALL)
  
  
  def test_byte_conversion (self):
    self.assertEqual ("1 Byte", Utils.human_readable_bytes (1))
    self.assertEqual ("0 Bytes", Utils.human_readable_bytes (0))
    self.assertEqual ("517 Bytes", Utils.human_readable_bytes (517))
    self.assertEqual ("1.0 KB", Utils.human_readable_bytes (1024))
    self.assertEqual ("1.1 KB", Utils.human_readable_bytes (1099))
    self.assertEqual ("2.2 MB", Utils.human_readable_bytes (2314897))
    self.assertEqual ("2.2 GB", Utils.human_readable_bytes (2314897000))
    self.assertEqual ("2.1 TB", Utils.human_readable_bytes (2314897000000))
    self.assertEqual ("2.1 PB", Utils.human_readable_bytes (2314897000000000))

  def test_create_dir (self):
    dd = tempfile.TemporaryDirectory()
    d = dd.name
    self.assertTrue(os.path.isdir(d), msg="tempfile didn't create temp directory!??")
    os.rmdir (d)
    self.assertFalse(os.path.isdir(d), msg="we weren't able to remove the temp directory during tests")
    Utils._create_dir (d)
    self.assertTrue(os.path.isdir(d), msg="Utils was not able to create a creatable directory")
    Utils._create_dir (d)
    self.assertTrue(os.path.isdir(d), msg="Utils was not able to create an existing directory")
    
    # make sure the user cannot create a dir in /
    self.assertTrue(os.geteuid() != 0, msg="you must not execute the tests as root user!")
    with self.assertRaises (PermissionError):
        Utils._create_dir ("/PYTHON_SHOULD_FAIL")
    
    self.assertTrue(os.path.isdir(d), msg="suddenly the directory is lost!?")
    
  def __get_sbml_model (self):
    sbml = SBMLReader().readSBML("test/gene-filter-example.xml")
    self.assertTrue (sbml.getNumErrors() == 0)
    return sbml.getModel()
    
  def __test_model_notes (self, model, filter_species, filter_reactions, filter_enzymes, filter_enzyme_complexes, remove_reaction_enzymes_removed, remove_reaction_missing_species):
    Utils.add_model_note (model, filter_species, filter_reactions, filter_enzymes, filter_enzyme_complexes, remove_reaction_enzymes_removed, remove_reaction_missing_species)
    notes = model.getNotesString ()
    
    if filter_species is not None:
      section = re.search (UtilsTests.__regex_species_section_notes, notes)
      self.assertTrue (section is not None)
      snotes = re.findall (UtilsTests.__regex_species_notes, section.group(1))
      self.assertEqual (len (snotes), len (filter_species))
      for n in snotes:
        self.assertTrue (n in filter_species)
      for n in filter_species:
        self.assertTrue (n in snotes)
    
    if filter_reactions is not None:
      section = re.search (UtilsTests.__regex_reactions_section_notes, notes)
      self.assertTrue (section is not None)
      snotes = re.findall (UtilsTests.__regex_reactions_notes, section.group(1))
      self.assertEqual (len (snotes), len (filter_reactions))
      for n in snotes:
        self.assertTrue (n in filter_reactions)
      for n in filter_reactions:
        self.assertTrue (n in snotes)
    
    if filter_enzymes is not None:
      section = re.search (UtilsTests.__regex_genes_section_notes, notes)
      self.assertTrue (section is not None)
      snotes = re.findall (UtilsTests.__regex_genes_notes, section.group(1))
      self.assertEqual (len (snotes), len (filter_enzymes))
      for n in snotes:
        self.assertTrue (n in filter_enzymes)
      for n in filter_enzymes:
        self.assertTrue (n in snotes)
    
    if filter_enzyme_complexes is not None:
      section = re.search (UtilsTests.__regex_gene_complexes_section_notes, notes)
      self.assertTrue (section is not None)
      snotes = re.findall (UtilsTests.__regex_gene_complexes_notes, section.group(1))
      self.assertEqual (len (snotes), len (filter_enzyme_complexes))
      for n in snotes:
        self.assertTrue (n in filter_enzyme_complexes)
      for n in filter_enzyme_complexes:
        self.assertTrue (n in snotes)
    
    self.assertTrue ("enzymes are removed: " + str (remove_reaction_enzymes_removed) in notes)
    self.assertTrue ("missing a species: " + str (remove_reaction_missing_species) in notes)
    
    
  
  def test_sbml_notes (self):
    self.__test_model_notes (self.__get_sbml_model (), ["S1", "S2"], ["R1", "R2"], ["G1, G2", "G3"], ["COMPLX1", "COMPLX2"], True, False)
    self.__test_model_notes (self.__get_sbml_model (), ["S1", "S2"], None, None, None, True, False)
    self.__test_model_notes (self.__get_sbml_model (), None, None, ["S1", "S2"], None, True, False)
    self.__test_model_notes (self.__get_sbml_model (), None, None, None, ["S1", "S2"], False, True)
