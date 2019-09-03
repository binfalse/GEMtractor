from django.urls import path

from . import views


app_name = 'api'
urlpatterns = [
    path('upload', views.upload, name='upload'),
    path('status', views.status, name='status'),
    path('get_network', views.get_network, name='get_network'),
    path('store_filter', views.store_filter, name='store_filter'),
    path('get_bigg_models', views.get_bigg_models, name='get_bigg_models'),
    path('select_bigg_model', views.select_bigg_model, name='select_bigg_model'),
    ]
