"""
URL configuration for santaelena project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include
from santaelena import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from santaelena.settings import *
from administrativo import commonviews

def protected_serve(request, path, document_root=None):
    try:
        permisototal = False
        if 'persona' in request.session:
            if request.session['persona'].usuario.is_superuser:
                permisototal = True
        if permisototal:
            return serve(request, path, document_root)
        if '.backup' not in path:
            return serve(request, path, document_root)
        else:
            pass
    except ObjectDoesNotExist:
        return HttpResponseRedirect("/?info=Ud. no tiene permisos para acceder a esta ruta")

def _routingpanel(request):
    try:
        if not DEBUG:
            if '127.0.0.1' in request.META['HTTP_HOST']:
                return commonviews.panel(request)
            else:
                return commonviews.panel(request)
        else:
            return commonviews.panel(request)
    except Exception as ex:
        return commonviews.panel(request)

urlpatterns = [
    re_path(r'^$', _routingpanel, name='panel'),
    re_path(r'^', include('administrativo.urls')),
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
