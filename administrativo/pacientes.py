# -*- coding: UTF-8 -*-
import json
import sys
import xlwt
from datetime import datetime
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models.query_utils import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
#from decorators import secure_module, last_access
from administrativo.commonviews import adduserdata
from administrativo.forms import PacientesForm, GrupoUsuarioForm, GrupoUsuarioMultipleForm
from administrativo.funciones import MiPaginador, calculate_username, puede_realizar_accion, lista_correo, \
    generar_usuario, resetear_clave, generar_nombre
from administrativo.correo import *
from administrativo.models import Persona, Administrativo, Paciente
#from sagest.funciones import log_view
from openpyxl import load_workbook
from django.template.loader import get_template

@login_required(redirect_field_name='ret', login_url='/loginclinica')
#@secure_module
#@last_access
@transaction.atomic()
def view(request):
    global ex
    data = {}
    adduserdata(request, data)
    data['persona'] = persona = data['persona']
    if request.method == 'POST':
        action = request.POST['action']

        if action == 'add':
            try:
                f = PacientesForm(request.POST)
                if f.is_valid():
                    if f.cleaned_data['identificacion'] and Persona.objects.filter(identificacion=f.cleaned_data['identificacion']).exists():
                        return JsonResponse({"result": "bad", "mensaje": u"El numero de identificacion ya está registrado."})
                    if not f.cleaned_data['identificacion']:
                        return JsonResponse({"result": "bad", "mensaje": u"Debe especificar un número de identificación."})
                    personaadmin = Persona(nombres=f.cleaned_data['nombres'],
                                           apellido1=f.cleaned_data['apellido1'],
                                           apellido2=f.cleaned_data['apellido2'],
                                           identificacion=f.cleaned_data['identificacion'],
                                           nacimiento=f.cleaned_data['nacimiento'],
                                           sexo=f.cleaned_data['sexo'],
                                           nacionalidad=f.cleaned_data['nacionalidad'],
                                           sector=f.cleaned_data['sector'],
                                           direccion=f.cleaned_data['direccion'],
                                           direccion2=f.cleaned_data['direccion2'],
                                           numeroresidencia=f.cleaned_data['numeroresidencia'],
                                           telefono=f.cleaned_data['telefono'],
                                           telefono_conv=f.cleaned_data['telefono_conv'],
                                           correo=f.cleaned_data['email'])
                    personaadmin.save(request)
                    paciente = Paciente(persona=personaadmin,
                                                    fechaingreso=datetime.now().date(),
                                                    activo=True)
                    paciente.save(request)
                    username = calculate_username(personaadmin)
                    generar_usuario(personaadmin, username, 1)
                    personaadmin.save(request)
                    personaadmin.crear_perfil(paciente=paciente)
                    return JsonResponse({"result": "ok", "id": paciente.id})
                else:
                     raise NameError('Error')
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": "bad", "mensaje": u"Error al guardar los datos." })

        elif action == 'edit':
            try:
                f = PacientesForm(request.POST)
                if f.is_valid():
                    administrativo = Administrativo.objects.get(pk=request.POST['id'])
                    personaadmin = administrativo.persona
                    personaadmin.nombres = f.cleaned_data['nombres']
                    personaadmin.apellido1 = f.cleaned_data['apellido1']
                    personaadmin.apellido2 = f.cleaned_data['apellido2']
                    personaadmin.nacimiento = f.cleaned_data['nacimiento']
                    personaadmin.sexo = f.cleaned_data['sexo']
                    personaadmin.nacionalidad = f.cleaned_data['nacionalidad']
                    personaadmin.pais = f.cleaned_data['pais']
                    personaadmin.provincia = f.cleaned_data['provincia']
                    personaadmin.ciudad = f.cleaned_data['ciudad']
                    personaadmin.parroquia = f.cleaned_data['parroquia']
                    personaadmin.sector = f.cleaned_data['sector']
                    personaadmin.direccion = f.cleaned_data['direccion']
                    personaadmin.direccion2 = f.cleaned_data['direccion2']
                    personaadmin.numeroresidencia = f.cleaned_data['numeroresidencia']
                    personaadmin.telefono = f.cleaned_data['telefono']
                    personaadmin.telefono_conv = f.cleaned_data['telefono_conv']
                    personaadmin.correo = f.cleaned_data['email']
                    personaadmin.save()
                    #log(u'Modifico administrativo: %s' % administrativo, request, "edit")
                    return JsonResponse({"result": "ok"})
                else:
                     raise NameError('Error')
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": "bad", "mensaje": u"Error al guardar los datos."})

        elif action == 'resetear':
            try:
                administrativo = Administrativo.objects.get(pk=request.POST['id'])
                resetear_clave(administrativo.persona)
                #log(u'Reseteo clave de usuario: %s' % administrativo, request, "edit")
                return JsonResponse({"result": "ok"})
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": "bad", "mensaje": u"Error al guardar los datos."})

        elif action == 'activar':
            try:
                administrativo = Administrativo.objects.get(pk=request.POST['id'])
                usuario = administrativo.persona.usuario
                usuario.is_active = True
                usuario.save()
                #log(u'Activo usuario: %s' % administrativo, request, "edit")
                return JsonResponse({"result": "ok"})
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": "bad", "mensaje": u"Error al guardar los datos."})

        elif action == 'activarperfil':
            try:
                administrativo = Administrativo.objects.get(pk=request.POST['id'])
                administrativo.activo = True
                administrativo.save()
                #log(u'Activo perfil de usuario: %s' % administrativo, request, "edit")
                return JsonResponse({"result": "ok"})
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": "bad", "mensaje": u"Error al guardar los datos."})

        elif action == 'desactivar':
            try:
                administrativo = Administrativo.objects.get(pk=request.POST['id'])
                ui = administrativo.persona.usuario
                ui.is_active = False
                ui.save()
                grupos_persona = administrativo.persona.usuario.groups.all()
                for gp in grupos_persona:
                    gp.user_set.remove(administrativo.persona.usuario)
                    gp.save()
                #log(u'Desactivo usuario: %s' % administrativo, request, "edit")
                return JsonResponse({"result": "ok"})
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": "bad", "mensaje": u"Error al guardar los datos."})

        elif action == 'desactivarperfil':
            try:
                administrativo = Administrativo.objects.get(pk=request.POST['id'])
                administrativo.activo = False
                administrativo.save()
                grupos_persona = administrativo.persona.usuario.groups.all()
                for gp in grupos_persona:
                    gp.user_set.remove(administrativo.persona.usuario)
                    gp.save()
                #log(u'Desactivo perfil de usuario: %s' % administrativo, request, "edit")
                return JsonResponse({"result": "ok"})
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": "bad", "mensaje": u"Error al guardar los datos."})

        elif action == 'addgrupo':
            try:
                administrativo = Administrativo.objects.get(pk=request.POST['id'])
                form = GrupoUsuarioMultipleForm(request.POST)
                if form.is_valid():
                    for grupo in form.cleaned_data['grupo']:
                        grupo.user_set.add(administrativo.persona.usuario)
                        grupo.save()
                        #log(u'Adiciono grupo de usuarios: %s' % grupo, request, "add")
                    return JsonResponse({"result": "ok"})
                else:
                     raise NameError('Error')
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": "bad", "mensaje": u"Error al guardar los datos."})

        elif action == 'delgrupo':
            try:
                administrativo = Administrativo.objects.get(pk=request.POST['id'])
                grupo = Group.objects.get(pk=request.POST['idg'])
                if administrativo.persona.usuario.groups.count() <= 1:
                    return JsonResponse({"result": "bad", "mensaje": u"El usuario debe de pertenecer a un grupo."})
                grupo.user_set.remove(administrativo.persona.usuario)
                grupo.save()
                #log(u'Elimino de grupo de usuarios: %s' % grupo, request, "del")
                return JsonResponse({"result": "ok"})
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": "bad", "mensaje": u"Error al guardar los datos."})

        elif action == 'cambiarpermisocurso':
            try:
                valor = 0
                persona= Persona.objects.get(id=request.POST['id'], status=True)
                if  persona.es_administrativo_perfilactivo():
                    administrativo = persona.administrativo()
                    if administrativo.curso:
                        administrativo.curso = False
                    else:
                        administrativo.curso = True
                        valor = 1
                    administrativo.save(request)
                    #log(u'activo o desactivo permiso a curso a administrador: %s - %s - %s' % (persona, administrativo.persona, administrativo.curso), request, "edit")
                return JsonResponse({"result": "ok", "valor": valor})
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": "bad", "mensaje": u"Error al obtener los datos."})

        elif action == 'changesellerstatus':
            try:
                id = request.POST.get('pk', None)
                value = json.loads(request.POST.get('value'))
                administrativo = Administrativo.objects.get(status=True, id=int(id))
                administrativo.es_vendedor = value
                administrativo.save(request)
                #log(f"Cambio el estado es vendedor a {value} del administrativo {administrativo}", request, 'change')
                res_js = {'ok': True}
            except Exception as ex:
                msg_err = f'{ex} ({sys.exc_info()[-1].tb_lineno})'
                transaction.set_rollback(True)
                res_js = {'ok': False, 'error': msg_err}
            return JsonResponse(res_js)

        return JsonResponse({"result": "bad", "mensaje": u"Solicitud Incorrecta."})
    else:
        data['title'] = u'Listado de personal administrativo'
        if 'action' in request.GET:
            action = request.GET['action']

            if action == 'add':
                try:
                    puede_realizar_accion(request, 'sga.puede_modificar_administrativos')
                    data['title'] = u'Adicionar personal administrativo'
                    form = PacientesForm()
                    data['form'] = form
                    return render(request, "administrativos/add.html", data)
                except Exception as ex:
                    pass

            elif action == 'desactivar':
                try:
                    puede_realizar_accion(request, 'sga.puede_modificar_administrativos')
                    data['title'] = u'Desactivar usuario'
                    data['administrativo'] = Administrativo.objects.get(pk=request.GET['id'])
                    return render(request, "administrativos/desactivar.html", data)
                except Exception as ex:
                    pass

            elif action == 'desactivarperfil':
                try:
                    puede_realizar_accion(request, 'sga.puede_modificar_administrativos')
                    data['title'] = u'Desactivar perfil de usuario'
                    data['administrativo'] = Administrativo.objects.get(pk=request.GET['id'])
                    return render(request, "administrativos/desactivarperfil.html", data)
                except Exception as ex:
                    pass

            elif action == 'activar':
                try:
                    puede_realizar_accion(request, 'sga.puede_modificar_administrativos')
                    data['title'] = u'Activar usuario'
                    data['administrativo'] = Administrativo.objects.get(pk=request.GET['id'])
                    return render(request, "administrativos/activar.html", data)
                except Exception as ex:
                    pass

            elif action == 'activarperfil':
                try:
                    puede_realizar_accion(request, 'sga.puede_modificar_administrativos')
                    data['title'] = u'Activar perfil de usuario'
                    data['administrativo'] = Administrativo.objects.get(pk=request.GET['id'])
                    return render(request, "administrativos/activarperfil.html", data)
                except Exception as ex:
                    pass

            elif action == 'edit':
                try:
                    #puede_realizar_accion(request, 'sga.puede_modificar_administrativos')
                    data = verificarbusqueda(request, data)
                    data['title'] = u'Editar personal administrativo'
                    data['administrativo'] = administrativo = Administrativo.objects.get(pk=request.GET['id'])
                    personaadmin = administrativo.persona
                    form = PacientesForm(initial={'nombres': personaadmin.nombres,
                                                        'apellido1': personaadmin.apellido1,
                                                        'apellido2': personaadmin.apellido2,
                                                        'identificacion': personaadmin.identificacion,
                                                        'sexo': personaadmin.sexo,
                                                        'nacimiento': personaadmin.nacimiento,
                                                        'nacionalidad': personaadmin.nacionalidad,
                                                        'pais': personaadmin.pais,
                                                        'provincia': personaadmin.provincia,
                                                        'ciudad': personaadmin.ciudad,
                                                        'parroquia': personaadmin.parroquia,
                                                        'sector': personaadmin.sector,
                                                        'direccion': personaadmin.direccion,
                                                        'direccion2': personaadmin.direccion2,
                                                        'numeroresidencia': personaadmin.numeroresidencia,
                                                        'telefono': personaadmin.telefono,
                                                        'telefono_conv': personaadmin.telefono_conv,
                                                        'email': personaadmin.correo})
                    data['form'] = form
                    return render(request, "administrativos/edit.html", data)
                except Exception as ex:
                    pass

            elif action == 'addgrupo':
                try:
                    #puede_realizar_accion(request, 'sga.puede_modificar_administrativos')
                    data['title'] = u'Adicionar grupo'
                    data['administrativo'] = Administrativo.objects.get(pk=request.GET['id'])
                    form = GrupoUsuarioMultipleForm()
                    form.grupos(Group.objects.all().order_by('name'))
                    data['form'] = form
                    return render(request, "administrativos/addgrupo.html", data)
                except Exception as ex:
                    pass

            elif action == 'resetear':
                try:
                    puede_realizar_accion(request, 'sga.puede_modificar_administrativos')
                    data['title'] = u'Resetear clave del usuario'
                    data['administrativo'] = Administrativo.objects.get(pk=request.GET['id'])
                    return render(request, "administrativos/resetear.html", data)
                except Exception as ex:
                    pass

            elif action == 'addprofesor':
                try:
                    puede_realizar_accion(request, 'sga.puede_modificar_administrativos')
                    data['title'] = u'Crear cuenta de profesor'
                    data['administrativo'] = Administrativo.objects.get(pk=request.GET['id'])
                    return render(request, "administrativos/addprofesor.html", data)
                except Exception as ex:
                    pass

            elif action == 'delgrupo':
                try:
                    puede_realizar_accion(request, 'sga.puede_modificar_administrativos')
                    data['title'] = u'Eliminar de grupo'
                    data['administrativo'] = Administrativo.objects.get(pk=request.GET['id'])
                    data['grupo'] = Group.objects.get(pk=request.GET['idg'])
                    return render(request, "administrativos/delgrupo.html", data)
                except Exception as ex:
                    pass

            return HttpResponseRedirect(request.path)
        else:
            try:
                data['listado_grupos'] = listado_grupos = Group.objects.all().order_by('name')
                estado, search, grupo, filtro, url_vars = request.GET.get('estado', ''), request.GET.get('search', ''), request.GET.getlist('grupo', ''), Q(status=True), ''
                if estado:
                    data['estado'] = estsolicitud = int(estado)
                    if estsolicitud == 1:
                        filtro = filtro & Q(activo=True)
                    else:
                        filtro = filtro & Q(activo=False)
                    url_vars += "&estado={}".format(estado)
                if grupo:
                    data["grupo"] = gruposids = list(map(lambda x: int(x), grupo))
                    for scl in gruposids:
                        url_vars += "&grupo={}".format(scl)
                    filtro = filtro & Q(persona__usuario__groups__in=gruposids)
                if search:
                    data['search'] = search
                    s = search.split()
                    if len(s) == 1:
                        filtro = filtro & (Q(persona__cedula__icontains=search) | Q(persona__nombres__icontains=search)| Q(persona__apellido1__icontains=search) | Q(persona__apellido2__icontains=search))
                    else:
                        filtro = filtro & (Q(persona__apellido1__icontains=s[0]) & Q(persona__apellido2__icontains=s[1]))
                    url_vars += '&search={}'.format(search)
                if not url_vars:
                    filtro = filtro & Q(activo=True)
                listado = Administrativo.objects.filter(filtro).distinct()
                paging = MiPaginador(listado.order_by('persona__apellido1'), 25)
                p = 1
                try:
                    paginasesion = 1
                    if 'paginador' in request.session:
                        paginasesion = int(request.session['paginador'])
                    if 'page' in request.GET:
                        p = int(request.GET['page'])
                    else:
                        p = paginasesion
                    try:
                        page = paging.page(p)
                    except:
                        p = 1
                    page = paging.page(p)
                except:
                    page = paging.page(p)
                request.session['paginador'] = p
                data['paging'] = paging
                data['rangospaging'] = paging.rangos_paginado(p)
                data['page'] = page
                data['search'] = search if search else ""
                data['administrativos'] = page.object_list
                data["url_vars"] = url_vars
                data['grupo_administrativos'] = 1
                data['administrativos_total'] = listado.count()
                # if not url_vars:
                #     log_view(request)
                return render(request, "administrativos/view.html", data)
            except Exception as ex:
                messages.error(request, f'Error: {ex}')
                return redirect('/')

def verificarbusqueda(request, data):
    perfil = None
    search = None
    gruposelect = None
    regreso=False
    if 'g' in request.GET:
        gruposelect = request.GET['g']
        regreso=True
    if 's' in request.GET:
        search = request.GET['s']
        regreso = True
    if 'perfil' in request.GET:
        perfil = request.GET['perfil']
        regreso = True
    data['gruposelect'] = gruposelect
    data['search'] = search
    data['perfil'] = perfil
    data['regreso'] = regreso
    return data
