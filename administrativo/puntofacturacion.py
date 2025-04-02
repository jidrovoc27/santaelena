# -*- coding: UTF-8 -*-
import json

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.forms import model_to_dict
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.shortcuts import render
from django.template.loader import get_template

#from decorators import secure_module, last_access
from administrativo.forms import LugarRecaudacionForm, PuntoVentaForm, SecuencialRecaudacionesForm
from administrativo.models import LugarRecaudacion, PuntoVenta, SecuencialRecaudaciones, ComprobantePago, Administrativo, Persona
# from settings import TESORERO_ID
from administrativo.commonviews import adduserdata
from administrativo.funciones import MiPaginador, encrypt


@login_required(redirect_field_name='ret', login_url='/loginclinica')
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
                f = LugarRecaudacionForm(request.POST)
                if f.is_valid():
                    if LugarRecaudacion.objects.filter(persona_id=f.cleaned_data['persona'], puntoventa=f.cleaned_data['puntoventa'], activo=True).exists():
                        return JsonResponse({"result": "bad", "mensaje": u"Ya esta registrado un lugar de recaudacion con esta persona y este punto de venta."})
                    lugarrecaudacion = LugarRecaudacion(persona_id=int(f.cleaned_data['persona']),
                                           puntoventa=f.cleaned_data['puntoventa'],
                                           nombre=f.cleaned_data['nombre'],
                                           activo=f.cleaned_data['activo'])
                    lugarrecaudacion.save(request)
                    #log(u'Adiciono lugar de recaudacion: %s' % lugarrecaudacion, request, "add")
                    return JsonResponse({"result": "ok"})
                else:
                    raise NameError('Error')
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": "bad", "mensaje": u"Error al guardar los datos."})
        elif action == 'edit':
            try:
                f = LugarRecaudacionForm(request.POST)
                lugarrecaudacion = LugarRecaudacion.objects.get(id=request.POST['id'])
                if f.is_valid():
                    if LugarRecaudacion.objects.filter(persona_id=f.cleaned_data['persona'], puntoventa=f.cleaned_data['puntoventa'], activo=True).exclude(id=lugarrecaudacion.id).exists():
                        return JsonResponse({"result": "bad", "mensaje": u"Ya esta registrado un lugar de recaudacion con esta persona y este punto de venta."})
                    lugarrecaudacion.persona_id=int(f.cleaned_data['persona'])
                    lugarrecaudacion.puntoventa=f.cleaned_data['puntoventa']
                    lugarrecaudacion.nombre=f.cleaned_data['nombre']
                    lugarrecaudacion.activo=f.cleaned_data['activo']
                    lugarrecaudacion.save(request)
                    #log(u'Edito un lugar de recaudacion: %s' % lugarrecaudacion, request, "edit")
                    return JsonResponse({"result": "ok"})
                else:
                    raise NameError('Error')
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": "bad", "mensaje": u"Error al guardar los datos."})
        elif action == 'desactivar':
            try:
                lugarrecaudacion = LugarRecaudacion.objects.get(id=request.POST['id'])
                if lugarrecaudacion.activo==True:
                    lugarrecaudacion.activo = False
                    #log(u'Desactivo un lugar de recaudacion: %s' % lugarrecaudacion, request, "edit")
                else:
                    lugarrecaudacion.activo = True
                    #log(u'Activo un lugar de recaudacion: %s' % lugarrecaudacion, request, "edit")
                lugarrecaudacion.save(request)
                return JsonResponse({"result": "ok"})
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": "bad", "mensaje": u"Error al guardar los datos."})
        elif action == 'delete':
            try:
                lugarrecaudacion = LugarRecaudacion.objects.get(id=request.POST['id'])
                lugarrecaudacion.status = False
                lugarrecaudacion.save(request)
                #log(u'Elimino un lugar de recaudacion: %s' % lugarrecaudacion, request, "del")
                return JsonResponse({"result": "ok"})
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": "bad", "mensaje": u"Error al guardar los datos."})
        elif action == 'buscar_persona':
            try:
                term = request.POST['term']
                data = []
                for persona in Administrativo.objects.filter(Q(persona__nombres__icontains=term) | Q(persona__apellido1__icontains=term) | Q(persona__apellido2__icontains=term) & Q(status=True))[:10]:
                    item = {'id': persona.persona.id, 'text': persona.persona.nombre_completo()}
                    data.append(item)
                return HttpResponse(json.dumps(data), content_type='application/json')
            except Exception as e:
                pass
        elif action == 'addpunto':
            try:
                with transaction.atomic():
                    form = PuntoVentaForm(request.POST, request.FILES)
                    if form.is_valid():
                        filtro = PuntoVenta(nombreestablecimiento=form.cleaned_data['nombreestablecimiento'],
                                            direccion=form.cleaned_data['direccion'],
                                            establecimiento=form.cleaned_data['establecimiento'],
                                            puntoventa=form.cleaned_data['puntoventa'],
                                            activo=form.cleaned_data['activo'],
                                            facturaelectronica=form.cleaned_data['facturaelectronica'],
                                            imprimirfactura=form.cleaned_data['imprimirfactura'])
                        filtro.save(request)
                        #log(u'Adicionó Punto de Venta: %s' % filtro, request, "add")
                        return JsonResponse({"result": False}, safe=False)
                    else:
                        transaction.set_rollback(True)
                        return JsonResponse({"result": True, "mensaje": "Complete los datos"}, safe=False)
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": True, "mensaje": "Intentelo más tarde."}, safe=False)
        elif action == 'changepunto':
            try:
                with transaction.atomic():
                    filtro = PuntoVenta.objects.get(pk=request.POST['id'])
                    f = PuntoVentaForm(request.POST, request.FILES)
                    if f.is_valid():
                        filtro.nombreestablecimiento = f.cleaned_data['nombreestablecimiento']
                        filtro.direccion = f.cleaned_data['direccion']
                        filtro.establecimiento = f.cleaned_data['establecimiento']
                        filtro.puntoventa = f.cleaned_data['puntoventa']
                        filtro.activo = f.cleaned_data['activo']
                        filtro.facturaelectronica = f.cleaned_data['facturaelectronica']
                        filtro.imprimirfactura = f.cleaned_data['imprimirfactura']
                        filtro.save(request)
                        #log(u'Edito Punto de Venta: %s' % filtro, request, "edit")
                        return JsonResponse({"result": False}, safe=False)
                    else:
                        transaction.set_rollback(True)
                        return JsonResponse({"result": True, "mensaje": "Complete los datos requeridos."}, safe=False)
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": True, "mensaje": "Intentelo más tarde."}, safe=False)
        elif action == 'delpunto':
            try:
                filtro = PuntoVenta.objects.get(pk=request.POST['id'])
                filtro.status = False
                filtro.save(request)
                #log(u'Eliminó Punto de Venta: %s' % filtro, request, "del")
                return JsonResponse({"result": False,"error":False}, safe=False)
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": True, "mensaje": "Intentelo más tarde."}, safe=False)
        elif action == 'addsecuencial':
            try:
                with transaction.atomic():
                    form = SecuencialRecaudacionesForm(request.POST, request.FILES)
                    if form.is_valid():
                        filtro = SecuencialRecaudaciones(puntoventa=form.cleaned_data['puntoventa'],
                                            comprobante=form.cleaned_data['comprobante'],
                                            cajero=form.cleaned_data['cajero'])
                        filtro.save(request)
                        #log(u'Adicionó Secuencial de Recaudación: %s' % filtro, request, "add")
                        return JsonResponse({"result": False}, safe=False)
                    else:
                        transaction.set_rollback(True)
                        return JsonResponse({"result": True, "mensaje": "Complete los datos"}, safe=False)
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": True, "mensaje": "Intentelo más tarde."}, safe=False)
        elif action == 'changesecuencial':
            try:
                with transaction.atomic():
                    filtro = SecuencialRecaudaciones.objects.get(pk=request.POST['id'])
                    f = SecuencialRecaudacionesForm(request.POST, request.FILES)
                    if f.is_valid():
                        filtro.puntoventa = f.cleaned_data['puntoventa']
                        filtro.comprobante = f.cleaned_data['comprobante']
                        filtro.save(request)
                        #log(u'Edito Secuencial de Recaudación: %s' % filtro, request, "edit")
                        return JsonResponse({"result": False}, safe=False)
                    else:
                        transaction.set_rollback(True)
                        return JsonResponse({"result": True, "mensaje": "Complete los datos requeridos."}, safe=False)
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": True, "mensaje": "Intentelo más tarde."}, safe=False)
        elif action == 'delsecuencial':
            try:
                filtro = SecuencialRecaudaciones.objects.get(pk=request.POST['id'])
                filtro.status = False
                filtro.save(request)
                #log(u'Eliminó Secuencial de Recaudación: %s' % filtro, request, "del")
                return JsonResponse({"result": False,"error":False}, safe=False)
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": True, "mensaje": "Intentelo más tarde."}, safe=False)
        return JsonResponse({"result": "bad", "mensaje": u"Solicitud Incorrecta."})
    else:
        if 'action' in request.GET:
            data['action'] = action = request.GET['action']
            if action == 'add':
                try:
                    data['title'] = u'Agregar lugar de recaudacion'
                    data['action'] = action
                    data['form'] = LugarRecaudacionForm()
                    return render(request, "puntofacturacion/add.html", data)
                except Exception as ex:
                    pass
            elif action == 'edit':
                try:
                    data['lugar'] = lugar = LugarRecaudacion.objects.get(id=int(encrypt(request.GET['id'])))
                    data['title'] = u'Editar lugar de recaudacion'
                    data['action'] = action
                    data['persona'] = lugar.persona
                    data['id'] = lugar.id
                    data['form'] = LugarRecaudacionForm(initial=model_to_dict(lugar))
                    return render(request, "puntofacturacion/add.html", data)
                except Exception as ex:
                    pass
            elif action == 'desactivar':
                try:
                    data['lugarrecaudacion'] = lugarrecaudacion = LugarRecaudacion.objects.get(pk=int(encrypt(request.GET['id'])))
                    data['estado'] = 'Desactivar'  if lugarrecaudacion.activo else 'Activar'
                    data['title'] = u'Desactivar Lugar de recaudacion' if lugarrecaudacion.activo else  u'Activar Lugar de recaudacion'
                    data['action'] = action
                    return render(request, "puntofacturacion/delete.html", data)
                except Exception as ex:
                    pass
            elif action == 'delete':
                try:
                    data['lugarrecaudacion'] = lugarrecaudacion = LugarRecaudacion.objects.get(pk=int(encrypt(request.GET['id'])))
                    data['estado'] = 'Eliminar'
                    data['title'] = u'Eliminar Lugar de recaudacion'
                    data['action'] = action
                    return render(request, "puntofacturacion/delete.html", data)
                except Exception as ex:
                    pass
            elif action == 'puntosventa':
                try:
                    data['title'] = u'Puntos de Venta'
                    data['listado'] = listado = PuntoVenta.objects.filter(status=True).order_by('establecimiento')
                    return render(request, "puntofacturacion/puntoventas.html", data)
                except Exception as ex:
                    pass
            elif action == 'addpunto':
                try:
                    form = PuntoVentaForm()
                    data['form'] = form
                    template = get_template("puntofacturacion/formmodal.html")
                    return JsonResponse({"result": True, 'data': template.render(data)})
                except Exception as ex:
                    return JsonResponse({"result": False, 'message': str(ex)})
            elif action == 'changepunto':
                try:
                    data['id'] = request.GET['id']
                    data['filtro'] = filtro = PuntoVenta.objects.get(pk=request.GET['id'])
                    data['form'] = PuntoVentaForm(initial=model_to_dict(filtro))
                    template = get_template("puntofacturacion/formmodal.html")
                    return JsonResponse({"result": True, 'data': template.render(data)})
                except Exception as ex:
                    pass
            elif action == 'secuencial':
                try:
                    data['title'] = u'Secuenciales de Recaudación'
                    data['ultimafactura'] = ComprobantePago.objects.filter(status=True).order_by('-id').first()
                    data['listado'] = listado = SecuencialRecaudaciones.objects.filter(status=True).order_by('puntoventa__establecimiento')
                    return render(request, "puntofacturacion/secuencialrecaudacion.html", data)
                except Exception as ex:
                    pass
            elif action == 'addsecuencial':
                try:
                    form = SecuencialRecaudacionesForm()
                    data['form'] = form
                    template = get_template("puntofacturacion/formmodal.html")
                    return JsonResponse({"result": True, 'data': template.render(data)})
                except Exception as ex:
                    return JsonResponse({"result": False, 'message': str(ex)})
            elif action == 'changesecuencial':
                try:
                    data['id'] = request.GET['id']
                    data['filtro'] = filtro = SecuencialRecaudaciones.objects.get(pk=request.GET['id'])
                    data['form'] = SecuencialRecaudacionesForm(initial=model_to_dict(filtro))
                    template = get_template("puntofacturacion/formmodal.html")
                    return JsonResponse({"result": True, 'data': template.render(data)})
                except Exception as ex:
                    pass
            return HttpResponseRedirect(request.path)
        else:
            try:
                data['title'] = u'Lugares de Recaudacion'
                ids = None
                search = None
                search, filtro, url_vars = request.GET.get('s', ''), Q(status=True), ''
                searchdate = None
                sesiones = None
                lugar = LugarRecaudacion.objects.filter(puntoventa__activo=True, status=True).select_related().order_by('-puntoventa')

                if 's' in request.GET:
                    if request.GET['s'] != '':
                        data['search'] = search = request.GET['s']
                        url_vars += f'&s={search}'
                if search:
                    search = request.GET['s'].strip()
                    ss = search.split(' ')
                    if len(ss) == 1:
                        lugar = lugar.filter(Q(persona__apellido1__icontains=search) |
                                                             Q(persona__apellido2__icontains=search) |
                                                             Q(persona__nombres__icontains=search) |
                                                             Q(nombre__icontains=search)
                                             & Q(puntoventa__activo=True) & Q(status=True)).distinct().order_by('-puntoventa')
                    else:
                        lugar = lugar.filter(Q(persona__apellido1__icontains=ss[0]) &
                                                             Q(persona__apellido2__icontains=ss[1]) |
                                             Q(nombre__icontains=ss[1])
                                             & Q(puntoventa__activo=True) & Q(status=True)).distinct().order_by('-puntoventa')

                elif search is None:
                    lugar = lugar.filter(puntoventa__activo=True, status=True).distinct().order_by('-puntoventa')

                paging = MiPaginador(lugar, 25)
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
                data['lugares'] = page.object_list
                data['search'] = search if search else ""
                return render(request, "puntofacturacion/view.html", data)
            except Exception as ex:
                return JsonResponse({"result": "bad", "mensaje": str(ex)})