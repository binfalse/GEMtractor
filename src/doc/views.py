from django.shortcuts import render

# Create your views here.
def start(request):
  context = {}
  return render(request, 'doc/start.html', context)
