from django.test import TestCase, Client
from modules.enalyzer_utils.constants import Constants
import json
from django.conf import settings
from modules.enalyzer_utils.utils import Utils, InvalidBiggId, InvalidBiomodelsId
import tempfile

import logging
# logging.getLogger('tmp').debug("---->>>>> " + str(j))

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
    self._expect_response (response, True)
    f = response.json()["filter"]
    self.assertEqual(len(f["filter_species"]), 1)
    self.assertEqual(len(f["filter_reactions"]), 0)
    self.assertEqual(len(f["filter_genes"]), 0)
    
    response = self.client.post('/api/store_filter', json.dumps({'species': ["a","b"]}),content_type="application/json")
    self._expect_response (response, True)
    f = response.json()["filter"]
    self.assertEqual(len(f["filter_species"]), 2)
    self.assertEqual(len(f["filter_reactions"]), 0)
    self.assertEqual(len(f["filter_genes"]), 0)
    
    response = self.client.post('/api/store_filter', json.dumps({'reaction': ["a"]}),content_type="application/json")
    self._expect_response (response, True)
    f = response.json()["filter"]
    self.assertEqual(len(f["filter_species"]), 2)
    self.assertEqual(len(f["filter_reactions"]), 1)
    self.assertEqual(len(f["filter_genes"]), 0)
    
    response = self.client.post('/api/store_filter', json.dumps({'species': ["a"], 'genes': ["x","y"]}),content_type="application/json")
    self._expect_response (response, True)
    f = response.json()["filter"]
    self.assertEqual(len(f["filter_species"]), 1)
    self.assertEqual(len(f["filter_reactions"]), 1)
    self.assertEqual(len(f["filter_genes"]), 2)
    
    response = self.client.post('/api/store_filter', json.dumps({'species': ["x","y","a"], 'reaction': ["x","y","a"], 'genes': ["x","y","x","y"]}),content_type="application/json")
    self._expect_response (response, True)
    f = response.json()["filter"]
    self.assertEqual(len(f["filter_species"]), 3)
    self.assertEqual(len(f["filter_reactions"]), 3)
    self.assertEqual(len(f["filter_genes"]), 4)
    
    
  
  def test_clear_session (self):
    
    # test session is cleared
    response = self.client.get('/api/get_session_data')
    self._expect_response (response, True)
    self.assertEqual(len (response.json()["data"]), 0)
    
    # create session
    response = self.client.get('/enalyzing/')
    response = self.client.get('/api/get_session_data')
    self._expect_response (response, True)
    self.assertEqual("yes", response.json()["data"]["session"]["has_session"])
    
    # clear the session
    response = self.client.get('/api/clear_data')
    self._expect_response (response, True)
    
    # test session is cleared
    response = self.client.get('/api/get_session_data')
    self._expect_response (response, True)
    self.assertEqual(len (response.json()["data"]["session"]), 0)
    
  
  
  def test_get_bigg_models (self):
    d = tempfile.TemporaryDirectory()
    with self.settings(STORAGE=d.name):
      with self.settings(URLS_BIGG_MODELS='https://binfalse.de'):
        response = self.client.get('/api/get_bigg_models')
        self._expect_response (response, False)
      
      response = self.client.get('/api/get_bigg_models')
      self._expect_response (response, True)
      self.assertTrue(response.json()["results_count"] > 0)
      
      # even if we now change the url, it should still be cached...
      with self.settings(URLS_BIGG_MODELS='https://binfalse.de'):
        response = self.client.get('/api/get_bigg_models')
        self.assertEqual("success", response.json()["status"], msg="does caching not work properly?")
        self._expect_response (response, True)
    
    d = tempfile.TemporaryDirectory()
    with self.settings(STORAGE=d.name):
      with self.settings(URLS_BIGG_MODELS='https://binfalse.de/enalyzer/404/trigger'):
        response = self.client.get('/api/get_bigg_models')
        self._expect_response (response, False)
      with self.settings(URLS_BIGG_MODELS='https://hopefully.no.t.existent.domainexception/enalyzer/404/trigger'):
        response = self.client.get('/api/get_bigg_models')
        self._expect_response (response, False)
    
  
  
  def test_get_bigg_model (self):
    d = tempfile.TemporaryDirectory()
    with self.settings(STORAGE=d.name):
      response = self.client.get('/api/select_bigg_model')
      self.assertEqual(response.status_code, 302)
      self.assertEqual("/", response["location"])
      
      
      
      # test invalid data
      response = self.client.post('/api/select_bigg_model', json.dumps({'something else': " lkasdfj !ldskf3%"}),content_type="application/json")
      self._expect_response (response, False)
      response = self.client.post('/api/select_bigg_model', {'bigg_id': " lkasdfj !ldskf3%"})
      self._expect_response (response, False)
      
      response = self.client.post('/api/select_bigg_model', json.dumps({'bigg_id': " lkasdfj !ldskf3%"}),content_type="application/json")
      self._expect_response (response, False)
      
      
      response = self.client.post('/api/select_bigg_model', json.dumps({'bigg_id': "e_coli_core"}),content_type="application/json")
      self._expect_response (response, True)
      response = self.client.get('/api/get_session_data')
      self._expect_response (response, True)
      self.assertEqual("e_coli_core", response.json()["data"]["session"][Constants.SESSION_MODEL_ID])
      self.assertEqual(Constants.SESSION_MODEL_TYPE_BIGG, response.json()["data"]["session"][Constants.SESSION_MODEL_TYPE])
      
      
      response = self.client.post('/api/select_bigg_model', json.dumps({'bigg_id': "sdalfkj3"}),content_type="application/json")
      self._expect_response (response, False)
      
      response = self.client.get('/api/get_session_data')
      self._expect_response (response, True)
      self.assertEqual("e_coli_core", response.json()["data"]["session"][Constants.SESSION_MODEL_ID])
      self.assertEqual(Constants.SESSION_MODEL_TYPE_BIGG, response.json()["data"]["session"][Constants.SESSION_MODEL_TYPE])
    
    
    d = tempfile.TemporaryDirectory()
    with self.settings(STORAGE=d.name):
      with self.settings(URLS_BIGG_MODEL = lambda model_id: "'https://binfalse.de/enalyzer/404/trigger/"+model_id+".xml"):
        response = self.client.post('/api/select_bigg_model', json.dumps({'bigg_id': "e_coli_core"}),content_type="application/json")
        self._expect_response (response, False)
      with self.settings(URLS_BIGG_MODEL = lambda model_id: "https://hopefully.no.t.existent.domainexception/enalyzer/404/trigger/"+model_id+".xml"):
        response = self.client.post('/api/select_bigg_model', json.dumps({'bigg_id': "e_coli_core"}),content_type="application/json")
        self._expect_response (response, False)
  
  
  def test_get_biomodels (self):
    d = tempfile.TemporaryDirectory()
    with self.settings(STORAGE=d.name):
      with self.settings(URLS_BIOMODELS='https://binfalse.de'):
        response = self.client.get('/api/get_biomodels')
        self._expect_response (response, False)
      
      response = self.client.get('/api/get_biomodels')
      self._expect_response (response, True)
      self.assertTrue(response.json()["matches"] > 0)
      
      # even if we now change the url, it should still be cached...
      with self.settings(URLS_BIOMODELS='https://binfalse.de'):
        response = self.client.get('/api/get_biomodels')
        self.assertEqual("success", response.json()["status"], msg="does caching not work properly?")
        self._expect_response (response, True)
        
    
    d = tempfile.TemporaryDirectory()
    with self.settings(STORAGE=d.name):
      with self.settings(URLS_BIOMODELS='https://binfalse.de/enalyzer/404/trigger'):
        response = self.client.get('/api/get_biomodels')
        self._expect_response (response, False)
      with self.settings(URLS_BIOMODELS='https://hopefully.no.t.existent.domainexception/enalyzer/404/trigger'):
        response = self.client.get('/api/get_biomodels')
        self._expect_response (response, False)
    
  
  
  def test_get_biomodel (self):
    d = tempfile.TemporaryDirectory()
    with self.settings(STORAGE=d.name):
      response = self.client.get('/api/select_biomodel')
      self.assertEqual(response.status_code, 302)
      self.assertEqual("/", response["location"])
      
      
      # test invalid data
      response = self.client.post('/api/select_biomodel', json.dumps({'something else': " lkasdfj !ldskf3%"}),content_type="application/json")
      self._expect_response (response, False)
      response = self.client.post('/api/select_biomodel', {'biomodels_id': " lkasdfj !ldskf3%"})
      self._expect_response (response, False)
      
      
      response = self.client.post('/api/select_biomodel', json.dumps({'biomodels_id': " lkasdfj !ldskf3%"}),content_type="application/json")
      self._expect_response (response, False)
      
      
      response = self.client.post('/api/select_biomodel', json.dumps({'biomodels_id': "BIOMD0000000007"}),content_type="application/json")
      self._expect_response (response, True)
      response = self.client.get('/api/get_session_data')
      self._expect_response (response, True)
      self.assertEqual("BIOMD0000000007", response.json()["data"]["session"][Constants.SESSION_MODEL_ID])
      self.assertEqual(Constants.SESSION_MODEL_TYPE_BIOMODELS, response.json()["data"]["session"][Constants.SESSION_MODEL_TYPE])
      
      
      response = self.client.post('/api/select_biomodel', json.dumps({'biomodels_id': "MODEL6614787694"}),content_type="application/json")
      self._expect_response (response, True)
      response = self.client.get('/api/get_session_data')
      self._expect_response (response, True)
      self.assertEqual("MODEL6614787694", response.json()["data"]["session"][Constants.SESSION_MODEL_ID])
      self.assertEqual(Constants.SESSION_MODEL_TYPE_BIOMODELS, response.json()["data"]["session"][Constants.SESSION_MODEL_TYPE])
      
      
      response = self.client.post('/api/select_biomodel', json.dumps({'biomodels_id': "sdalfkj3"}),content_type="application/json")
      self._expect_response (response, False)
      
      response = self.client.get('/api/get_session_data')
      self._expect_response (response, True)
      self.assertEqual("MODEL6614787694", response.json()["data"]["session"][Constants.SESSION_MODEL_ID])
      self.assertEqual(Constants.SESSION_MODEL_TYPE_BIOMODELS, response.json()["data"]["session"][Constants.SESSION_MODEL_TYPE])
    
    
    d = tempfile.TemporaryDirectory()
    with self.settings(STORAGE=d.name):
      with self.settings(URLS_BIOMODEL_INFO = lambda model_id: "'https://binfalse.de/enalyzer/404/trigger/"+model_id+".xml"):
        response = self.client.post('/api/select_biomodel', json.dumps({'biomodels_id': "e_coli_core"}),content_type="application/json")
        self._expect_response (response, False)
      with self.settings(URLS_BIOMODEL_INFO = lambda model_id: "https://hopefully.no.t.existent.domainexception/enalyzer/404/trigger/"+model_id+".xml"):
        response = self.client.post('/api/select_biomodel', json.dumps({'biomodels_id': "e_coli_core"}),content_type="application/json")
        self._expect_response (response, False)
      
      with self.settings(URLS_BIOMODEL_SBML = lambda model_id, filename: "'https://binfalse.de/enalyzer/404/trigger/"+model_id+"."+filename):
        response = self.client.post('/api/select_biomodel', json.dumps({'biomodels_id': "e_coli_core"}),content_type="application/json")
        self._expect_response (response, False)
      with self.settings(URLS_BIOMODEL_SBML = lambda model_id, filename: "https://hopefully.no.t.existent.domainexception/enalyzer/404/trigger/"+model_id+"."+filename):
        response = self.client.post('/api/select_biomodel', json.dumps({'biomodels_id': "e_coli_core"}),content_type="application/json")
        self._expect_response (response, False)
      
    
  
  
  def test_get_network (self):
    d = tempfile.TemporaryDirectory()
    with self.settings(STORAGE=d.name):
      
      response = self.client.get('/api/get_network')
      self.assertEqual(response.status_code, 302)
      self.assertEqual("/", response["location"])
      
      response = self.client.post('/api/get_network', {})
      self.assertEqual(response.status_code, 302)
      self.assertEqual("/", response["location"])
      
      response = self.client.post('/api/select_biomodel', json.dumps({'biomodels_id': "BIOMD0000000007"}),content_type="application/json")
      self._expect_response (response, True)
      response = self.client.get('/api/get_session_data')
      self._expect_response (response, True)
      self.assertEqual("BIOMD0000000007", response.json()["data"]["session"][Constants.SESSION_MODEL_ID])
      self.assertEqual(Constants.SESSION_MODEL_TYPE_BIOMODELS, response.json()["data"]["session"][Constants.SESSION_MODEL_TYPE])
    
      
      response = self.client.get('/api/get_network')
      self._expect_response (response, True)
      self.assertTrue(len (response.json()["network"]) > 0)
      
    
      response = self.client.post('/api/store_filter', json.dumps({'species': ["x","y","a"], 'reaction': ["x","y","a"], 'genes': ["x","y","x","y"]}),content_type="application/json")
      self._expect_response (response, True)
      f = response.json()["filter"]
      self.assertEqual(len(f["filter_species"]), 3)
      self.assertEqual(len(f["filter_reactions"]), 3)
      self.assertEqual(len(f["filter_genes"]), 4)
    
      
      response = self.client.get('/api/get_network')
      self._expect_response (response, True)
      self.assertTrue(len (response.json()["network"]) > 0)
      
      
      
    
  def _expect_response (self, response, succ = True):
    self.assertEqual(response.status_code, 200)
    if succ:
      self.assertEqual("success", response.json()["status"], msg = "response was: " + str(response.json()))
    else:
      self.assertEqual("failed", response.json()["status"], msg = "response was: " + str(response.json()))
      self.assertTrue("error" in response.json(), msg = "response was: " + str(response.json()))
    
  
