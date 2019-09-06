
from modules.enalyzer_utils.constants import Constants
from django.test import TestCase
import os
import tempfile

class ConstantsTests (TestCase):
  def test_constants (self):
    # does that make sense at all?
    assert isinstance (Constants.SESSION_MODEL_ID, str)
