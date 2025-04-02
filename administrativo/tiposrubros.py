# -*- coding: UTF-8 -*-
import json
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Value, Case, When, CharField
from django.db.models.functions import Concat
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.shortcuts import render
from django.template.loader import get_template

#from decorators import secure_module
from administrativo.commonviews import adduserdata
from administrativo.forms import TipoOtroRubroForm
from administrativo.models import TipoOtroRubro, AnioEjercicio, FormaDePago
from administrativo.funciones import MiPaginador, generar_nombre


@login_required(redirect_field_name='ret', login_url='/loginclinica')
#@secure_module
@transaction.atomic()
def view(request):
    data = {}
    adduserdata(request, data)
    data['persona'] = persona = data['persona']
    if request.method == 'POST':
        action = request.POST['action']

        if action == 'addrubros':
            try:
                form = TipoOtroRubroForm(request.POST)
                if form.is_valid():
                    registro = TipoOtroRubro(nombre=form.cleaned_data['nombre'],
                                             valor=form.cleaned_data['valor'],
                                             ivaaplicado=form.cleaned_data['ivaaplicado'],
                                             activo=form.cleaned_data['activo'],
                                             requierefactura=form.cleaned_data['requierefactura'],
                                             tiporubro=form.cleaned_data['tiporubro'],
                                             )
                    registro.save(request)
                    #log(u'Registro nuevo rubro: %s' % registro, request, "add")
                    return JsonResponse({"result": "ok"})
                else:
                     raise NameError('Error')
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": "bad", "mensaje": "Nombre de rubro ya existe. %s" % ex})

        if action == 'editrubros':
            try:
                form = TipoOtroRubroForm(request.POST)
                if form.is_valid():
                    registro = TipoOtroRubro.objects.get(pk=int(request.POST['id']))
                    registro.nombre = form.cleaned_data['nombre']
                    registro.valor = form.cleaned_data['valor']
                    registro.ivaaplicado = form.cleaned_data['ivaaplicado']
                    registro.activo = form.cleaned_data['activo']
                    registro.requierefactura = form.cleaned_data['requierefactura']
                    registro.tiporubro = form.cleaned_data['tiporubro']
                    registro.save(request)
                    #log(u'Registro modificado Rubros: %s' % registro, request, "edit")
                    return JsonResponse({"result": "ok"})
                else:
                     raise NameError('Error')
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": "bad", "mensaje": "Error al editar los datos."})

        if action == 'deleterubros':
            try:
                campo = TipoOtroRubro.objects.get(pk=request.POST['id'], status=True)
                if campo.en_uso():
                    return JsonResponse({"result": "bad", "mensaje": "El campo se encuentra en uso."})
                campo.delete()
                #log(u'Elimino campos contratos: %s' % campo, request, "del")
                return JsonResponse({"result": "ok"})
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": "bad", "mensaje": "Error al eliminar los datos."})


        if action == 'checkservicio':
            try:
                pk, estado = request.POST['id'], request.POST['val']
                mensaje = 'Servicio Activado' if estado == 'true' else 'Servicio Desactivado'
                retorno = 1 if estado == 'true' else 2
                qsbase = TipoOtroRubro.objects.get(pk=pk)
                qsbase.activo = True if retorno == 1 else False
                qsbase.save()
                return HttpResponse(json.dumps({'result': True, 'mensaje': mensaje, 'retorno': retorno}))
            except Exception as ex:
                return HttpResponse(json.dumps({'result': False, 'mensaje': ex, 'retorno': 1}))

        return JsonResponse({"result": "bad", "mensaje": "Solicitud Incorrecta."})
    else:
        if 'action' in request.GET:
            action = request.GET['action']

            if action == 'addrubros':
                try:
                    data['title'] = u'Nuevo Rubro'
                    data['form'] = TipoOtroRubroForm()
                    return render(request, "tiposrubros/addrubros.html", data)
                except Exception as ex:
                    pass

            if action == 'editrubros':
                try:
                    data['title'] = u'Modificación Rubro'
                    data['tipootrorubro'] = tipootrorubro = TipoOtroRubro.objects.get(pk=request.GET['id'])
                    form = TipoOtroRubroForm(initial={'nombre': tipootrorubro.nombre,
                                                      'ivaaplicado': tipootrorubro.ivaaplicado,
                                                      'valor': tipootrorubro.valor,
                                                      'activo': tipootrorubro.activo,
                                                      'exportabanco': tipootrorubro.exportabanco,
                                                      'requierefactura': tipootrorubro.requierefactura,
                                                      'tiporubro': tipootrorubro.tiporubro,
                                                      })
                    data['form'] = form
                    return render(request, "tiposrubros/editrubros.html", data)
                except Exception as ex:
                    pass

            if action == 'deleterubros':
                try:
                    data['title'] = u'Eliminar Rubro'
                    data['rubro'] = TipoOtroRubro.objects.get(pk=request.GET['id'])
                    return render(request, 'tiposrubros/delete.html', data)
                except Exception as ex:
                    pass

            if action == 'cambioperiodo':
                try:
                    anio = AnioEjercicio.objects.get(id=int(request.GET['id']))
                    request.session['aniofiscalpresupuesto'] = anio.anioejercicio
                except Exception as ex:
                    pass

            if action == 'formapago':
                data['title'] = u'Forma de Pago'
                search = None
                tipo = None

                if 's' in request.GET:
                    search = request.GET['s']
                if search:
                    formapago = FormaDePago.objects.filter(nombre__icontains=search, status=True)
                else:
                    formapago = FormaDePago.objects.filter(status=True).order_by('nombre')
                paging = MiPaginador(formapago, 25)
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
                data['formapago'] = page.object_list
                return render(request, "tiposrubros/formapago.html", data)

            return HttpResponseRedirect(request.path)
        else:
            try:
                data['title'] = u'Rubros'

                estados, criterio, filtros, url_vars = request.GET.get('estados', ''), request.GET.get('criterio', ''), Q(status=True), ''

                if criterio:
                    data['criterio'] = criterio
                    filtros = filtros & (Q(nombre__icontains=criterio))
                    url_vars += '&criterio=' + criterio

                if estados:
                    data['estados'] = estados
                    url_vars += "&estados={}".format(estados)
                    if estados == '1':
                        filtros = filtros & Q(activo=True)
                    if estados == '2':
                        filtros = filtros & Q(activo=False)

                data["url_vars"] = url_vars

                rubro = TipoOtroRubro.objects.filter(filtros).order_by('-pk')

                paging = MiPaginador(rubro, 25)
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
                data['rubros'] = page.object_list
                return render(request, 'tiposrubros/view.html', data)
            except Exception as ex:
                print(ex)