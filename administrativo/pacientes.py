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
from administrativo.models import Persona, Paciente, Paciente
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
                    personapaciente = Persona(nombres=f.cleaned_data['nombres'],
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
                    personapaciente.save(request)
                    paciente = Paciente(persona=personapaciente,
                                                    fechaingreso=datetime.now().date(),
                                                    activo=True)
                    paciente.save(request)
                    personapaciente.crear_perfil(paciente=paciente)
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
                    paciente = Paciente.objects.get(pk=request.POST['id'])
                    personaadmin = paciente.persona
                    personaadmin.nombres = f.cleaned_data['nombres']
                    personaadmin.apellido1 = f.cleaned_data['apellido1']
                    personaadmin.apellido2 = f.cleaned_data['apellido2']
                    personaadmin.identificacion = f.cleaned_data['identificacion']
                    personaadmin.nacimiento = f.cleaned_data['nacimiento']
                    personaadmin.sexo = f.cleaned_data['sexo']
                    personaadmin.nacionalidad = f.cleaned_data['nacionalidad']
                    personaadmin.sector = f.cleaned_data['sector']
                    personaadmin.direccion = f.cleaned_data['direccion']
                    personaadmin.direccion2 = f.cleaned_data['direccion2']
                    personaadmin.numeroresidencia = f.cleaned_data['numeroresidencia']
                    personaadmin.telefono = f.cleaned_data['telefono']
                    personaadmin.telefono_conv = f.cleaned_data['telefono_conv']
                    personaadmin.correo = f.cleaned_data['email']
                    personaadmin.save()
                    #log(u'Modifico paciente: %s' % paciente, request, "edit")
                    return JsonResponse({"result": "ok"})
                else:
                     raise NameError('Error')
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": "bad", "mensaje": u"Error al guardar los datos."})

        elif action == 'resetear':
            try:
                paciente = Paciente.objects.get(pk=request.POST['id'])
                resetear_clave(paciente.persona)
                #log(u'Reseteo clave de usuario: %s' % paciente, request, "edit")
                return JsonResponse({"result": "ok"})
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": "bad", "mensaje": u"Error al guardar los datos."})

        elif action == 'activar':
            try:
                paciente = Paciente.objects.get(pk=request.POST['id'])
                usuario = paciente.persona.usuario
                usuario.is_active = True
                usuario.save()
                #log(u'Activo usuario: %s' % paciente, request, "edit")
                return JsonResponse({"result": "ok"})
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": "bad", "mensaje": u"Error al guardar los datos."})

        elif action == 'activarperfil':
            try:
                paciente = Paciente.objects.get(pk=request.POST['id'])
                paciente.activo = True
                paciente.save()
                #log(u'Activo perfil de usuario: %s' % paciente, request, "edit")
                return JsonResponse({"result": "ok"})
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": "bad", "mensaje": u"Error al guardar los datos."})

        elif action == 'desactivar':
            try:
                paciente = Paciente.objects.get(pk=request.POST['id'])
                ui = paciente.persona.usuario
                ui.is_active = False
                ui.save()
                grupos_persona = paciente.persona.usuario.groups.all()
                for gp in grupos_persona:
                    gp.user_set.remove(paciente.persona.usuario)
                    gp.save()
                #log(u'Desactivo usuario: %s' % paciente, request, "edit")
                return JsonResponse({"result": "ok"})
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": "bad", "mensaje": u"Error al guardar los datos."})

        elif action == 'desactivarperfil':
            try:
                paciente = Paciente.objects.get(pk=request.POST['id'])
                paciente.activo = False
                paciente.save()
                grupos_persona = paciente.persona.usuario.groups.all()
                for gp in grupos_persona:
                    gp.user_set.remove(paciente.persona.usuario)
                    gp.save()
                #log(u'Desactivo perfil de usuario: %s' % paciente, request, "edit")
                return JsonResponse({"result": "ok"})
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": "bad", "mensaje": u"Error al guardar los datos."})

        return JsonResponse({"result": "bad", "mensaje": u"Solicitud Incorrecta."})
    else:
        data['title'] = u'Listado de pacientes'
        if 'action' in request.GET:
            action = request.GET['action']

            if action == 'add':
                try:
                    puede_realizar_accion(request, 'sga.puede_modificar_administrativos')
                    data['title'] = u'Adicionar paciente'
                    form = PacientesForm()
                    data['form'] = form
                    return render(request, "personas/add.html", data)
                except Exception as ex:
                    pass

            elif action == 'desactivar':
                try:
                    puede_realizar_accion(request, 'sga.puede_modificar_administrativos')
                    data['title'] = u'Desactivar usuario'
                    data['paciente'] = Paciente.objects.get(pk=request.GET['id'])
                    return render(request, "personas/desactivar.html", data)
                except Exception as ex:
                    pass

            elif action == 'desactivarperfil':
                try:
                    puede_realizar_accion(request, 'sga.puede_modificar_administrativos')
                    data['title'] = u'Desactivar perfil de usuario'
                    data['paciente'] = Paciente.objects.get(pk=request.GET['id'])
                    return render(request, "personas/desactivarperfil.html", data)
                except Exception as ex:
                    pass

            elif action == 'activar':
                try:
                    puede_realizar_accion(request, 'sga.puede_modificar_administrativos')
                    data['title'] = u'Activar usuario'
                    data['paciente'] = Paciente.objects.get(pk=request.GET['id'])
                    return render(request, "personas/activar.html", data)
                except Exception as ex:
                    pass

            elif action == 'activarperfil':
                try:
                    puede_realizar_accion(request, 'sga.puede_modificar_administrativos')
                    data['title'] = u'Activar perfil de usuario'
                    data['paciente'] = Paciente.objects.get(pk=request.GET['id'])
                    return render(request, "personas/activarperfil.html", data)
                except Exception as ex:
                    pass

            elif action == 'edit':
                try:
                    #puede_realizar_accion(request, 'sga.puede_modificar_administrativos')
                    data = verificarbusqueda(request, data)
                    data['title'] = u'Editar personal paciente'
                    data['paciente'] = paciente = Paciente.objects.get(pk=request.GET['id'])
                    personaadmin = paciente.persona
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
                    return render(request, "personas/edit.html", data)
                except Exception as ex:
                    pass

            elif action == 'addgrupo':
                try:
                    #puede_realizar_accion(request, 'sga.puede_modificar_administrativos')
                    data['title'] = u'Adicionar grupo'
                    data['paciente'] = Paciente.objects.get(pk=request.GET['id'])
                    form = GrupoUsuarioMultipleForm()
                    form.grupos(Group.objects.all().order_by('name'))
                    data['form'] = form
                    return render(request, "personas/addgrupo.html", data)
                except Exception as ex:
                    pass

            elif action == 'resetear':
                try:
                    puede_realizar_accion(request, 'sga.puede_modificar_administrativos')
                    data['title'] = u'Resetear clave del usuario'
                    data['paciente'] = Paciente.objects.get(pk=request.GET['id'])
                    return render(request, "personas/resetear.html", data)
                except Exception as ex:
                    pass

            elif action == 'addprofesor':
                try:
                    puede_realizar_accion(request, 'sga.puede_modificar_administrativos')
                    data['title'] = u'Crear cuenta de profesor'
                    data['paciente'] = Paciente.objects.get(pk=request.GET['id'])
                    return render(request, "personas/addprofesor.html", data)
                except Exception as ex:
                    pass

            elif action == 'delgrupo':
                try:
                    puede_realizar_accion(request, 'sga.puede_modificar_administrativos')
                    data['title'] = u'Eliminar de grupo'
                    data['paciente'] = Paciente.objects.get(pk=request.GET['id'])
                    data['grupo'] = Group.objects.get(pk=request.GET['idg'])
                    return render(request, "personas/delgrupo.html", data)
                except Exception as ex:
                    pass

            return HttpResponseRedirect(request.path)
        else:
            try:
                estado, search, grupo, filtro, url_vars = request.GET.get('estado', ''), request.GET.get('search', ''), request.GET.getlist('grupo', ''), Q(status=True), ''
                if estado:
                    data['estado'] = estsolicitud = int(estado)
                    if estsolicitud == 1:
                        filtro = filtro & Q(activo=True)
                    else:
                        filtro = filtro & Q(activo=False)
                    url_vars += "&estado={}".format(estado)
                if search:
                    data['search'] = search
                    s = search.split()
                    if len(s) == 1:
                        filtro = filtro & (Q(persona__identificacion__icontains=search) | Q(persona__nombres__icontains=search)| Q(persona__apellido1__icontains=search) | Q(persona__apellido2__icontains=search))
                    else:
                        filtro = filtro & (Q(persona__apellido1__icontains=s[0]) & Q(persona__apellido2__icontains=s[1]))
                    url_vars += '&search={}'.format(search)
                if not url_vars:
                    filtro = filtro & Q(activo=True)
                listado = Paciente.objects.filter(filtro).distinct()
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
                data['pacientes'] = page.object_list
                data["url_vars"] = url_vars
                data['grupo_administrativos'] = 1
                data['administrativos_total'] = listado.count()
                # if not url_vars:
                #     log_view(request)
                return render(request, "personas/view.html", data)
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
