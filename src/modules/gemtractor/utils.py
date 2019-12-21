# This file is part of the GEMtractor
# Copyright (C) 2019 Martin Scharm <https://binfalse.de>
# 
# The GEMtractor is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# The GEMtractor is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import errno
import hashlib
import json
import logging
import os
import re
import time
import urllib.request
from shutil import copyfile

from django.conf import settings
from django.http import HttpResponse

from .constants import Constants
from .exceptions import UnableToRetrieveBiomodel, InvalidBiomodelsId, InvalidBiggId


class Utils:
  
  """
  some utils that may make life easier
  """
  
  __logger = logging.getLogger(__name__)
  
  
  @staticmethod
  def __cleanup (root_dir, max_age):
    """
    get rid of old stuff
    
    will remove cached and unused file in a certain directory
    
    :param root_dir: the directory to traverse
    :param max_age: the max age of files that will survive
    
    :type root_dir: str
    :type max_age: int
    """
    for dirName, subdirList, fileList in os.walk(root_dir):
      for fname in fileList:
        if  time.time() - os.path.getmtime(os.path.join (dirName, fname)) > max_age:
          try:
            Utils.__logger.info('deleting old file: ' + os.path.join (dirName, fname))
            os.remove (os.path.join (dirName, fname))
          except Exception as e:
            Utils.__logger.critical('error deleting old file: ' + os.path.join (dirName, fname) + " -- error: " + getattr(e, 'message', repr(e)))
    
  
  
  @staticmethod
  def cleanup ():
    """
    get rid of old stuff
    
    will remove cached and unused file for the whole instance
    """
    Utils.__cleanup (os.path.join (settings.STORAGE, "cache", "biomodels"), settings.CACHE_BIOMODELS_MODEL)
    Utils.__cleanup (os.path.join (settings.STORAGE, "cache", "bigg"), settings.CACHE_BIGG_MODEL)
    Utils.__cleanup (os.path.join (settings.STORAGE, Constants.STORAGE_GENERATED_DIR), settings.KEEP_GENERATED)
    Utils.__cleanup (os.path.join (settings.STORAGE, Constants.STORAGE_UPLOAD_DIR), settings.KEEP_UPLOADED)
            
  
  
  @staticmethod
  def rm_flux_file (request):
    fbpath = Utils.get_upload_path (request.session.session_key) + "-fb-results"
    if os.path.isfile(fbpath):
        os.remove (fbpath)
  
  @staticmethod
  def __collect_stats (root_dir):
    """
    collect some stats about the files below root_dir
    
    :param root_dir: the root directory
    :type root_dir: str
    
    :return: tupel of number of files and the sum of their sizes
    :rtype: typel of ints
    """
    nfiles = 0
    size = 0
    for dirName, subdirList, fileList in os.walk(root_dir):
      for fname in fileList:
        nfiles += 1
        size += os.path.getsize (os.path.join (dirName, fname))
    
    return nfiles, size
  
  @staticmethod
  def collect_stats (response_obj):
    """
    collect some health stats about this instance
    
    will check cached and uploaded files and their sizes
    
    :param response_obj: the response object to attach the information to
    :type response_obj: dict
    """
    response_obj['cache'] = {}
    response_obj['user'] = {}
    
    nfiles, size = Utils.__collect_stats (os.path.join (settings.STORAGE, "cache", "biomodels"))
    response_obj['cache']['biomodels'] = {"nfiles" : nfiles, "size": size}
    
    nfiles, size = Utils.__collect_stats (os.path.join (settings.STORAGE, "cache", "bigg"))
    response_obj['cache']['bigg'] = {"nfiles" : nfiles, "size": size}
    
    nfiles, size = Utils.__collect_stats (os.path.join (settings.STORAGE,  Constants.STORAGE_UPLOAD_DIR))
    response_obj['user']['uploaded'] = {"nfiles" : nfiles, "size": size}
    
    nfiles, size = Utils.__collect_stats (os.path.join (settings.STORAGE,  Constants.STORAGE_GENERATED_DIR))
    response_obj['user']['generated'] = {"nfiles" : nfiles, "size": size}
    
  
  @staticmethod
  def add_model_note (model, filter_species, filter_reactions, filter_enzymes, filter_enzyme_complexes, remove_reaction_enzymes_removed, remove_ghost_species, discard_fake_enzymes, remove_reaction_missing_species, removing_enzyme_removes_complex):
    """'
    annotate the model to indicate that is has been generated using the GEMtractor
    
    adds a note to the model note..
    
    :param model: the SBML model
    :param filter_species: species identifiers to get rid of
    :param filter_reactions: reaction identifiers to get rid of
    :param filter_enzymes: enzyme identifiers to get rid of
    :param filter_enzyme_complexes: enzyme-complex identifiers to get rid of, every list-item should be of format: 'A + B + gene42'
    :param remove_reaction_enzymes_removed: should we remove a reaction if all it's genes were removed?
    :param remove_ghost_species: should species be removed, that do not participate in any reaction anymore - even though they might be required in other entities?
    :param discard_fake_enzymes: should fake enzymes (implicitly assumes enzymes, if no enzymes are annotated to a reaction) be removed?
    :param remove_reaction_missing_species: remove a reaction if one of the participating genes was removed?
    :param removing_enzyme_removes_complex: if an enzyme is removed, should also all enzyme complexes be removed in which it participates?
    
    :type model: `libsbml:Model <http://sbml.org/Special/Software/libSBML/docs/python-api/classlibsbml_1_1_model.html>`_
    :type filter_species: list of str
    :type filter_reactions: list of str
    :type filter_enzymes: list of str
    :type filter_enzyme_complexes: list of str
    :type remove_reaction_enzymes_removed: bool
    :type remove_ghost_species: bool
    :type discard_fake_enzymes: bool
    :type remove_reaction_missing_species: bool
    :type removing_enzyme_removes_complex: bool
    
    
    """
    # TODO can we do better? eg. annotate with proper structure?
    note = model.getNotesString ()
    # print (note)
    if note is None or len (note) < 1 or "</body>" not in note:
        note = '<notes><body xmlns="http://www.w3.org/1999/xhtml"></body></notes>'
    
    additional_note = "<p>This file was generated at the GEMtractor (https://gemtractor.bio.informatik.uni-rostock.de/) using the following settings:</p>"
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
    if filter_enzymes is not None and len (filter_enzymes) > 0:
      additional_note = additional_note + "<p>Filter Enzymes:</p><ul>"
      for s in filter_enzymes:
        additional_note = additional_note + "<li>"+s+"</li>"
      additional_note = additional_note + "</ul>"
    if filter_enzyme_complexes is not None and len (filter_enzyme_complexes) > 0:
      additional_note = additional_note + "<p>Filter Enzyme Complexes:</p><ul>"
      for s in filter_enzyme_complexes:
        additional_note = additional_note + "<li>"+s+"</li>"
      additional_note = additional_note + "</ul>"
    additional_note = additional_note + "<p>Remove reactions whose enzymes are removed: " +str(remove_reaction_enzymes_removed)+ "</p>"
    additional_note = additional_note + "<p>Remove ghost species: " +str(remove_ghost_species)+ "</p>"
    additional_note = additional_note + "<p>Discard fake enzymes: " +str(discard_fake_enzymes)+ "</p>"
    additional_note = additional_note + "<p>Remove reactions that are missing a species: " +str(remove_reaction_missing_species)+ "</p>"
    additional_note = additional_note + "<p>Remove enzyme complexes which are missing an enzyme: " +str(removing_enzyme_removes_complex)+ "</p>"
    
    model.setNotes (note.replace ("</body>", additional_note + "</body>"))
  
  @staticmethod
  def _create_dir (d):
    """
    create some directory (recursively) the pythonic way
    
    :param d: the directories to create
    :type d: str
    """
    try:
      os.makedirs(d)
    except OSError as e:
      if e.errno != errno.EEXIST:
        raise
    
  
  @staticmethod
  def create_generated_file_web (sessionid):
    """
    get a file to generate something for the user
    
    :param sessionid: the users' session id
    :type sessionid: str
    
    :return: path to a file that is safe for the user
    :rtype: str
    
    """
    d = os.path.join (settings.STORAGE, Constants.STORAGE_GENERATED_DIR)
    Utils._create_dir(d)
    return os.path.join (d, sessionid)
    
  
  @staticmethod
  def get_upload_path (sessionid):
    """
    get a file to upload something for the user
    
    :param sessionid: the users' session id
    :type sessionid: str
    
    :return: path to a file that is safe for the user
    :rtype: str
    
    """
    d = os.path.join (settings.STORAGE, Constants.STORAGE_UPLOAD_DIR)
    Utils._create_dir(d)
    return os.path.join (d, sessionid)
    
  
  @staticmethod
  def get_bigg_models (force = False):
    """ Retrieve the list of models from BiGG
    
    :param force: should the cache be renewed even if it's not too old?
    :type force: bool
    
    :return: the list of models at BiGG
    :rtype: json object
    
    :raises HTTPError: if there was a problem contacting BiGG
    :raises URLError: if there was a problem contacting BiGG
    :raises JSONDecodeError: if the BiGG answer is no proper JSON
    """
    d = os.path.join (settings.STORAGE, "cache", "bigg")
    Utils._create_dir(d)
    f = os.path.join (d, "models.json")
    if force or not os.path.isfile (f):
      Utils.__logger.info('need to (re)download the list of models from BiGG')
      urllib.request.urlretrieve (settings.URLS_BIGG_MODELS, f)
    if time.time() - os.path.getmtime(f) > settings.CACHE_BIGG:
      return Utils.get_bigg_models (True)
    try:
      with open(f, 'r') as json_data:
        return json.load(json_data)
    except Exception as e:
      Utils.__logger.critical('error retrieving bigg models list -- json error: ' + getattr(e, 'message', repr(e)))
      try:
        os.remove (f)
      except Exception as e:
        Utils.__logger.critical('error removing bigg models list: ' + getattr(e, 'message', repr(e)))
      raise e
      
  @staticmethod
  def _get_bigg_model_base_path (model_id):
    """
    get the path at which we would store a BiGG model
    
    :param model_id: the model's id
    :type model_id: str

    :return: the path to the cached BiGG model
    :rtype: str
    """
    if not re.match('^[a-zA-Z0-9_-]+$', model_id):
      raise InvalidBiggId ("this BiGG id is invalid: " + model_id)
    d = os.path.join (settings.STORAGE, "cache", "bigg")
    Utils._create_dir(d)
    h = hashlib.sha512 (model_id.encode("utf-8")).hexdigest()
    return os.path.join (d, h)
  
  @staticmethod
  def rm_cached_bigg_model (model_id):
    """
    remove a cached BiGG model
    
    uses :func:`_get_bigg_model_base_path` to determine the path to the model
    
    :param model_id: the model's id
    :type model_id: str

    """
    try:
      os.remove (Utils._get_bigg_model_base_path (model_id))
    except Exception as e:
      Utils.__logger.critical('error removing cached biomodels sbml file: ' + model_id + ' -- ' + getattr(e, 'message', repr(e)))
  
  @staticmethod
  def get_bigg_model (model_id, force = False):
    """ Retrieve a specific model from BiGG
    
    uses :func:`_get_bigg_model_base_path` to determine the path to the model
    
    :param model_id: the model's id
    :param force: should the cache be renewed even if it's not too old?
    :type model_id: str
    :type force: bool
    
    :return: the path to the model
    :rtype: str
    
    :raises HTTPError: if there was a problem contacting BiGG
    :raises URLError: if there was a problem contacting BiGG
    """
    f = Utils._get_bigg_model_base_path (model_id)
    if force or not os.path.isfile (f):
      Utils.__logger.info('need to (re)download the model from BiGG: ' + model_id)
      urllib.request.urlretrieve (settings.URLS_BIGG_MODEL (model_id), f)
    if time.time() - os.path.getmtime(f) > settings.CACHE_BIGG_MODEL:
      return Utils.get_bigg_model (model_id, True)
    
    return f
  
  @staticmethod
  def get_biomodels (request, force = False):
    """ Retrieve the list of models from Biomodels
    
    :param force: should the cache be renewed even if it's not too old?
    :type force: bool
    
    :return: the list of models for our search at Biomodels
    :rtype: json object
    
    :raises HTTPError: if there was a problem contacting Biomodels
    :raises URLError: if there was a problem contacting Biomodels
    :raises JSONDecodeError: if the Biomodels answer is no proper JSON
    """
    d = os.path.join (settings.STORAGE, "cache", "biomodels")
    Utils._create_dir(d)
    f = os.path.join (d, "models.json")
    if force or not os.path.isfile (f):
      biomodels_url = settings.URLS_BIOMODELS
      if 'http' not in biomodels_url:
        copyfile (biomodels_url, f)
      else:
        urllib.request.urlretrieve (biomodels_url, f)
    if time.time() - os.path.getmtime(f) > settings.CACHE_BIOMODELS:
      return Utils.get_biomodels (True)
    try:
      with open(f, 'r') as json_data:
        return json.load(json_data)
    except Exception as e:
      Utils.__logger.critical('error retrieving biomodels list -- json error: ' + getattr(e, 'message', repr(e)))
      try:
        os.remove (f)
      except Exception as e:
        Utils.__logger.critical('error removing biomodels list: ' + getattr(e, 'message', repr(e)))
      raise e
      
  @staticmethod
  def _get_biomodel_base_path (model_id):
    """
    get the path at which we would store a biomodels model
    
    :param model_id: the model's id
    :type model_id: str

    :return: the path to the cached model from biomodels
    :rtype: str
    """
    if not re.match('^[BM][A-Z]+[0-9]{10}$', model_id):
      raise InvalidBiomodelsId ("this biomodels id is invalid: " + model_id)
    d = os.path.join (settings.STORAGE, "cache", "biomodels")
    Utils._create_dir(d)
    h = hashlib.sha512 (model_id.encode("utf-8")).hexdigest()
    return os.path.join (d, h)
  
  @staticmethod
  def rm_cached_biomodel (model_id):
    """
    remove a cached model from biomodels
    
    uses :func:`_get_biomodel_base_path` to determine the path to the model
    
    :param model_id: the model's id
    :type model_id: str

    """
    try:
      os.remove (Utils._get_biomodel_base_path (model_id) + ".sbml")
    except Exception as e:
      Utils.__logger.critical('error removing cached biomodels sbml file: ' + model_id + ' -- ' + getattr(e, 'message', repr(e)))
    try:
      os.remove (Utils._get_biomodel_base_path (model_id) + ".json")
    except Exception as e:
      Utils.__logger.critical('error removing cached biomodels json file: ' + model_id + ' -- ' + getattr(e, 'message', repr(e)))
  
  @staticmethod
  def get_biomodel (model_id, force = False):
    """ Retrieve a specific model from biomodels
    
    uses :func:`_get_biomodel_base_path` to determine the path to the model
    
    :param model_id: the model's id
    :param force: should the cache be renewed even if it's not too old?
    :type model_id: str
    :type force: bool
    
    :return: the path to the model
    :rtype: str
    
    :raises HTTPError: if there was a problem contacting biomodels
    :raises URLError: if there was a problem contacting biomodels
    """
    f = Utils._get_biomodel_base_path (model_id) + ".json"
    if force or not os.path.isfile (f):
      Utils.__logger.info('need to (re)download the model information from biomodels: ' + model_id)
      urllib.request.urlretrieve (settings.URLS_BIOMODEL_INFO (model_id), f)
    if  time.time() - os.path.getmtime(f) > settings.CACHE_BIOMODELS_MODEL:
      return Utils.get_biomodel (model_id, True)
    
    
    try:
      with open(f, 'r') as json_data:
        model = json.load(json_data)
        sbmlfile = Utils._get_biomodel_base_path (model_id) + ".sbml"
        if force or not os.path.isfile (sbmlfile):
          Utils.__logger.info('need to (re)download the model from biomodels: ' + model_id)
          filename = model["files"]["main"][0]["name"]
          urllib.request.urlretrieve (settings.URLS_BIOMODEL_SBML (model_id, filename), sbmlfile)
        if time.time() - os.path.getmtime(sbmlfile) > settings.CACHE_BIOMODELS_MODEL:
          return Utils.get_biomodel (model_id, True)
        return sbmlfile
    except json.decoder.JSONDecodeError as e:
      Utils.__logger.critical('error retrieving biomodel '+model_id+': ' + getattr(e, 'message', repr(e)))
      Utils.rm_cached_biomodel (model_id)
      raise UnableToRetrieveBiomodel ("could not read biomodel: " + model_id + " -- json response is invalid")
  
  @staticmethod
  def get_model_path (model_type, model_id, sessionid):
    """
    get the path to a model
    
    depending on how the model was obtained (downloaded from BiGG/biomodels or uploaded) the path may differ
    
    :param model_type: the obtain type (see :class:`.constants.Constants`)
    :param model_id: the model's id
    :param sessionid: the user's session id - only relevant if the model was uploaded
    
    :type model_type: str
    :type model_id: str
    :type sessionid: str
    
    :return: the path to the model
    :rtype: str
    
    """
    if model_type == Constants.SESSION_MODEL_TYPE_UPLOAD:
      return Utils.get_upload_path (sessionid)
    if model_type == Constants.SESSION_MODEL_TYPE_BIGG:
      return Utils.get_bigg_model (model_id)
    if model_type == Constants.SESSION_MODEL_TYPE_BIOMODELS:
      return Utils.get_biomodel (model_id)
      
  @staticmethod
  def serve_file (file_path, file_name, file_type):
    """
    deliver a file to the user
    
    :param file_path: the path to the file to deliver
    :param file_name: the name to suggest to the client (browser)
    :param file_type: the mime type to suggest to the client (browser)
    :type file_path: str
    :type file_name: str
    :type file_type: str
    """
    with open(file_path, 'rb') as fh:
      response = HttpResponse(fh.read(), content_type=file_type)
      response['Content-Disposition'] = 'attachment; filename=' + file_name
      return response
    
  @staticmethod
  def del_session_key (request, context, key):
    """
    delete a certain session key as requested by the user
    
    :param request: django's HTTP request object
    :param context: the context object
    :param key: the key to delete
    :type key: str
    :type context: dict
    :type request: `django:HttpRequest <https://docs.djangoproject.com/en/2.2/_modules/django/http/request/#HttpRequest>`_
    """
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
    
    :param byt: the byte size
    :type byt: int
    
    :return: the human readable  size (such as 1 MB or 2.7 TB)
    :rtype: str
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
  
  @staticmethod
  def is_number (s):
    try:
        float(s)
        return True
    except ValueError:
        return False
