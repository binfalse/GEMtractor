"""GEMtractor URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
"""
from django.conf.urls import url
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('', include('index.urls')),
    path('gemtract/', include('gemtract.urls')),
    path('api/', include('api.urls')),
    url(r'^admin/', admin.site.urls),
]
