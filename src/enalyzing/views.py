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

from django.shortcuts import render, redirect
import os
from modules.enalyzer_utils.utils import Utils
from django.http import HttpResponse
from modules.enalyzer_utils.enalyzer import Enalyzer
from modules.enalyzer_utils.constants import Constants
from .forms import ExportForm
from libsbml import *

def __prepare_context (request):
  context = {}
  if Constants.SESSION_MODEL_NAME in request.session:
    context[Constants.SESSION_MODEL_NAME] = request.session[Constants.SESSION_MODEL_NAME]
  if Constants.SESSION_FILTER_SPECIES in request.session:
    context[Constants.SESSION_FILTER_SPECIES] = request.session[Constants.SESSION_FILTER_SPECIES]
  if Constants.SESSION_FILTER_REACTION in request.session:
    context[Constants.SESSION_FILTER_REACTION] = request.session[Constants.SESSION_FILTER_REACTION]
  if Constants.SESSION_FILTER_GENES in request.session:
    context[Constants.SESSION_FILTER_GENES] = request.session[Constants.SESSION_FILTER_GENES]
  context['current_url'] = request.resolver_match.route
  return context



def model_exists (request, context):
  if not Constants.SESSION_MODEL_ID in request.session:
    return False
  
  if Constants.SESSION_MODEL_TYPE in request.session and os.path.isfile (Utils.get_model_path (request.session[Constants.SESSION_MODEL_TYPE], request.session[Constants.SESSION_MODEL_ID], request.session.session_key)):
    os.utime (Utils.get_model_path (request.session[Constants.SESSION_MODEL_TYPE], request.session[Constants.SESSION_MODEL_ID], request.session.session_key))
    return True
  
  return False
    




# Create your views here.
def index(request):
  
  if request.session.session_key is None:
    request.session[Constants.SESSION_HAS_SESSION] = Constants.SESSION_HAS_SESSION_VALUE
    request.session.save()
  
  if request.method == 'POST' and 'custom-model' in request.FILES and request.FILES['custom-model']:
    model = request.FILES['custom-model']
    
    filename = Utils.get_upload_path (request.session.session_key)
    with open(filename, 'wb+') as destination:
      for chunk in model.chunks():
        destination.write(chunk)
    
    request.session[Constants.SESSION_MODEL_ID] = os.path.basename(filename)
    request.session[Constants.SESSION_MODEL_NAME] = model.name
    request.session[Constants.SESSION_MODEL_TYPE] = Constants.SESSION_MODEL_TYPE_UPLOAD
    Utils.del_session_key (request, None, Constants.SESSION_FILTER_SPECIES)
    Utils.del_session_key (request, None, Constants.SESSION_FILTER_REACTION)
    Utils.del_session_key (request, None, Constants.SESSION_FILTER_GENES)
    
    return redirect('enalyzing:filter')
    # filterModel (request)
    # #return HttpResponseRedirect (reverse ('enalyzing:filter'))
    # #render(request, 'enalyzing/index.html', {'model': request.session['model']})
    
  
  
  context = __prepare_context (request)
  if not model_exists (request, context):
    if Constants.SESSION_MODEL_ID in request.session:
      context['error'] = "did not find model on the server... either your session expired or our storage needed to be cleaned for some reason."
    Utils.del_session_key (request, context, Constants.SESSION_MODEL_ID)
    Utils.del_session_key (request, context, Constants.SESSION_MODEL_NAME)
    Utils.del_session_key (request, context, Constants.SESSION_MODEL_TYPE)
    Utils.del_session_key (request, context, Constants.SESSION_FILTER_SPECIES)
    Utils.del_session_key (request, context, Constants.SESSION_FILTER_REACTION)
    Utils.del_session_key (request, context, Constants.SESSION_FILTER_GENES)
    
  return render(request, 'enalyzing/index.html', context)


def filter(request):
  if Constants.SESSION_MODEL_ID not in request.session:
    return redirect('enalyzing:index')
  
  
  context = __prepare_context (request)
  if not model_exists (request, context):
    return redirect('enalyzing:index')
  
  return render(request, 'enalyzing/filter.html', context)


def export(request):
  if Constants.SESSION_MODEL_ID not in request.session:
    return redirect('enalyzing:index')
  
  context = __prepare_context (request)
  if not model_exists (request, context):
    return redirect('enalyzing:index')
  
  context = __prepare_context (request)
  
  
  if request.method == 'POST':
    form = ExportForm(request.POST)
    if (form.is_valid()):
      file_name = request.session[Constants.SESSION_MODEL_NAME] + "-enalyzed"
      
      enalyzer = Enalyzer (Utils.get_model_path (request.session[Constants.SESSION_MODEL_TYPE], request.session[Constants.SESSION_MODEL_ID], request.session.session_key))
      sbml = enalyzer.get_sbml (
        request.session[Constants.SESSION_FILTER_SPECIES],
        request.session[Constants.SESSION_FILTER_REACTION],
        request.session[Constants.SESSION_FILTER_GENES],
        form.cleaned_data['remove_reaction_genes_removed'],
        form.cleaned_data['remove_reaction_missing_species'])
      
      if form.cleaned_data['network_type'] == 'en':
        file_name = file_name + "-EnzymeNetwork"
        net = enalyzer.extract_network_from_sbml (sbml)
        net.calc_genenet ()
        if form.cleaned_data['network_format'] == 'sbml':
          context['error'] = "not yet implemented"
          
          
          file_name = file_name + ".sbml"
          file_path = Utils.create_generated_file_web (request.session.session_key)
          net.export_en_sbml (file_path, request.session[Constants.SESSION_MODEL_ID], request.session[Constants.SESSION_MODEL_NAME],
              request.session[Constants.SESSION_FILTER_SPECIES],
              request.session[Constants.SESSION_FILTER_REACTION],
              request.session[Constants.SESSION_FILTER_GENES],
              form.cleaned_data['remove_reaction_genes_removed'],
              form.cleaned_data['remove_reaction_missing_species'])
          if os.path.exists(file_path):
            return Utils.serve_file (file_path, file_name, "application/xml")
          else:
            context['error'] = "error generating SBML file"
        else:
          if form.cleaned_data['network_format'] == 'dot':
            file_name = file_name + ".dot"
            file_path = Utils.create_generated_file_web (request.session.session_key)
            net.export_en_dot (file_path)
            if os.path.exists(file_path):
              return Utils.serve_file (file_path, file_name, "application/dot")
            else:
              context['error'] = "error generating file"
          elif form.cleaned_data['network_format'] == 'graphml':
            file_name = file_name + ".graphml"
            file_path = Utils.create_generated_file_web (request.session.session_key)
            net.export_en_graphml (file_path)
            if os.path.exists(file_path):
              return Utils.serve_file (file_path, file_name, "application/xml")
            else:
              context['error'] = "error generating file"
          elif form.cleaned_data['network_format'] == 'gml':
            file_name = file_name + ".gml"
            file_path = Utils.create_generated_file_web (request.session.session_key)
            net.export_en_gml (file_path)
            if os.path.exists(file_path):
              return Utils.serve_file (file_path, file_name, "application/gml")
            else:
              context['error'] = "error generating file"
          else:
            context['error'] = "invalid format"
      elif form.cleaned_data['network_type'] == 'rn':
        file_name = file_name + "-ReactionNetwork"
        if form.cleaned_data['network_format'] == 'sbml':
          file_name = file_name + ".sbml"
          file_path = Utils.create_generated_file_web (request.session.session_key)
          SBMLWriter().writeSBML (sbml, file_path)
          if os.path.exists(file_path):
            return Utils.serve_file (file_path, file_name, "application/xml")
          else:
            context['error'] = "error generating file"
        else:
          net = enalyzer.extract_network_from_sbml (sbml)
          if form.cleaned_data['network_format'] == 'dot':
            file_name = file_name + ".dot"
            file_path = Utils.create_generated_file_web (request.session.session_key)
            net.export_rn_dot (file_path)
            if os.path.exists(file_path):
              return Utils.serve_file (file_path, file_name, "application/dot")
            else:
              context['error'] = "error generating file"
          elif form.cleaned_data['network_format'] == 'graphml':
            file_name = file_name + ".graphml"
            file_path = Utils.create_generated_file_web (request.session.session_key)
            net.export_rn_graphml (file_path)
            if os.path.exists(file_path):
              return Utils.serve_file (file_path, file_name, "application/xml")
            else:
              context['error'] = "error generating file"
          elif form.cleaned_data['network_format'] == 'gml':
            file_name = file_name + ".gml"
            file_path = Utils.create_generated_file_web (request.session.session_key)
            net.export_rn_gml (file_path)
            if os.path.exists(file_path):
              return Utils.serve_file (file_path, file_name, "application/gml")
            else:
              context['error'] = "error generating file"
          else:
            context['error'] = "invalid format"
      else:
        context['error'] = "this is not a valid network type"
  else:
    form = ExportForm(initial={'network_type':'en','remove_reaction_genes_removed': True, 'remove_reaction_missing_species': False,'network_format': 'sbml'})
  context['form'] = form
  return render(request, 'enalyzing/export.html', context)
  
