# -*- coding: UTF-8 -*-
import serial
import base64
import io
import os
import json
import random
from datetime import datetime
from escpos.printer import Serial
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
from administrativo.models import ComprobantePago, LugarRecaudacion, Rubro, Pago, SesionCaja, TipoOtroRubro
from administrativo.forms import VentaForm
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
    puerto = '/dev/ttyUSB0'
    if persona.puede_recibir_pagos():
        caja = persona.caja()
        sesion_caja = caja.sesion_caja()
        data['sesion_caja'] = sesion_caja
    if request.method == 'POST':
        action = request.POST['action']

        if action == 'add':
            try:
                from administrativo.models import TipoOtroRubro
                form = VentaForm(request.POST)
                persona_ = int(request.POST['persona'])
                id_rubros = request.POST.getlist('id_rubros')
                valores_rubros = request.POST.getlist('valores_rubros')
                valores_descuentos = request.POST.getlist('valores_descuentos')
                if len(id_rubros) == 0:
                    return JsonResponse({"result": True, 'mensaje': 'Por favor ingrese al menos un rubro'})
                qscaja = SesionCaja.objects.filter(status=True, fecha=datetime.now().date(), abierta=True,
                                                   caja__puntoventa__activo=True, caja__activo=True)
                sesioncj_ = None
                if qscaja.exists():
                    sesioncj_ = qscaja.first()
                else:
                    return JsonResponse({"result": True, 'mensaje': 'No cuenta con sesión de caja con fecha de hoy'})
                caja = sesioncj_.caja
                sesion_caja = caja.sesion_caja()
                secuencia = secuencia_recaudacion(request, sesion_caja.caja.puntoventa)
                puntoventa = secuencia.puntoventa
                while ComprobantePago.objects.filter(puntoventa=puntoventa, numero=secuencia.comprobante).exists():
                    secuencia.comprobante += 1
                    secuencia.save()
                if ComprobantePago.objects.filter(puntoventa=puntoventa, numero=secuencia.comprobante).exists():
                    transaction.set_rollback(True)
                    return False, u"Numero de comprobante existente"
                numerocompleto = caja.puntoventa.establecimiento.strip() + "-" + caja.puntoventa.puntoventa.strip() + "-" + str(secuencia.comprobante).zfill(9)
                newcomprobante = ComprobantePago(puntoventa=puntoventa,
                                                 persona_id=persona_,
                                                 numero=secuencia.comprobante,
                                                 numerocompleto=numerocompleto,
                                                 sesioncaja=sesion_caja)
                newcomprobante.save(request)
                contador = 0
                totalpagado = 0
                for idrubro in id_rubros:
                    tiprubro = TipoOtroRubro.objects.get(id=int(idrubro))
                    valor_rubro = float(valores_rubros[contador])
                    valor_descuento = float(valores_descuentos[contador])
                    valorTotalPagado = valor_rubro - valor_descuento
                    newrubro = Rubro(tipo=tiprubro,
                                     persona_id=persona_,
                                     nombre=tiprubro.nombre,
                                     fecha=datetime.now().date(),
                                     fechavence=datetime.now().date(),
                                     iva_id=1,
                                     valor=float(valor_rubro),
                                     valordescuento=float(valor_descuento),
                                     valortotal=float(valorTotalPagado),
                                     cancelado=True)
                    newrubro.save(request)
                    newpago = Pago(sesion=sesion_caja,
                                   rubro=newrubro,
                                   fecha=datetime.now().date(),
                                   preciounitario=float(valor_rubro),
                                   subtotal0=float(valor_rubro),
                                   valordescuento=float(valor_descuento),
                                   valortotal=float(valorTotalPagado))
                    newpago.save(request)
                    totalpagado = float(totalpagado) + float(valorTotalPagado)
                    newcomprobante.pagos.add(newpago)
                    contador += 1
                newcomprobante.valor = totalpagado
                newcomprobante.save(request)
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

        elif action == 'generarticket':
            try:
                comprobante = ComprobantePago.objects.get(id=int(request.POST['id']))
                pagos = comprobante.pagos.filter(status=True).values_list('rubro_id', flat=True)
                rubros = Rubro.objects.filter(status=True, id__in=pagos)
                total = rubros.aggregate(valor=Sum('valortotal'))['valor']
                # Generar texto plano alineado manualmente
                ticket_content = [
                    "      CLINICA SANTA ELENA      ",
                    "      RUC: 0993285838001       ",
                    "Av. Colon y Pedro Brito J Montero",
                    "Tel: 0985893859 / 974593       ",
                    "-" * 32,
                    f"COMPROBANTE No: {comprobante.numerocompleto}",
                    f"FECHA: {comprobante.fecha_creacion.strftime('%Y-%m-%d %H:%M')}",
                    f"CLIENTE: {comprobante.persona}",
                    f"C.I.: {comprobante.persona.identificacion}",
                    "-" * 32,
                    "DESCRIPCION  VAL   DESC   TOTAL",
                ]

                for rubro in rubros:
                    ticket_content.append(f"{rubro.nombre.ljust(10)} ${str(rubro.valor).ljust(5)} ${str(rubro.valordescuento).ljust(1)}  ${rubro.valortotal:.2f}")

                ticket_content.extend([
                    "-" * 32,
                    f"TOTAL: ${total:.2f}".rjust(31),
                    "-" * 32,
                    "  Gracias por su preferencia  ",
                ])

                response = HttpResponse("\n".join(ticket_content), content_type="text/plain")
                response['Content-Disposition'] = 'inline; filename="ticket.txt"'
                return response
            except Exception as ex:
                pass

        elif action == 'generardatospaciente':
            try:
                # Datos de ejemplo (reemplázalos con los reales)
                comprobante = ComprobantePago.objects.get(id=int(request.POST['id']))
                datos = {
                    "nombre": comprobante.persona,
                    "pa": "________________",
                    "p": "________________",
                    "spo": "________________",
                    "gli": "________________",
                    "t": "________________",
                    "peso": "________________",
                    "talla": "________________",
                    "fr": "________________",
                    "dr": "________________",
                }

                # Generar el contenido del ticket
                contenido = [
                    "      SIGNOS VITALES      ",
                    "   CLINICA 'SANTA ELENA'   ",
                    "",
                    f"NOMBRE: {datos['nombre']}",
                    "",
                    f"PA:    {datos['pa']}",
                    f"P:     {datos['p']}",
                    f"SPO:   {datos['spo']}",
                    f"GLI:   {datos['gli']}",
                    f"T:     {datos['t']}",
                    f"PESO:  {datos['peso']}",
                    f"TALLA: {datos['talla']}",
                    f"FR:    {datos['fr']}",
                    f"DR:    {datos['dr']}",
                    "",
                    "  Gracias por su visita  ",
                ]

                # Unir las líneas con saltos de línea
                contenido_texto = "\n".join(contenido)

                # Devolver como respuesta de texto plano
                response = HttpResponse(contenido_texto, content_type="text/plain")
                response['Content-Disposition'] = 'inline; filename="signos_vitales.txt"'
                return response

            except Exception as e:
                return HttpResponse(f"Error al generar el formato: {str(e)}", status=500)

        elif action == 'imprimirdatopaciente':
            try:
                # Configurar la impresora (ajusta el puerto según tu sistema)
                printer = Serial(devfile=puerto, baudrate=19200)  # Linux
                # printer = Serial(devfile='COM3', baudrate=19200)  # Windows

                # Encabezado (centrado)
                printer.set(align='center')
                printer.text("SIGNOS VITALES\n")
                printer.text("CLINICA 'SANTA ELENA'\n")
                printer.text("\n")  # Espacio en blanco

                # Datos del paciente (alineación izquierda)
                printer.set(align='left')
                printer.text("NOMBRE: [Nombre del Paciente]\n")
                printer.text("\n")  # Espacio en blanco

                # Signos vitales (formato tabla)
                printer.text("PA:    [Valor] mmHg\n")  # Presión arterial
                printer.text("P:     [Valor] lpm\n")  # Pulso
                printer.text("SPO:   [Valor] %\n")  # Saturación de oxígeno
                printer.text("GLI:   [Valor] mg/dL\n")  # Glucosa
                printer.text("T:     [Valor] °C\n")  # Temperatura
                printer.text("PESO:  [Valor] kg\n")  # Peso
                printer.text("TALLA: [Valor] cm\n")  # Talla
                printer.text("FR:    [Valor] rpm\n")  # Frecuencia respiratoria
                printer.text("DR:    [Valor]\n")  # Diagnóstico o observación

                # Espacio y mensaje final
                printer.text("\n")  # Espacio en blanco
                printer.set(align='center')
                printer.text("Gracias por su visita\n")

                # Cortar papel (opcional)
                printer.cut()

                return JsonResponse({"result": True, "mensaje": u'Ticket enviado a la impresora correctamente.'})

            except Exception as ex:
                mensaje = f"{ex} - {sys.exc_info()[-1].tb_lineno}"
                return JsonResponse({"result": False, "mensaje": mensaje})

        elif action == 'imprimirticket':
            try:
                comprobante = ComprobantePago.objects.get(id=int(request.POST['id']))
                pagos = comprobante.pagos.filter(status=True).values_list('rubro_id', flat=True)
                rubros = Rubro.objects.filter(status=True, id__in=pagos)
                total = rubros.aggregate(valor=Sum('valortotal'))['valor']

                #PRUEBA DE CONEXIÓN
                baudrate = 19200
                with serial.Serial(puerto, baudrate, timeout=1) as ser:
                    ser.write(b"Test\n")  # Enviar comando de prueba
                    print(f"Conexión exitosa en {puerto}!")

                # Configurar la impresora (ajusta el puerto según tu sistema)
                printer = Serial(devfile=puerto, baudrate=19200)  # Linux
                # printer = Serial(devfile='COM3', baudrate=19200)  # Windows

                # Encabezado del ticket
                printer.set(align='center')
                printer.text("CLINICA SANTA ELENA\n")
                printer.text("RUC: 0993285838001\n")
                printer.text("Av. Colon y Pedro Brito J Montero\n")
                printer.text("Tel: 0985893859 / 974593\n")
                printer.text("-" * 32 + "\n")

                # Detalles del comprobante
                printer.set(align='left')
                printer.text(f"COMPROBANTE No: {comprobante.numerocompleto}\n")
                printer.text(f"FECHA: {comprobante.fecha_creacion.strftime('%Y-%m-%d %H:%M')}\n")
                printer.text(f"CLIENTE: {comprobante.persona}\n")
                printer.text(f"C.I.: {comprobante.persona.identificacion}\n")
                printer.text("-" * 32 + "\n")

                # Lista de rubros
                printer.text("DESCRIPCION          VAL      DESC     TOTAL\n")
                printer.text("-" * 42 + "\n")  # Línea separadora

                for rubro in rubros:
                    total = rubro.valortotal  # Asumo que valortotal ya es (valor - descuento)
                    valor_original = rubro.valor  # Campo con el valor sin descuento
                    descuento = rubro.valordescuento  # Campo con el monto descontado

                    # Formatea la línea con 4 columnas alineadas
                    linea = (
                        f"{rubro.nombre.ljust(18)} "  # DESCRIPCIÓN (18 caracteres)
                        f"${valor_original:.2f}   "  # VAL (alineado)
                        f"${descuento:.2f}   "  # DESC (alineado)
                        f"${total:.2f}\n"  # TOTAL
                    )
                    printer.text(linea)

                # Línea final con el total general (opcional)
                printer.text("-" * 42 + "\n")
                printer.text(f"TOTAL GENERAL: ${sum(r.valortotal for r in rubros):.2f}\n".rjust(42))
                printer.set(align='center')
                printer.text("-" * 32 + "\n")
                printer.text("Gracias por su preferencia\n")

                # Cortar el papel (opcional)
                printer.cut()

                return JsonResponse({"result": True, "mensaje": u'Ticket enviado a la impresora correctamente.'})
            except Exception as ex:
                mensaje = f"{ex} - {sys.exc_info()[-1].tb_lineno}"
                return JsonResponse({"result": False, "mensaje": mensaje})

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
                    form = VentaForm()
                    data['form'] = form
                    data['id'] = request.GET['id']
                    template = get_template("comprobantes/modal/form_venta.html")
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

        else:
            try:
                data['title'] = u'Comprobantes de pago'
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

                data['comprobantes'] = comprobantes = ComprobantePago.objects.filter(filtro).distinct().order_by(
                    '-fecha_creacion', '-id')
                paging = MiPaginador(comprobantes, 25)
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
                data['tota_recaudado'] = Pago.objects.filter(status=True).aggregate(total=Coalesce(Sum('valortotal'), 0, output_field=FloatField())).get('total')
                data['tota_ventas'] = ComprobantePago.objects.filter(status=True).count()
                return render(request, "comprobantes/view.html", data)
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