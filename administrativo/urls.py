from django.urls import re_path, path
from administrativo import views, adm_producto, administrativos, adm_modulos, tiposrubros, puntofacturacion, comprobantes, \
    sesioncaja, pacientes, salidas, facturas
from administrativo.commonviews import *
from django.conf.urls.static import static

urlpatterns = [
    re_path(r'^administrativos', administrativos.view, name='administrativos'),
    re_path(r'^modulos', adm_modulos.view, name='adm_modulos'),
    re_path(r'^producto', adm_producto.view, name='productotiendavirtual'),
    re_path(r'^tiposrubros', tiposrubros.view, name='tiposrubros'),
    re_path(r'^puntofacturacion', puntofacturacion.view, name='puntofacturacion'),
    re_path(r'^comprobantes', comprobantes.view, name='comprobantes'),
    re_path(r'^salidas', salidas.view, name='salidas'),
    re_path(r'^facturas', facturas.view, name='facturas'),
    re_path(r'^pacientes', pacientes.view, name='pacientes'),
    re_path(r'^sesioncaja', sesioncaja.view, name='sesioncaja'),
    re_path(r'^loginclinica$', login_user, name='login_view'),
    re_path(r'^logoutclinica$', logout_user, name='logout_user'),
]