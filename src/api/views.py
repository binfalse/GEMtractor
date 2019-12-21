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

import json
import logging
import os
import tempfile
import urllib
import csv

from django.conf import settings
from django.http import (HttpResponseBadRequest, HttpResponseServerError,
                         JsonResponse)
from django.shortcuts import redirect, reverse
from django.views.decorators.csrf import csrf_exempt
from libsbml import SBMLWriter

from gemtract.forms import ExportForm
from modules.gemtractor.constants import Constants
from modules.gemtractor.gemtractor import GEMtractor
from modules.gemtractor.utils import Utils
from modules.gemtractor.exceptions import (InvalidBiggId, InvalidBiomodelsId,
                                      InvalidGeneComplexExpression,
                                      InvalidGeneExpression, TooBigForBrowser,
                                      UnableToRetrieveBiomodel)

logging.config.dictConfig(settings.LOGGING)
__logger = logging.getLogger(__name__)

def get_session_data (request):
  """
  get your session data at /api/get_session_data
  
  the returned JSON object will have the following keys:
  
  - status: 'success' if it was successful
  - data: dict of the data:
    - session: dict on session keys and values
    - files: array of string about uploaded files
  
  example:
  
  .. code-block:: json
  
    {
      "status": "success",
      "data": {
        "session": {
          "has_session": "yes",
          "model_id": "e_coli_core",
          "model_name": "e_coli_core",
          "model_type": "bigg",
          "filter_species": [],
          "filter_reactions": [],
          "filter_enzymes": [],
          "filter_enzyme_complexes": []
        },
        "files": []
      }
    }
  
  :param request: the request
  :type request: `django:HttpRequest <https://docs.djangoproject.com/en/2.2/_modules/django/http/request/#HttpRequest>`_
  
  :return: json object with information about the user's session
  :rtype: `django:JsonResponse <https://docs.djangoproject.com/en/2.2/ref/request-response/#jsonresponse-objects>`_
  """
  if request.session.session_key is None:
    return JsonResponse ({
            "status":"success",
            "data": {}
          })
  files = []
  if Constants.SESSION_MODEL_TYPE in request.session and request.session[Constants.SESSION_MODEL_TYPE] == Constants.SESSION_MODEL_TYPE_UPLOAD:
    files.append (request.session[Constants.SESSION_MODEL_ID] + " (" + Utils.human_readable_bytes (os.path.getsize(Utils.get_model_path (request.session[Constants.SESSION_MODEL_TYPE], request.session[Constants.SESSION_MODEL_ID], request.session.session_key))) + ")")
  fbpath = Utils.get_upload_path (request.session.session_key) + "-fb-results"
  if os.path.isfile(fbpath):
      files.append ("FB results (" + Utils.human_readable_bytes (os.path.getsize(fbpath)) + ")")
  s = {}
  for key, value in request.session.items ():
    s[key] = value
  return JsonResponse ({
          "status":"success",
          "data": {
            "session": s,
            "files": files
          }
        })

def clear_data (request):
  """
  clear your data at /api/clear_data
  
  will return a JSON object with one key 'status' and the value 'success' if successful
  
  :param request: the request
  :type request: `django:HttpRequest <https://docs.djangoproject.com/en/2.2/_modules/django/http/request/#HttpRequest>`_
  
  :return: json object with information about the success
  :rtype: `django:JsonResponse <https://docs.djangoproject.com/en/2.2/ref/request-response/#jsonresponse-objects>`_
  """
  if Constants.SESSION_MODEL_TYPE in request.session and request.session[Constants.SESSION_MODEL_TYPE] == Constants.SESSION_MODEL_TYPE_UPLOAD:
    os.remove (Utils.get_model_path (request.session[Constants.SESSION_MODEL_TYPE], request.session[Constants.SESSION_MODEL_ID], request.session.session_key))
  Utils.rm_flux_file (request)
  Utils.del_session_key (request, None, Constants.SESSION_HAS_SESSION)
  Utils.del_session_key (request, None, Constants.SESSION_MODEL_ID)
  Utils.del_session_key (request, None, Constants.SESSION_MODEL_NAME)
  Utils.del_session_key (request, None, Constants.SESSION_MODEL_TYPE)
  Utils.del_session_key (request, None, Constants.SESSION_FILTER_SPECIES)
  Utils.del_session_key (request, None, Constants.SESSION_FILTER_REACTION)
  Utils.del_session_key (request, None, Constants.SESSION_FILTER_ENZYMES)
  Utils.del_session_key (request, None, Constants.SESSION_FILTER_ENZYME_COMPLEXES)
  return JsonResponse ({
          "status":"success"
        })

def get_network (request):
  """
  get the network at /api/get_network
  
  as encoded in the currently selected model
  
  the returned JSON object will look like this (check for 'status' = 'success'):
  
  .. code-block:: json
  
    { 
      "status":"success",
      "network":{ 
        "species":[ 
          { 
            "id":"EmptySet",
            "name":"",
            "occ":[ 27, 10 ]
          },
          {"...": "..."}
        ],
        "reactions":[
          { 
            "id":"Reaction1",
            "name":"",
            "rev":false,
            "cons":[ 30, 10 ],
            "prod":[ 17 ],
            "enzs":[ 13 ],
            "enzc":[ 1 ]
          },
          {"...": "..."}
        ],
        "enzs":[
          { 
            "id":"b0351",
            "reactions":[ 22 ],
            "cplx":[ 42 ]
          },
          {"...": "..."}
        ],
        "enzc":[
          { 
            "id":"b0116 + b0738",
            "enzs":[ 12, 28 ],
            "reactions":[ 23 ]
          },
          {"...": "..."}
        ]
      },
      "filter":{ 
        "filter_species":[ "..." ],
        "filter_reactions":[ "..." ],
        "filter_enzymes":[ "..." ],
        "filter_enzyme_complexes":[ "..." ]
      }
    }
  
  special notes:
  
  - network.species[x].occ: in which reactions does the species appear? -> link into the network.reactions array
  - network.reactions[x].cons: which species are consumed? -> link into the network.species array
  - network.reactions[x].prod: which species are produced? -> link into the snetwork.pecies array
  - network.reactions[x].enzs: which enzymes catalyze the reaction? -> link into the network.enzs array
  - network.reactions[x].enzc: which enzyme complexes catalyze the reaction? -> link into the network.enzc array
  - network.enzs[x].reactions: which reactions are catalyzed by the enzyme? -> link into the network.reactions array
  - network.enzs[x].cplx: in which enzyme complexes does the enzyme participate? -> link into the network.enzc array
  - network.enzc[x].enzs: which enzymes participate in this complex? -> link into the network.enzs array
  - network.enzc[x].reactions: which reactions are catalyzed by this complex? -> link into the network.reactions array
  - network.filter.filter_species: list of species identifiers (str)
  - network.filter.filter_reactions: list of reaction identifiers (str)
  - network.filter.filter_enzymes: list of gene identifiers (str)
  - network.filter.filter_enzyme_complexes: list of gene complex identifiers (str)
  
  if the request was not successful, the 'status' key will have a value other than 'success'
  and there will be an 'error' key with some information about what went wrong
  
  
  
  :param request: the request
  :type request: `django:HttpRequest <https://docs.djangoproject.com/en/2.2/_modules/django/http/request/#HttpRequest>`_
  
  :return: json object with information about the network
  :rtype: `django:JsonResponse <https://docs.djangoproject.com/en/2.2/ref/request-response/#jsonresponse-objects>`_
  
  
  """
  
  
  if request.method == 'POST':
    # TODO
    return redirect('index:index')
  
  if Constants.SESSION_MODEL_ID in request.session:
    try:
      __logger.info ("getting sbml")
      gemtractor = GEMtractor (Utils.get_model_path (request.session[Constants.SESSION_MODEL_TYPE], request.session[Constants.SESSION_MODEL_ID], request.session.session_key))
      # gemtractor.get_sbml ()
      network = gemtractor.extract_network_from_sbml ()
      if len (network.species) + len (network.reactions) > settings.MAX_ENTITIES_FILTER:
        raise TooBigForBrowser ("This model is probably too big for your browser... It contains "+str (len (network.species))+" species and "+str (len (network.reactions))+" reactions. We won't load it for filtering, as you're browser is very likely to die when trying to process that amount of data.. Max is currently set to "+str (settings.MAX_ENTITIES_FILTER)+" entities in total. Please export it w/o filtering or use the API instead.")
      __logger.info ("got sbml")
      # ~ network.calc_genenet ()
      # ~ __logger.info ("got genenet")
      filter_species = []
      filter_reaction = []
      filter_enzymes = []
      filter_enzyme_complexes = []
      if Constants.SESSION_FILTER_SPECIES in request.session:
        filter_species = request.session[Constants.SESSION_FILTER_SPECIES]
      if Constants.SESSION_FILTER_REACTION in request.session:
        filter_reaction = request.session[Constants.SESSION_FILTER_REACTION]
      if Constants.SESSION_FILTER_ENZYMES in request.session:
          filter_enzymes = request.session[Constants.SESSION_FILTER_ENZYMES]
      if Constants.SESSION_FILTER_ENZYME_COMPLEXES in request.session:
          filter_enzyme_complexes = request.session[Constants.SESSION_FILTER_ENZYME_COMPLEXES]
      __logger.info ("sending response")
      if len (network.species) + len (network.reactions) + len (network.genes) + len (network.gene_complexes) > settings.MAX_ENTITIES_FILTER:
        raise TooBigForBrowser ("This model is probably too big for your browser... It contains "+str (len (network.species))+" species, "+str (len (network.reactions))+" reactions, "+str (len (network.genes))+" genes, and "+str (len (network.gene_complexes))+" gene complexes. We won't load it for filtering, as you're browser is very likely to die when trying to process that amount of data.. Max is currently set to "+str (settings.MAX_ENTITIES_FILTER)+" entities in total. Please export it w/o filtering or use the API instead.")
      net = network.serialize()
      fluxfile = Utils.get_upload_path (request.session.session_key) + "-fb-results"
      fluxes = {}
      fbpath = Utils.get_upload_path (request.session.session_key) + "-fb-results"
      if os.path.isfile(fbpath):
        with open(fbpath) as csvDataFile:
          csvReader = csv.reader(csvDataFile)
          for row in csvReader:
            if Utils.is_number (row[0]):
              fluxes[row[1]] = row[0]
            else:
              fluxes[row[0]] = row[1]

      __logger.info ("serialised the network")
      return JsonResponse ({
            "status":"success",
            "network":net,
            "fluxes": fluxes,
            "filter": {
            Constants.SESSION_FILTER_SPECIES: filter_species,
            Constants.SESSION_FILTER_REACTION: filter_reaction,
            Constants.SESSION_FILTER_ENZYMES: filter_enzymes,
            Constants.SESSION_FILTER_ENZYME_COMPLEXES: filter_enzyme_complexes,
            }
            })
    except TooBigForBrowser as e:
      __logger.error ("error retrieving network: " + getattr(e, 'message', repr(e)))
      return JsonResponse ({"status":"failed","error":getattr(e, 'message', repr(e))})
    except IOError as e:
      __logger.error ("error retrieving network: " + getattr(e, 'message', repr(e)))
      return JsonResponse ({"status":"failed","error":getattr(e, 'message', repr(e))})
    except InvalidGeneExpression as e:
      __logger.error("InvalidGeneExpression in model " + request.session[Constants.SESSION_MODEL_ID] + ": " + getattr(e, 'message', repr(e)))
      return JsonResponse ({"status":"failed","error": "The model uses an invalid gene expression: " + getattr(e, 'message', repr(e))})
    #return JsonResponse ({"nope": "nope"})
  
  # invalid api request
  return redirect('index:index')

def prepare_filter (request):
  """
  prepare the session filter setup
  
  produced empty arrays for 
  
  - request.session[Constants.SESSION_FILTER_SPECIES]
  - request.session[Constants.SESSION_FILTER_REACTION]
  - request.session[Constants.SESSION_FILTER_ENZYMES]
  - request.session[Constants.SESSION_FILTER_ENZYME_COMPLEXES]
  
  :param request: the request
  :type request: `django:HttpRequest <https://docs.djangoproject.com/en/2.2/_modules/django/http/request/#HttpRequest>`_
  """
  if not Constants.SESSION_FILTER_SPECIES in request.session:
    request.session[Constants.SESSION_FILTER_SPECIES] = []
  if not Constants.SESSION_FILTER_REACTION in request.session:
    request.session[Constants.SESSION_FILTER_REACTION] = []
  if not Constants.SESSION_FILTER_ENZYMES in request.session:
    request.session[Constants.SESSION_FILTER_ENZYMES] = []
  if not Constants.SESSION_FILTER_ENZYME_COMPLEXES in request.session:
    request.session[Constants.SESSION_FILTER_ENZYME_COMPLEXES] = []

def sort_gene_complexes (complexes):
  """
  sorts the genes in the gene complex identifiers
  
  splits every identifier it at " + ", sorts the parts, and joins them with " + "
  
  :Example:
  
  - input: ["z + k + y", "a + b"]
  - output: ["k + y + z", "a + b"]
  
  
  :param complexes: the complex identifiers
  :type complexes: list of str
  
  :return: the sorted identifiers
  :rtype: list of str
  
  """
  c2 = []
  for c in complexes:
    if " + " not in c:
      raise InvalidGeneComplexExpression ("do not understand the following gene complex: " + c)
    c2.append (" + ".join (sorted (c.split (" + "))))
  return c2

def store_filter (request):
  """
  store the user's filters in the session at /api/store_filter
  
  returns the stored filters in a json object just like this
  
  .. code-block:: json
  
    { 
      "status":"success",
      "filter":{ 
        "filter_species":[ 
           "M_13dpg_c",
           "M_2pg_c"
        ],
        "filter_reactions":[ 
           "reaction1"
        ],
        "filter_enzymes":[ 

        ],
        "filter_enzyme_complexes":[ 

        ]
      }
    }
    
  check for "status" = "success"
  
  if the request was not successful, the 'status' key will have a value other than 'success'
  and there will be an 'error' key with some information about what went wrong
  
  :param request: the request
  :type request: `django:HttpRequest <https://docs.djangoproject.com/en/2.2/_modules/django/http/request/#HttpRequest>`_
  
  :return: json object with information about the filters
  :rtype: `django:JsonResponse <https://docs.djangoproject.com/en/2.2/ref/request-response/#jsonresponse-objects>`_
  
  """
  if request.method != 'POST':
    # TODO
    return redirect('index:index')
  
  prepare_filter (request)
    
  succ, data = parse_json_body (request)
  if not succ:
    return JsonResponse ({"status":"failed","error":data})
  
  if "species" in data and isinstance(data["species"], list):
    request.session[Constants.SESSION_FILTER_SPECIES] = data["species"]
  if "reaction" in data and isinstance(data["reaction"], list):
    request.session[Constants.SESSION_FILTER_REACTION] = data["reaction"]
  if "enzymes" in data and isinstance(data["enzymes"], list):
    request.session[Constants.SESSION_FILTER_ENZYMES] = data["enzymes"]
  if "enzyme_complexes" in data and isinstance(data["enzyme_complexes"], list):
    try:
      request.session[Constants.SESSION_FILTER_ENZYME_COMPLEXES] = sort_gene_complexes (data["enzyme_complexes"])
    except InvalidGeneComplexExpression as e:
      return JsonResponse ({"status":"failed","error":str (getattr(e, 'code', repr(e))) + getattr(e, 'message', repr(e))})
  
  return JsonResponse ({"status":"success",
            "filter": {
            Constants.SESSION_FILTER_SPECIES: request.session[Constants.SESSION_FILTER_SPECIES],
            Constants.SESSION_FILTER_REACTION: request.session[Constants.SESSION_FILTER_REACTION],
            Constants.SESSION_FILTER_ENZYMES: request.session[Constants.SESSION_FILTER_ENZYMES],
            Constants.SESSION_FILTER_ENZYME_COMPLEXES: request.session[Constants.SESSION_FILTER_ENZYME_COMPLEXES],
            }})
  
def get_bigg_models (request):
  """
  get the list of models from BiGG at /api/get_bigg_models
  
  returns the models in a json object just like this
  
  .. code-block:: json
  
    { 
      "status":"success",
      "results_count":108,
      "results":[ 
        { 
           "reaction_count":95,
           "metabolite_count":72,
           "organism":"Escherichia coli str. K-12 substr. MG1655",
           "bigg_id":"e_coli_core",
           "gene_count":137
        },
        {"...": "..."}
      ]
    }
    
  check for "status" = "success"
  
  if the request was not successful, the 'status' key will have a value other than 'success'
  and there will be an 'error' key with some information about what went wrong
  
  :param request: the request
  :type request: `django:HttpRequest <https://docs.djangoproject.com/en/2.2/_modules/django/http/request/#HttpRequest>`_
  
  :return: json object with information about the models
  :rtype: `django:JsonResponse <https://docs.djangoproject.com/en/2.2/ref/request-response/#jsonresponse-objects>`_
  
  """
  try:
    models = Utils.get_bigg_models ()
    models["status"] = "success"
    return JsonResponse (models)
  except json.decoder.JSONDecodeError as e:
      __logger.error ("error getting bigg models: " + getattr(e, 'message', repr(e)))
      return JsonResponse ({"status":"failed","error":"is BiGG models down? "+str (getattr(e, 'code', repr(e))) + getattr(e, 'message', repr(e))})
  except urllib.error.HTTPError  as e:
      __logger.error ("error getting bigg models: " + getattr(e, 'message', repr(e)))
      return JsonResponse ({"status":"failed","error":str (getattr(e, 'code', repr(e))) + getattr(e, 'message', repr(e))})
  except urllib.error.URLError as e:
    if hasattr(e, 'reason'):
      __logger.error ("error getting bigg models: " + str (getattr(e, 'reason', repr(e))) + getattr(e, 'message', repr(e)))
      return JsonResponse ({"status":"failed","error":str (getattr(e, 'reason', repr(e))) + getattr(e, 'message', repr(e))})
    elif hasattr(e, 'code'):
      __logger.error ("error getting bigg models: " + str (getattr(e, 'code', repr(e))) + getattr(e, 'message', repr(e)))
      return JsonResponse ({"status":"failed","error":str (getattr(e, 'code', repr(e))) + getattr(e, 'message', repr(e))})
  
def select_bigg_model (request):
  """
  select a certain model from BiGG at /api/select_bigg_model
  
  expects JSON with the key "bigg_id" posted to this endpoint, just like:
  
  .. code-block:: json
  
    {
      "bigg_id":"e_coli_core"
    }
  
  returns JSON {"status": "success"} if successful
  
  if the request was not successful, the 'status' key will have a value other than 'success'
  and there will be an 'error' key with some information about what went wrong
  
  :param request: the request
  :type request: `django:HttpRequest <https://docs.djangoproject.com/en/2.2/_modules/django/http/request/#HttpRequest>`_
  
  :return: json object with information about the success
  :rtype: `django:JsonResponse <https://docs.djangoproject.com/en/2.2/ref/request-response/#jsonresponse-objects>`_
  
  """
  if request.method != 'POST':
    # TODO
    return redirect('index:index')
  
  succ, data = parse_json_body (request, ["bigg_id"])
  if not succ:
    return JsonResponse ({"status":"failed","error":data})
  
  try:
    Utils.get_bigg_model (data["bigg_id"])
    request.session[Constants.SESSION_MODEL_ID] = data["bigg_id"]
    request.session[Constants.SESSION_MODEL_NAME] = data["bigg_id"]
    request.session[Constants.SESSION_MODEL_TYPE] = Constants.SESSION_MODEL_TYPE_BIGG
    Utils.rm_flux_file (request)
    Utils.del_session_key (request, {}, Constants.SESSION_FILTER_SPECIES)
    Utils.del_session_key (request, {}, Constants.SESSION_FILTER_REACTION)
    Utils.del_session_key (request, {}, Constants.SESSION_FILTER_ENZYMES)
    Utils.del_session_key (request, {}, Constants.SESSION_FILTER_ENZYME_COMPLEXES)
    return JsonResponse ({"status":"success"})

  except InvalidBiggId  as e:
      __logger.error ("error getting bigg model: " + data["bigg_id"] + " -- " + getattr(e, 'message', repr(e)))
      return JsonResponse ({"status":"failed","error":getattr(e, 'message', repr(e))})
  except urllib.error.HTTPError  as e:
      __logger.error ("error getting bigg model: " + data["bigg_id"] + " -- " + getattr(e, 'message', repr(e)))
      return JsonResponse ({"status":"failed","error":str (getattr(e, 'code', repr(e))) + getattr(e, 'message', repr(e))})
  except urllib.error.URLError as e:
    if hasattr(e, 'reason'):
      __logger.error ("error getting bigg model: " + data["bigg_id"] + " -- " + str (getattr(e, 'reason', repr(e))) + getattr(e, 'message', repr(e)))
      return JsonResponse ({"status":"failed","error":str (getattr(e, 'reason', repr(e))) + getattr(e, 'message', repr(e))})
    elif hasattr(e, 'code'):
      __logger.error ("error getting bigg model: " + data["bigg_id"] + " -- " + str (getattr(e, 'code', repr(e))) + getattr(e, 'message', repr(e)))
      return JsonResponse ({"status":"failed","error":str (getattr(e, 'code', repr(e))) + getattr(e, 'message', repr(e))})
  
  
  
def get_biomodels (request):
  """
  get the list of models from biomodels at /api/get_biomodels
  
  returns the models in a json object just like this
  
  .. code-block:: json
  
    { 
      "status":"success",
      "matches":6979,
      "models":[ 
        { 
           "format":"SBML",
           "id":"BIOMD0000000239",
           "lastModified":"2016-04-07T23:00:00Z",
           "name":"Jiang2007 - GSIS system, Pancreatic Beta Cells",
           "submissionDate":"2016-04-07T23:00:00Z",
           "submitter":"Kieran Smallbone",
           "url":"https://www.ebi.ac.uk/biomodels/BIOMD0000000239"
        },
        {"...": "..."}
      ]
    }
    
  check for "status" = "success"
  
  if the request was not successful, the 'status' key will have a value other than 'success'
  and there will be an 'error' key with some information about what went wrong
  
  :param request: the request
  :type request: `django:HttpRequest <https://docs.djangoproject.com/en/2.2/_modules/django/http/request/#HttpRequest>`_
  
  :return: json object with information about the models
  :rtype: `django:JsonResponse <https://docs.djangoproject.com/en/2.2/ref/request-response/#jsonresponse-objects>`_
  
  """
  try:
    models = Utils.get_biomodels (request)
    models["status"] = "success"
    return JsonResponse (models)
  except json.decoder.JSONDecodeError as e:
      __logger.error ("error getting biomodels: " + getattr(e, 'message', repr(e)))
      return JsonResponse ({"status":"failed","error":"is biomodels down? "+str (getattr(e, 'code', repr(e))) + getattr(e, 'message', repr(e))})
  except urllib.error.HTTPError  as e:
      __logger.error ("error getting biomodels models: " + getattr(e, 'message', repr(e)))
      return JsonResponse ({"status":"failed","error":str (getattr(e, 'code', repr(e))) + getattr(e, 'message', repr(e))})
  except urllib.error.URLError as e:
    if hasattr(e, 'reason'):
      __logger.error ("error getting biomodels models: " + str (getattr(e, 'reason', repr(e))) + getattr(e, 'message', repr(e)))
      return JsonResponse ({"status":"failed","error":str (getattr(e, 'reason', repr(e))) + getattr(e, 'message', repr(e))})
    elif hasattr(e, 'code'):
      __logger.error ("error getting biomodels models: " + str (getattr(e, 'code', repr(e))) + getattr(e, 'message', repr(e)))
      return JsonResponse ({"status":"failed","error":str (getattr(e, 'code', repr(e))) + getattr(e, 'message', repr(e))})
  
def select_biomodel (request):
  """
  select a certain model from biomodels at /api/select_biomodel
  
  expects JSON with the key "biomodels_id" posted to this endpoint, just like:
  
  .. code-block:: json
  
    {
      "biomodels_id":"BIOMD0000000496"
    }
  
  returns JSON {"status": "success"} if successful
  
  if the request was not successful, the 'status' key will have a value other than 'success'
  and there will be an 'error' key with some information about what went wrong
  
  :param request: the request
  :type request: `django:HttpRequest <https://docs.djangoproject.com/en/2.2/_modules/django/http/request/#HttpRequest>`_
  
  :return: json object with information about the success
  :rtype: `django:JsonResponse <https://docs.djangoproject.com/en/2.2/ref/request-response/#jsonresponse-objects>`_
  
  """
  if request.method != 'POST':
    # TODO
    return redirect('index:index')
  
  succ, data = parse_json_body (request, ["biomodels_id"])
  if not succ:
    return JsonResponse ({"status":"failed","error":data})
  
  try:
    Utils.get_biomodel (data["biomodels_id"])
    request.session[Constants.SESSION_MODEL_ID] = data["biomodels_id"]
    request.session[Constants.SESSION_MODEL_NAME] = data["biomodels_id"]
    request.session[Constants.SESSION_MODEL_TYPE] = Constants.SESSION_MODEL_TYPE_BIOMODELS
    Utils.rm_flux_file (request)
    Utils.del_session_key (request, {}, Constants.SESSION_FILTER_SPECIES)
    Utils.del_session_key (request, {}, Constants.SESSION_FILTER_REACTION)
    Utils.del_session_key (request, {}, Constants.SESSION_FILTER_ENZYMES)
    Utils.del_session_key (request, {}, Constants.SESSION_FILTER_ENZYME_COMPLEXES)
    return JsonResponse ({"status":"success"})

  except UnableToRetrieveBiomodel  as e:
      __logger.error ("error getting biomodels model: "  + data["biomodels_id"] + " -- "+ getattr(e, 'message', repr(e)))
      return JsonResponse ({"status":"failed","error":getattr(e, 'message', repr(e))})
  except InvalidBiomodelsId  as e:
      __logger.error ("error getting biomodels model: "  + data["biomodels_id"] + " -- " + getattr(e, 'message', repr(e)))
      return JsonResponse ({"status":"failed","error":getattr(e, 'message', repr(e))})
  except urllib.error.HTTPError  as e:
      __logger.error ("error getting biomodels model: "  + data["biomodels_id"] + " -- " + getattr(e, 'message', repr(e)))
      return JsonResponse ({"status":"failed","error": "Does such a model exist? Can't download from Biomodels: " + str (getattr(e, 'code', repr(e))) + getattr(e, 'message', repr(e))})
  except urllib.error.URLError as e:
    if hasattr(e, 'reason'):
      __logger.error ("error getting biomodels model: "  + data["biomodels_id"] + " -- " + str (getattr(e, 'reason', repr(e))) + getattr(e, 'message', repr(e)))
      return JsonResponse ({"status":"failed","error":str (getattr(e, 'reason', repr(e))) + getattr(e, 'message', repr(e))})
    elif hasattr(e, 'code'):
      __logger.error ("error getting biomodels model: "  + data["biomodels_id"] + " -- " + str (getattr(e, 'code', repr(e))) + getattr(e, 'message', repr(e)))
      return JsonResponse ({"status":"failed","error":str (getattr(e, 'code', repr(e))) + getattr(e, 'message', repr(e))})
  

def parse_json_body (request, expected_keys = []):
  """
  parse some json payload
  
  loads the json payload from the request and checks if all keys in expected_keys are present
  
  :param request: the request
  :param expected_keys: array of keys to expect
  :type request: `django:HttpRequest <https://docs.djangoproject.com/en/2.2/_modules/django/http/request/#HttpRequest>`_
  :type expected_keys: array of str
  
  :return: [true, parsed data] if all expected keys were found, otherwise [false, error message]
  :rtype: [bool, dict] or [bool, message]
  """
  try:
    data=json.loads(request.body)
    
    for k in expected_keys:
      if k not in data:
        return False, "request is missing key: " + k
    
    return True, data
  except json.decoder.JSONDecodeError:
    return False, "request is not proper json"

def serve_file (request, file_name, file_type):
  """
  server a file at /api/serve/file_name/file_type
  
  serves the file user-generated file
    
  :param request: the request
  :param file_name: the name of the file, will be used in HTTP's Content-Disposition
  :param file_type: the mime type of the file, will be used to indicate the mime-type in the HTTP response
  :type request: `django:HttpRequest <https://docs.djangoproject.com/en/2.2/_modules/django/http/request/#HttpRequest>`_
  :type file_name: str
  :type file_type: str
  
  :return: HTTP 200 and the file or 404 if no such file
  :rtype: `django:HttpResponse <https://docs.djangoproject.com/en/2.2/ref/request-response/#httpresponse-objects>`_
  """
  if request.session.session_key is None:
    return HttpResponseBadRequest("bad session")
  file_path = Utils.create_generated_file_web (request.session.session_key)
  if not os.path.exists(file_path):
    return HttpResponseBadRequest("file does not exist")
  
  return Utils.serve_file (file_path, file_name, file_type)

def export (request):
  """
  export the gemtracted file at /api/export
  
  generates the export and returns some JSON data to call /api/serve ... (-> :func:`serve_file`)
  
  expects a job submitted as HTTP POST form data (see :class:`.gemtract.forms.ExportForm`), just like:
  
  .. code-block:: python
  
    network_type: en
    network_format: sbml
    removing_enzyme_removes_complex: on
  
  returns as JSON object such as:
  
  .. code-block:: python
  
    {
      "status": "success",
      "name": "BIOMD0000000006-gemtracted-EnzymeNetwork.sbml",
      "mime": "application/xml"
    }
    
  check for "status" = "success"
  
  if the request was not successful, the 'status' key will have a value other than 'success'
  and there will be an 'error' key with some information about what went wrong
  
  :param request: the request
  :type request: `django:HttpRequest <https://docs.djangoproject.com/en/2.2/_modules/django/http/request/#HttpRequest>`_
  
  :return: json object with information about the exported file
  :rtype: `django:JsonResponse <https://docs.djangoproject.com/en/2.2/ref/request-response/#jsonresponse-objects>`_
  
  """
  if request.session.session_key is None or Constants.SESSION_MODEL_NAME not in request.session:
    return HttpResponseBadRequest("no such session")
    
  
  prepare_filter (request)
  
  form = ExportForm(request.POST)
  if (form.is_valid()):
    file_name = request.session[Constants.SESSION_MODEL_NAME] + "-gemtracted"
    
    try:
      gemtractor = GEMtractor (Utils.get_model_path (request.session[Constants.SESSION_MODEL_TYPE], request.session[Constants.SESSION_MODEL_ID], request.session.session_key))
    except Exception as e:
      return JsonResponse ({"status":"failed","error":"the model has an issue: " + getattr(e, 'message', repr(e))})
    sbml = gemtractor.get_sbml (
      filter_species = request.session[Constants.SESSION_FILTER_SPECIES],
      filter_reactions = request.session[Constants.SESSION_FILTER_REACTION],
      filter_genes = request.session[Constants.SESSION_FILTER_ENZYMES],
      filter_gene_complexes = request.session[Constants.SESSION_FILTER_ENZYME_COMPLEXES],
      remove_reaction_enzymes_removed = form.cleaned_data['remove_reaction_enzymes_removed'],
      remove_ghost_species = form.cleaned_data['remove_ghost_species'],
      discard_fake_enzymes = form.cleaned_data['discard_fake_enzymes'],
      remove_reaction_missing_species = form.cleaned_data['remove_reaction_missing_species'],
      removing_enzyme_removes_complex = form.cleaned_data['removing_enzyme_removes_complex'])
    
    if form.cleaned_data['network_type'] == 'en':
      file_name = file_name + "-EnzymeNetwork"
      net = gemtractor.extract_network_from_sbml ()
      net.calc_genenet ()
      if form.cleaned_data['network_format'] == 'sbml':
        file_name = file_name + ".sbml"
        file_path = Utils.create_generated_file_web (request.session.session_key)
        net.export_en_sbml (file_path, gemtractor, request.session[Constants.SESSION_MODEL_ID], request.session[Constants.SESSION_MODEL_NAME],
            filter_species = request.session[Constants.SESSION_FILTER_SPECIES],
            filter_reactions = request.session[Constants.SESSION_FILTER_REACTION],
            filter_genes = request.session[Constants.SESSION_FILTER_ENZYMES],
            filter_gene_complexes = request.session[Constants.SESSION_FILTER_ENZYME_COMPLEXES],
            remove_reaction_enzymes_removed = form.cleaned_data['remove_reaction_enzymes_removed'],
            remove_ghost_species = form.cleaned_data['remove_ghost_species'],
            discard_fake_enzymes = form.cleaned_data['discard_fake_enzymes'],
            remove_reaction_missing_species = form.cleaned_data['remove_reaction_missing_species'],
            removing_enzyme_removes_complex = form.cleaned_data['removing_enzyme_removes_complex'])
        if os.path.exists(file_path):
          return JsonResponse ({"status":"success", "name": file_name, "mime": "application/xml"})
        else:
          return JsonResponse ({"status":"failed","error":"error generating SBML file"})
      else:
        if form.cleaned_data['network_format'] == 'dot':
          file_name = file_name + ".dot"
          file_path = Utils.create_generated_file_web (request.session.session_key)
          net.export_en_dot (file_path)
          if os.path.exists(file_path):
            return JsonResponse ({"status":"success", "name": file_name, "mime": "application/dot"})
          else:
            return JsonResponse ({"status":"failed","error":"error generating file"})
        elif form.cleaned_data['network_format'] == 'graphml':
          file_name = file_name + ".graphml"
          file_path = Utils.create_generated_file_web (request.session.session_key)
          net.export_en_graphml (file_path)
          if os.path.exists(file_path):
            return JsonResponse ({"status":"success", "name": file_name, "mime": "application/xml"})
          else:
            return JsonResponse ({"status":"failed","error":"error generating file"})
        elif form.cleaned_data['network_format'] == 'gml':
          file_name = file_name + ".gml"
          file_path = Utils.create_generated_file_web (request.session.session_key)
          net.export_en_gml (file_path)
          if os.path.exists(file_path):
            return JsonResponse ({"status":"success", "name": file_name, "mime": "application/gml"})
          else:
            return JsonResponse ({"status":"failed","error":"error generating file"})
        elif form.cleaned_data['network_format'] == 'csv':
          file_name = file_name + ".csv"
          file_path = Utils.create_generated_file_web (request.session.session_key)
          net.export_en_csv (file_path)
          if os.path.exists(file_path):
            return JsonResponse ({"status":"success", "name": file_name, "mime": "text/csv"})
          else:
            return JsonResponse ({"status":"failed","error":"error generating file"})
        else:
          return JsonResponse ({"status":"failed","error":"invalid format"})
    elif form.cleaned_data['network_type'] == 'rn':
      file_name = file_name + "-ReactionNetwork"
      net = gemtractor.extract_network_from_sbml ()
      net.calc_reaction_net ()
      if form.cleaned_data['network_format'] == 'sbml':
        file_name = file_name + ".sbml"
        file_path = Utils.create_generated_file_web (request.session.session_key)
        net.export_rn_sbml (file_path, gemtractor, request.session[Constants.SESSION_MODEL_ID], request.session[Constants.SESSION_MODEL_NAME],
            filter_species = request.session[Constants.SESSION_FILTER_SPECIES],
            filter_reactions = request.session[Constants.SESSION_FILTER_REACTION],
            filter_genes = request.session[Constants.SESSION_FILTER_ENZYMES],
            filter_gene_complexes = request.session[Constants.SESSION_FILTER_ENZYME_COMPLEXES],
            remove_reaction_enzymes_removed = form.cleaned_data['remove_reaction_enzymes_removed'],
            remove_ghost_species = form.cleaned_data['remove_ghost_species'],
            discard_fake_enzymes = form.cleaned_data['discard_fake_enzymes'],
            remove_reaction_missing_species = form.cleaned_data['remove_reaction_missing_species'],
            removing_enzyme_removes_complex = form.cleaned_data['removing_enzyme_removes_complex'])
        if os.path.exists(file_path):
          return JsonResponse ({"status":"success", "name": file_name, "mime": "application/xml"})
        else:
          return JsonResponse ({"status":"failed","error":"error generating SBML file"})
      else:
        if form.cleaned_data['network_format'] == 'dot':
          file_name = file_name + ".dot"
          file_path = Utils.create_generated_file_web (request.session.session_key)
          net.export_rn_dot (file_path)
          if os.path.exists(file_path):
            return JsonResponse ({"status":"success", "name": file_name, "mime": "application/dot"})
          else:
            return JsonResponse ({"status":"failed","error":"error generating file"})
        elif form.cleaned_data['network_format'] == 'graphml':
          file_name = file_name + ".graphml"
          file_path = Utils.create_generated_file_web (request.session.session_key)
          net.export_rn_graphml (file_path)
          if os.path.exists(file_path):
            return JsonResponse ({"status":"success", "name": file_name, "mime": "application/xml"})
          else:
            return JsonResponse ({"status":"failed","error":"error generating file"})
        elif form.cleaned_data['network_format'] == 'gml':
          file_name = file_name + ".gml"
          file_path = Utils.create_generated_file_web (request.session.session_key)
          net.export_rn_gml (file_path)
          if os.path.exists(file_path):
            return JsonResponse ({"status":"success", "name": file_name, "mime": "application/gml"})
          else:
            return JsonResponse ({"status":"failed","error":"error generating file"})
        elif form.cleaned_data['network_format'] == 'csv':
          file_name = file_name + ".csv"
          file_path = Utils.create_generated_file_web (request.session.session_key)
          net.export_rn_csv (file_path)
          if os.path.exists(file_path):
            return JsonResponse ({"status":"success", "name": file_name, "mime": "text/csv"})
          else:
            return JsonResponse ({"status":"failed","error":"error generating file"})
        else:
          return JsonResponse ({"status":"failed","error":"invalid format"})
    elif form.cleaned_data['network_type'] == 'mn':
      file_name = file_name + "-MetabolicNetwork"
      if form.cleaned_data['network_format'] == 'sbml':
        file_name = file_name + ".sbml"
        file_path = Utils.create_generated_file_web (request.session.session_key)
        SBMLWriter().writeSBML (sbml, file_path)
        if os.path.exists(file_path):
          return JsonResponse ({"status":"success", "name": file_name, "mime": "application/xml"})
        else:
          return JsonResponse ({"status":"failed","error":"error generating file"})
      else:
        net = gemtractor.extract_network_from_sbml ()
        if form.cleaned_data['network_format'] == 'dot':
          file_name = file_name + ".dot"
          file_path = Utils.create_generated_file_web (request.session.session_key)
          net.export_mn_dot (file_path)
          if os.path.exists(file_path):
            return JsonResponse ({"status":"success", "name": file_name, "mime": "application/dot"})
          else:
            return JsonResponse ({"status":"failed","error":"error generating file"})
        elif form.cleaned_data['network_format'] == 'graphml':
          file_name = file_name + ".graphml"
          file_path = Utils.create_generated_file_web (request.session.session_key)
          net.export_mn_graphml (file_path)
          if os.path.exists(file_path):
            return JsonResponse ({"status":"success", "name": file_name, "mime": "application/xml"})
          else:
            return JsonResponse ({"status":"failed","error":"error generating file"})
        elif form.cleaned_data['network_format'] == 'gml':
          file_name = file_name + ".gml"
          file_path = Utils.create_generated_file_web (request.session.session_key)
          net.export_mn_gml (file_path)
          if os.path.exists(file_path):
            return JsonResponse ({"status":"success", "name": file_name, "mime": "application/gml"})
          else:
            return JsonResponse ({"status":"failed","error":"error generating file"})
        elif form.cleaned_data['network_format'] == 'csv':
          file_name = file_name + ".csv"
          file_path = Utils.create_generated_file_web (request.session.session_key)
          net.export_mn_csv (file_path)
          if os.path.exists(file_path):
            return JsonResponse ({"status":"success", "name": file_name, "mime": "text/csv"})
          else:
            return JsonResponse ({"status":"failed","error":"error generating file"})
        else:
          return JsonResponse ({"status":"failed","error":"invalid format"})
    else:
      return JsonResponse ({"status":"failed","error":"invalid network type"})
  return JsonResponse ({"status":"failed","error":"submitted data is invalid"})

@csrf_exempt
def execute (request):
  """
  execute a job at /api/execute
  
  processed the job, that is send as JSON HTTP POST data, such as:
  
  .. code-block:: python
  
    {
      "export": {
          "network_type":"en",
          "network_format":"sbml"
      },
      "filter": {
          "species": ["h2o", "atp"],
          "reactions": [],
          "enzymes": ["gene_abc"],
          "enzyme_complexes": ["a + b + c", "x + Y", "b_098 + r_abc"],
      },
      "file": model
    }
  
  returns HTTP 200 and the generated file, or some other HTTP status and an error message
  
  :param request: the request
  :type request: `django:HttpRequest <https://docs.djangoproject.com/en/2.2/_modules/django/http/request/#HttpRequest>`_
  
  :return: HTTP 200 and the file or 404 if no such file
  :rtype: `django:HttpResponse <https://docs.djangoproject.com/en/2.2/ref/request-response/#httpresponse-objects>`_
  
  """
  if request.method != 'POST':
    return redirect(reverse('index:learn') + '#api')

  succ, data = parse_json_body (request, ["file", "export"])
  if not succ:
    return HttpResponseBadRequest(data)
  
  inputFile = tempfile.NamedTemporaryFile()
  with open(inputFile.name, 'w') as f:
    f.write (data['file'])
  
  filter_species = []
  filter_reactions = []
  filter_enzymes = []
  filter_enzyme_complexes = []
  
  if "filter" in data:
    if "species" in data["filter"]:
      filter_species = data["filter"]["species"]
    if "reactions" in data["filter"]:
      filter_reactions = data["filter"]["reactions"]
    if "enzymes" in data["filter"]:
      filter_enzymes = data["filter"]["enzymes"]
    if "enzyme_complexes" in data["filter"]:
      try:
        filter_enzyme_complexes = sort_gene_complexes (data["filter"]["enzyme_complexes"])
      except InvalidGeneComplexExpression as e:
        return HttpResponseBadRequest ("error: " + str (getattr(e, 'code', repr(e))) + getattr(e, 'message', repr(e)))
  
  if not isinstance(filter_species, list):
    return HttpResponseBadRequest("filter species needs to be an array")
  if not isinstance(filter_reactions, list):
    return HttpResponseBadRequest("filter for reactions needs to be an array")
  if not isinstance(filter_enzymes, list):
    return HttpResponseBadRequest("filter for enzymes needs to be an array")
  if not isinstance(filter_enzyme_complexes, list):
    return HttpResponseBadRequest("filter for enzyme complexes needs to be an array")
  
  export = data["export"]
  
  if "network_type" not in export:
    return HttpResponseBadRequest ("job is missing the desired network_type (en|rn|mn)")
  if "network_format" not in export:
    return HttpResponseBadRequest ("job is missing the desired network_format (sbml|dot|graphml|gml|csv)")
    
  
  remove_reaction_enzymes_removed = True
  remove_reaction_missing_species = False
  remove_ghost_species = False
  discard_fake_enzymes = False
  removing_enzyme_removes_complex = True
  
  if "remove_reaction_enzymes_removed" in export:
    remove_reaction_enzymes_removed = export["remove_reaction_enzymes_removed"]
  if "remove_ghost_species" in export:
    remove_ghost_species = export["remove_ghost_species"]
  if "discard_fake_enzymes" in export:
    discard_fake_enzymes = export["discard_fake_enzymes"]
  if "remove_reaction_missing_species" in export:
    remove_reaction_missing_species = export["remove_reaction_missing_species"]
  if "removing_enzyme_removes_complex" in export:
    removing_enzyme_removes_complex =  export["removing_enzyme_removes_complex"]
  try:
    gemtractor = GEMtractor (inputFile.name)
    sbml = gemtractor.get_sbml (
        filter_species = filter_species,
        filter_reactions = filter_reactions,
        filter_genes = filter_enzymes,
        filter_gene_complexes = filter_enzyme_complexes,
        remove_reaction_enzymes_removed = remove_reaction_enzymes_removed,
        remove_ghost_species = remove_ghost_species,
        discard_fake_enzymes = discard_fake_enzymes,
        remove_reaction_missing_species = remove_reaction_missing_species,
        removing_enzyme_removes_complex = removing_enzyme_removes_complex)
  except Exception as e:
    return HttpResponseBadRequest ("the model has an issue: " + getattr(e, 'message', repr(e)))
  
  outputFile = tempfile.NamedTemporaryFile()
  
  
  
  
  if export["network_type"] == "en":
    net = gemtractor.extract_network_from_sbml ()
    # net.calc_genenet ()
    if export["network_format"] == "sbml":
      net.export_en_sbml (outputFile.name, gemtractor, sbml.getModel ().getId (), sbml.getModel ().getName (), 
          filter_species = filter_species, 
          filter_reactions = filter_reactions,
          filter_genes = filter_enzymes,
          filter_gene_complexes = filter_enzyme_complexes,
          remove_reaction_enzymes_removed = remove_reaction_enzymes_removed,
          remove_ghost_species = remove_ghost_species,
          discard_fake_enzymes = discard_fake_enzymes,
          remove_reaction_missing_species = remove_reaction_missing_species,
          removing_enzyme_removes_complex = removing_enzyme_removes_complex)
      if os.path.exists(outputFile.name):
        return Utils.serve_file (outputFile.name, "gemtracted-model.sbml", "application/xml")
      else:
        return HttpResponseServerError ("couldn't generate the sbml file")
    elif export["network_format"] == "dot":
      net.export_en_dot (outputFile.name)
      if os.path.exists(outputFile.name):
        return Utils.serve_file (outputFile.name, "gemtracted-model.dot", "application/dot")
      else:
        return HttpResponseServerError ("couldn't generate the dot file")
    elif export["network_format"] == "graphml":
      net.export_en_graphml (outputFile.name)
      if os.path.exists(outputFile.name):
        return Utils.serve_file (outputFile.name, "gemtracted-model.graphml", "application/xml")
      else:
        return HttpResponseServerError ("couldn't generate the graphml file")
    elif export["network_format"] == "gml":
      net.export_en_gml (outputFile.name)
      if os.path.exists(outputFile.name):
        return Utils.serve_file (outputFile.name, "gemtracted-model.gml", "application/gml")
      else:
        return HttpResponseServerError ("couldn't generate the gml file")
    elif export["network_format"] == "csv":
      net.export_en_csv (outputFile.name)
      if os.path.exists(outputFile.name):
        return Utils.serve_file (outputFile.name, "gemtracted-model.csv", "text/csv")
      else:
        return HttpResponseServerError ("couldn't generate the csv file")
  elif export["network_type"] == "rn":
    net = gemtractor.extract_network_from_sbml ()
    # net.calc_reaction_net ()
    if export["network_format"] == "sbml":
      net.export_rn_sbml (outputFile.name, gemtractor, sbml.getModel ().getId () + "_RN", sbml.getModel ().getName () + " converted to ReactionNetwork",
          filter_species = filter_species, 
          filter_reactions = filter_reactions,
          filter_genes = filter_enzymes,
          filter_gene_complexes = filter_enzyme_complexes,
          remove_reaction_enzymes_removed = remove_reaction_enzymes_removed,
          remove_ghost_species = remove_ghost_species,
          discard_fake_enzymes = discard_fake_enzymes,
          remove_reaction_missing_species = remove_reaction_missing_species,
          removing_enzyme_removes_complex = removing_enzyme_removes_complex)
      if os.path.exists(outputFile.name):
        return Utils.serve_file (outputFile.name, "gemtracted-model.sbml", "application/xml")
      else:
        return HttpResponseServerError ("couldn't generate the sbml file")
    elif export["network_format"] == "dot":
      net.export_rn_dot (outputFile.name)
      if os.path.exists(outputFile.name):
        return Utils.serve_file (outputFile.name, "gemtracted-model.dot", "application/dot")
      else:
        return HttpResponseServerError ("couldn't generate the dot file")
    elif export["network_format"] == "graphml":
      net.export_rn_graphml (outputFile.name)
      if os.path.exists(outputFile.name):
        return Utils.serve_file (outputFile.name, "gemtracted-model.graphml", "application/xml")
      else:
        return HttpResponseServerError ("couldn't generate the graphml file")
    elif export["network_format"] == "gml":
      net.export_rn_gml (outputFile.name)
      if os.path.exists(outputFile.name):
        return Utils.serve_file (outputFile.name, "gemtracted-model.gml", "application/gml")
      else:
        return HttpResponseServerError ("couldn't generate the gml file")
    elif export["network_format"] == "csv":
      net.export_rn_csv (outputFile.name)
      if os.path.exists(outputFile.name):
        return Utils.serve_file (outputFile.name, "gemtracted-model.csv", "text/csv")
      else:
        return HttpResponseServerError ("couldn't generate the csv file")
  elif export["network_type"] == "mn":
    if export["network_format"] == "sbml":
      SBMLWriter().writeSBML (sbml, outputFile.name)
      if os.path.exists(outputFile.name):
        return Utils.serve_file (outputFile.name, "gemtracted-model.sbml", "application/xml")
      else:
        return HttpResponseServerError ("couldn't generate the sbml file")
    else:
      net = gemtractor.extract_network_from_sbml ()
      if export["network_format"] == "dot":
        net.export_mn_dot (outputFile.name)
        if os.path.exists(outputFile.name):
          return Utils.serve_file (outputFile.name, "gemtracted-model.dot", "application/dot")
        else:
          return HttpResponseServerError ("couldn't generate the dot file")
      elif export["network_format"] == "graphml":
        net.export_mn_graphml (outputFile.name)
        if os.path.exists(outputFile.name):
          return Utils.serve_file (outputFile.name, "gemtracted-model.graphml", "application/xml")
        else:
          return HttpResponseServerError ("couldn't generate the graphml file")
      elif export["network_format"] == "gml":
        net.export_mn_gml (outputFile.name)
        if os.path.exists(outputFile.name):
          return Utils.serve_file (outputFile.name, "gemtracted-model.gml", "application/gml")
        else:
          return HttpResponseServerError ("couldn't generate the gml file")
      elif export["network_format"] == "csv":
        net.export_mn_csv (outputFile.name)
        if os.path.exists(outputFile.name):
          return Utils.serve_file (outputFile.name, "gemtracted-model.csv", "text/csv")
        else:
          return HttpResponseServerError ("couldn't generate the csv file")
  
  
  return HttpResponseBadRequest ("job is not well formed, not sure what to do...")
  
  




@csrf_exempt
def status (request):
  """
  get the status of this instance
  
  this will clean obsolete files
  
  send the health-secret as JSON POST to get health information about this instance:
  
  .. code-block:: json
  
    {"secret": "XXXX"}
  
  this will then return a json object listing how many files and data we store, such as:
  
  .. code-block:: json
  
    {
      "status": "success",
      "cache": {
        "biomodels": {
          "nfiles": 8,
          "size": 212254013
        },
        "bigg": {
          "nfiles": 5,
          "size": 59429817
        }
      },
      "user": {
        "uploaded": {
          "nfiles": 0,
          "size": 0
        },
        "generated": {
          "nfiles": 0,
          "size": 0
        }
      }
    }
  
  
  :param request: the request
  :type request: `django:HttpRequest <https://docs.djangoproject.com/en/2.2/_modules/django/http/request/#HttpRequest>`_
  
  :return: json object with information about the exported file
  :rtype: `django:JsonResponse <https://docs.djangoproject.com/en/2.2/ref/request-response/#jsonresponse-objects>`_
  """
  
  Utils.cleanup ()
  
  response = {"status": "success"}
  
  if request.method == 'POST':
    succ, data = parse_json_body (request, [])
    if not succ:
      return HttpResponseBadRequest(data)
    
    if settings.HEALTH_SECRET == "" or ("secret" in data and data["secret"] == settings.HEALTH_SECRET):
      Utils.collect_stats (response)
  
  # TODO bit more information
  return JsonResponse (response)
