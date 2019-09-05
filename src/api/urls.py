from django.urls import path

from . import views


app_name = 'api'
urlpatterns = [
    path('status', views.status, name='status'),
    path('get_network', views.get_network, name='get_network'),
    path('store_filter', views.store_filter, name='store_filter'),
    path('get_bigg_models', views.get_bigg_models, name='get_bigg_models'),
    path('select_bigg_model', views.select_bigg_model, name='select_bigg_model'),
    path('get_biomodels', views.get_biomodels, name='get_biomodels'),
    path('select_biomodel', views.select_biomodel, name='select_biomodel'),
    path('get_session_data', views.get_session_data, name='get_session_data'),
    path('clear_data', views.clear_data, name='clear_data'),
    ]
