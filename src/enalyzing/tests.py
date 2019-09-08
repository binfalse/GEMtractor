from django.test import TestCase, Client
from .forms import ExportForm
import tempfile
import os
import json
from xml.dom import minidom
from libsbml import SBMLReader
from modules.enalyzer_utils.utils import Utils, InvalidBiggId, InvalidBiomodelsId

import logging
# logging.getLogger('tmp').debug("---->>>>> " + str(j))


# Create your tests here.
class EnalyzingTest(TestCase):
  def setUp(self):
    self.client = Client()
    
  def test_untained_gets (self):
    response = self.client.get('/enalyzing/')
    self.assertEqual(response.status_code, 200)
    self.assertTrue (b"Select a model" in response.content)
    
    response = self.client.get('/enalyzing/filter')
    self.assertEqual(response.status_code, 302)
    self.assertEqual("/enalyzing/", response["location"])
    
    response = self.client.get('/enalyzing/export')
    self.assertEqual(response.status_code, 302)
    self.assertEqual("/enalyzing/", response["location"])
    
  def test_index_lost_model (self):
    d = tempfile.TemporaryDirectory()
    with self.settings(STORAGE=d.name):
      with open("test/gene-filter-example.xml") as fp:
        response = self.client.post('/enalyzing/', {"custom-model": fp})
        self.assertEqual(response.status_code, 302)
        self.assertEqual("/enalyzing/filter", response["location"])
        
        # test session uploaded file
    
        response = self.client.get('/api/get_session_data')
        self.assertEqual(response.status_code, 200)
        self.assertEqual("success", response.json()["status"], msg = "response was: " + str(response.json()))
        self.assertEqual("yes", response.json()["data"]["session"]["has_session"])
        self.assertEqual(len (response.json()["data"]["files"]), 1)
        
        # make sure model is stored on server
        uploaded_file = Utils.get_upload_path (response.json ()["data"]["session"]["model_id"])
        self.assertTrue(os.path.isfile (uploaded_file))
        
        os.remove (uploaded_file)
        
        
        response = self.client.get('/enalyzing/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue (b"Select a model" in response.content)
        # expect an error, as the file is lost...
        self.assertTrue(b"did not find model on the server" in response.content)
    
  def test_filter_lost_model (self):
    d = tempfile.TemporaryDirectory()
    with self.settings(STORAGE=d.name):
      with open("test/gene-filter-example.xml") as fp:
        response = self.client.post('/enalyzing/', {"custom-model": fp})
        self.assertEqual(response.status_code, 302)
        self.assertEqual("/enalyzing/filter", response["location"])
        
        # test session uploaded file
    
        response = self.client.get('/api/get_session_data')
        self.assertEqual(response.status_code, 200)
        self.assertEqual("success", response.json()["status"], msg = "response was: " + str(response.json()))
        self.assertEqual("yes", response.json()["data"]["session"]["has_session"])
        self.assertEqual(len (response.json()["data"]["files"]), 1)
        
        # make sure model is stored on server
        uploaded_file = Utils.get_upload_path (response.json ()["data"]["session"]["model_id"])
        self.assertTrue(os.path.isfile (uploaded_file))
        
        os.remove (uploaded_file)
        
        
        response = self.client.get('/enalyzing/filter')
        self.assertEqual(response.status_code, 302)
        self.assertEqual("/enalyzing/", response["location"])
    
  def test_export_lost_model (self):
    d = tempfile.TemporaryDirectory()
    with self.settings(STORAGE=d.name):
      with open("test/gene-filter-example.xml") as fp:
        response = self.client.post('/enalyzing/', {"custom-model": fp})
        self.assertEqual(response.status_code, 302)
        self.assertEqual("/enalyzing/filter", response["location"])
        
        # test session uploaded file
    
        response = self.client.get('/api/get_session_data')
        self.assertEqual(response.status_code, 200)
        self.assertEqual("success", response.json()["status"], msg = "response was: " + str(response.json()))
        self.assertEqual("yes", response.json()["data"]["session"]["has_session"])
        self.assertEqual(len (response.json()["data"]["files"]), 1)
        
        # make sure model is stored on server
        uploaded_file = Utils.get_upload_path (response.json ()["data"]["session"]["model_id"])
        self.assertTrue(os.path.isfile (uploaded_file))
        
        os.remove (uploaded_file)
        
        
        response = self.client.get('/enalyzing/export')
        self.assertEqual(response.status_code, 302)
        self.assertEqual("/enalyzing/", response["location"])
    
    
  def test_workflow_upload (self):
    d = tempfile.TemporaryDirectory()
    with self.settings(STORAGE=d.name):
      with open("test/gene-filter-example.xml") as fp:
        response = self.client.post('/enalyzing/', {"custom-model": fp})
        self.assertEqual(response.status_code, 302)
        self.assertEqual("/enalyzing/filter", response["location"])
        
        # test session uploaded file
    
        response = self.client.get('/api/get_session_data')
        self.assertEqual(response.status_code, 200)
        self.assertEqual("success", response.json()["status"], msg = "response was: " + str(response.json()))
        self.assertEqual("yes", response.json()["data"]["session"]["has_session"])
        self.assertEqual(len (response.json()["data"]["files"]), 1)
        
        
        response = self.client.post('/api/store_filter', json.dumps({'species': ["x","y","a"], 'reaction': ["x","y","a"], 'genes': ["x","y","x","y"]}),content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual("success", response.json()["status"], msg = "response was: " + str(response.json()))
        f = response.json()["filter"]
        self.assertEqual(len(f["filter_species"]), 3)
        self.assertEqual(len(f["filter_reactions"]), 3)
        self.assertEqual(len(f["filter_genes"]), 4)
        
        
        response = self.client.get('/enalyzing/filter')
        self.assertEqual(response.status_code, 200)
        self.assertTrue (b"Filter Model Entities" in response.content)
        
        
        
        response = self.client.get('/enalyzing/export')
        self.assertEqual(response.status_code, 200)
        self.assertTrue (b"Export Your Model" in response.content)
        
        
        form = self._create_export ('rn', 'sbml', False, True)
        self.assertTrue (form.is_valid())
        response = self.client.post('/enalyzing/export', form.cleaned_data)
        self.assertEqual(response.status_code, 200)
        valid, sbml_rn = self._valid_sbml (response.content)
        self.assertTrue (valid, msg="invalid SBML of rn")
        
        rnSpecies = sbml_rn.getModel ().getNumSpecies ()
        rnReactions = sbml_rn.getModel ().getNumReactions ()
        rnEdges = 0
        for r in range (rnReactions):
          reaction = sbml_rn.getModel ().getReaction (r)
          rnEdges += reaction.getNumReactants ()
          rnEdges += reaction.getNumProducts ()
        logging.getLogger('tmp').debug("----r>>>>> " + str (rnSpecies))
        logging.getLogger('tmp').debug("----r>>>>> " + str (rnReactions))
        logging.getLogger('tmp').debug("----r>>>>> " + str (rnEdges))
        
        form = self._create_export ('en', 'sbml', False, True)
        self.assertTrue (form.is_valid())
        response = self.client.post('/enalyzing/export', form.cleaned_data)
        self.assertEqual(response.status_code, 200)
        valid, sbml_en = self._valid_sbml (response.content)
        self.assertTrue (valid, msg="invalid SBML of en")
        
        enSpecies = sbml_en.getModel ().getNumSpecies ()
        enReactions = sbml_en.getModel ().getNumReactions ()
        enEdges = 0
        for r in range (enReactions):
          reaction = sbml_en.getModel ().getReaction (r)
          enEdges += reaction.getNumReactants ()
          enEdges += reaction.getNumProducts ()
        logging.getLogger('tmp').debug("----e>>>>> " + str (enSpecies))
        logging.getLogger('tmp').debug("----e>>>>> " + str (enReactions))
        logging.getLogger('tmp').debug("----e>>>>> " + str (enEdges))
        
        
        
        form = self._create_export ('rn', 'graphml', False, True)
        self.assertTrue (form.is_valid())
        response = self.client.post('/enalyzing/export', form.cleaned_data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue (self._valid_xml (response.content))
        c = response.content.decode("utf-8")
        self.assertEqual (c.count ("<node "), rnSpecies + rnReactions)
        self.assertEqual (c.count (">species</data"), rnSpecies)
        self.assertEqual (c.count (">reaction<"), rnReactions)
        self.assertEqual (c.count ("<edge"), rnEdges)
        
        
        
        form = self._create_export ('en', 'graphml', False, True)
        self.assertTrue (form.is_valid())
        response = self.client.post('/enalyzing/export', form.cleaned_data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue (self._valid_xml (response.content))
        c = response.content.decode("utf-8")
        self.assertEqual (c.count ("<node "), enSpecies)
        self.assertEqual (c.count (">gene</data"), enSpecies)
        self.assertEqual (c.count ("<edge"), enReactions)
        
        
        
        form = self._create_export ('rn', 'gml', False, True)
        self.assertTrue (form.is_valid())
        response = self.client.post('/enalyzing/export', form.cleaned_data)
        self.assertEqual(response.status_code, 200)
        c = response.content.decode("utf-8")
        self.assertEqual (c.count ("node ["), rnSpecies + rnReactions)
        self.assertEqual (c.count ("edge ["), rnEdges)
        
        
        
        form = self._create_export ('en', 'gml', False, True)
        self.assertTrue (form.is_valid())
        response = self.client.post('/enalyzing/export', form.cleaned_data)
        self.assertEqual(response.status_code, 200)
        c = response.content.decode("utf-8")
        self.assertEqual (c.count ("node ["), enSpecies)
        self.assertEqual (c.count ("edge ["), enReactions)
        
        
        
        form = self._create_export ('rn', 'dot', False, True)
        self.assertTrue (form.is_valid())
        response = self.client.post('/enalyzing/export', form.cleaned_data)
        self.assertEqual(response.status_code, 200)
        c = response.content.decode("utf-8")
        self.assertEqual (c.count ("label="), rnSpecies + rnReactions)
        self.assertEqual (c.count (" -> "), rnEdges)
        
        
        
        form = self._create_export ('en', 'dot', False, True)
        self.assertTrue (form.is_valid())
        response = self.client.post('/enalyzing/export', form.cleaned_data)
        self.assertEqual(response.status_code, 200)
        c = response.content.decode("utf-8")
        self.assertEqual (c.count ("label="), enSpecies)
        self.assertEqual (c.count (" -> "), enReactions)
        
        
        
        
        # logging.getLogger('tmp').debug("---->>>>> " + str(response.content))
        
        
        
    
  def _create_export (self, network_type, network_format, remove_reaction_genes_removed, remove_reaction_missing_species):
    return ExportForm(data={
      'network_type': network_type,
      'remove_reaction_genes_removed': remove_reaction_genes_removed,
      'remove_reaction_missing_species': remove_reaction_missing_species,
      'network_format': network_format,
      })
  
  def _valid_xml (self, xml):
    try:
      xmldoc = minidom.parseString (xml)
      return True
    except:
      logging.getLogger('tmp').debug("XML BAD")
      return False
  
  def _valid_sbml (self, xml):
    if not self._valid_xml (xml):
      return False, None
    
    sbml = SBMLReader().readSBMLFromString(xml.decode("utf-8"))
    if sbml.getNumErrors() > 0:
      for i in range (0, sbml.getNumErrors()):
        logging.getLogger('tmp').debug("SBML BAD: " + sbml.getError(i).getMessage())
      return False, None
    return True, sbml
  
  def test_export_form(self):
    form = self._create_export ('en', 'sbml', False, True)
    self.assertTrue (form.is_valid())
    self.assertTrue (form.cleaned_data['remove_reaction_genes_removed'])
    
    form = self._create_export ('blah', 'sbml', False, True)
    self.assertFalse (form.is_valid())
    
    form = self._create_export ('rn', 'gml', False, True)
    self.assertTrue (form.is_valid())
    
    form = self._create_export ('rn', 'gasdfml', False, True)
    self.assertFalse (form.is_valid())
