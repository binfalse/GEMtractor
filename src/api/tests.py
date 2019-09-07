from django.test import TestCase, Client
from modules.enalyzer_utils.constants import Constants
import json
from django.conf import settings
from modules.enalyzer_utils.utils import Utils, InvalidBiggId

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
  
  def test_store_filter (self):
    # only post allowed
    response = self.client.get('/api/store_filter')
    self.assertEqual(response.status_code, 302)
    self.assertEqual("/", response["location"])
    
    response = self.client.post('/api/store_filter', json.dumps({'species': ["a"]}),content_type="application/json")
    self.assertEqual(response.status_code, 200)
    f = response.json()["filter"]
    self.assertEqual(len(f["filter_species"]), 1)
    self.assertEqual(len(f["filter_reactions"]), 0)
    self.assertEqual(len(f["filter_genes"]), 0)
    
    response = self.client.post('/api/store_filter', json.dumps({'species': ["a","b"]}),content_type="application/json")
    self.assertEqual(response.status_code, 200)
    f = response.json()["filter"]
    self.assertEqual(len(f["filter_species"]), 2)
    self.assertEqual(len(f["filter_reactions"]), 0)
    self.assertEqual(len(f["filter_genes"]), 0)
    
    response = self.client.post('/api/store_filter', json.dumps({'reaction': ["a"]}),content_type="application/json")
    self.assertEqual(response.status_code, 200)
    f = response.json()["filter"]
    self.assertEqual(len(f["filter_species"]), 2)
    self.assertEqual(len(f["filter_reactions"]), 1)
    self.assertEqual(len(f["filter_genes"]), 0)
    
    response = self.client.post('/api/store_filter', json.dumps({'species': ["a"], 'genes': ["x","y"]}),content_type="application/json")
    self.assertEqual(response.status_code, 200)
    f = response.json()["filter"]
    self.assertEqual(len(f["filter_species"]), 1)
    self.assertEqual(len(f["filter_reactions"]), 1)
    self.assertEqual(len(f["filter_genes"]), 2)
    
    
  
  def test_clear_session (self):
    
    # test session is cleared
    response = self.client.get('/api/get_session_data')
    self.assertEqual(response.status_code, 200)
    self.assertEqual(len (response.json()["data"]), 0)
    
    # create session
    response = self.client.get('/enalyzing/')
    response = self.client.get('/api/get_session_data')
    self.assertEqual(response.status_code, 200)
    self.assertEqual("yes", response.json()["data"]["session"]["has_session"])
    
    # clear the session
    response = self.client.get('/api/clear_data')
    self.assertEqual(response.status_code, 200)
    
    # test session is cleared
    response = self.client.get('/api/get_session_data')
    self.assertEqual(response.status_code, 200)
    self.assertEqual(len (response.json()["data"]["session"]), 0)
    
  
  
  def test_get_bigg_models (self):
    response = self.client.get('/api/get_bigg_models')
    self.assertEqual(response.status_code, 200)
    j = response.json()
    self.assertEqual("success", j["status"])
    self.assertTrue(j["results_count"] > 0)
    
  
  
  def test_get_bigg_model (self):
    response = self.client.get('/api/select_bigg_model')
    self.assertEqual(response.status_code, 302)
    self.assertEqual("/", response["location"])
    
    
    with self.assertRaises (InvalidBiggId):
      response = self.client.post('/api/select_bigg_model', json.dumps({'bigg_id': " lkasdfj !ldskf3%"}),content_type="application/json")
    
    
    response = self.client.post('/api/select_bigg_model', json.dumps({'bigg_id': " lkasdfj !ldskf3%"}),content_type="application/json")
    
    
  
