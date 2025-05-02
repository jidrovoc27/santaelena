# -*- coding: UTF-8 -*-
import base64
import io
import os
import json
import random
from datetime import datetime

import pyqrcode
import xlsxwriter
import xlwt
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction, connection, connections
from django.db.models.query_utils import Q
from django.db.models.functions import Coalesce
from django.db.models import Sum, F, FloatField
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import get_template
from xlwt import *
from zeep import Client
import santaelena.settings
from administrativo.funciones import secuencia_recaudacion, MiPaginador, convertir_fecha, generar_nombre, null_to_decimal, \
    conviert_html_to_pdf, encrypt
from administrativo.commonviews import Sum, adduserdata
from santaelena.settings import SITE_ROOT, MEDIA_ROOT, SITE_STORAGE, \
    MEDIA_URL
from administrativo.models import ComprobantePago, LugarRecaudacion, Rubro, Pago, SesionCaja, TipoOtroRubro, SalidaRecaudacion, \
    DetalleSalidaRecaudacion
from administrativo.forms import VentaForm, SalidaRecaudacionForm
from django.forms.models import model_to_dict
from decimal import Decimal
import sys

unicode = str
Text = str

@login_required(redirect_field_name='ret', login_url='/loginclinica')
@transaction.atomic()
def view(request):
    data = {}
    adduserdata(request, data)
    data['persona'] = persona = data['persona']
    data['sesion_caja'] = None
    if persona.puede_recibir_pagos():
        caja = persona.caja()
        sesion_caja = caja.sesion_caja()
        data['sesion_caja'] = sesion_caja
    if request.method == 'POST':
        action = request.POST['action']

        if action == 'add':
            try:
                form = SalidaRecaudacionForm(request.POST)
                id_conceptos = request.POST.getlist('id_conceptos')
                valores_conceptos = request.POST.getlist('valores_conceptos')
                if len(id_conceptos) == 0:
                    return JsonResponse({"result": True, 'mensaje': 'Por favor ingrese al menos un concepto con su valor'})
                qscaja = SesionCaja.objects.filter(status=True, fecha=datetime.now().date(), abierta=True,
                                                   caja__puntoventa__activo=True, caja__activo=True, caja__persona=persona)
                sesioncj_ = None
                if qscaja.exists():
                    sesioncj_ = qscaja.first()
                else:
                    return JsonResponse({"result": True, 'mensaje': 'No cuenta con sesión de caja con fecha de hoy'})
                caja = sesioncj_.caja
                sesion_caja = caja.sesion_caja()
                secuencia = secuencia_recaudacion(request, sesion_caja.caja.puntoventa)
                puntoventa = secuencia.puntoventa
                while SalidaRecaudacion.objects.filter(puntoventa=puntoventa, numero=secuencia.salidarecaudacion).exists():
                    secuencia.salidarecaudacion += 1
                    secuencia.save()
                if SalidaRecaudacion.objects.filter(puntoventa=puntoventa, numero=secuencia.salidarecaudacion).exists():
                    transaction.set_rollback(True)
                    return False, u"Numero de salida de recaudación existente"
                numerocompleto = caja.puntoventa.establecimiento.strip() + "-" + caja.puntoventa.puntoventa.strip() + "-" + str(secuencia.salidarecaudacion).zfill(9)
                newsalida = SalidaRecaudacion(puntoventa=puntoventa,
                                                 numero=secuencia.salidarecaudacion,
                                                 numerocompleto=numerocompleto,
                                                 sesioncaja=sesion_caja)
                newsalida.save(request)
                contador = 0
                totalpagado = 0
                for id_concepto in id_conceptos:
                    valor_concepto = valores_conceptos[contador]
                    newdetalle = DetalleSalidaRecaudacion(sesion=sesion_caja,
                                   salida=newsalida,
                                   fecha=datetime.now().date(),
                                   concepto=id_concepto,
                                   valor=float(valor_concepto))
                    newdetalle.save(request)
                    totalpagado = float(totalpagado) + float(valor_concepto)
                    contador += 1
                newsalida.valor = totalpagado
                newsalida.save(request)
                return JsonResponse({"result": False})
            except Exception as ex:
                transaction.set_rollback(True)
                return JsonResponse({"result": True, 'mensaje': str(ex)})

        elif action == 'buscar_persona':
            try:
                from administrativo.models import Persona
                term = request.POST['term']
                data = []
                for persona in Persona.objects.filter(Q(nombres__icontains=term) | Q(apellido1__icontains=term) | Q(apellido2__icontains=term) | Q(identificacion__icontains=term) & Q(status=True))[:10]:
                    item = {'id': persona.id, 'text': persona.nombre_completo()}
                    data.append(item)
                return HttpResponse(json.dumps(data), content_type='application/json')
            except Exception as e:
                pass

        elif action == 'imprimircomprobante':
            try:
                comprobante = ComprobantePago.objects.get(id=int(request.POST['id']))
                pagos = comprobante.pagos.filter(status=True).values_list('rubro_id', flat=True)
                rubros = Rubro.objects.filter(status=True, id__in=pagos)
                total = rubros.aggregate(valor=Sum('valortotal'))['valor']
                return conviert_html_to_pdf('comprobantes/reporte/imprimircomprobante.html',
                                            {'pagesize': 'A4',
                                             'comprobante': comprobante, 'rubros': rubros, 'total': total})
            except Exception as ex:
                pass

        return JsonResponse({"result": "bad", "mensaje": u"Solicitud Incorrecta."})
    else:
        if 'action' in request.GET:
            data['action'] = action = request.GET['action']

            if action == 'add':
                try:
                    form = SalidaRecaudacionForm()
                    data['form'] = form
                    data['id'] = request.GET['id']
                    template = get_template("salidas/modal/form_salida.html")
                    return JsonResponse({"result": True, 'data': template.render(data)})
                except Exception as ex:
                    return JsonResponse({"result": False, 'mensaje': str(ex)})

            if action == 'getValor':
                try:
                    from administrativo.models import TipoOtroRubro
                    id = int(request.GET['id'])
                    tipo = TipoOtroRubro.objects.get(id=id)
                    return JsonResponse({"result": True, 'valor': tipo.valor})
                except Exception as ex:
                    return JsonResponse({"result": False, 'mensaje': str(ex)})

            if action == 'getMovimientos':
                try:
                    data['title'] = u'Detalle de movimientos'
                    salida = SalidaRecaudacion.objects.get(id=int(request.GET['id']))
                    data['egresos'] = egresos = salida.detallesalidarecaudacion_set.filter(status=True)
                    data['totalegresos'] = totalegresos = null_to_decimal(egresos.aggregate(valor=Sum('valor'))['valor'], 2)
                    template = get_template("salidas/modal/movimientos.html")
                    return JsonResponse({"result": True, 'data': template.render(data)})
                except Exception as ex:
                    pass

        else:
            try:
                data['title'] = u'Salida de efectivo'
                ids, search, a, filtro, url_vars = None, None, None, Q(status=True), f'&action='
                request.session['viewactivo'] = 1
                if 's' in request.GET:
                    search = request.GET['s'].strip()
                    ss = search.split(' ')
                    url_vars += '&s=' + request.GET['s']
                    if len(ss) == 1:
                        filtro = filtro & (Q(sesioncaja__caja__persona__apellido1__icontains=search) |
                                           Q(sesioncaja__caja__persona__apellido2__icontains=search) |
                                           Q(sesioncaja__caja__persona__nombres__icontains=search) |
                                           Q(sesioncaja__caja__persona__identificacion__icontains=search) |
                                           Q(concepto__icontains=search) |
                                           Q(persona__nombres__icontains=search) |
                                           Q(persona__apellido1__icontains=search) |
                                           Q(persona__apellido2__icontains=search) |
                                           Q(persona__identificacion__icontains=search))
                    else:
                        filtro = filtro & (Q(sesioncaja__caja__persona__apellido1__icontains=ss[0]) & Q(
                            sesioncaja__caja__persona__apellido2__icontains=ss[1]) |
                                           Q(persona__apellido1__icontains=ss[0]) & Q(
                                    persona__apellido2__icontains=ss[1]))
                elif 'id' in request.GET:
                    ids = request.GET['id']
                    filtro = filtro & Q(id=ids)

                data['salidas'] = salidas = SalidaRecaudacion.objects.filter(filtro).distinct().order_by(
                    '-fecha_creacion', '-id')
                paging = MiPaginador(salidas, 25)
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
                sesioncaja = None
                data['sesioncaja'] = sesioncaja
                data['rangospaging'] = paging.rangos_paginado(p)
                data['a'] = a if a else ""
                data['ids'] = ids if ids else None
                data['page'] = page
                data['comprobantes'] = page.object_list
                data['search'] = search if search else ""
                data['s'] = search if search else ""
                data['url_vars'] = url_vars
                data['tota_salida_efectivo'] = SalidaRecaudacion.objects.filter(status=True).aggregate(total=Coalesce(Sum('valor'), 0, output_field=FloatField())).get('total')
                data['tota_salidas'] = SalidaRecaudacion.objects.filter(status=True).count()
                return render(request, "salidas/view.html", data)
            except Exception as ex:
                pass


def append_pdf(input, output):
    [output.addPage(input.getPage(page_num)) for page_num in range(input.numPages)]

def fetch_resources(uri, rel):
    return os.path.join(MEDIA_ROOT, uri.replace(MEDIA_URL, ""))

def write_pdf(template_src, context_dict, filename, folders=None):
    from xhtml2pdf import pisa
    import io as StringIO
    template = get_template(template_src)
    if not folders:
        output_folder = os.path.join(SITE_STORAGE, 'media', 'diarios')
    else:
        output_folder = os.path.join(SITE_STORAGE, 'media', folders)
    try:
        os.makedirs(output_folder)
    except Exception as ex:
        pass
    html = template.render(context_dict).encode(encoding="UTF-8")
    filepdf = open(output_folder + os.sep + filename, "w+b")
    pdf = pisa.pisaDocument(StringIO.BytesIO(html), dest=filepdf, link_callback=fetch_resources)
    filepdf.close()
    return "".join([folders, '/', filename])