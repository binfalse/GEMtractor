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
from django.shortcuts import redirect, reverse
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseServerError

from modules.gemtractor.gemtractor import GEMtractor
from modules.gemtractor.constants import Constants
from modules.gemtractor.utils import Utils, InvalidGeneExpression, InvalidBiomodelsId, UnableToRetrieveBiomodel, InvalidBiggId, TooBigForBrowser

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
  Utils.del_session_key (request, None, Constants.SESSION_FILTER_GENES)
  return JsonResponse ({
          "status":"success"
        })

def get_network (request):
  if request.method == 'POST':
    # TODO
    return redirect('index:index')
  
  if Constants.SESSION_MODEL_ID in request.session:
    gemtractor = GEMtractor (Utils.get_model_path (request.session[Constants.SESSION_MODEL_TYPE], request.session[Constants.SESSION_MODEL_ID], request.session.session_key))
    try:
      __logger.info ("getting sbml")
      network = gemtractor.extract_network_from_sbml (gemtractor.get_sbml ())
      if len (network.species) + len (network.reactions) > settings.MAX_ENTITIES_FILTER:
        raise TooBigForBrowser ("This model is probably too big for your browser... It contains "+str (len (network.species))+" species and "+str (len (network.reactions))+" reactions. We won't load it for filtering, as you're browser is very likely to die when trying to process that amount of data.. Max is currently set to "+str (settings.MAX_ENTITIES_FILTER)+" entities in total. Please export it w/o filtering or use the API instead.")
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
      if len (network.species) + len (network.reactions) + len (network.genenet) > settings.MAX_ENTITIES_FILTER:
        raise TooBigForBrowser ("This model is probably too big for your browser... It contains "+str (len (network.species))+" species, "+str (len (network.reactions))+" reactions and "+str (len (network.genenet))+" gene combinations. We won't load it for filtering, as you're browser is very likely to die when trying to process that amount of data.. Max is currently set to "+str (settings.MAX_ENTITIES_FILTER)+" entities in total. Please export it w/o filtering or use the API instead.")
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

def prepare_filter (request):
  if not Constants.SESSION_FILTER_SPECIES in request.session:
    request.session[Constants.SESSION_FILTER_SPECIES] = []
  if not Constants.SESSION_FILTER_REACTION in request.session:
    request.session[Constants.SESSION_FILTER_REACTION] = []
  if not Constants.SESSION_FILTER_GENES in request.session:
    request.session[Constants.SESSION_FILTER_GENES] = []
  
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
  if "genes" in data and isinstance(data["genes"], list):
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
    
    gemtractor = GEMtractor (Utils.get_model_path (request.session[Constants.SESSION_MODEL_TYPE], request.session[Constants.SESSION_MODEL_ID], request.session.session_key))
    sbml = gemtractor.get_sbml (
      request.session[Constants.SESSION_FILTER_SPECIES],
      request.session[Constants.SESSION_FILTER_REACTION],
      request.session[Constants.SESSION_FILTER_GENES],
      form.cleaned_data['remove_reaction_genes_removed'],
      form.cleaned_data['remove_reaction_missing_species'])
    
    if form.cleaned_data['network_type'] == 'en':
      file_name = file_name + "-EnzymeNetwork"
      net = gemtractor.extract_network_from_sbml (sbml)
      net.calc_genenet ()
      if form.cleaned_data['network_format'] == 'sbml':
        file_name = file_name + ".sbml"
        file_path = Utils.create_generated_file_web (request.session.session_key)
        net.export_en_sbml (file_path, request.session[Constants.SESSION_MODEL_ID], request.session[Constants.SESSION_MODEL_NAME],
            request.session[Constants.SESSION_FILTER_SPECIES],
            request.session[Constants.SESSION_FILTER_REACTION],
            request.session[Constants.SESSION_FILTER_GENES],
            form.cleaned_data['remove_reaction_genes_removed'],
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
        else:
          return JsonResponse ({"status":"failed","error":"invalid format"})
    elif form.cleaned_data['network_type'] == 'rn':
      file_name = file_name + "-ReactionNetwork"
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
  filter_genes = []
  
  if "filter" in data:
    if "species" in data["filter"]:
      filter_species = data["filter"]["species"]
    if "reactions" in data["filter"]:
      filter_reactions = data["filter"]["reactions"]
    if "genes" in data["filter"]:
      filter_genes = data["filter"]["genes"]
  
  if not isinstance(filter_species, list):
    return HttpResponseBadRequest("filter needs to be an array")
  if not isinstance(filter_reactions, list):
    return HttpResponseBadRequest("filter needs to be an array")
  if not isinstance(filter_genes, list):
    return HttpResponseBadRequest("filter needs to be an array")
  
  export = data["export"]
  
  if "network_type" not in export:
    return HttpResponseBadRequest ("job is missing the desired network_type (en|rn)")
  if "network_format" not in export:
    return HttpResponseBadRequest ("job is missing the desired network_format (sbml|dot|graphml|gml)")
    
  
  remove_reaction_genes_removed = True
  remove_reaction_missing_species = False
  
  if "remove_reaction_genes_removed" in export:
    remove_reaction_genes_removed = export["remove_reaction_genes_removed"]
  if "remove_reaction_missing_species" in export:
    remove_reaction_missing_species = export["remove_reaction_missing_species"]
  
  gemtractor = GEMtractor (inputFile.name)
  try:
    sbml = gemtractor.get_sbml (
        filter_species,
        filter_reactions,
        filter_genes,
        remove_reaction_genes_removed,
        remove_reaction_missing_species)
  except Exception as e:
    return HttpResponseBadRequest ("the model has an issue: " + getattr(e, 'message', repr(e)))
  
  outputFile = tempfile.NamedTemporaryFile()
  
  
  
  
  if export["network_type"] == "en":
    net = gemtractor.extract_network_from_sbml (sbml)
    net.calc_genenet ()
    if export["network_format"] == "sbml":
      net.export_en_sbml (outputFile.name, sbml.getModel ().getId () + "_EN", sbml.getModel ().getName () + " converted to EnzymeNetwork", filter_species, filter_reactions, filter_genes, remove_reaction_genes_removed, remove_reaction_missing_species)
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
  elif export["network_type"] == "rn":
    if export["network_format"] == "sbml":
      SBMLWriter().writeSBML (sbml, outputFile.name)
      if os.path.exists(outputFile.name):
        return Utils.serve_file (outputFile.name, "gemtracted-model.sbml", "application/xml")
      else:
        return HttpResponseServerError ("couldn't generate the sbml file")
    else:
      net = gemtractor.extract_network_from_sbml (sbml)
      if export["network_format"] == "dot":
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
  
  
  return HttpResponseBadRequest ("job is not well formed, not sure what to do...")
  
  




@csrf_exempt
def status (request):
  
  Utils.cleanup ()
  # TODO bit more information
  return JsonResponse ({"status": "success"})
  
