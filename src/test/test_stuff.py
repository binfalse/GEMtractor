
from django.test import TestCase
from django.conf import settings

# ~ import logging
# logging.getLogger(__name__).debug("---->>>>> " + str(j))


class EnalyzerTests (TestCase):
  def test_key (self):
    self.assertFalse (settings.SECRET_KEY == "!6qdx@dba$w9uh(6efjcnm_!gblg9i5_d^r&#8btxo=0na$b&)")
  def test_debug (self):
    self.assertFalse (settings.DEBUG)
  def test_caches (self):
    self.assertFalse (settings.CACHE_BIOMODELS > settings.CACHE_BIOMODELS_MODEL)
    self.assertFalse (settings.CACHE_BIGG > settings.CACHE_BIGG_MODEL)
