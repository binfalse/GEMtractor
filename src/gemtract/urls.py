from django.urls import path

from . import views

app_name = 'gemtract'
urlpatterns = [
    path('', views.index, name='index'),
    path('filter', views.filter, name='filter'),
    path('export', views.export, name='export'),
    ]
