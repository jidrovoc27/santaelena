# -*- coding: UTF-8 -*-
import datetime
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.forms import model_to_dict
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.template.loader import get_template
from administrativo.funciones import *
# Ok
from administrativo.models import LugarRecaudacion, SesionCaja, RecaudacionFinalSesionCaja, AnioEjercicio
from administrativo.commonviews import adduserdata
from decimal import Decimal


@login_required(redirect_field_name='ret', login_url='/loginclinica')
@transaction.atomic()
def view(request):
    global ex
    data = {}
    adduserdata(request, data)
    persona = data['persona']
    anio = datetime.now().date().year
    if request.method == 'POST':
        action = request.POST['action']

        if action == 'addsesion':
            try:
                lugarrecaudacion = persona.lugar_recaudacion()
                if not lugarrecaudacion:
                    return JsonResponse({"result": False, "mensaje": u"No existe lugar de recaudación definido para esta persona."})
                if lugarrecaudacion.esta_abierta():
                    return JsonResponse({"result": False, "mensaje": u"La caja se encuentra abierta."})
                secuencia = secuencia_caja(request, datetime.now().year)
                secuencia.secuenciacaja += 1
                secuencia.save(request)
                if SesionCaja.objects.filter(caja=lugarrecaudacion, fecha=datetime.now().date()).exists():
                    return JsonResponse({"result": False, "mensaje": u"Ya hubo una sesión de caja en este dia."})
                sesioncaja = SesionCaja(caja=lugarrecaudacion,
                                        fecha=datetime.now().date(),
                                        fondo=0,
                                        abierta=True,
                                        numero=secuencia.secuenciacaja)
                sesioncaja.save(request)
                return JsonResponse({"result": True})
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": False, "mensaje": u"Error al guardar los datos."})

        elif action == 'cerrarsesion':
            try:
                lugarrecaudacion = LugarRecaudacion.objects.filter(persona=persona).first()
                sesioncaja = lugarrecaudacion.sesioncaja_set.get(pk=int(request.POST['id']))
                if not sesioncaja.abierta:
                    return JsonResponse({"result": False, "mensaje": u"La sesión de caja ya esta cerrada."})
                total_recaudado = sesioncaja.total_recibocaja_sesion()
                total_egresado = sesioncaja.total_egresado_recibocaja_sesion()
                total_neto = sesioncaja.total_neto_recibocaja_sesion()
                rf = RecaudacionFinalSesionCaja(sesion=sesioncaja,
                                      total=total_neto,
                                      comprobante=total_recaudado,
                                      salidarecaudacion=total_egresado,
                                      fecha=datetime.now())

                rf.save(request)
                sesioncaja.abierta = False
                sesioncaja.save(request)
                return JsonResponse({"result": True})
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": False, "mensaje": u"Error al guardar los datos."})

        elif action == 'detalle_sesioncaja':
            try:
                data['sesion'] = sesion = SesionCaja.objects.get(pk=int(request.POST['id']))
                data['cierre'] = sesion.cierre_sesion()
                template = get_template("rec_caja/detalle.html")
                json_content = template.render((data))
                return JsonResponse({"result": "ok", 'html': json_content})
            except Exception as ex:
                return JsonResponse({"result": "bad", "mensaje": u"Error al obtener los datos."})

        elif action == 'delete':
            try:
                sesion = SesionCaja.objects.get(pk=request.POST['id'])
                #log(u'Elimino sesion de caja: %s' % sesion, request, "del")
                sesion.status = False
                sesion.save(request)
                return JsonResponse({"result": "ok"})
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": "bad", "mensaje": f"Error al eliminar los datos. {str(ex)}"})

        elif action == 'delarchivo':
            try:
                filtro = SesionCaja.objects.get(pk=request.POST['id'])
                filtro.archivo = None
                filtro.save(request)
                #log(u'Eliminó archivo: %s' % filtro, request, "del")
                return JsonResponse({"result": False,"error":False}, safe=False)
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": True, "mensaje": "Intentelo más tarde."}, safe=False)

        return JsonResponse({"result": "bad", "mensaje": u"Solicitud Incorrecta."})
    else:
        if 'action' in request.GET:
            action = request.GET['action']

            if action == 'addsesion':
                try:
                    data['title'] = u'Abrir sesión de cobranzas en caja'
                    lugarrecaudacion = LugarRecaudacion.objects.get(persona=request.session['persona'], origenrecaudacion=1)
                    return render(request, "rec_caja/addsesion.html", data)
                except Exception as ex:
                    pass

            if action == 'getMovimientos':
                try:
                    data['title'] = u'Detalle de movimientos'
                    sesioncaja = SesionCaja.objects.get(id=int(request.GET['id']))
                    data['ingresos'] = pagos = sesioncaja.get_pagos_sesion()
                    data['totalingresos'] = totalingresos = sesioncaja.total_recibocaja_sesion()
                    data['egresos'] = egresos = sesioncaja.get_detallesalida_sesion()
                    data['totalegresos'] = totalegresos = sesioncaja.total_egresado_recibocaja_sesion()
                    data['totalneto'] = totalneto = sesioncaja.total_neto_recibocaja_sesion()
                    template = get_template("sesioncaja/modal/detallemovimientos.html")
                    return JsonResponse({"result": True, 'data': template.render(data)})
                except Exception as ex:
                    pass

            return HttpResponseRedirect(request.path)
        else:
            try:
                data['title'] = u'Sesiones diarias de recaudación'
                ids = None
                search = None
                searchdate = None
                data['mianio'] = anio
                sesiones = None
                tiene_sesion_abierta = False
                tiene_sesion_abierta = SesionCaja.objects.filter(status=True, caja__persona=persona, fecha=datetime.now(), abierta=True).exists()
                if not tiene_sesion_abierta:
                    if SesionCaja.objects.filter(status=True, caja__persona=persona, abierta=True).exists():
                        tiene_sesion_abierta = True
                if not persona.usuario.is_superuser:
                    sesiones = SesionCaja.objects.filter(status=True, caja__persona=persona).order_by('-fecha')
                else:
                    sesiones = SesionCaja.objects.filter(status=True).order_by('-fecha')



                if 's' in request.GET:
                    if request.GET['s'] != '':
                        data['search'] = search = request.GET['s']
                if 'date' in request.GET:
                    if request.GET['date'] != '':
                        data['searchdate'] = searchdate = request.GET['date']

                if search and searchdate is None:
                    search = request.GET['s'].strip()
                    ss = search.split(' ')
                    if len(ss) == 1:
                        sesiones = sesiones.filter(Q(caja__persona__apellido1__icontains=search) |
                                                             Q(caja__persona__apellido2__icontains=search) |
                                                             Q(caja__persona__nombres__icontains=search)).distinct().order_by('-fecha')
                    else:
                        sesiones = sesiones.filter(Q(caja__persona__apellido1__icontains=ss[0]) &
                                                             Q(caja__persona__apellido2__icontains=ss[1])).distinct().order_by('-fecha')


                elif searchdate and search is None:
                    sesiones = sesiones.filter(fecha=searchdate).distinct().order_by('-fecha')

                elif search and searchdate:
                    search = request.GET['s'].strip()
                    ss = search.split(' ')
                    if len(ss) == 1:
                        sesiones = sesiones.filter(Q(caja__persona__apellido1__icontains=search) |
                                                             Q(caja__persona__apellido2__icontains=search) |
                                                             Q(caja__persona__nombres__icontains=search)).filter(fecha=searchdate).distinct().order_by('-fecha')
                    else:
                        sesiones = sesiones.filter(Q(caja__persona__apellido1__icontains=ss[0]) &
                                                             Q(caja__persona__apellido2__icontains=ss[1])).filter(fecha=searchdate).distinct().order_by('-fecha')

                elif 'id' in request.GET:
                    ids = request.GET['id']
                    sesiones = sesiones.filter(id=ids).order_by('-fecha')
                else:
                    sesiones = sesiones.filter(status=True).order_by('-fecha')
                paging = MiPaginador(sesiones, 25)
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
                lugar_rec = LugarRecaudacion.objects.filter(status=True, persona=persona, puntoventa__activo=True, activo=True)
                if lugar_rec.exists():
                    data['caja'] = lugar_rec.first()
                data['rangospaging'] = paging.rangos_paginado(p)
                data['ids'] = ids if ids else None
                data['page'] = page
                data['sesiones'] = page.object_list
                data['anios'] = AnioEjercicio.objects.all()
                data['anioejercicio'] = anio
                data['search'] = search if search else ""
                data['tiene_sesion_abierta'] = tiene_sesion_abierta
                return render(request, "sesioncaja/view.html", data)
            except Exception as ex:
                pass