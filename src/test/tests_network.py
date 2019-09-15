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


from modules.gemtractor.network import Species, Reaction, Network, Gene, GeneComplex
from django.test import TestCase

# there are also many tests in EnalyzerTests

class NetworkTests (TestCase):
  def test_network (self):
    net = Network ()
    ns = net.serialize ()
    self.assertEqual (len (ns), 4, msg="expected 4 items in serialised network")
    
  
  def test_species_serialisation (self):
    s = Species ("someid", "somename")
    ss = s.serialize ()
    self.assertEqual (len (ss), 3, msg="expected 3 items in serialised species")
    self.assertEqual (ss["name"], "somename", msg="unexpected species name")
    self.assertEqual (ss["id"], "someid", msg="unexpected species id")
    self.assertEqual (len (ss["occ"]), 0, msg="new species already occurred somewhere?")
    
    s.name = s.name + "2"
    s.genes_for_consumption["g"].add ("test")
    s.genes_for_consumption["g"].add ("test")
    s.genes_for_consumption["g"].add ("test2")
    s.occurence.append ("test2")
    
    ss2 = s.serialize ()
    self.assertEqual (len (ss2), 3, msg="expected 3 items in serialised species 2")
    self.assertEqual (ss["name"] + "2", ss2["name"], msg="unexpected species name")
    self.assertEqual (ss["id"], ss2["id"], msg="unexpected species id")
    self.assertEqual (len (ss2["occ"]), 1, msg="new species already occurred somewhere?")
    self.assertEqual (len (s.genes_for_consumption["g"]), 2, msg="is consumtion a set?")
    self.assertEqual (len (s.genes_for_production["g"]), 0, msg="production changed unexpectedly")
    self.assertEqual (len (s.genes_for_consumption["gc"]), 0, msg="consumtion changed unexpectedly")
    self.assertEqual (len (s.genes_for_production["gc"]), 0, msg="production changed unexpectedly")
    
    s.genes_for_production["g"].add ("test")
    s.genes_for_production["g"].add ("test")
    s.genes_for_production["g"].add ("test2")
    
    self.assertEqual (len (s.genes_for_consumption["g"]), 2, msg="consumption changed unexpectedly")
    self.assertEqual (len (s.genes_for_production["g"]), 2, msg="is production a set?")
    self.assertEqual (len (s.genes_for_consumption["gc"]), 0, msg="consumtion changed unexpectedly")
    self.assertEqual (len (s.genes_for_production["gc"]), 0, msg="production changed unexpectedly")
    
    
    
    s.genes_for_consumption["gc"].add ("test")
    s.genes_for_consumption["gc"].add ("test")
    s.genes_for_consumption["gc"].add ("test2")
    
    self.assertEqual (len (s.genes_for_consumption["g"]), 2, msg="consumtion changed unexpectedly")
    self.assertEqual (len (s.genes_for_production["g"]), 2, msg="production changed unexpectedly")
    self.assertEqual (len (s.genes_for_consumption["gc"]), 2, msg="is consumtion a set?")
    self.assertEqual (len (s.genes_for_production["gc"]), 0, msg="production changed unexpectedly")
    
    s.genes_for_production["gc"].add ("test")
    s.genes_for_production["gc"].add ("test")
    s.genes_for_production["gc"].add ("test2")
    
    self.assertEqual (len (s.genes_for_consumption["g"]), 2, msg="consumption changed unexpectedly")
    self.assertEqual (len (s.genes_for_production["g"]), 2, msg="production changed unexpectedly")
    self.assertEqual (len (s.genes_for_consumption["gc"]), 2, msg="consumtion changed unexpectedly")
    self.assertEqual (len (s.genes_for_production["gc"]), 2, msg="is production a set?")
  
  def test_gene_serialisation (self):
    g = Gene ("testgene")
    gs1 = g.serialize ()
    self.assertEqual (len (gs1), 3, msg="expected 3 items in serialised gene")
    self.assertEqual (gs1["id"], "testgene", msg="unexpected gene id")
    self.assertEqual (len (gs1["reactions"]), 0, msg="unexpected number of reactions")
    self.assertEqual (len (gs1["cplx"]), 0, msg="unexpected number of complexes")
    
    g.reactions.append ("r1")
    g.reactions.append ("r2")
    
    gs1 = g.serialize ()
    self.assertEqual (len (gs1), 3, msg="expected 3 items in serialised gene")
    self.assertEqual (gs1["id"], "testgene", msg="unexpected gene id")
    self.assertEqual (len (gs1["reactions"]), 2, msg="unexpected number of reactions")
    self.assertEqual (len (gs1["cplx"]), 0, msg="unexpected number of complexes")
    
    
  
  def test_reaction_serialisation (self):
    r = Reaction ("id", "somename")
    rs1 = r.serialize (None, None, None)
    
    self.assertEqual (len (rs1), 7, msg="expected 7 items in serialised reaction")
    self.assertEqual (rs1["name"], "somename", msg="unexpected reaction name")
    self.assertEqual (rs1["id"], "id", msg="unexpected reaction id")
    self.assertTrue (rs1["rev"], msg="reaction should be reversible by default")
    self.assertEqual (len (rs1["cons"]), 0)
    self.assertEqual (len (rs1["prod"]), 0)
    self.assertEqual (len (rs1["genes"]), 0)
    self.assertEqual (len (rs1["genec"]), 0)
    
    s1 = Species ("someid", "somename")
    s2 = Species ("someid2", "somename2")
    mapper = {"someid": 0, "someid2": 1}
    
    r.add_input (s1)
    rs1 = r.serialize (mapper,mapper,mapper)
    
    self.assertEqual (len (rs1), 7, msg="expected 6 items in serialised reaction")
    self.assertEqual (rs1["name"], "somename", msg="unexpected reaction name")
    self.assertEqual (rs1["id"], "id", msg="unexpected reaction id")
    self.assertTrue (rs1["rev"], msg="reaction should be reversible by default")
    self.assertEqual (len (rs1["cons"]), 1)
    self.assertEqual (rs1["cons"][0], mapper[s1.identifier])
    self.assertEqual (len (rs1["prod"]), 0)
    self.assertEqual (len (rs1["genes"]), 0)
    self.assertEqual (len (rs1["genec"]), 0)
    
    self.assertEqual (len (s1.occurence), 1)
    self.assertEqual (len (s2.occurence), 0)
    
    r.add_output (s1)
    rs1 = r.serialize (mapper,mapper,mapper)
    
    self.assertEqual (len (rs1), 7, msg="expected 7 items in serialised reaction")
    self.assertEqual (rs1["name"], "somename", msg="unexpected reaction name")
    self.assertEqual (rs1["id"], "id", msg="unexpected reaction id")
    self.assertTrue (rs1["rev"], msg="reaction should be reversible by default")
    self.assertEqual (len (rs1["cons"]), 1)
    self.assertEqual (rs1["cons"][0], mapper[s1.identifier])
    self.assertEqual (len (rs1["prod"]), 1)
    self.assertEqual (rs1["prod"][0], mapper[s1.identifier])
    self.assertEqual (len (rs1["genes"]), 0)
    self.assertEqual (len (rs1["genec"]), 0)
    
    self.assertEqual (len (s1.occurence), 2)
    self.assertEqual (len (s2.occurence), 0)
    
    r.add_output (s2)
    r.reversible = False
    rs1 = r.serialize (mapper,mapper,mapper)
    
    self.assertEqual (len (rs1), 7, msg="expected 7 items in serialised reaction")
    self.assertEqual (rs1["name"], "somename", msg="unexpected reaction name")
    self.assertEqual (rs1["id"], "id", msg="unexpected reaction id")
    self.assertFalse (rs1["rev"], msg="reaction should not be reversible")
    self.assertEqual (len (rs1["cons"]), 1)
    self.assertEqual (rs1["cons"][0], mapper[s1.identifier])
    self.assertEqual (len (rs1["prod"]), 2)
    self.assertEqual (rs1["prod"][0], mapper[s1.identifier])
    self.assertEqual (rs1["prod"][1], mapper[s2.identifier])
    self.assertEqual (len (rs1["genes"]), 0)
    self.assertEqual (len (rs1["genec"]), 0)
    
    self.assertEqual (len (s1.occurence), 2)
    self.assertEqual (len (s2.occurence), 1)
    
    
    
    
