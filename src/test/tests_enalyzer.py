
from modules.enalyzer_utils.enalyzer import Enalyzer
from django.test import TestCase
import os
import tempfile

class EnalyzerTests (TestCase):
  def test_implode_genes (self):
      genes = ['a', 'b and c', 'sdkflj alskd2345 34lk5 w34knflk324']
      
      enalyzer = Enalyzer ()
      self.assertEqual ("(a) or (b and c) or (sdkflj alskd2345 34lk5 w34knflk324)", enalyzer._implode_genes (genes))
