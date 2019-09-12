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


from modules.gemtractor.gemtractor import GEMtractor
from django.test import TestCase
import os
import tempfile
import pyparsing as pp
from modules.gemtractor.utils import InvalidGeneExpression
from xml.dom import minidom

class GEMtractorTests (TestCase):
  def test_sbml_filter1 (self):
        f = "test/gene-filter-example.xml"
        self.assertTrue (os.path.isfile(f), msg="cannot find test file")
        
        gemtractor = GEMtractor (f)
        sbml = gemtractor.get_sbml (filter_species = ["a"], filter_genes = ["y"])
        self.assertEqual (sbml.getNumErrors(), 0)
        
        self.assertTrue ("modelname" in sbml.getModel ().getName ()) 
        self.assertTrue ("modelid" in sbml.getModel ().getId ())
        
        net = gemtractor.extract_network_from_sbml (sbml)
        self.assertEqual (len (net.species), 3)
        self.assertEqual (len (net.reactions), 3)
        self.assertEqual (len (net.genenet), 0)
        
        
        self.assertEqual (len(net.reactions["r1"].consumed), 0)
        self.assertEqual (len(net.reactions["r1"].produced), 1)
        self.assertEqual (len(net.reactions["r1"].genes), 6)
        
        self.assertEqual (len(net.reactions["r2"].consumed), 1)
        self.assertEqual (len(net.reactions["r2"].produced), 1)
        self.assertEqual (len(net.reactions["r2"].genes), 1)
        
        
        
        
  def test_sbml_filter3 (self):
        f = "test/gene-filter-example-3.xml"
        self.assertTrue (os.path.isfile(f), msg="cannot find test file")
        
        gemtractor = GEMtractor (f)
        sbml = gemtractor.get_sbml (filter_species = ["a"], filter_genes = ["a"])
        self.assertEqual (sbml.getNumErrors(), 0)
        
        self.assertTrue ("modelname" in sbml.getModel ().getName ()) 
        self.assertTrue ("modelid" in sbml.getModel ().getId ())
        
        net = gemtractor.extract_network_from_sbml (sbml)
        self.assertEqual (len (net.species), 3)
        self.assertEqual (len (net.reactions), 3)
        self.assertEqual (len (net.genenet), 0)
        
        
        self.assertEqual (len(net.reactions["r1"].consumed), 0)
        self.assertEqual (len(net.reactions["r1"].produced), 1)
        self.assertEqual (len(net.reactions["r1"].genes), 5)
        
        self.assertEqual (len(net.reactions["r2"].consumed), 1)
        self.assertEqual (len(net.reactions["r2"].produced), 1)
        self.assertEqual (len(net.reactions["r2"].genes), 4)
        
        
        
  def test_sbml_filter2 (self):
        f = "test/gene-filter-example-2.xml"
        self.assertTrue (os.path.isfile(f), msg="cannot find test file")
        
        gemtractor = GEMtractor (f)
        sbml = gemtractor.get_sbml (filter_species = ["a"], filter_genes = ["a"])
        self.assertEqual (sbml.getNumErrors(), 0)
        
        self.assertTrue ("modelid" in sbml.getModel ().getName ()) 
        self.assertTrue ("modelid" in sbml.getModel ().getId ())
        
        net = gemtractor.extract_network_from_sbml (sbml)
        self.assertEqual (len (net.species), 3)
        self.assertEqual (len (net.reactions), 3)
        self.assertEqual (len (net.genenet), 0)
        
        
        self.assertEqual (len(net.reactions["r1"].consumed), 0)
        self.assertEqual (len(net.reactions["r1"].produced), 1)
        self.assertEqual (len(net.reactions["r1"].genes), 5)
        
        self.assertEqual (len(net.reactions["r2"].consumed), 1)
        self.assertEqual (len(net.reactions["r2"].produced), 1)
        self.assertEqual (len(net.reactions["r2"].genes), 2)
        
      
      
      
        gemtractor = GEMtractor (f)
        sbml = gemtractor.get_sbml (filter_species = ["b"], remove_reaction_missing_species = False)
        self.assertEqual (sbml.getNumErrors(), 0)
        
        net = gemtractor.extract_network_from_sbml (sbml)
        self.assertEqual (len (net.species), 3)
        self.assertEqual (len (net.reactions), 3)
        self.assertEqual (len (net.genenet), 0)
        
      
      
      
        gemtractor = GEMtractor (f)
        sbml = gemtractor.get_sbml (filter_species = ["a", "b"])
        self.assertEqual (sbml.getNumErrors(), 0)
        
        net = gemtractor.extract_network_from_sbml (sbml)
        self.assertEqual (len (net.species), 3)
        self.assertEqual (len (net.reactions), 2)
        self.assertEqual (len (net.genenet), 0)
        
      
      
      
        gemtractor = GEMtractor (f)
        sbml = gemtractor.get_sbml (filter_species = ["a", "c"], remove_reaction_missing_species = True)
        self.assertEqual (sbml.getNumErrors(), 0)
        
        net = gemtractor.extract_network_from_sbml (sbml)
        self.assertEqual (len (net.species), 3)
        self.assertEqual (len (net.reactions), 2)
        self.assertEqual (len (net.genenet), 0)
        
      
      
      
        gemtractor = GEMtractor (f)
        sbml = gemtractor.get_sbml (filter_species = ["a", "c"], filter_reactions = ["r3"], remove_reaction_missing_species = True)
        self.assertEqual (sbml.getNumErrors(), 0)
        
        net = gemtractor.extract_network_from_sbml (sbml)
        self.assertEqual (len (net.species), 3)
        self.assertEqual (len (net.reactions), 1)
        self.assertEqual (len (net.genenet), 0)
        
      
        
        
        gemtractor = GEMtractor (f)
        sbml = gemtractor.get_sbml (filter_genes = ["x", "y"])
        self.assertEqual (sbml.getNumErrors(), 0)
        
        net = gemtractor.extract_network_from_sbml (sbml)
        self.assertEqual (len (net.species), 3)
        self.assertEqual (len (net.reactions), 1)
        self.assertEqual (len (net.genenet), 0)
        
      
        
        
        gemtractor = GEMtractor (f)
        sbml = gemtractor.get_sbml (filter_genes = ["x", "y"], remove_reaction_genes_removed = False)
        self.assertEqual (sbml.getNumErrors(), 0)
        
        net = gemtractor.extract_network_from_sbml (sbml)
        self.assertEqual (len (net.species), 3)
        self.assertEqual (len (net.reactions), 3)
        self.assertEqual (len (net.genenet), 0)
        
        
  def test_sbml (self):
        f = "test/gene-filter-example.xml"
        self.assertTrue (os.path.isfile(f), msg="cannot find test file")
        
        gemtractor = GEMtractor (f)
        sbml = gemtractor.get_sbml ()
        self.assertEqual (sbml.getNumErrors(), 0)
        
        net = gemtractor.extract_network_from_sbml (sbml)
        self.assertEqual (len (net.species), 3)
        self.assertEqual (len (net.reactions), 3)
        self.assertEqual (len (net.genenet), 0)
        
        net.calc_genenet ()
        self.assertEqual (len (net.species), 3)
        self.assertEqual (len (net.reactions), 3)
        self.assertEqual (len (net.genenet), 7)
        
        self.assertEqual (len(net.species["a"].occurence), 1)
        self.assertEqual (len(net.species["b"].occurence), 2)
        self.assertEqual (len(net.species["c"].occurence), 2)
        
        self.assertEqual (len(net.reactions["r1"].consumed), 1)
        self.assertEqual (len(net.reactions["r1"].produced), 1)
        self.assertEqual (len(net.reactions["r1"].genes), 6)
        
        self.assertEqual (len(net.reactions["r2"].consumed), 1)
        self.assertEqual (len(net.reactions["r2"].produced), 1)
        self.assertEqual (len(net.reactions["r2"].genes), 2)
        
        ns = net.serialize ()
        self.assertEqual (len (net.species), len (ns["species"]))
        self.assertEqual (len (net.reactions), len (ns["reactions"]))
        self.assertEqual (len (net.genenet), len (ns["genenet"]))
        self.assertEqual (len (net.species), 3)
        self.assertEqual (len (net.reactions), 3)
        self.assertEqual (len (net.genenet), 7)
        
        links_in_rn = 0
        for r in net.reactions:
              links_in_rn += len (net.reactions[r].consumed) + len (net.reactions[r].produced)
        
        tf = tempfile.NamedTemporaryFile()
        
        # test outputs
        net.export_rn_dot (tf.name)
        with open (tf.name, 'r') as r:
              c = r.read().replace('\n', '')
              self.assertEqual (c.count ("label="), len (ns["species"]) + len (ns["reactions"]))
              self.assertEqual (c.count (" -> "), links_in_rn)
        
        net.export_rn_gml (tf.name)
        with open (tf.name, 'r') as r:
              c = r.read().replace('\n', '')
              self.assertEqual (c.count ("node ["), len (ns["species"]) + len (ns["reactions"]))
              self.assertEqual (c.count ("edge ["), links_in_rn)
        
        net.export_rn_graphml (tf.name)
        xmldoc = minidom.parse(tf.name)
        self.assertEqual (len (xmldoc.getElementsByTagName('node')), len (ns["species"]) + len (ns["reactions"]))
        with open (tf.name, 'r') as r:
              c = r.read().replace('\n', '')
              self.assertEqual (c.count ("<node "), len (ns["species"]) + len (ns["reactions"]))
              self.assertEqual (c.count (">species</data"), len (ns["species"]))
              self.assertEqual (c.count (">reaction<"), len (ns["reactions"]))
              self.assertEqual (c.count ("<edge"), links_in_rn)
        
        n_genelinks = 0
        for g in net.genenet:
              n_genelinks += len (net.genenet[g]["links"])
        
        # test enzyme network
        net.export_en_dot (tf.name)
        with open (tf.name, 'r') as r:
              c = r.read().replace('\n', '')
              self.assertEqual (c.count ("label="), len (ns["genenet"]))
              self.assertEqual (c.count (" -> "), n_genelinks)
        
        net.export_en_gml (tf.name)
        with open (tf.name, 'r') as r:
              c = r.read().replace('\n', '')
              self.assertEqual (c.count ("node ["), len (ns["genenet"]))
              self.assertEqual (c.count ("edge ["), n_genelinks)
        
        net.export_en_graphml (tf.name)
        xmldoc = minidom.parse(tf.name)
        self.assertEqual (len (xmldoc.getElementsByTagName('node')), len (ns["genenet"]))
        with open (tf.name, 'r') as r:
              c = r.read().replace('\n', '')
              self.assertEqual (c.count ("<node "), len (ns["genenet"]))
              self.assertEqual (c.count (">gene</data"), len (ns["genenet"]))
              self.assertEqual (c.count ("<edge"), n_genelinks)
        
        net.export_en_sbml (tf.name, "testid")
        gemtractor2 = GEMtractor (tf.name)
        sbml = gemtractor2.get_sbml ()
        self.assertEqual (sbml.getNumErrors(), 0)
        self.assertEqual (sbml.getModel().getNumSpecies (), len (ns["genenet"]))
        self.assertEqual (sbml.getModel().getNumReactions (), n_genelinks)
        
        
      
      
  def test_parse_expression (self):
      gemtractor = GEMtractor (None)
      
      expr = gemtractor._unfold_complex_expression (gemtractor._parse_expression ("something"))
      self.assertEqual (len (expr), 1)
      self.assertEqual (expr[0], "something")
      
      expr = gemtractor._unfold_complex_expression (gemtractor._parse_expression ("a or ((b and c) or (d and e and f)) or (g and h) or (i or j)"))
      self.assertEqual (len (expr), 6)
      self.assertEqual (expr[0], "a")
      self.assertEqual (expr[1], "b and c")
      self.assertEqual (expr[2], "d and e and f")
      self.assertEqual (expr[3], "g and h")
      self.assertEqual (expr[4], "i")
      self.assertEqual (expr[5], "j")
      
      expr = gemtractor._unfold_complex_expression (gemtractor._parse_expression ("a or (b and c)"))
      self.assertEqual (len (expr), 2)
      self.assertEqual (expr[0], "a")
      self.assertEqual (expr[1], "b and c")
      
      with self.assertRaises (InvalidGeneExpression):
        gemtractor._parse_expression ("a or a (b and c)")
        
      with self.assertRaises (NotImplementedError):
        pr = pp.ParseResults ()
        pr.append ("a")
        pr.append ("and")
        pr.append ("b")
        pr.append ("or")
        pr.append ("c")
        gemtractor._unfold_complex_expression (pr)
        
      with self.assertRaises (NotImplementedError):
        pr = pp.ParseResults ()
        pr.append ("a")
        pr.append ("b")
        gemtractor._unfold_complex_expression (pr)
      
  def test_extract_from_notes (self):
      gemtractor = GEMtractor (None)
      
      note = """
      <html xmlns="http://www.w3.org/1999/xhtml"><p>GENE_ASSOCIATION: (a or (b and c) or d or (f and g and k) or (k and a))</p><p>GENE_LIST: whatever</p><p>SUBSYSTEM: Pyruvate Metabolism</p></html>
      """
      self.assertEqual (gemtractor._extract_genes_from_sbml_notes (note, "def"), "(a or (b and c) or d or (f and g and k) or (k and a))")
      
      
      note = """
      <html xmlns="http://www.w3.org/1999/xhtml"><p>GENE_ASSOCIATION:(a or (b and c) or d or (f and g and k) or (k and a))</p><p>GENE_LIST: whatever</p><p>SUBSYSTEM: Pyruvate Metabolism</p></html>
      """
      self.assertEqual (gemtractor._extract_genes_from_sbml_notes (note, "def"), "(a or (b and c) or d or (f and g and k) or (k and a))")
      
      
      note = """
      <html xmlns="http://www.w3.org/1999/xhtml"><p>GENE_ASSOCIATION:a or b</p><p>GENEsadfsdflism</p></html>
      """
      self.assertEqual (gemtractor._extract_genes_from_sbml_notes (note, "def"), "a or b")
      
      
      note = """
      <html xmlns="http://www.w3.org/1999/xhtml"><p>GENE_ASSOCIATION:gene</p><p>GENEsadfsdflism</p></html>
      """
      self.assertEqual (gemtractor._extract_genes_from_sbml_notes (note, "def"), "gene")
      
      
      note = """
      <html xmlns="http://www.w3.org/1999/xhtml"><p>GENE_ASSOCIATION:            gene         </p><p>GENEsadfsdflism</p></html>
      """
      self.assertEqual (gemtractor._extract_genes_from_sbml_notes (note, "def"), "gene")
      
      
      note = """
      <html xmlns="http://www.w3.org/1999/xhtml"><p></p><p>GENEsadfsdflism</p></html>
      """
      self.assertEqual (gemtractor._extract_genes_from_sbml_notes (note, "def"), "def")
      
      
  def test_implode_genes (self):
      genes = ['a', 'b and c', 'sdkflj alskd2345 34lk5 w34knflk324']
      
      gemtractor = GEMtractor (None)
      self.assertEqual ("(a) or (b and c) or (sdkflj alskd2345 34lk5 w34knflk324)", gemtractor._implode_genes (genes))
