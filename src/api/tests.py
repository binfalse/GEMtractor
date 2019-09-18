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
from modules.gemtractor.constants import Constants
import json
import tempfile
from libsbml import SBMLReader
from xml.dom import minidom

import logging
# logging.getLogger(__name__).debug("---->>>>> " + str(j))

# Create your tests here.
class ApiTest(TestCase):
  def setUp(self):
    self.client = Client()
  
  def test_status_get (self):
    response = self.client.get('/api/status')
    self._expect_response (response, True)
  
  def test_status_post (self):
    response = self.client.post('/api/status', json.dumps({'request': 'something'}),content_type="application/json")
    self._expect_response (response, True)
    
  
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
    self.assertEqual(len(f["filter_enzymes"]), 0)
    
    response = self.client.post('/api/store_filter', json.dumps({'species': ["a","b"]}),content_type="application/json")
    self._expect_response (response, True)
    f = response.json()["filter"]
    self.assertEqual(len(f["filter_species"]), 2)
    self.assertEqual(len(f["filter_reactions"]), 0)
    self.assertEqual(len(f["filter_enzymes"]), 0)
    
    response = self.client.post('/api/store_filter', json.dumps({'reaction': ["a"]}),content_type="application/json")
    self._expect_response (response, True)
    f = response.json()["filter"]
    self.assertEqual(len(f["filter_species"]), 2)
    self.assertEqual(len(f["filter_reactions"]), 1)
    self.assertEqual(len(f["filter_enzymes"]), 0)
    
    response = self.client.post('/api/store_filter', json.dumps({'species': ["a"], 'enzymes': ["x","y"]}),content_type="application/json")
    self._expect_response (response, True)
    f = response.json()["filter"]
    self.assertEqual(len(f["filter_species"]), 1)
    self.assertEqual(len(f["filter_reactions"]), 1)
    self.assertEqual(len(f["filter_enzymes"]), 2)
    
    response = self.client.post('/api/store_filter', json.dumps({'species': ["x","y","a"], 'reaction': ["x","y","a"], 'enzymes': ["x","y","x","y"]}),content_type="application/json")
    self._expect_response (response, True)
    f = response.json()["filter"]
    self.assertEqual(len(f["filter_species"]), 3)
    self.assertEqual(len(f["filter_reactions"]), 3)
    self.assertEqual(len(f["filter_enzymes"]), 4)
    
    
  
  def test_clear_session (self):
    
    # test session is cleared
    response = self.client.get('/api/get_session_data')
    self._expect_response (response, True)
    self.assertEqual(len (response.json()["data"]), 0)
    
    # create session
    response = self.client.get('/gemtract/')
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
      with self.settings(URLS_BIGG_MODELS='https://binfalse.de/GEMtractor/404/trigger'):
        response = self.client.get('/api/get_bigg_models')
        self._expect_response (response, False)
      with self.settings(URLS_BIGG_MODELS='https://hopefully.no.t.existent.domainexception/GEMtractor/404/trigger'):
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
      with self.settings(URLS_BIGG_MODEL = lambda model_id: "'https://binfalse.de/GEMtractor/404/trigger/"+model_id+".xml"):
        response = self.client.post('/api/select_bigg_model', json.dumps({'bigg_id': "e_coli_core"}),content_type="application/json")
        self._expect_response (response, False)
      with self.settings(URLS_BIGG_MODEL = lambda model_id: "https://hopefully.no.t.existent.domainexception/GEMtractor/404/trigger/"+model_id+".xml"):
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
      with self.settings(URLS_BIOMODELS='https://binfalse.de/GEMtractor/404/trigger'):
        response = self.client.get('/api/get_biomodels')
        self._expect_response (response, False)
      with self.settings(URLS_BIOMODELS='https://hopefully.no.t.existent.domainexception/GEMtractor/404/trigger'):
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
      with self.settings(URLS_BIOMODEL_INFO = lambda model_id: "'https://binfalse.de/GEMtractor/404/trigger/"+model_id+".xml"):
        response = self.client.post('/api/select_biomodel', json.dumps({'biomodels_id': "e_coli_core"}),content_type="application/json")
        self._expect_response (response, False)
      with self.settings(URLS_BIOMODEL_INFO = lambda model_id: "https://hopefully.no.t.existent.domainexception/GEMtractor/404/trigger/"+model_id+".xml"):
        response = self.client.post('/api/select_biomodel', json.dumps({'biomodels_id': "e_coli_core"}),content_type="application/json")
        self._expect_response (response, False)
      
      with self.settings(URLS_BIOMODEL_SBML = lambda model_id, filename: "'https://binfalse.de/gemtract/404/trigger/"+model_id+"."+filename):
        response = self.client.post('/api/select_biomodel', json.dumps({'biomodels_id': "e_coli_core"}),content_type="application/json")
        self._expect_response (response, False)
      with self.settings(URLS_BIOMODEL_SBML = lambda model_id, filename: "https://hopefully.no.t.existent.domainexception/gemtract/404/trigger/"+model_id+"."+filename):
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
      
    
      response = self.client.post('/api/store_filter', json.dumps({'species': ["x","y","a"], 'reaction': ["x","y","a"], 'enzymes': ["x","y","x","y"]}),content_type="application/json")
      self._expect_response (response, True)
      f = response.json()["filter"]
      self.assertEqual(len(f["filter_species"]), 3)
      self.assertEqual(len(f["filter_reactions"]), 3)
      self.assertEqual(len(f["filter_enzymes"]), 4)
    
      
      response = self.client.get('/api/get_network')
      self._expect_response (response, True)
      self.assertTrue(len (response.json()["network"]) > 0)
      
      
  def test_api (self):
    response = self.client.get('/api/execute')
    self.assertEqual(response.status_code, 302)
    self.assertEqual("/learn#api", response["location"])

    
    with open("test/gene-filter-example.xml") as f:
      model=f.read().replace('\n', '')
      
      response = self.client.post('/api/execute', json.dumps({
          "export": {
            "network_type":"rn",
            "network_format":"sbml"
          },
          "file": model
          }),content_type="application/json")
      self.assertEqual(response.status_code, 200)
      valid, sbml_rn = self._valid_sbml (response.content)
      self.assertTrue (valid, msg="invalid SBML of rn")
      
      response = self.client.post('/api/execute', json.dumps({
          "export": {
            "network_type":"en",
            "network_format":"sbml"
          },
          "file": model
          }),content_type="application/json")
      self.assertEqual(response.status_code, 200)
      valid, sbml_en = self._valid_sbml (response.content)
      self.assertTrue (valid, msg="invalid SBML of en")
      
      
        
      rnSpecies = sbml_rn.getModel ().getNumSpecies ()
      rnReactions = sbml_rn.getModel ().getNumReactions ()
      rnEdges = 0
      for r in range (rnReactions):
        reaction = sbml_rn.getModel ().getReaction (r)
        rnEdges += reaction.getNumReactants ()
        rnEdges += reaction.getNumProducts ()
        
      enSpecies = sbml_en.getModel ().getNumSpecies ()
      enReactions = sbml_en.getModel ().getNumReactions ()
      enEdges = 0
      for r in range (enReactions):
        reaction = sbml_en.getModel ().getReaction (r)
        enEdges += reaction.getNumReactants ()
        enEdges += reaction.getNumProducts ()
      
      
      
      response = self.client.post('/api/execute', json.dumps({
          "export": {
            "network_type":"rn",
            "network_format":"graphml"
          },
          "file": model
          }),content_type="application/json")
      self.assertEqual(response.status_code, 200)
      self.assertTrue (self._valid_xml (response.content), msg="invalid xml of rn")
      c = response.content.decode("utf-8")
      self.assertEqual (c.count ("<node "), rnSpecies + rnReactions)
      self.assertEqual (c.count (">species</data"), rnSpecies)
      self.assertEqual (c.count (">reaction<"), rnReactions)
      self.assertEqual (c.count ("<edge"), rnEdges)
      
      response = self.client.post('/api/execute', json.dumps({
          "export": {
            "network_type":"en",
            "network_format":"graphml"
          },
          "file": model
          }),content_type="application/json")
      self.assertEqual(response.status_code, 200)
      self.assertTrue (self._valid_xml (response.content), msg="invalid xml of en")
      c = response.content.decode("utf-8")
      self.assertEqual (c.count ("<node "), enSpecies)
      self.assertEqual (c.count (">enzyme</data") + c.count (">enzyme_complex</data"), enSpecies)
      self.assertEqual (c.count ("<edge"), enReactions)
      
      
      response = self.client.post('/api/execute', json.dumps({
          "export": {
            "network_type":"rn",
            "network_format":"gml"
          },
          "file": model
          }),content_type="application/json")
      self.assertEqual(response.status_code, 200)
      c = response.content.decode("utf-8")
      self.assertEqual (c.count ("node ["), rnSpecies + rnReactions)
      self.assertEqual (c.count ("edge ["), rnEdges)
      
      response = self.client.post('/api/execute', json.dumps({
          "export": {
            "network_type":"en",
            "network_format":"gml"
          },
          "file": model
          }),content_type="application/json")
      self.assertEqual(response.status_code, 200)
      c = response.content.decode("utf-8")
      self.assertEqual (c.count ("node ["), enSpecies)
      self.assertEqual (c.count ("edge ["), enReactions)
      
      response = self.client.post('/api/execute', json.dumps({
          "export": {
            "network_type":"rn",
            "network_format":"dot"
          },
          "file": model
          }),content_type="application/json")
      self.assertEqual(response.status_code, 200)
      c = response.content.decode("utf-8")
      self.assertEqual (c.count ("label="), rnSpecies + rnReactions)
      self.assertEqual (c.count (" -> "), rnEdges)
      
      response = self.client.post('/api/execute', json.dumps({
          "export": {
            "network_type":"en",
            "network_format":"dot"
          },
          "file": model
          }),content_type="application/json")
      self.assertEqual(response.status_code, 200)
      c = response.content.decode("utf-8")
      self.assertEqual (c.count ("label="), enSpecies)
      self.assertEqual (c.count (" -> "), enReactions)
      
      
      
      
      
      
      # test filters and other options
      response = self.client.post('/api/execute', json.dumps({
          "export": {
            "network_type":"rn",
            "network_format":"sbml"
          },
          "filter": {
            "species": ["k"],
            "reactions": ["b","x"],
            "enzymes": ["a"],
            "filter_enzyme_complexes": ["a + k"],
          },
          "file": model
          }),content_type="application/json")
      self.assertEqual(response.status_code, 200)
      valid, sbml_xx = self._valid_sbml (response.content)
      self.assertTrue (valid, msg="invalid SBML of rn")
      
      response = self.client.post('/api/execute', json.dumps({
          "export": {
            "network_type":"en",
            "network_format":"sbml",
            "remove_reaction_enzymes_removed": False,
            "remove_reaction_missing_species": True
          },
          "file": model
          }),content_type="application/json")
      self.assertEqual(response.status_code, 200)
      valid, sbml_xx = self._valid_sbml (response.content)
      self.assertTrue (valid, msg="invalid SBML of en")

    
      
      
      # trigger some errors
      response = self.client.post('/api/execute', json.dumps({
          "export": {
            "network_type":"rn",
            "network_format":"gm;"
          },
          "file": model
          }),content_type="application/json")
      self.assertEqual(response.status_code, 400)
      
      response = self.client.post('/api/execute', json.dumps({
          "export": {
            "network_type":"enn",
            "network_format":"gml"
          },
          "file": model
          }),content_type="application/json")
      self.assertEqual(response.status_code, 400)
      
      
      response = self.client.post('/api/execute', json.dumps({
          "export": {
            "network_type":"rn",
            "network_format":"sbml"
          },
          "filter": {
            "species": "k",
          },
          "file": model
          }),content_type="application/json")
      self.assertEqual(response.status_code, 400)
      response = self.client.post('/api/execute', json.dumps({
          "export": {
            "network_type":"rn",
            "network_format":"sbml"
          },
          "filter": {
            "reactions": "k",
          },
          "file": model
          }),content_type="application/json")
      self.assertEqual(response.status_code, 400)
      response = self.client.post('/api/execute', json.dumps({
          "export": {
            "network_type":"rn",
            "network_format":"sbml"
          },
          "filter": {
            "enzymes": "k",
          },
          "file": model
          }),content_type="application/json")
      self.assertEqual(response.status_code, 400)
      response = self.client.post('/api/execute', json.dumps({
          "export": {
            "network_type":"rn",
            "network_format":"sbml"
          },
          }),content_type="application/json")
      self.assertEqual(response.status_code, 400)
      response = self.client.post('/api/execute', json.dumps({
          "file": model
          }),content_type="application/json")
      self.assertEqual(response.status_code, 400)
      response = self.client.post('/api/execute', json.dumps({
          "export": {
            "network_format":"sbml"
          },
          "file": model
          }),content_type="application/json")
      self.assertEqual(response.status_code, 400)
      response = self.client.post('/api/execute', json.dumps({
          "export": {
            "network_type":"rn"
          },
          "file": model
          }),content_type="application/json")
      self.assertEqual(response.status_code, 400)
      response = self.client.post('/api/execute', json.dumps({
          "export": {
            "network_type":"rn",
            "network_format":"sbml"
          },
          "file": "not a model!"
          }),content_type="application/json")
      self.assertEqual(response.status_code, 400)
      
      
      
      
    
  
  def _valid_xml (self, xml):
    try:
      minidom.parseString (xml)
      return True
    except Exception as e:
      logging.getLogger(__name__).info("XML BAD: " + str (e))
      return False
  
  def _valid_sbml (self, xml):
    if not self._valid_xml (xml):
      return False, None
    
    sbml = SBMLReader().readSBMLFromString(xml.decode("utf-8"))
    if sbml.getNumErrors() > 0:
      for i in range (0, sbml.getNumErrors()):
        logging.getLogger(__name__).info("SBML BAD: " + sbml.getError(i).getMessage())
      return False, None
    return True, sbml
    
    
  def _expect_response (self, response, succ = True):
    self.assertEqual(response.status_code, 200)
    if succ:
      self.assertEqual("success", response.json()["status"], msg = "response was: " + str(response.json()))
    else:
      self.assertEqual("failed", response.json()["status"], msg = "response was: " + str(response.json()))
      self.assertTrue("error" in response.json(), msg = "response was: " + str(response.json()))
    
  
