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

from django.test import TestCase
from django.conf import settings

# ~ import logging
# logging.getLogger(__name__).debug("---->>>>> " + str(j))


class StuffTests (TestCase):
  def test_key (self):
    self.assertFalse (settings.SECRET_KEY == "!6qdx@dba$w9uh(6efjcnm_!gblg9i5_d^r&#8btxo=0na$b&)")
  def test_debug (self):
    self.assertFalse (settings.DEBUG)
  def test_caches (self):
    self.assertFalse (settings.CACHE_BIOMODELS > settings.CACHE_BIOMODELS_MODEL)
    self.assertFalse (settings.CACHE_BIGG > settings.CACHE_BIGG_MODEL)
