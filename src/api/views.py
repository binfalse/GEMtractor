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

from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
import logging
from django.conf import settings
import json
import os
from django.http import JsonResponse
from modules.enalyzer_utils.utils import Utils, InvalidGeneExpression, InvalidBiomodelsId, UnableToRetrieveBiomodel, InvalidBiggId, TooBigForBrowser
from modules.enalyzer_utils.enalyzer import Enalyzer
from modules.enalyzer_utils.constants import Constants
import urllib

logging.config.dictConfig(settings.LOGGING)
__logger = logging.getLogger(__name__)

def get_session_data (request):
  if request.session.session_key is None:
    return JsonResponse ({
            "status":"success",
            "data": {}
          })
  files = []
  if Constants.SESSION_MODEL_TYPE in request.session and request.session[Constants.SESSION_MODEL_TYPE] == Constants.SESSION_MODEL_TYPE_UPLOAD:
    files.append (request.session[Constants.SESSION_MODEL_ID] + " (" + Utils.human_readable_bytes (os.path.getsize(Utils.get_model_path (request.session[Constants.SESSION_MODEL_TYPE], request.session[Constants.SESSION_MODEL_ID], request.session.session_key))) + ")")
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
  Utils.del_session_key (request, None, Constants.SESSION_HAS_SESSION)
  Utils.del_session_key (request, None, Constants.SESSION_MODEL_ID)
  Utils.del_session_key (request, None, Constants.SESSION_MODEL_NAME)
  Utils.del_session_key (request, None, Constants.SESSION_MODEL_TYPE)
  Utils.del_session_key (request, None, Constants.SESSION_FILTER_SPECIES)
  Utils.del_session_key (request, None, Constants.SESSION_FILTER_REACTION)
  Utils.del_session_key (request, None, Constants.SESSION_FILTER_GENES)
  return JsonResponse ({
          "status":"success"
        })

def get_network (request):
  if request.method == 'POST':
    # TODO
    return redirect('index:index')
  
  if Constants.SESSION_MODEL_ID in request.session:
    enalyzer = Enalyzer (Utils.get_model_path (request.session[Constants.SESSION_MODEL_TYPE], request.session[Constants.SESSION_MODEL_ID], request.session.session_key))
    try:
      __logger.info ("getting sbml")
      network = enalyzer.extract_network_from_sbml (enalyzer.get_sbml ())
      if len (network.species) + len (network.reactions) > 10000:
        raise TooBigForBrowser ("This model is probably too big for your browser... It contains "+str (len (network.species))+" species, "+str (len (network.reactions))+" reactions. We won't load it for filtering, as you're browser is very likely to die when trying to process that amount of data.. Please export it directly or try the API instead.")
      __logger.info ("got sbml")
      network.calc_genenet ()
      __logger.info ("got genenet")
      filter_species = []
      filter_reaction = []
      filter_genes = []
      if Constants.SESSION_FILTER_SPECIES in request.session:
        filter_species = request.session[Constants.SESSION_FILTER_SPECIES]
      if Constants.SESSION_FILTER_REACTION in request.session:
        filter_reaction = request.session[Constants.SESSION_FILTER_REACTION]
      if Constants.SESSION_FILTER_GENES in request.session:
          filter_genes = request.session[Constants.SESSION_FILTER_GENES]
      __logger.info ("sending response")
      if len (network.species) + len (network.reactions) + len (network.genenet) > 10000:
        raise TooBigForBrowser ("This model is probably too big for your browser... It contains "+str (len (network.species))+" species, "+str (len (network.reactions))+" reactions, "+str (len (network.genenet))+" gene combinations. We won't load it for filtering, as you're browser is very likely to die when trying to process that amount of data.. Please export it directly or try the API instead.")
      net = network.serialize()
      __logger.info ("serialised the network")
      return JsonResponse ({
            "status":"success",
            "network":net,
            "filter": {
            Constants.SESSION_FILTER_SPECIES: filter_species,
            Constants.SESSION_FILTER_REACTION: filter_reaction,
            Constants.SESSION_FILTER_GENES: filter_genes,
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
  
  
def store_filter (request):
  if request.method != 'POST':
    # TODO
    return redirect('index:index')
  
  if not Constants.SESSION_FILTER_SPECIES in request.session:
    request.session[Constants.SESSION_FILTER_SPECIES] = []
  if not Constants.SESSION_FILTER_REACTION in request.session:
    request.session[Constants.SESSION_FILTER_REACTION] = []
  if not Constants.SESSION_FILTER_GENES in request.session:
    request.session[Constants.SESSION_FILTER_GENES] = []
    
  succ, data = parse_json_body (request)
  if not succ:
    return JsonResponse ({"status":"failed","error":data})
  
  if "species" in data:
    request.session[Constants.SESSION_FILTER_SPECIES] = data["species"]
  if "reaction" in data:
    request.session[Constants.SESSION_FILTER_REACTION] = data["reaction"]
  if "genes" in data:
    request.session[Constants.SESSION_FILTER_GENES] = data["genes"]
  
  return JsonResponse ({"status":"success",
            "filter": {
            Constants.SESSION_FILTER_SPECIES: request.session[Constants.SESSION_FILTER_SPECIES],
            Constants.SESSION_FILTER_REACTION: request.session[Constants.SESSION_FILTER_REACTION],
            Constants.SESSION_FILTER_GENES: request.session[Constants.SESSION_FILTER_GENES],
            }})
  
def get_bigg_models (request):
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
    Utils.del_session_key (request, {}, Constants.SESSION_FILTER_SPECIES)
    Utils.del_session_key (request, {}, Constants.SESSION_FILTER_REACTION)
    Utils.del_session_key (request, {}, Constants.SESSION_FILTER_GENES)
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
  try:
    models = Utils.get_biomodels ()
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
    Utils.del_session_key (request, {}, Constants.SESSION_FILTER_SPECIES)
    Utils.del_session_key (request, {}, Constants.SESSION_FILTER_REACTION)
    Utils.del_session_key (request, {}, Constants.SESSION_FILTER_GENES)
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
  try:
    data=json.loads(request.body)
    
    for k in expected_keys:
      if k not in data:
        return False, "request is missing key: " + k
    
    return True, data
  except json.decoder.JSONDecodeError as e:
    return False, "request is not proper json"


@csrf_exempt
def status (request):
  # TODO heartbeat
  if request.method != 'POST':
    return redirect('index:index')
  
  
  __logger.critical(request.body)
  try:
    data=json.loads(request.body)
    data["answer"] = "abc"
    return JsonResponse (data)
    #return HttpResponse(serializers.serialize('json', data), content_type='application/json')
  except Exception as e:
    __logger.critical(e)
    return JsonResponse ({"nope": "nope"})
    #return HttpResponse(serializers.serialize('json', {"nope": "nope"}), content_type='application/json')
  
