
from django.conf import settings
import hashlib
import time
import random
import os
import errno
import tempfile
import urllib.request
import json
import re

class InvalidBiggId (Exception): pass
class InvalidBiomodelsId (Exception): pass
class UnableToRetriebeBiomodel (Exception): pass
class BreakLoops (Exception): pass
class NotYetImplemented (Exception): pass
class InvalidGeneExpression (Exception): pass

class Utils:
  
  @staticmethod
  def _create_dir (d):
    try:
      os.makedirs(d)
    except OSError as e:
      if e.errno != errno.EEXIST:
        raise
  
  @staticmethod
  def get_path_of_generated_file_web (filename, sessionid):
    d = os.path.join (settings.STORAGE, "generated", "web", sessionid)
    Utils._create_dir(d)
    return os.path.join (d, filename)
    
  
  @staticmethod
  def create_generated_file_web (filename, sessionid):
    d = os.path.join (settings.STORAGE, "generated", "web", sessionid)
    Utils._create_dir(d)
    
    # tmp = hashlib.sha512 ((filename + str (time.time() + random.random())).encode("utf-8")).hexdigest ()
    # while os.path.exists(os.path.join (d, tmp)):
      # tmp = hashlib.sha512 ((filename + str (time.time() + random.random())).encode("utf-8")).hexdigest ()
    
    # return os.path.join (d, tmp)
    return os.path.join (d, filename)
    
  
  @staticmethod
  def get_path_of_uploaded_file (filename, sessionid):
    d = os.path.join (settings.STORAGE, "upload", sessionid)
    Utils._create_dir(d)
    return os.path.join (d, filename)
  
  @staticmethod
  def get_upload_path (filename, sessionid):
    d = os.path.join (settings.STORAGE, "upload", sessionid)
    Utils._create_dir(d)
    # tmp = hashlib.sha512 ((filename + str (time.time() + random.random())).encode("utf-8")).hexdigest ()
    # while os.path.exists(os.path.join (d, tmp)):
      # tmp = hashlib.sha512 ((filename + str (time.time() + random.random())).encode("utf-8")).hexdigest ()
    
    return os.path.join (d, filename)
    
  
  @staticmethod
  def get_bigg_models (force = False):
    """ Retrieve the list of models from BiGG
    
    may raise HTTPError or URLError (see api/get_bigg_models)
    """
    d = os.path.join (settings.STORAGE, "cache", "bigg")
    Utils._create_dir(d)
    f = os.path.join (d, "models.json")
    if force or not os.path.isfile (f):
      urllib.request.urlretrieve ("http://bigg.ucsd.edu/api/v2/models/", f)
    if time.time() - os.path.getmtime(f) > settings.CACHE_BIGG:
      return Utils.get_bigg_models (True)
    with open(f, 'r') as json_data:
      return json.load(json_data)
  
  @staticmethod
  def get_bigg_model (bigg_id):
    """ Retrieve a model from BiGG
    
    may raise HTTPError or URLError (see api/get_bigg_models)
    """
    if not re.match('^[a-zA-Z0-9_-]+$', bigg_id):
      raise InvalidBiggId ("this BiGG id is invalid: " + bigg_id)
    
    d = os.path.join (settings.STORAGE, "cache", "bigg")
    Utils._create_dir(d)
    h = hashlib.sha512 (bigg_id.encode("utf-8")).hexdigest()
    f = os.path.join (d, h)
    if os.path.isfile (f):
      return f
    
    urllib.request.urlretrieve ("http://bigg.ucsd.edu/static/models/"+bigg_id+".xml", f)
    return f
  
  @staticmethod
  def get_biomodels (force = False):
    d = os.path.join (settings.STORAGE, "cache", "biomodels")
    Utils._create_dir(d)
    f = os.path.join (d, "models.json")
    if force or not os.path.isfile (f):
      urllib.request.urlretrieve ('https://www.ebi.ac.uk/biomodels/search?format=json&query=genome+scale+metabolic+model+modelformat%3A%22SBML%22+NOT+%22nicolas+le%22&numResults=100&sort=id-asc', f)
    if time.time() - os.path.getmtime(f) > settings.CACHE_BIOMODELS:
      return Utils.get_biomodels (True)
    with open(f, 'r') as json_data:
      return json.load(json_data)
  
  @staticmethod
  def get_biomodel (model_id):
    if not re.match('^[BM][A-Z0-9_-]+$', model_id):
      raise InvalidBiomodelsId ("this biomodels id is invalid: " + model_id)
      
    d = os.path.join (settings.STORAGE, "cache", "biomodels")
    Utils._create_dir(d)
    h = hashlib.sha512 (model_id.encode("utf-8")).hexdigest()
    f = os.path.join (d, h + ".json")
    if not os.path.isfile (f) or time.time() - os.path.getmtime(f) > settings.CACHE_BIOMODEL_FILE:
      urllib.request.urlretrieve ("https://www.ebi.ac.uk/biomodels/"+model_id+"?format=json", f)
    
    
    with open(f, 'r') as json_data:
      model = json.load(json_data)
      sbmlfile = os.path.join (d, h + ".sbml")
      if not os.path.isfile (sbmlfile) or time.time() - os.path.getmtime(sbmlfile) > settings.CACHE_BIOMODEL_FILE:
        # print (type (model["files"]["main"][0]["name"]))
        filename = model["files"]["main"][0]["name"]
        # print (filename)
        urllib.request.urlretrieve ("https://www.ebi.ac.uk/biomodels/model/download/"+model_id+"?filename="+filename, sbmlfile)
      return sbmlfile
    raise UnableToRetriebeBiomodel ("could not download biomodel: " + model_id)
  
  @staticmethod
  def get_model_path (model_type, model_id, sessionid):
    if model_type == 'upload':
      return Utils.get_path_of_uploaded_file (model_id, sessionid)
    if model_type == 'bigg':
      return Utils.get_bigg_model (model_id)
    if model_type == 'biomodels':
      return Utils.get_biomodel (model_id)
    
  @staticmethod
  def del_session_key (request, context, key):
    try:
      del request.session[key]
    except KeyError:
      pass
    try:
      del context[key]
    except KeyError:
      pass
