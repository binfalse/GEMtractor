from django.shortcuts import render
from django.http import HttpResponse
from modules.ppin_extractor.ppin_extractor import PpinExtractor
import os

# Create your views here.
def index(request):
    #return HttpResponse("Hello, world. You're at the index.")
    context = {'test': os.path.isfile("test/ecoli_core_model.xml")}
    # ppin = PpinExtractor()
    # net = ppin.extract_network_from_sbml ("test/ecoli_core_model.xml")
    # context['net'] = net.to_json()
    # net.calc_genenet ()
    # gn = net.genenet ()
    # print (str (gn))
    return render(request, 'index/index.html', context)
def imprint(request):
    return render(request, 'index/imprint.html', {})
def filter(request):
    #return HttpResponse("Hello, world. You're at the index.")
    context = {'test': 124.3}
    return render(request, 'index/index.html', context)
