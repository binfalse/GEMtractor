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

from django.conf import settings
from django.shortcuts import redirect, reverse
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseServerError

from modules.gemtractor.gemtractor import GEMtractor
from modules.gemtractor.constants import Constants
from modules.gemtractor.utils import Utils, InvalidGeneExpression, InvalidBiomodelsId, UnableToRetrieveBiomodel, InvalidBiggId, TooBigForBrowser, InvalidGeneComplexExpression

from gemtract.forms import ExportForm

import os
import json
import urllib
import logging
import tempfile
from libsbml import SBMLWriter

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
  if Constants.SESSION_MODEL_TYPE in request.session and request.session[Constants.SESSION_MODEL_TYPE] == Constants.SESSION_MODEL_TYPE_UPLOAD:
    os.remove (Utils.get_model_path (request.session[Constants.SESSION_MODEL_TYPE], request.session[Constants.SESSION_MODEL_ID], request.session.session_key))
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
  if request.method == 'POST':
    # TODO
    return redirect('index:index')
  
  if Constants.SESSION_MODEL_ID in request.session:
    try:
      __logger.info ("getting sbml")
      gemtractor = GEMtractor (Utils.get_model_path (request.session[Constants.SESSION_MODEL_TYPE], request.session[Constants.SESSION_MODEL_ID], request.session.session_key))
      network = gemtractor.extract_network_from_sbml (gemtractor.get_sbml ())
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
        raise TooBigForBrowser ("This model is probably too big for your browser... It contains "+str (len (network.species))+" species, "+str (len (network.reactions))+" reactions and "+str (len (network.genenet))+" gene combinations. We won't load it for filtering, as you're browser is very likely to die when trying to process that amount of data.. Max is currently set to "+str (settings.MAX_ENTITIES_FILTER)+" entities in total. Please export it w/o filtering or use the API instead.")
      net = network.serialize()
      __logger.info ("serialised the network")
      return JsonResponse ({
            "status":"success",
            "network":net,
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
  if not Constants.SESSION_FILTER_SPECIES in request.session:
    request.session[Constants.SESSION_FILTER_SPECIES] = []
  if not Constants.SESSION_FILTER_REACTION in request.session:
    request.session[Constants.SESSION_FILTER_REACTION] = []
  if not Constants.SESSION_FILTER_ENZYMES in request.session:
    request.session[Constants.SESSION_FILTER_ENZYMES] = []
  if not Constants.SESSION_FILTER_ENZYME_COMPLEXES in request.session:
    request.session[Constants.SESSION_FILTER_ENZYME_COMPLEXES] = []

def sort_gene_complexes (complexes):
  c2 = []
  for c in complexes:
    if " + " not in c:
      raise InvalidGeneComplexExpression ("do not understand the following gene complex: " + c)
    c2.append (" + ".join (sorted (c.split (" + "))))
  return c2

def store_filter (request):
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
  try:
    data=json.loads(request.body)
    
    for k in expected_keys:
      if k not in data:
        return False, "request is missing key: " + k
    
    return True, data
  except json.decoder.JSONDecodeError:
    return False, "request is not proper json"

def serve_file (request, file_name, file_type):
  file_path = Utils.create_generated_file_web (request.session.session_key)
  if not os.path.exists(file_path):
    return HttpResponseBadRequest("file does not exist")
  
  return Utils.serve_file (file_path, file_name, file_type)

def export (request):
  
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
      request.session[Constants.SESSION_FILTER_SPECIES],
      request.session[Constants.SESSION_FILTER_REACTION],
      request.session[Constants.SESSION_FILTER_ENZYMES],
      request.session[Constants.SESSION_FILTER_ENZYME_COMPLEXES],
      form.cleaned_data['remove_reaction_enzymes_removed'],
      form.cleaned_data['discard_fake_enzymes'],
      form.cleaned_data['remove_reaction_missing_species'])
    
    if form.cleaned_data['network_type'] == 'en':
      file_name = file_name + "-EnzymeNetwork"
      net = gemtractor.extract_network_from_sbml (sbml)
      net.calc_genenet ()
      if form.cleaned_data['network_format'] == 'sbml':
        file_name = file_name + ".sbml"
        file_path = Utils.create_generated_file_web (request.session.session_key)
        net.export_en_sbml (file_path, gemtractor, request.session[Constants.SESSION_MODEL_ID], request.session[Constants.SESSION_MODEL_NAME],
            request.session[Constants.SESSION_FILTER_SPECIES],
            request.session[Constants.SESSION_FILTER_REACTION],
            request.session[Constants.SESSION_FILTER_ENZYMES],
            request.session[Constants.SESSION_FILTER_ENZYME_COMPLEXES],
            form.cleaned_data['remove_reaction_enzymes_removed'],
            form.cleaned_data['remove_reaction_missing_species'])
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
      net = gemtractor.extract_network_from_sbml (sbml)
      net.calc_reaction_net ()
      if form.cleaned_data['network_format'] == 'sbml':
        file_name = file_name + ".sbml"
        file_path = Utils.create_generated_file_web (request.session.session_key)
        net.export_rn_sbml (file_path, gemtractor, request.session[Constants.SESSION_MODEL_ID], request.session[Constants.SESSION_MODEL_NAME],
            request.session[Constants.SESSION_FILTER_SPECIES],
            request.session[Constants.SESSION_FILTER_REACTION],
            request.session[Constants.SESSION_FILTER_ENZYMES],
            request.session[Constants.SESSION_FILTER_ENZYME_COMPLEXES],
            form.cleaned_data['remove_reaction_enzymes_removed'],
            form.cleaned_data['remove_reaction_missing_species'])
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
        net = gemtractor.extract_network_from_sbml (sbml)
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
  discard_fake_enzymes = False
  
  if "remove_reaction_enzymes_removed" in export:
    remove_reaction_enzymes_removed = export["remove_reaction_enzymes_removed"]
  if "discard_fake_enzymes" in export:
    discard_fake_enzymes = export["discard_fake_enzymes"]
  if "remove_reaction_missing_species" in export:
    remove_reaction_missing_species = export["remove_reaction_missing_species"]
  
  try:
    gemtractor = GEMtractor (inputFile.name)
    sbml = gemtractor.get_sbml (
        filter_species,
        filter_reactions,
        filter_enzymes,
        filter_enzyme_complexes,
        remove_reaction_enzymes_removed,
        discard_fake_enzymes,
        remove_reaction_missing_species)
  except Exception as e:
    return HttpResponseBadRequest ("the model has an issue: " + getattr(e, 'message', repr(e)))
  
  outputFile = tempfile.NamedTemporaryFile()
  
  
  
  
  if export["network_type"] == "en":
    net = gemtractor.extract_network_from_sbml (sbml)
    net.calc_genenet ()
    if export["network_format"] == "sbml":
      net.export_en_sbml (outputFile.name, gemtractor, sbml.getModel ().getId (), sbml.getModel ().getName (), filter_species, filter_reactions, filter_enzymes, filter_enzyme_complexes, remove_reaction_enzymes_removed, remove_reaction_missing_species)
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
    net = gemtractor.extract_network_from_sbml (sbml)
    net.calc_reaction_net ()
    if export["network_format"] == "sbml":
      net.export_rn_sbml (outputFile.name, gemtractor, sbml.getModel ().getId () + "_RN", sbml.getModel ().getName () + " converted to ReactionNetwork", filter_species, filter_reactions, filter_enzymes, filter_enzyme_complexes, remove_reaction_enzymes_removed, remove_reaction_missing_species)
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
      net = gemtractor.extract_network_from_sbml (sbml)
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
  
  Utils.cleanup ()
  # TODO bit more information
  return JsonResponse ({"status": "success"})
  
