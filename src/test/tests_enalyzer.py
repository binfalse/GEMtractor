
from modules.enalyzer_utils.enalyzer import Enalyzer
from django.test import TestCase
import os
import tempfile
import pyparsing as pp
from modules.enalyzer_utils.utils import BreakLoops, InvalidGeneExpression, Utils
from xml.dom import minidom

class EnalyzerTests (TestCase):
  def test_sbml (self):
        f = "test/gene-filter-example.xml"
        self.assertTrue (os.path.isfile(f), msg="cannot find test file")
        
        enalyzer = Enalyzer (f)
        sbml = enalyzer.get_sbml ()
        self.assertEqual (sbml.getNumErrors(), 0)
        
        net = enalyzer.extract_network_from_sbml (sbml)
        self.assertEqual (len (net.species), 3)
        self.assertEqual (len (net.reactions), 2)
        self.assertEqual (len (net.genenet), 0)
        
        net.calc_genenet ()
        self.assertEqual (len (net.species), 3)
        self.assertEqual (len (net.reactions), 2)
        self.assertEqual (len (net.genenet), 7)
        
        self.assertEqual (len(net.species["a"].occurence), 1)
        self.assertEqual (len(net.species["b"].occurence), 2)
        self.assertEqual (len(net.species["c"].occurence), 1)
        self.assertEqual (len(net.species["c"].occurence), 1)
        
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
        self.assertEqual (len (net.reactions), 2)
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
        enalyzer2 = Enalyzer (tf.name)
        sbml = enalyzer2.get_sbml ()
        self.assertEqual (sbml.getNumErrors(), 0)
        self.assertEqual (sbml.getModel().getNumSpecies (), len (ns["genenet"]))
        self.assertEqual (sbml.getModel().getNumReactions (), n_genelinks)
        
        
      
      
  def test_parse_expression (self):
      enalyzer = Enalyzer (None)
      
      expr = enalyzer._unfold_complex_expression (enalyzer._parse_expression ("something"))
      self.assertEqual (len (expr), 1)
      self.assertEqual (expr[0], "something")
      
      expr = enalyzer._unfold_complex_expression (enalyzer._parse_expression ("a or ((b and c) or (d and e and f)) or (g and h) or (i or j)"))
      self.assertEqual (len (expr), 6)
      self.assertEqual (expr[0], "a")
      self.assertEqual (expr[1], "b and c")
      self.assertEqual (expr[2], "d and e and f")
      self.assertEqual (expr[3], "g and h")
      self.assertEqual (expr[4], "i")
      self.assertEqual (expr[5], "j")
      
      expr = enalyzer._unfold_complex_expression (enalyzer._parse_expression ("a or (b and c)"))
      self.assertEqual (len (expr), 2)
      self.assertEqual (expr[0], "a")
      self.assertEqual (expr[1], "b and c")
      
      with self.assertRaises (InvalidGeneExpression):
        enalyzer._parse_expression ("a or a (b and c)")
        
      with self.assertRaises (NotImplementedError):
        pr = pp.ParseResults ()
        pr.append ("a")
        pr.append ("and")
        pr.append ("b")
        pr.append ("or")
        pr.append ("c")
        enalyzer._unfold_complex_expression (pr)
        
      with self.assertRaises (NotImplementedError):
        pr = pp.ParseResults ()
        pr.append ("a")
        pr.append ("b")
        enalyzer._unfold_complex_expression (pr)
      
  def test_extract_from_notes (self):
      enalyzer = Enalyzer (None)
      
      note = """
      <html xmlns="http://www.w3.org/1999/xhtml"><p>GENE_ASSOCIATION: (a or (b and c) or d or (f and g and k) or (k and a))</p><p>GENE_LIST: whatever</p><p>SUBSYSTEM: Pyruvate Metabolism</p></html>
      """
      self.assertEqual (enalyzer._extract_genes_from_sbml_notes (note, "def"), "(a or (b and c) or d or (f and g and k) or (k and a))")
      
      
      note = """
      <html xmlns="http://www.w3.org/1999/xhtml"><p>GENE_ASSOCIATION:(a or (b and c) or d or (f and g and k) or (k and a))</p><p>GENE_LIST: whatever</p><p>SUBSYSTEM: Pyruvate Metabolism</p></html>
      """
      self.assertEqual (enalyzer._extract_genes_from_sbml_notes (note, "def"), "(a or (b and c) or d or (f and g and k) or (k and a))")
      
      
      note = """
      <html xmlns="http://www.w3.org/1999/xhtml"><p>GENE_ASSOCIATION:a or b</p><p>GENEsadfsdflism</p></html>
      """
      self.assertEqual (enalyzer._extract_genes_from_sbml_notes (note, "def"), "a or b")
      
      
      note = """
      <html xmlns="http://www.w3.org/1999/xhtml"><p>GENE_ASSOCIATION:gene</p><p>GENEsadfsdflism</p></html>
      """
      self.assertEqual (enalyzer._extract_genes_from_sbml_notes (note, "def"), "gene")
      
      
      note = """
      <html xmlns="http://www.w3.org/1999/xhtml"><p>GENE_ASSOCIATION:            gene         </p><p>GENEsadfsdflism</p></html>
      """
      self.assertEqual (enalyzer._extract_genes_from_sbml_notes (note, "def"), "gene")
      
      
      note = """
      <html xmlns="http://www.w3.org/1999/xhtml"><p></p><p>GENEsadfsdflism</p></html>
      """
      self.assertEqual (enalyzer._extract_genes_from_sbml_notes (note, "def"), "def")
      
      
  def test_implode_genes (self):
      genes = ['a', 'b and c', 'sdkflj alskd2345 34lk5 w34knflk324']
      
      enalyzer = Enalyzer (None)
      self.assertEqual ("(a) or (b and c) or (sdkflj alskd2345 34lk5 w34knflk324)", enalyzer._implode_genes (genes))
