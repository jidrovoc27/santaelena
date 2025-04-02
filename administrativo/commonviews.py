import datetime
from datetime import datetime
from santaelena import settings
from administrativo.models import Persona, Modulo, ModuloGrupo, PerfilUsuario
from santaelena.settings import SERVER_RESPONSE
from administrativo.funciones import get_client_ip, miempresa

def adduserdata(request, data):
    data['rutaurl'] = request.path
    data["CLAVE_PUBLICA"] = settings.ENC_PUBLIC_KEY

    # ADICIONA EL USUARIO A LA SESSION
    if 'persona' not in request.session:
        if not request.user.is_authenticated:
            raise Exception('Usuario no autentificado en el sistema')
        #request.session['persona'] = Persona.objects.get(usuario=request.user)
    data['persona'] = Persona.objects.filter(usuario=request.user)[0]
    data['check_sesion'] = True
    data['server_response'] = SERVER_RESPONSE
    persona = data['persona']
    if 'ultimo_acceso' not in request.session:
        request.session['ultimo_acceso'] = datetime.now()
    if request.method == 'GET':
        if 'ret' in request.GET:
            data['ret'] = request.GET['ret']
        if 'mensj' in request.GET:
            data['mensj'] = request.GET['mensj']
    data['nombresistema'] = request.session['nombresistema']
    data['tiposistema'] = request.session['tiposistema']
    data['currenttime'] = datetime.now()
    #data['perfiles_usuario'] = request.session['perfiles']
    data['remoteaddr'] = '%s - %s' % (get_client_ip(request), request.META['SERVER_NAME'])
    #data['perfilprincipal'] = perfilprincipal = request.session['perfilprincipal']

    data['grupos_usuarios'] = request.user.groups
    if 'ruta' not in request.session:
        request.session['ruta'] = [['/', 'Inicio']]
    rutalista = request.session['ruta']
    if request.path:
        if Modulo.objects.filter(url=request.path[1:]).exists():
            modulo = Modulo.objects.filter(url=request.path[1:])[0]
            url = ['/' + modulo.url, modulo.nombre]
            if rutalista.count(url) <= 0:
                if rutalista.__len__() >= 8:
                    b = rutalista[1]
                    rutalista.remove(b)
                    rutalista.append(url)
                else:
                    rutalista.append(url)
            request.session['ruta'] = rutalista
            data["url_back"] = '/'
            url_back = [data['url_back']]
            request.session['url_back'] = url_back
    data["ruta"] = rutalista
    data["formlocation"] = True
    data['permite_modificar'] = True
    if 'info' in request.GET:
        data['info'] = request.GET['info']
    # NOTIFICACIONES WEB
    # from administrativo.models import Notificacion
    # fecha_ahora = datetime.now()
    # qsnotification = Notificacion.objects.filter(available=True, leido=False, destinatario=persona, fecha_hora_visible__gte=fecha_ahora, app_label__icontains='SAGEST').order_by('-pk')[:5]
    # data['listnotification'] = qsnotification
    # data['totnotification'] = len(qsnotification)

    webpush_settings = getattr(settings, 'WEBPUSH_SETTINGS', {})
    vapid_key = webpush_settings.get('VAPID_PUBLIC_KEY')
    data['vapid_key'] = vapid_key
    data['eTemplateBaseSetting'] = eTemplateBaseSetting = request.session['eTemplateBaseSetting'] if 'eTemplateBaseSetting' in request.session and request.session['eTemplateBaseSetting'] else None
    
# coding=latin-1
import sys
from urllib.parse import urlencode
from urllib.request import urlopen, Request
import json
import random
from datetime import datetime, timedelta
from django.contrib.auth import authenticate, logout, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction, connection
from django.db.models import F, Sum
from django.db.models.aggregates import Count
from django.db.models.query_utils import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect

#from decorators import secure_module, last_access
from santaelena.settings import *
from administrativo.funciones import to_unicode, puede_realizar_accion_afirmativo, null_to_decimal, encrypt
from administrativo.models import Persona, ModuloGrupo, \
    Empresa, Modulo, CategoriaModulo, MenuFavoriteProfile, TemplateBaseSetting
from administrativo.correo import send_html_mail, CUENTAS_CORREOS

unicode = str


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# AUTENTIFICA EL USUARIO
@transaction.atomic()
def login_user(request):
    data = {}
    ipvalidas = ['192.168.61.96', '192.168.61.97', '192.168.61.98', '192.168.61.99']
    client_address = get_client_ip(request)
    if request.method == 'POST':
        if 'action' in request.POST:
            action = request.POST['action']
            if action == 'login':
                try:
                    browser = request.POST['navegador']
                    ops = request.POST['os']
                    cookies = request.POST['cookies']
                    screensize = request.POST['screensize']
                    user = authenticate(username=request.POST['user'].lower().strip(), password=request.POST['pass'])
                    if user is not None:
                        if not user.is_active:
                            return JsonResponse({"result": "bad", 'mensaje': u'Login fallido, usuario no activo.'})
                        else:
                            if Persona.objects.filter(usuario=user).exists():
                                persona = Persona.objects.filter(usuario=user)[0]
                                if persona.tiene_perfil():
                                    app = 'administrativo'
                                    perfiles = persona.mis_perfilesusuarios_app(app)
                                    perfilprincipal = persona.perfilusuario_principal(perfiles, app)
                                    if not perfilprincipal:
                                        return JsonResponse({"result": "bad",
                                                             'mensaje': u'No existe un perfiles para esta aplicacion.'})
                                    request.session.set_expiry(240 * 60)
                                    login(request, user)
                                    #request.session['perfiles'] = list(perfiles.values_list('id', flat=True))
                                    #request.session['persona'] = persona
                                    request.session['tiposistema'] = app
                                    #request.session['perfilprincipal'] = perfilprincipal.id
                                    request.session['nombresistema'] = u'Clínica Santa Elena'
                                    eTemplateBaseSetting = TemplateBaseSetting.objects.filter(status=True,
                                                                                              app=2).first()
                                    if eTemplateBaseSetting:
                                        nombresistema = eTemplateBaseSetting.name_system
                                    request.session['eTemplateBaseSetting'] = eTemplateBaseSetting
                                    # send_html_mail("Login exitoso SAGEST", "emails/loginexito.html", {'sistema': request.session['nombresistema'], 'fecha': datetime.now().date(), 'hora': datetime.now().time(), 'bs': browser, 'ip': client_address, 'os': ops, 'cookies': cookies, 'screensize': screensize, 't': miinstitucion()}, persona.lista_emails_envio(), [], coneccion=CUENTAS_CORREOS[1][1])
                                    return JsonResponse({"result": "ok", "sessionid": request.session.session_key})
                                else:
                                    return JsonResponse(
                                        {"result": "bad", 'mensaje': u'Login fallido, no existen perfiles activos.'})
                            else:
                                return JsonResponse(
                                    {"result": "bad", 'mensaje': u'Login fallido, no existe el usuario.'})
                    else:
                        if Persona.objects.filter(usuario__username=request.POST['user'].lower()).exists():
                            persona = Persona.objects.filter(usuario__username=request.POST['user'].lower())[0]
                            # send_html_mail("Login fallido SAGEST.", "emails/loginfallido.html", {'sistema': u'Login fallido, no existen perfiles activos.', 'fecha': datetime.now().date(), 'hora': datetime.now().time(), 'bs': browser, 'ip': client_address, 'os': ops, 'cookies': cookies, 'screensize': screensize, 't': miinstitucion()}, persona.lista_emails_envio(), [], coneccion=CUENTAS_CORREOS[1][1])
                        return JsonResponse({"result": "bad", 'mensaje': u'Login fallido, credenciales incorrectas.'})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"result": "bad", 'mensaje': u'Login fallido, Error en el sistema.'})

        return JsonResponse({"result": "bad", "mensaje": u"Solicitud Incorrecta."})
    else:
        if request.user.id:
            if Persona.objects.filter(usuario=request.user):
                return HttpResponseRedirect("/")
        data = {"title": u"Login", "background": random.randint(1, 2)}
        data['request'] = request
        hoy = datetime.now().date()
        data['currenttime'] = datetime.now()
        data['institucion'] = miempresa().nombre
        if client_address in ipvalidas:
            data['validar_con_captcha'] = False
            data['declaracion_sga'] = False

        data['server_response'] = SERVER_RESPONSE
        data['tipoentrada'] = "SGA"
        return render(request, "login.html", data)


# CIERRA LA SESSION DEL USUARIO
def logout_user(request):
    logout(request)
    return HttpResponseRedirect("/loginclinica")


# ADICIONA LOS DATOS DEL USUARIO A LA SESSION
def adduserdata(request, data):
    data['rutaurl'] = request.path
    data["CLAVE_PUBLICA"] = settings.ENC_PUBLIC_KEY

    # ADICIONA EL USUARIO A LA SESSION
    if 'persona' not in request.session:
        if not request.user.is_authenticated:
            raise Exception('Usuario no autentificado en el sistema')
        #request.session['persona'] = Persona.objects.get(usuario=request.user)
    data['persona'] = Persona.objects.filter(usuario=request.user)[0]
    data['check_sesion'] = True
    data['server_response'] = SERVER_RESPONSE
    persona = data['persona']
    if 'ultimo_acceso' not in request.session:
        request.session['ultimo_acceso'] = datetime.now()
    if request.method == 'GET':
        if 'ret' in request.GET:
            data['ret'] = request.GET['ret']
        if 'mensj' in request.GET:
            data['mensj'] = request.GET['mensj']
    data['nombresistema'] = request.session['nombresistema']
    data['tiposistema'] = request.session['tiposistema']
    data['currenttime'] = datetime.now()
    #data['perfiles_usuario'] = request.session['perfiles']
    data['remoteaddr'] = '%s - %s' % (get_client_ip(request), request.META['SERVER_NAME'])
    #data['pie_pagina_creative_common_licence'] = PIE_PAGINA_CREATIVE_COMMON_LICENCE
    #data['perfilprincipal'] = perfilprincipal = request.session['perfilprincipal']

    data['grupos_usuarios'] = request.user.groups
    if 'ruta' not in request.session:
        request.session['ruta'] = [['/', 'Inicio']]
    rutalista = request.session['ruta']
    if request.path:
        if Modulo.objects.filter(url=request.path[1:]).exists():
            modulo = Modulo.objects.filter(url=request.path[1:])[0]
            url = ['/' + modulo.url, modulo.nombre]
            if rutalista.count(url) <= 0:
                if rutalista.__len__() >= 8:
                    b = rutalista[1]
                    rutalista.remove(b)
                    rutalista.append(url)
                else:
                    rutalista.append(url)
            request.session['ruta'] = rutalista
            data["url_back"] = '/'
            url_back = [data['url_back']]
            request.session['url_back'] = url_back
    data["ruta"] = rutalista
    data["formlocation"] = True
    data['permite_modificar'] = True
    if 'info' in request.GET:
        data['info'] = request.GET['info']
    # NOTIFICACIONES WEB
    # from administrativo.models import Notificacion
    # fecha_ahora = datetime.now()
    # qsnotification = Notificacion.objects.filter(status=True, leido=False, destinatario=persona, fecha_hora_visible__gte=fecha_ahora, app_label__icontains='SAGEST').order_by('-pk')[:5]
    # data['listnotification'] = qsnotification
    # data['totnotification'] = len(qsnotification)

    webpush_settings = getattr(settings, 'WEBPUSH_SETTINGS', {})
    vapid_key = webpush_settings.get('VAPID_PUBLIC_KEY')
    data['vapid_key'] = vapid_key
    data['eTemplateBaseSetting'] = eTemplateBaseSetting = request.session['eTemplateBaseSetting'] if 'eTemplateBaseSetting' in request.session and request.session['eTemplateBaseSetting'] else None

# PANEL PRINCIPAL DEL SISTEMA


# @login_required(redirect_field_name='ret', login_url='/#loginsga')
@login_required(login_url='/loginclinica')
# @secure_module
# @last_access
# @transaction.atomic()
def panel(request):
    data = {}
    adduserdata(request, data)
    persona = data['persona']
    perfiles = persona.mis_perfilesusuarios_app('administrativo')
    perfilprincipal = persona.perfilusuario_principal(perfiles, 'administrativo')
    # if persona.es_empleador():
    #     return HttpResponseRedirect('/bolsalaboral')
    if request.method == 'POST':
        if 'action' in request.POST:
            action = request.POST['action']

            if action == 'saveFavoriteMenu':
                try:
                    if not 'idm' in request.POST:
                        raise NameError(u"Parameto de modulo no encontrado")
                    idm = int(request.POST['idm'])
                    if not Modulo.objects.values("id").filter(pk=idm).exists():
                        raise NameError(u"Modulo no encontrado")
                    eModulo = Modulo.objects.get(pk=idm)
                    if not 'value' in request.POST:
                        raise NameError(u"Parameto de valor no encontrado")
                    """
                    * value = 1 => QUITAR MODULO DE FAVORITOS
                    * value = 0 => AGREGAR MODULO DE FAVORITOS
                    """
                    value = int(request.POST['value'])
                    eTemplateBaseSetting = request.session['eTemplateBaseSetting']
                    if MenuFavoriteProfile.objects.values("id").filter(setting=eTemplateBaseSetting, profile=perfilprincipal).exists():
                        eMenuFavoriteProfile = MenuFavoriteProfile.objects.filter(setting=eTemplateBaseSetting, profile=perfilprincipal)[0]
                    else:
                        eMenuFavoriteProfile = MenuFavoriteProfile(setting=eTemplateBaseSetting,
                                                                   profile=perfilprincipal)
                        eMenuFavoriteProfile.save(request)
                    modulos_ids = eMenuFavoriteProfile.mis_modulos_id()
                    if value == 1:
                        if eModulo.id in modulos_ids:
                            eMenuFavoriteProfile.modules.remove(eModulo.id)
                            #log(u'Quito modulo favorito: %s de la APP: %s' % (eModulo, eMenuFavoriteProfile.setting), request, "del")
                    else:
                        if not modulos_ids:
                            eMenuFavoriteProfile.modules.add(eModulo.id)
                            #log(u'Agrego modulo favorito: %s de la APP: %s' % (eModulo, eMenuFavoriteProfile.setting), request, "add")
                        else:
                            if eMenuFavoriteProfile.mis_modulos().count() > 100:
                                raise NameError(u"Limite de seleccionar módulos favorito es de %s" % str(100))
                            elif not eModulo.id in modulos_ids:
                                eMenuFavoriteProfile.modules.add(eModulo.id)
                                #log(u'Agrego modulo favorito: %s de la APP: %s' % (eModulo, eMenuFavoriteProfile.setting), request, "add")

                    return JsonResponse({'result': "ok", "mensaje": u"¡Has quitado un módulo de tus favoritos!" if value == 1 else u"¡Has agregado un módulo a tus favoritos!"})
                except Exception as ex:
                    transaction.set_rollback(True)
                    return JsonResponse({"result": "bad", "mensaje": u"Error al guardar los datos. {}".format(ex.__str__())})

        return JsonResponse({"result": "bad", "mensaje": u"Solicitud Incorrecta."})
    else:
        # hoy = datetime.now()
        data['title'] = 'SANTA ELENA'
        if 'action' in request.GET:

            action = request.GET['action']

            return HttpResponseRedirect(request.path)
        else:
            try:
                if 'paginador' in request.session:
                    del request.session['paginador']
                # if perfilprincipal.es_vendedor():
                #     misgrupos = ModuloGrupo.objects.filter(grupos__in=[175]).distinct()
                #     data['mismodulos'] = Modulo.objects.filter(modu#logrupo__in=misgrupos, activo=True,
                #                                                sagest=True).distinct().order_by('nombre')
                # elif perfilprincipal.es_supervisor():
                #     misgrupos = ModuloGrupo.objects.filter(grupos__in=[178]).distinct()
                #     data['mismodulos'] = Modulo.objects.filter(modu#logrupo__in=misgrupos, activo=True,
                #                                                sagest=True).distinct().order_by('nombre')
                # else:
                misgrupos = ModuloGrupo.objects.filter(grupos__in=persona.usuario.groups.all()).distinct()
                modulos = Modulo.objects.filter(Q(modulogrupo__in=misgrupos), activo=True).distinct().order_by('nombre')
                if data['tiposistema'] == 'administrativo':
                    modulos = modulos.filter(administrativo=True).distinct().order_by('nombre')
                data['mismodulos'] = modulos
                data['CATEGORIAS_MODULOS'] = CategoriaModulo.objects.filter(status=True, id__in=modulos.values_list('categoria',flat=True)).order_by('orden')
                tiposistema = request.session['tiposistema']
                data['tipoentrada'] = "SAGEST"
                data['institucion'] = 'Empresa Publica de Produccion y Desarrollo Estratégico de la Universidad Estatal de Milagro'
                if 'info' in request.GET:
                    data['info'] = request.GET['info']
                # LIQUIDACIONES

                data['currenttime'] = datetime.now()
                fecha = datetime.today().date() - timedelta(days=15)

                data['eTemplateBaseSetting'] = eTemplateBaseSetting = request.session['eTemplateBaseSetting'] if 'eTemplateBaseSetting' in request.session and request.session['eTemplateBaseSetting'] else None
                modulos_favoritos = None
                ids_modulos_favoritos = []
                if eTemplateBaseSetting and request.method == 'GET':
                    if eTemplateBaseSetting.use_menu_favorite_module:
                        if MenuFavoriteProfile.objects.values("id").filter(setting=eTemplateBaseSetting, profile=perfilprincipal).exists():
                            eMenuFavoriteProfile = MenuFavoriteProfile.objects.filter(setting=eTemplateBaseSetting, profile=perfilprincipal)[0]
                            ids_modulos_favoritos = eMenuFavoriteProfile.mis_modulos_id()
                            modulos_favoritos = eMenuFavoriteProfile.mis_modulos()
                #data['CATEGORIZACION_MODULOS'] = variable_valor('CATEGORIZACION_MODULOS')
                data['ids_modulos_favoritos'] = ids_modulos_favoritos
                data['modulos_favoritos'] = modulos_favoritos

                lista_urls = []
                return render(request, 'panelnew.html', data)
            except Exception as ex:
                text_error = 'Error on line {}, {}'.format(sys.exc_info()[-1].tb_lineno, ex)
                return JsonResponse({'resp': f'{text_error}'})
                # return HttpResponseRedirect('/#logout')


# CAMBIO CLAVES
# @#login_required(redirect_field_name='ret', #login_url='/#loginsga')
@login_required(redirect_field_name='ret', login_url='/#loginsagest')
#@last_access
@transaction.atomic()
def passwd(request):
    if request.method == 'POST':
        if 'action' in request.POST:

            action = request.POST['action']

        return JsonResponse({"result": "bad", "mensaje": u"Solicitud Incorrecta."})