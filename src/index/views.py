from django.shortcuts import render

def index(request):
    return render(request, 'index/index.html', {})
def imprint(request):
    return render(request, 'index/imprint.html', {})
def learn(request):
    return render(request, 'index/learn.html', {})
