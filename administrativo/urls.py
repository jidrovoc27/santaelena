from django.urls import re_path, path
from administrativo import views, adm_producto, administrativos, adm_modulos
from administrativo.commonviews import *
from django.conf.urls.static import static

urlpatterns = [
    re_path(r'^administrativos', administrativos.view, name='administrativos'),
    re_path(r'^modulos', adm_modulos.view, name='adm_modulos'),
    re_path(r'^producto', adm_producto.view, name='productotiendavirtual'),
    re_path(r'^loginclinica$', login_user, name='login_view'),
    re_path(r'^logoutclinica$', logout_user, name='logout_user'),
]