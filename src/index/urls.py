from django.urls import path

from . import views


app_name = 'index'
urlpatterns = [
    path('', views.index, name='index'),
    path('imprint', views.imprint, name='imprint'),
    path('filter', views.filter, name='filter'),
    ]
