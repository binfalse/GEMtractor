
from modules.enalyzer_utils.network import Species, Reaction
from django.test import TestCase

# there are also many tests in EnalyzerTests

class NetworkTests (TestCase):
  
  
  def test_species_serialisation (self):
      s = Species ("somename", "someid")
      ss = s.serialize ()
      self.assertEqual (len (ss), 3, msg="expected 3 items in serialised species")
      self.assertEqual (ss["name"], "somename", msg="unexpected species name")
      self.assertEqual (ss["identifier"], "someid", msg="unexpected species id")
      self.assertEqual (len (ss["occurence"]), 0, msg="new species already occurred somewhere?")
      
      s.name = s.name + "2"
      s.genes_for_consumption.add ("test")
      s.genes_for_consumption.add ("test")
      s.genes_for_consumption.add ("test2")
      s.occurence.append ("test2")
      
      ss2 = s.serialize ()
      self.assertEqual (len (ss2), 3, msg="expected 3 items in serialised species 2")
      self.assertEqual (ss["name"] + "2", ss2["name"], msg="unexpected species name")
      self.assertEqual (ss["identifier"], ss2["identifier"], msg="unexpected species id")
      self.assertEqual (len (ss2["occurence"]), 1, msg="new species already occurred somewhere?")
      self.assertEqual (len (s.genes_for_consumption), 2, msg="is consumtion a set?")
      self.assertEqual (len (s.genes_for_production), 0, msg="production changed unexpectedly")
      
      s.genes_for_production.add ("test")
      s.genes_for_production.add ("test")
      s.genes_for_production.add ("test2")
      
      self.assertEqual (len (s.genes_for_consumption), 2, msg="consumption changed unexpectedly")
      self.assertEqual (len (s.genes_for_production), 2, msg="is production a set?")
  
  def test_reaction_serialisation (self):
    r = Reaction ("id", "somename")
    rs1 = r.serialize ()
    
    self.assertEqual (len (rs1), 6, msg="expected 6 items in serialised reaction")
    self.assertEqual (rs1["name"], "somename", msg="unexpected reaction name")
    self.assertEqual (rs1["identifier"], "id", msg="unexpected reaction id")
    self.assertFalse (rs1["reversible"], msg="reaction should be reversible by default")
    self.assertEqual (len (rs1["consumed"]), 0)
    self.assertEqual (len (rs1["produced"]), 0)
    self.assertEqual (len (rs1["genes"]), 0)
    
    s1 = Species ("somename", "someid")
    s2 = Species ("somename2", "someid2")
    
    r.add_input (s1)
    
    self.assertEqual (len (rs1), 6, msg="expected 6 items in serialised reaction")
    self.assertEqual (rs1["name"], "somename", msg="unexpected reaction name")
    self.assertEqual (rs1["identifier"], "id", msg="unexpected reaction id")
    self.assertFalse (rs1["reversible"], msg="reaction should be reversible by default")
    self.assertEqual (len (rs1["consumed"]), 1)
    self.assertEqual (len (rs1["produced"]), 0)
    self.assertEqual (len (rs1["genes"]), 0)
    
    self.assertEqual (len (s1.occurence), 1)
    self.assertEqual (len (s2.occurence), 0)
    
    r.add_output (s1)
    
    self.assertEqual (len (rs1), 6, msg="expected 6 items in serialised reaction")
    self.assertEqual (rs1["name"], "somename", msg="unexpected reaction name")
    self.assertEqual (rs1["identifier"], "id", msg="unexpected reaction id")
    self.assertFalse (rs1["reversible"], msg="reaction should be reversible by default")
    self.assertEqual (len (rs1["consumed"]), 1)
    self.assertEqual (len (rs1["produced"]), 1)
    self.assertEqual (len (rs1["genes"]), 0)
    
    self.assertEqual (len (s1.occurence), 2)
    self.assertEqual (len (s2.occurence), 0)
    
    r.add_output (s2)
    
    self.assertEqual (len (rs1), 6, msg="expected 6 items in serialised reaction")
    self.assertEqual (rs1["name"], "somename", msg="unexpected reaction name")
    self.assertEqual (rs1["identifier"], "id", msg="unexpected reaction id")
    self.assertFalse (rs1["reversible"], msg="reaction should be reversible by default")
    self.assertEqual (len (rs1["consumed"]), 1)
    self.assertEqual (len (rs1["produced"]), 2)
    self.assertEqual (len (rs1["genes"]), 0)
    
    self.assertEqual (len (s1.occurence), 2)
    self.assertEqual (len (s2.occurence), 1)
    
