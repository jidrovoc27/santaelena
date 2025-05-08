# -*- coding: UTF-8 -*-
from django.db import transaction
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from administrativo.models import Factura
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def factura(request, weburl):
    if request.method == 'POST':

        try:
            archivo = request.FILES['archivo']
            data = archivo.read()
            consulta_comp = Factura.objects.filter(weburl=weburl)
            if consulta_comp.exists():
                comprobante = consulta_comp.first()
                comprobante.xmlfirmado = data.decode('utf-8')
                comprobante.firmada = True
                comprobante.save(request)
                return JsonResponse({'result': 'ok'})
            else:
                return JsonResponse({'result': 'bad', 'mensaje': 'No existe el Documento a firmar'})

        except Exception as ex:
            transaction.set_rollback(True)
            return JsonResponse({'result': 'bad', 'mensaje': 'Error al guardar'})

        return JsonResponse({'result': 'bad'})
    else:
        consulta_comp = Factura.objects.filter(weburl=weburl)
        if consulta_comp.exists():
            comprobante = consulta_comp.first()
            data = {'representacion': comprobante, 'representacionnombre': 'FACTURA'}
            return render(request, "sign/form.html", data, content_type="text/plain")
        return HttpResponseRedirect("/")