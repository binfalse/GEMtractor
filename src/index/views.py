# This file is part of the GEMtractor
# Copyright (C) 2019 Martin Scharm <https://binfalse.de>
# 
# The GEMtractor is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# The GEMtractor is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from django.conf import settings
from django.shortcuts import render


def index(request):
    context = {}
    context["NEXT_l"] = False
    context["PREV_l"] = False
    return render(request, 'index/index.html', context)
def imprint(request):
    context = {}
    context["NEXT_l"] = False
    context["PREV_l"] = False
    context["KEEP_UPLOADED"] = settings.KEEP_UPLOADED / (60*60)
    return render(request, 'index/imprint.html', context)
def learn(request):
    context = {}
    context["NEXT_l"] = False
    context["PREV_l"] = False
    context["DJANGO_DEBUG"] = settings.DEBUG
    context["DJANGO_LOG_LEVEL"] = settings.DJANGO_LOG_LEVEL
    context["DJANGO_ALLOWED_HOSTS"] = settings.ALLOWED_HOSTS
    context["STORAGE_DIR"] = settings.STORAGE
    context["KEEP_UPLOADED"] = settings.KEEP_UPLOADED
    context["KEEP_GENERATED"] = settings.KEEP_GENERATED
    context["CACHE_BIGG"] = settings.CACHE_BIGG
    context["CACHE_BIGG_MODEL"] = settings.CACHE_BIGG_MODEL
    context["CACHE_BIOMODELS"] = settings.CACHE_BIOMODELS
    context["CACHE_BIOMODELS_MODEL"] = settings.CACHE_BIOMODELS_MODEL
    context["MAX_ENTITIES_FILTER"] = settings.MAX_ENTITIES_FILTER
    return render(request, 'index/learn.html', context)
