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

from django.test import TestCase, Client

# Create your tests here.
class IndexTest(TestCase):
  def setUp(self):
    self.client = Client(enforce_csrf_checks=True)
  
  def test_index (self):
    response = self.client.get('/')
    self.assertEqual(response.status_code, 200)
    self.assertTrue (b"Choose an SBML model" in response.content)
  
  def test_imprint (self):
    response = self.client.get('/imprint')
    self.assertEqual(response.status_code, 200)
    self.assertTrue (b"Scharm" in response.content)
  
  def test_doc (self):
    response = self.client.get('/learn')
    self.assertEqual(response.status_code, 200)
    self.assertTrue (b"Frequently asked" in response.content)
