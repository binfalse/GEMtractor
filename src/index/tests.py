from django.test import TestCase, Client

# Create your tests here.
class IndexTest(TestCase):
  def setUp(self):
    self.client = Client(enforce_csrf_checks=True)
  
  def test_index (self):
    response = self.client.get('/')
    self.assertEqual(response.status_code, 200)
    self.assertTrue (b"Upload an SBML model" in response.content)
  
  def test_imprint (self):
    response = self.client.get('/imprint')
    self.assertEqual(response.status_code, 200)
    self.assertTrue (b"Scharm" in response.content)
  
  def test_doc (self):
    response = self.client.get('/learn')
    self.assertEqual(response.status_code, 200)
    self.assertTrue (b"Frequently asked" in response.content)
