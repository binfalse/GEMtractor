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
from modules.gemtractor.network import Gene, GeneComplex
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
        
        
        self.assertEqual (len(net.reactions["r1"].consumed), 0)
        self.assertEqual (len(net.reactions["r1"].produced), 1)
        self.assertEqual (len(net.reactions["r1"].genes), 3)
        self.assertEqual (len(net.reactions["r1"].genes), 3)
        
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
        
        
        self.assertEqual (len(net.reactions["r1"].consumed), 0)
        self.assertEqual (len(net.reactions["r1"].produced), 1)
        self.assertEqual (len(net.reactions["r1"].genes), 2)
        self.assertEqual (len(net.reactions["r1"].genec), 2)
        
        self.assertEqual (len(net.reactions["r2"].consumed), 1)
        self.assertEqual (len(net.reactions["r2"].produced), 1)
        self.assertEqual (len(net.reactions["r2"].genes), 1)
        self.assertEqual (len(net.reactions["r2"].genec), 2)
        
        
        
        
  def test_sbml_filter4 (self):
        f = "test/gene-filter-example-4.xml"
        self.assertTrue (os.path.isfile(f), msg="cannot find test file")
        
        gemtractor = GEMtractor (f)
        sbml = gemtractor.get_sbml (filter_species = ["a"], filter_genes = ["r"])
        self.assertEqual (sbml.getNumErrors(), 0)
        
        self.assertTrue ("modelname" in sbml.getModel ().getName ()) 
        self.assertTrue ("modelid" in sbml.getModel ().getId ())
        
        net = gemtractor.extract_network_from_sbml (sbml)
        self.assertEqual (len (net.species), 3)
        self.assertEqual (len (net.reactions), 3)
        
        
        self.assertEqual (len(net.reactions["r1"].consumed), 0)
        self.assertEqual (len(net.reactions["r1"].produced), 1)
        self.assertEqual (len(net.reactions["r1"].genes), 3)
        self.assertEqual (len(net.reactions["r1"].genec), 3)
        
        self.assertEqual (len(net.reactions["r2"].consumed), 1)
        self.assertEqual (len(net.reactions["r2"].produced), 1)
        self.assertEqual (len(net.reactions["r2"].genes), 2)
        self.assertEqual (len(net.reactions["r2"].genec), 3)
        
        self.assertEqual (len(net.reactions["r3"].consumed), 0)
        self.assertEqual (len(net.reactions["r3"].produced), 1)
        self.assertEqual (len(net.reactions["r3"].genes), 1)
        self.assertEqual (len(net.reactions["r3"].genec), 0)
        
        
        
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
        
        
        self.assertEqual (len(net.reactions["r1"].consumed), 0)
        self.assertEqual (len(net.reactions["r1"].produced), 1)
        self.assertEqual (len(net.reactions["r1"].genes), 2)
        self.assertEqual (len(net.reactions["r1"].genec), 2)
        
        self.assertEqual (len(net.reactions["r2"].consumed), 1)
        self.assertEqual (len(net.reactions["r2"].produced), 1)
        self.assertEqual (len(net.reactions["r1"].genes), 2)
        self.assertEqual (len(net.reactions["r1"].genec), 2)
        
      
      
      
        gemtractor = GEMtractor (f)
        sbml = gemtractor.get_sbml (filter_species = ["b"], remove_reaction_missing_species = False)
        self.assertEqual (sbml.getNumErrors(), 0)
        
        net = gemtractor.extract_network_from_sbml (sbml)
        self.assertEqual (len (net.species), 3)
        self.assertEqual (len (net.reactions), 3)
        
      
      
      
        gemtractor = GEMtractor (f)
        sbml = gemtractor.get_sbml (filter_species = ["a", "b"])
        self.assertEqual (sbml.getNumErrors(), 0)
        
        net = gemtractor.extract_network_from_sbml (sbml)
        self.assertEqual (len (net.species), 3)
        self.assertEqual (len (net.reactions), 2)
        
      
      
      
        gemtractor = GEMtractor (f)
        sbml = gemtractor.get_sbml (filter_species = ["a", "c"], remove_reaction_missing_species = True)
        self.assertEqual (sbml.getNumErrors(), 0)
        
        net = gemtractor.extract_network_from_sbml (sbml)
        self.assertEqual (len (net.species), 3)
        self.assertEqual (len (net.reactions), 2)
        
      
      
      
        gemtractor = GEMtractor (f)
        sbml = gemtractor.get_sbml (filter_species = ["a", "c"], filter_reactions = ["r3"], remove_reaction_missing_species = True)
        self.assertEqual (sbml.getNumErrors(), 0)
        
        net = gemtractor.extract_network_from_sbml (sbml)
        self.assertEqual (len (net.species), 3)
        self.assertEqual (len (net.reactions), 1)
        
      
        
        
        gemtractor = GEMtractor (f)
        sbml = gemtractor.get_sbml (filter_genes = ["x", "y"])
        self.assertEqual (sbml.getNumErrors(), 0)
        
        net = gemtractor.extract_network_from_sbml (sbml)
        self.assertEqual (len (net.species), 3)
        self.assertEqual (len (net.reactions), 1)
        
      
        
        
        gemtractor = GEMtractor (f)
        sbml = gemtractor.get_sbml (filter_genes = ["x", "y"], remove_reaction_genes_removed = False)
        self.assertEqual (sbml.getNumErrors(), 0)
        
        net = gemtractor.extract_network_from_sbml (sbml)
        self.assertEqual (len (net.species), 3)
        self.assertEqual (len (net.reactions), 3)
        
        
  def test_sbml (self):
        f = "test/gene-filter-example.xml"
        self.assertTrue (os.path.isfile(f), msg="cannot find test file")
        
        gemtractor = GEMtractor (f)
        sbml = gemtractor.get_sbml ()
        self.assertEqual (sbml.getNumErrors(), 0)
        
        net = gemtractor.extract_network_from_sbml (sbml)
        self.assertEqual (len (net.species), 3)
        self.assertEqual (len (net.reactions), 3)
        
        net.calc_genenet ()
        self.assertEqual (len (net.species), 3)
        self.assertEqual (len (net.reactions), 3)
        self.assertEqual (len (net.genes), 9)
        self.assertEqual (len (net.gene_complexes), 3)
        
        self.assertEqual (len(net.species["a"].occurence), 1)
        self.assertEqual (len(net.species["b"].occurence), 2)
        self.assertEqual (len(net.species["c"].occurence), 2)
        
        self.assertEqual (len(net.reactions["r1"].consumed), 1)
        self.assertEqual (len(net.reactions["r1"].produced), 1)
        self.assertEqual (len(net.reactions["r1"].genes), 3)
        self.assertEqual (len(net.reactions["r1"].genec), 3)
        
        self.assertEqual (len(net.reactions["r2"].consumed), 1)
        self.assertEqual (len(net.reactions["r2"].produced), 1)
        self.assertEqual (len(net.reactions["r2"].genes), 2)
        
        ns = net.serialize ()
        self.assertEqual (len (net.species), len (ns["species"]))
        self.assertEqual (len (net.reactions), len (ns["reactions"]))
        self.assertEqual (len (net.genes), len (ns["enzs"]))
        self.assertEqual (len (net.gene_complexes), len (ns["enzc"]))
        self.assertEqual (len (net.species), 3)
        self.assertEqual (len (net.reactions), 3)
        
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
        for g in net.genes:
              n_genelinks += len (net.genes[g].links["g"])
              n_genelinks += len (net.genes[g].links["gc"])
        for g in net.gene_complexes:
              n_genelinks += len (net.gene_complexes[g].links["g"])
              n_genelinks += len (net.gene_complexes[g].links["gc"])
        
        # test enzyme network
        net.export_en_dot (tf.name)
        with open (tf.name, 'r') as r:
              c = r.read().replace('\n', '')
              self.assertEqual (c.count ("label="), len (ns["enzs"]) + len(ns["enzc"]))
              self.assertEqual (c.count (" -> "), n_genelinks)
        
        net.export_en_gml (tf.name)
        with open (tf.name, 'r') as r:
              c = r.read().replace('\n', '')
              self.assertEqual (c.count ("node ["), len (ns["enzs"]) + len(ns["enzc"]))
              self.assertEqual (c.count ("edge ["), n_genelinks)
        
        net.export_en_graphml (tf.name)
        xmldoc = minidom.parse(tf.name)
        self.assertEqual (len (xmldoc.getElementsByTagName('node')), len (ns["enzs"]) + len(ns["enzc"]))
        with open (tf.name, 'r') as r:
              c = r.read().replace('\n', '')
              self.assertEqual (c.count ("<node "), len (ns["enzs"]) + len(ns["enzc"]))
              self.assertEqual (c.count (">enzyme</data"), len (ns["enzs"]))
              self.assertEqual (c.count (">enzyme_complex</data"), len(ns["enzc"]))
              self.assertEqual (c.count ("<edge"), n_genelinks)
        
        net.export_en_sbml (tf.name, gemtractor, "testid")
        gemtractor2 = GEMtractor (tf.name)
        sbml = gemtractor2.get_sbml ()
        self.assertEqual (sbml.getNumErrors(), 0)
        self.assertEqual (sbml.getModel().getNumSpecies (), len (ns["enzs"]) + len(ns["enzc"]))
        self.assertEqual (sbml.getModel().getNumReactions (), n_genelinks)
        model = sbml.getModel()
        found_x = False
        for n in range (model.getNumSpecies ()):
          s = model.getSpecies (n)
          identifier = s.getName ()
          if " + " in identifier:
            print (s.getAnnotationString ())
            self.assertTrue ("<bqbiol:hasPart>" in s.getAnnotationString ())
            self.assertEqual (len (net.gene_complexes[identifier].genes), s.getAnnotationString ().count ("<rdf:li rdf:resource="))
          elif identifier == "x":
            self.assertTrue (len (s.getAnnotationString ()) > 100)
            found_x = True
        self.assertTrue (found_x, msg="didnt find gene x")
        
      
      
  def test_parse_expression (self):
      gemtractor = GEMtractor (None)
      
      expr = gemtractor._unfold_complex_expression (gemtractor._parse_expression ("something"))
      self.assertEqual (len (expr), 1)
      self.assertEqual (len (expr[0].genes), 1)
      self.assertEqual (next(iter(expr[0].genes)).identifier, "something")
      
      expr = gemtractor._unfold_complex_expression (gemtractor._parse_expression ("a or ((b and c) or (d and e and f)) or (g and h) or (i or j)"))
      self.assertEqual (len (expr), 6)
      self.assertEqual (len (expr[0].genes), 1)
      self.assertEqual (next(iter(expr[0].genes)).identifier, "a")
      
      self.assertEqual (len (expr[1].genes), 2)
      self.assertTrue (next(iter(expr[1].genes)).identifier, "b")
      self.assertTrue (next(iter(expr[1].genes)).identifier, "c")
      
      self.assertEqual (len (expr[2].genes), 3)
      self.assertTrue (next(iter(expr[2].genes)).identifier, "d")
      self.assertTrue (next(iter(expr[3].genes)).identifier, "e")
      self.assertTrue (next(iter(expr[3].genes)).identifier, "f")
      
      self.assertEqual (len (expr[3].genes), 2)
      self.assertTrue (next(iter(expr[3].genes)).identifier, "g")
      self.assertTrue (next(iter(expr[3].genes)).identifier, "h")
      
      self.assertEqual (len (expr[4].genes), 1)
      self.assertEqual (next(iter(expr[4].genes)).identifier, "i")
      
      self.assertEqual (len (expr[5].genes), 1)
      self.assertEqual (next(iter(expr[5].genes)).identifier, "j")
      
      
      
      expr = gemtractor._unfold_complex_expression (gemtractor._parse_expression ("a or (b and c)"))
      self.assertEqual (len (expr), 2)
      self.assertEqual (len (expr[0].genes), 1)
      self.assertEqual (next(iter(expr[0].genes)).identifier, "a")
      
      self.assertEqual (len (expr[1].genes), 2)
      self.assertTrue (next(iter(expr[1].genes)).identifier, "b")
      self.assertTrue (next(iter(expr[1].genes)).identifier, "c")
      
      
      
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
      genes = [Gene ('a')]
      genes.append (GeneComplex (Gene ('x')))
      
      gc = GeneComplex ()
      gc.add_gene (Gene ("b"))
      gc.add_gene (Gene ("c"))
      genes.append (gc)
      
      
      genes.append (Gene ('sdkflj alskd2345 34lk5 w34knflk324'))
      
      gemtractor = GEMtractor (None)
      self.assertEqual ("((a) or (x) or (b and c) or (sdkflj alskd2345 34lk5 w34knflk324))", gemtractor._implode_genes (genes))
