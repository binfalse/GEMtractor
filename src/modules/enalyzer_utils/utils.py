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

from django.conf import settings
import hashlib
import time
import os
import errno
import urllib.request
import json
import re
from .constants import Constants
import logging

class InvalidBiggId (Exception): pass
class InvalidBiomodelsId (Exception): pass
class UnableToRetrieveBiomodel (Exception): pass
class BreakLoops (Exception): pass
class NotYetImplemented (Exception): pass
class InvalidGeneExpression (Exception): pass

class Utils:
  
  __logger = logging.getLogger('enalyzer-class')
  
  
  @staticmethod
  def add_model_note (model, filter_species, filter_reactions, filter_genes, remove_reaction_genes_removed, remove_reaction_missing_species):
    # TODO can we do better? eg. annotate with proper structure?
    note = model.getNotesString ()
    # print (note)
    if note is None or len (note) < 1 or "</body>" not in note:
        note = '<notes><body xmlns="http://www.w3.org/1999/xhtml"></body></notes>'
    
    additional_note = "<p>This file was generated at the enalyzer (https://enalyzer.bio.informatik.uni-rostock.de/) using the following settings:</p>"
    if filter_species is not None and len (filter_species) > 0:
      additional_note = additional_note + "<p>Filter Species:</p><ul>"
      for s in filter_species:
        additional_note = additional_note + "<li>"+s+"</li>"
      additional_note = additional_note + "</ul>"
    if filter_reactions is not None and len (filter_reactions) > 0:
      additional_note = additional_note + "<p>Filter Reactions:</p><ul>"
      for s in filter_reactions:
        additional_note = additional_note + "<li>"+s+"</li>"
      additional_note = additional_note + "</ul>"
    if filter_genes is not None and len (filter_genes) > 0:
      additional_note = additional_note + "<p>Filter Genes:</p><ul>"
      for s in filter_genes:
        additional_note = additional_note + "<li>"+s+"</li>"
      additional_note = additional_note + "</ul>"
    additional_note = additional_note + "<p>Remove reactions who's genes are removed: " +str(remove_reaction_genes_removed)+ "</p>"
    additional_note = additional_note + "<p>Remove reactions that are missing a species: " +str(remove_reaction_missing_species)+ "</p>"
    
    model.setNotes (note.replace ("</body>", additional_note + "</body>"))
  
  @staticmethod
  def _create_dir (d):
    try:
      os.makedirs(d)
    except OSError as e:
      if e.errno != errno.EEXIST:
        raise
    
  
  @staticmethod
  def create_generated_file_web (sessionid):
    d = os.path.join (settings.STORAGE, Constants.STORAGE_GENERATED_DIR)
    Utils._create_dir(d)
    return os.path.join (d, sessionid)
    
  
  @staticmethod
  def get_upload_path (sessionid):
    d = os.path.join (settings.STORAGE, Constants.STORAGE_UPLOAD_DIR)
    Utils._create_dir(d)
    return os.path.join (d, sessionid)
    
  
  @staticmethod
  def get_bigg_models (force = False):
    """ Retrieve the list of models from BiGG
    
    may raise HTTPError or URLError (see api/get_bigg_models)
    """
    d = os.path.join (settings.STORAGE, "cache", "bigg")
    Utils._create_dir(d)
    f = os.path.join (d, "models.json")
    if force or not os.path.isfile (f):
      Utils.__logger.info('need to (re)download the list of models from BiGG')
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
    if not os.path.isfile (f):
      Utils.__logger.info('need to (re)download the model from BiGG: ' + bigg_id)
      urllib.request.urlretrieve ("http://bigg.ucsd.edu/static/models/"+bigg_id+".xml", f)
    
    return f
  
  @staticmethod
  def get_biomodels (force = False):
    d = os.path.join (settings.STORAGE, "cache", "biomodels")
    Utils._create_dir(d)
    f = os.path.join (d, "models.json")
    if force or not os.path.isfile (f):
      Utils.__logger.info('need to (re)download the list of models from biomodels')
      urllib.request.urlretrieve ('https://www.ebi.ac.uk/biomodels/search?format=json&query=genome+scale+metabolic+model+modelformat%3A%22SBML%22+NOT+%22nicolas+le%22&numResults=100&sort=id-asc', f)
    if time.time() - os.path.getmtime(f) > settings.CACHE_BIOMODELS:
      return Utils.get_biomodels (True)
    with open(f, 'r') as json_data:
      return json.load(json_data)
  
  @staticmethod
  def get_biomodel (model_id):
    if not re.match('^[BM][A-Z]+[0-9]{10}$', model_id):
      raise InvalidBiomodelsId ("this biomodels id is invalid: " + model_id)
      
    d = os.path.join (settings.STORAGE, "cache", "biomodels")
    Utils._create_dir(d)
    h = hashlib.sha512 (model_id.encode("utf-8")).hexdigest()
    f = os.path.join (d, h + ".json")
    if not os.path.isfile (f) or time.time() - os.path.getmtime(f) > settings.CACHE_BIOMODEL_FILE:
      Utils.__logger.info('need to (re)download the model information from biomodels: ' + model_id)
      urllib.request.urlretrieve ("https://www.ebi.ac.uk/biomodels/"+model_id+"?format=json", f)
    
    
    try:
      with open(f, 'r') as json_data:
        model = json.load(json_data)
        sbmlfile = os.path.join (d, h + ".sbml")
        if not os.path.isfile (sbmlfile) or time.time() - os.path.getmtime(sbmlfile) > settings.CACHE_BIOMODEL_FILE:
          Utils.__logger.info('need to (re)download the model from biomodels: ' + model_id)
          filename = model["files"]["main"][0]["name"]
          urllib.request.urlretrieve ("https://www.ebi.ac.uk/biomodels/model/download/"+model_id+"?filename="+filename, sbmlfile)
        return sbmlfile
    except JSONDecodeError as e:
      Utils.__logger.critical('error retrieving biomodel '+model_id+': ' + getattr(e, 'message', repr(e)))
      raise UnableToRetrieveBiomodel ("could not read biomodel: " + model_id + " -- json response is invalid")
    
    Utils.__logger.critical('was not able to download biomodel '+model_id+' -- expexted file does not exist')
    raise UnableToRetrieveBiomodel ("could not download biomodel: " + model_id)
  
  @staticmethod
  def get_model_path (model_type, model_id, sessionid):
    if model_type == Constants.SESSION_MODEL_TYPE_UPLOAD:
      return Utils.get_upload_path (sessionid)
    if model_type == Constants.SESSION_MODEL_TYPE_BIGG:
      return Utils.get_bigg_model (model_id)
    if model_type == Constants.SESSION_MODEL_TYPE_BIOMODELS:
      return Utils.get_biomodel (model_id)
    
  @staticmethod
  def del_session_key (request, context, key):
    try:
      del request.session[key]
    except KeyError:
      pass
    if context is not None:
      try:
        del context[key]
      except KeyError:
        pass
    
  @staticmethod
  def human_readable_bytes (byt):
    """
    convert a size in bytes to a human readable string
    
    Parameters:
    -----------
    byt: int
      the byte size
    
    Returns
    -------
    string
      the human readable  size (such as 1 MB or 2.7 TB)
    """
    if byt == 1:
      return "1 Byte"
    if byt < 1024:
      return str (byt) + " Bytes"
    
    for count in ['Bytes', 'KB', 'MB', 'GB', 'TB']:
      if byt > -1024.0 and byt < 1024.0:
        return "%3.1f %s" % (byt, count)
      byt /= 1024.
    return "%3.1f %s" % (byt, 'PB')
