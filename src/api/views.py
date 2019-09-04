from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers
import logging
import json
import os
from django.http import JsonResponse, HttpResponse, Http404
from modules.enalyzer_utils.utils import Utils, InvalidGeneExpression, InvalidBiomodelsId, UnableToRetrieveBiomodel
from modules.ppin_extractor.ppin_extractor import PpinExtractor
from modules.enalyzer_utils.constants import Constants
import time
import urllib
import pyparsing as pp

from libsbml import *

# Create your views here.
def upload (request):
  # if request.method == 'POST' and request.FILES['custom-model']:
    # model = request.FILES['custom-model']
    
    
    # filename = Utils.get_upload_path (model.name)
    # with open(filename, 'wb+') as destination:
      # for chunk in model.chunks():
        # destination.write(chunk)
        
    # ppin = PpinExtractor ()
    # network = ppin.extract_network_from_sbml (filename)
    # if network:
      # request.session['model_id'] = os.path.basename(filename)
      # request.session['model_name'] = model.name
      # request.session['model_type'] = 'upload'
      # return JsonResponse ({"upload": "success", "model_id": request.session['model_id'], "network": network})
    # else:
      # os.remove (filename)
      # error = "error"
      # return JsonResponse ({"upload": "failed", "msg": "file is not valid: " + error})
    
  return redirect('index:index')


def get_network (request):
  __logger = logging.getLogger('get_network')
  if request.method == 'POST':
    # TODO
    return redirect('index:index')
  
  if Constants.SESSION_MODEL_ID in request.session:
    ppin = PpinExtractor ()
    # __logger.critical(f)
    try:
      network = ppin.extract_network_from_sbml (ppin.get_sbml (Utils.get_model_path (request.session[Constants.SESSION_MODEL_TYPE], request.session[Constants.SESSION_MODEL_ID], request.session.session_key)))
      network.calc_genenet ()
      filter_species = []
      filter_reaction = []
      filter_genes = []
      if Constants.SESSION_FILTER_SPECIES in request.session:
        filter_species = request.session[Constants.SESSION_FILTER_SPECIES]
      if Constants.SESSION_FILTER_REACTION in request.session:
        filter_reaction = request.session[Constants.SESSION_FILTER_REACTION]
      if Constants.SESSION_FILTER_GENES in request.session:
          fiter_genes = request.session[Constants.SESSION_FILTER_GENES]
      return JsonResponse ({
            "status":"success",
            "network":network.serialize(),
            "filter": {
            Constants.SESSION_FILTER_SPECIES: filter_species,
            Constants.SESSION_FILTER_REACTION: filter_reaction,
            Constants.SESSION_FILTER_GENES: filter_genes,
            }
            })
    except IOError as e:
      return JsonResponse ({"status":"failed","error":getattr(e, 'message', repr(e))})
    except InvalidGeneExpression as e:
      __logger.critical("InvalidGeneExpression in model " + request.session[Constants.SESSION_MODEL_ID] + ": " + getattr(e, 'message', repr(e)))
      return JsonResponse ({"status":"failed","error": "The model uses an invalid gene expression: " + getattr(e, 'message', repr(e))})
    #return JsonResponse ({"nope": "nope"})
  
  # invalid api request
  return redirect('index:index')
  
  
def store_filter (request):
  __logger = logging.getLogger('store_filter')
  if request.method != 'POST':
    # TODO
    return redirect('index:index')
  
  data=json.loads(request.body)
  request.session[Constants.SESSION_FILTER_SPECIES] = data["species"]
  request.session[Constants.SESSION_FILTER_REACTION] = data["reaction"]
  request.session[Constants.SESSION_FILTER_GENES] = data["genes"]
  __logger.critical(data)
  return JsonResponse ({"status":"success"})
  
def get_bigg_models (request):
  # time.sleep(5)
  try:
    models = Utils.get_bigg_models ()
    models["status"] = "success"
    return JsonResponse (models)
  except urllib.error.HTTPError  as e:
      return JsonResponse ({"status":"failed","error":str (getattr(e, 'code', repr(e))) + getattr(e, 'message', repr(e))})
  except urllib.error.URLError as e:
    if hasattr(e, 'reason'):
      return JsonResponse ({"status":"failed","error":str (getattr(e, 'reason', repr(e))) + getattr(e, 'message', repr(e))})
    elif hasattr(e, 'code'):
      return JsonResponse ({"status":"failed","error":str (getattr(e, 'code', repr(e))) + getattr(e, 'message', repr(e))})
  
def select_bigg_model (request):
  if request.method != 'POST':
    # TODO
    return redirect('index:index')
  data=json.loads(request.body)
  
  try:
    Utils.get_bigg_model (data["bigg_id"])
    request.session[Constants.SESSION_MODEL_ID] = data["bigg_id"]
    request.session[Constants.SESSION_MODEL_NAME] = data["bigg_id"]
    request.session[Constants.SESSION_MODEL_TYPE] = 'bigg'
    Utils.del_session_key (request, {}, Constants.SESSION_FILTER_SPECIES)
    Utils.del_session_key (request, {}, Constants.SESSION_FILTER_REACTION)
    Utils.del_session_key (request, {}, Constants.SESSION_FILTER_GENES)
    return JsonResponse ({"status":"success"})

  except urllib.error.HTTPError  as e:
      return JsonResponse ({"status":"failed","error":str (getattr(e, 'code', repr(e))) + getattr(e, 'message', repr(e))})
  except urllib.error.URLError as e:
    if hasattr(e, 'reason'):
      return JsonResponse ({"status":"failed","error":str (getattr(e, 'reason', repr(e))) + getattr(e, 'message', repr(e))})
    elif hasattr(e, 'code'):
      return JsonResponse ({"status":"failed","error":str (getattr(e, 'code', repr(e))) + getattr(e, 'message', repr(e))})
  
  
  
def get_biomodels (request):
  # time.sleep(5)
  try:
    models = Utils.get_biomodels ()
    models["status"] = "success"
    return JsonResponse (models)
  except urllib.error.HTTPError  as e:
      return JsonResponse ({"status":"failed","error":str (getattr(e, 'code', repr(e))) + getattr(e, 'message', repr(e))})
  except urllib.error.URLError as e:
    if hasattr(e, 'reason'):
      return JsonResponse ({"status":"failed","error":str (getattr(e, 'reason', repr(e))) + getattr(e, 'message', repr(e))})
    elif hasattr(e, 'code'):
      return JsonResponse ({"status":"failed","error":str (getattr(e, 'code', repr(e))) + getattr(e, 'message', repr(e))})
  
def select_biomodel (request):
  if request.method != 'POST':
    # TODO
    return redirect('index:index')
  data=json.loads(request.body)
  
  try:
    Utils.get_biomodel (data["biomodels_id"])
    request.session[Constants.SESSION_MODEL_ID] = data["biomodels_id"]
    request.session[Constants.SESSION_MODEL_NAME] = data["biomodels_id"]
    request.session[Constants.SESSION_MODEL_TYPE] = 'biomodels'
    Utils.del_session_key (request, {}, Constants.SESSION_FILTER_SPECIES)
    Utils.del_session_key (request, {}, Constants.SESSION_FILTER_REACTION)
    Utils.del_session_key (request, {}, Constants.SESSION_FILTER_GENES)
    return JsonResponse ({"status":"success"})

  except UnableToRetrieveBiomodel  as e:
      return JsonResponse ({"status":"failed","error":getattr(e, 'message', repr(e))})
  except InvalidBiomodelsId  as e:
      return JsonResponse ({"status":"failed","error":getattr(e, 'message', repr(e))})
  except urllib.error.HTTPError  as e:
      return JsonResponse ({"status":"failed","error": "Does such a model exist? Can't download from Biomodels: " + str (getattr(e, 'code', repr(e))) + getattr(e, 'message', repr(e))})
  except urllib.error.URLError as e:
    if hasattr(e, 'reason'):
      return JsonResponse ({"status":"failed","error":str (getattr(e, 'reason', repr(e))) + getattr(e, 'message', repr(e))})
    elif hasattr(e, 'code'):
      return JsonResponse ({"status":"failed","error":str (getattr(e, 'code', repr(e))) + getattr(e, 'message', repr(e))})
  
  
# def download (request):
  # __logger = logging.getLogger('download')
  # if request.method != 'POST':
    # # TODO
    # return redirect('index:index')
  
  # data=json.loads(request.body)
  # __logger.critical(data)
  # ppin = PpinExtractor ()
  # sbml = ppin.get_sbml (Utils.get_path_of_uploaded_file (request.session[Constants.SESSION_MODEL_ID]),
    # request.session[Constants.SESSION_FILTER_SPECIES],
    # request.session[Constants.SESSION_FILTER_REACTION],
    # request.session[Constants.SESSION_FILTER_GENES])
  # file_path = "/tmp/filtered_sbml.sbml"
  # SBMLWriter().writeSBML (sbml, file_path)
  # if os.path.exists(file_path):
        # with open(file_path, 'rb') as fh:
          # response = HttpResponse(fh.read(), content_type="application/xml")
          # response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(file_path)
          # return response
  # raise Http404
  # # return JsonResponse ({"status":"success"})
  


@csrf_exempt
def status (request):
  if request.method != 'POST':
    return redirect('index:index')
  
  __logger = logging.getLogger('status')
  
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
  
