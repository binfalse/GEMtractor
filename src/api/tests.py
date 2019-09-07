from django.test import TestCase, Client
import json

# Create your tests here.
class ApiTest(TestCase):
  def setUp(self):
    self.client = Client()
  
  def test_status_get (self):
    response = self.client.get('/api/status')
    self.assertEqual(response.status_code, 302)
    self.assertEqual("/", response["location"])
  
  def test_status_post (self):
    response = self.client.post('/api/status', json.dumps({'request': 'something'}),content_type="application/json")
    self.assertEqual(response.status_code, 200)
    #TODO
    self.assertEqual("abc",response.json()["answer"])
