import os
from santaelena.settings import STATIC_URL, STATIC_ROOT, MEDIA_URL, MEDIA_ROOT
from django.db import models
import datetime
from datetime import datetime, date
from django.core.paginator import Paginator
from django.db import transaction, connections
from django.contrib.auth.models import User, Group
from django import forms

unicode = str

def link_callback(uri, rel):
    sUrl = STATIC_URL      # Typically /static/
    sRoot = STATIC_ROOT    # Typically /home/userX/project_static/
    mUrl = MEDIA_URL       # Typically /static/media/
    mRoot = MEDIA_ROOT     # Typically /home/userX/project_static/media/

    if uri.startswith(mUrl):
        path = os.path.join(mRoot, uri.replace(mUrl, ""))
    elif uri.startswith(sUrl):
        path = os.path.join(sRoot, uri.replace(sUrl, ""))
    else:
        return uri                  # handle absolute uri (ie: http://some.tld/foo.png)

    # make sure that file exists
    if not os.path.isfile(path):
        raise Exception('media URI must start with %s or %s' % (sUrl, mUrl))

    return path


class ModeloBase(models.Model):
    """ Modelo base para todos los modelos del proyecto """
    from django.contrib.auth.models import User
    status = models.BooleanField(default=True)
    usuario_creacion = models.ForeignKey(User, on_delete=models.PROTECT, related_name='+', blank=True, null=True)
    fecha_creacion = models.DateTimeField(blank=True, null=True)
    usuario_modificacion = models.ForeignKey(User, on_delete=models.PROTECT, related_name='+', blank=True, null=True)
    fecha_modificacion = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        usuario = None
        if len(args):
            usuario = args[0].user.id
        if self.id:
            self.usuario_modificacion_id = usuario if usuario else None
            self.fecha_modificacion = datetime.now()
        else:
            self.usuario_creacion_id = usuario if usuario else None
            self.fecha_creacion = datetime.now()
        models.Model.save(self)

    class Meta:
        abstract = True

class ExtFileField(forms.FileField):
    """
    * max_upload_size - a number indicating the maximum file size allowed for upload.
            500Kb - 524288
            1MB - 1048576
            2.5MB - 2621440
            5MB - 5242880
            10MB - 10485760
            20MB - 20971520
            50MB - 5242880
            100MB 104857600
            250MB - 214958080
            500MB - 429916160
    t = ExtFileField(ext_whitelist=(".pdf", ".txt"), max_upload_size=)
    """
    def __init__(self, *args, **kwargs):
        ext_whitelist = kwargs.pop("ext_whitelist")
        self.ext_whitelist = [i.lower() for i in ext_whitelist]
        self.max_upload_size = kwargs.pop("max_upload_size")
        super(ExtFileField, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        upload = super(ExtFileField, self).clean(*args, **kwargs)
        if upload:
            size = upload.size
            filename = upload.name
            ext = os.path.splitext(filename)[1]
            ext = ext.lower()
            if size == 0 or ext not in self.ext_whitelist or size > self.max_upload_size:
                raise forms.ValidationError("Tipo de fichero o tamanno no permitido!")


class MiPaginador(Paginator):
    def __init__(self, object_list, per_page, orphans=0, allow_empty_first_page=True, rango=5):
        super(MiPaginador, self).__init__(object_list, per_page, orphans=orphans,
                                          allow_empty_first_page=allow_empty_first_page)
        self.rango = rango
        self.paginas = []
        self.primera_pagina = False
        self.ultima_pagina = False

    def rangos_paginado(self, pagina):
        left = pagina - self.rango
        right = pagina + self.rango
        if left < 1:
            left = 1
        if right > self.num_pages:
            right = self.num_pages
        self.paginas = range(left, right + 1)
        self.primera_pagina = True if left > 1 else False
        self.ultima_pagina = True if right < self.num_pages else False
        self.ellipsis_izquierda = left - 1
        self.ellipsis_derecha = right + 1

def convertir_fecha(s):
    if ':' in s:
        sep = ':'
    elif '-' in s:
        sep = '-'
    else:
        sep = '/'
    return date(int(s.split(sep)[2]), int(s.split(sep)[1]), int(s.split(sep)[0]))

def null_to_numeric(valor, decimales=None):
    if decimales:
        return round((valor if valor else 0), decimales)
    return valor if valor else 0

def null_to_decimal(valor, decimales=None):
    if not decimales is None and not valor is None:
        if decimales > 0:
            sql = """SELECT round(%s::numeric,%s)""" % (valor, decimales)
            cursor = connections['default'].cursor()
            cursor.execute(sql)
            results = cursor.fetchall()
            return float(results[0][0])
        else:
            sql = """SELECT round(%s::numeric,%s)""" % (valor, 0)
            cursor = connections['default'].cursor()
            cursor.execute(sql)
            results = cursor.fetchall()
            return float(results[0][0])
    return valor if valor else 0

def remover_caracteres_especiales_unicode(cadena):
    return cadena.replace(u'ñ', u'n').replace(u'Ñ', u'N').replace(u'Á', u'A').replace(u'á', u'a').replace(u'É',
                                                                                                          u'E').replace(
        u'é', u'e').replace(u'Í', u'I').replace(u'í', u'i').replace(u'Ó', u'O').replace(u'ó', u'o').replace(u'Ú',
                                                                                                            u'U').replace(
        u'ú', u'u').replace(u'ü', u'u').replace(u'Ü', u'U').replace(u'°', u'_').replace(u'º', u'_')

def generar_nombre(nombre, original):
    nombre = remover_caracteres_especiales_unicode(nombre).lower().replace(' ', '_')
    ext = ""
    if original.find(".") > 0:
        ext = original[original.rfind("."):]
    fecha = datetime.now().date()
    hora = datetime.now().time()
    return nombre + fecha.year.__str__() + fecha.month.__str__() + fecha.day.__str__() + hora.hour.__str__() + hora.minute.__str__() + hora.second.__str__() + ext.lower()

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def puede_realizar_accion_afirmativo(request, permiso):
    if request.user.has_perm(permiso):
        return True
    return False

def to_unicode(s):
    if isinstance(s, unicode):
        return s

    from locale import getpreferredencoding

    for cp in (getpreferredencoding(), "cp1255", "cp1250"):
        try:
            return unicode(s, cp)
        except UnicodeDecodeError:
            pass
        raise Exception("Conversion to unicode failed")

def encrypt(value):
    myencrip = ""
    if type(value) is int:
        value = str(value)
    i = 1
    for c in value.zfill(20):
        myencrip = myencrip + chr(int(44450/350) - ord(c) + int(i/int(9800/4900)))
        i = i + 1
    return myencrip

def miempresa():
    from administrativo.models import Empresa
    if Empresa.objects.exists():
        miempresa = Empresa.objects.all()[0]
    else:
        miempresa = Empresa(nombre="Mi empresa",
                                              direccion="",
                                              telefono="",
                                              correo="")
        miempresa.save()
    return miempresa

def customgetattr(object, name):
    r = getattr(object, name)
    if str(type(r)) == "<class 'method'>" or str(type(r)) == "<class 'function'>":
        return r()
    return r

def fechaletra_corta(fecha):
    fechafinal = ''
    if fecha.day == 1:
        fechafinal += 'al primer día '
    if fecha.day == 2:
        fechafinal += 'a los dos días '
    if fecha.day == 3:
        fechafinal += 'a los tres días '
    if fecha.day == 4:
        fechafinal += 'a los cuatro días '
    if fecha.day == 5:
        fechafinal += 'a los cinco días '
    if fecha.day == 6:
        fechafinal += 'a los seis días '
    if fecha.day == 7:
        fechafinal += 'a los siete días '
    if fecha.day == 8:
        fechafinal += 'a los ocho días '
    if fecha.day == 9:
        fechafinal += 'a los nueve días '
    if fecha.day == 10:
        fechafinal += 'a los diez días '
    if fecha.day == 11:
        fechafinal += 'a los once días '
    if fecha.day == 12:
        fechafinal += 'a los doce días '
    if fecha.day == 13:
        fechafinal += 'a los trece días '
    if fecha.day == 14:
        fechafinal += 'a los catorce días '
    if fecha.day == 15:
        fechafinal += 'a los quince días '
    if fecha.day == 16:
        fechafinal += 'a los dieciseis días '
    if fecha.day == 17:
        fechafinal += 'a los diecisiete días '
    if fecha.day == 18:
        fechafinal += 'a los dieciocho días '
    if fecha.day == 19:
        fechafinal += 'a los diecinueve días '
    if fecha.day == 20:
        fechafinal += 'a los veinte días '
    if fecha.day == 21:
        fechafinal += 'a los veintiun días '
    if fecha.day == 22:
        fechafinal += 'a los veintidos días '
    if fecha.day == 23:
        fechafinal += 'a los veintitres días '
    if fecha.day == 24:
        fechafinal += 'a los veinticuatro días '
    if fecha.day == 25:
        fechafinal += 'a los veinticinco días '
    if fecha.day == 26:
        fechafinal += 'a los veintiseis días '
    if fecha.day == 27:
        fechafinal += 'a los veintisiete días '
    if fecha.day == 28:
        fechafinal += 'a los veintiocho días '
    if fecha.day == 29:
        fechafinal += 'a los veintinueve días '
    if fecha.day == 30:
        fechafinal += 'a los treinta días '
    if fecha.day == 31:
        fechafinal += 'a los treinta y uno días '
    if fecha.month == 1:
        fechafinal += 'del mes de Enero del '
    if fecha.month == 2:
        fechafinal += 'del mes de Febrero del '
    if fecha.month == 3:
        fechafinal += 'del mes de Marzo del '
    if fecha.month == 4:
        fechafinal += 'del mes de Abril del '
    if fecha.month == 5:
        fechafinal += 'del mes de Mayo del '
    if fecha.month == 6:
        fechafinal += 'del mes de Junio del '
    if fecha.month == 7:
        fechafinal += 'del mes de Julio del '
    if fecha.month == 8:
        fechafinal += 'del mes de Agosto del '
    if fecha.month == 9:
        fechafinal += 'del mes de Septiembre del '
    if fecha.month == 10:
        fechafinal += 'del mes de Octubre del '
    if fecha.month == 11:
        fechafinal += 'del mes de Nomviembre del '
    if fecha.month == 12:
        fechafinal += 'del mes de Diciembre del '
    if fecha.year == 1998:
        fechafinal += 'mil novecientos noventa y ocho'
    if fecha.year == 1999:
        fechafinal += 'mil novecientos noventa y nueve'
    if fecha.year == 2000:
        fechafinal += 'dosmil'
    if fecha.year == 2001:
        fechafinal += 'dosmil uno'
    if fecha.year == 2002:
        fechafinal += 'dosmil dos'
    if fecha.year == 2003:
        fechafinal += 'dosmil tres'
    if fecha.year == 2004:
        fechafinal += 'dosmil cuatro'
    if fecha.year == 2005:
        fechafinal += 'dosmil cinco'
    if fecha.year == 2006:
        fechafinal += 'dosmil seis'
    if fecha.year == 2007:
        fechafinal += 'dosmil siete'
    if fecha.year == 2008:
        fechafinal += 'dosmil ocho'
    if fecha.year == 2009:
        fechafinal += 'dosmil nueve'
    if fecha.year == 2010:
        fechafinal += 'dosmil diez'
    if fecha.year == 2011:
        fechafinal += 'dosmil once'
    if fecha.year == 2012:
        fechafinal += 'dosmil doce'
    if fecha.year == 2013:
        fechafinal += 'dosmil trece'
    if fecha.year == 2014:
        fechafinal += 'dosmil catorce'
    if fecha.year == 2015:
        fechafinal += 'dosmil quince'
    if fecha.year == 2016:
        fechafinal += 'dosmil dieciseis'
    if fecha.year == 2017:
        fechafinal += 'dosmil diecisiete'
    if fecha.year == 2018:
        fechafinal += 'dosmil dieciocho'
    if fecha.year == 2019:
        fechafinal += 'dosmil diecinueve'
    if fecha.year == 2020:
        fechafinal += 'dosmil veinte'
    if fecha.year == 2021:
        fechafinal += 'dosmil veintiuno'
    if fecha.year == 2022:
        fechafinal += 'dosmil veintidos'
    if fecha.year == 2023:
        fechafinal += 'dosmil veintitres'
    if fecha.year == 2024:
        fechafinal += 'dosmil veinticuatro'
    if fecha.year == 2025:
        fechafinal += 'dosmil veinticinco'
    if fecha.year == 2026:
        fechafinal += 'dosmil veintiseis'
    if fecha.year == 2027:
        fechafinal += 'dosmil veintisiete'
    if fecha.year == 2028:
        fechafinal += 'dosmil veintiocho'
    if fecha.year == 2029:
        fechafinal += 'dosmil veintinueve'
    if fecha.year == 2030:
        fechafinal += 'dosmil treinta'
    return fechafinal


def fields_model(classname, app):
    try:
        d = locals()
        exec('from %s.models import %s' % (app, classname), globals(), d)
        # exec('from %s.models import %s' % (app, classname))
        fields = eval(classname + '._meta.get_fields()')
        return fields
    except:
        return []


def field_default_value_model(field):
    try:
        value = str(field)
        return value if 'django.db.models.fields.NOT_PROVIDED' not in value else ''
    except:
        return ''

def calculate_username(persona, variant=1):
    alfabeto = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u',
                'v', 'w', 'x', 'y', 'z', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    s = persona.nombres.lower().split(' ')
    while '' in s:
        s.remove('')
    if persona.apellido2:
        usernamevariant = s[0][0] + persona.apellido1.lower() + persona.apellido2.lower()[0]
    else:
        usernamevariant = s[0][0] + persona.apellido1.lower()
    usernamevariant = usernamevariant.replace(' ', '').replace(u'ñ', 'n').replace(u'á', 'a').replace(u'é', 'e').replace(
        u'í', 'i').replace(u'ó', 'o').replace(u'ú', 'u')
    usernamevariantfinal = ''
    for letra in usernamevariant:
        if letra in alfabeto:
            usernamevariantfinal += letra
    if variant > 1:
        usernamevariantfinal += str(variant)
    if not User.objects.filter(username=usernamevariantfinal).exclude(persona=persona).exists():
        return usernamevariantfinal
    else:
        return calculate_username(persona, variant + 1)

def puede_realizar_accion(request, permiso):
    if request.user.has_perm(permiso):
        return True
    raise Exception('Permiso denegado.')

def lista_correo(listagrupos):
    from administrativo.models import Persona
    lista = []
    for persona in Persona.objects.filter(usuario__groups__id__in=listagrupos).distinct():
        lista.extend(persona.lista_emails_envio())
    return lista

def generar_usuario(persona, usuario, group_id):
    password = 'clinica'
    anio = ''
    if persona.nacimiento:
        anio = "*" + str(persona.nacimiento)[0:4]
    password = persona.identificacion.strip() + anio
    if User.objects.filter(username=usuario):
        usuario = usuario + '1'
    user = User.objects.create_user(usuario, '', password)
    user.save()
    persona.usuario = user
    persona.save()
    g = Group.objects.filter(pk=group_id)
    if g.exists():
        g = g.first()
        g.user_set.add(user)
        g.save()

def resetear_clave(persona):
    password = 'clinica'
    anio = ''
    if persona.nacimiento:
        anio = "*" + str(persona.nacimiento)[0:4]
    password = persona.identificacion.strip() + anio
    user = persona.usuario
    user.set_password(password)
    user.save()

def secuencia_recaudacion(request, puntoventa):
    from administrativo.models import SecuencialRecaudaciones
    secuencial_ = SecuencialRecaudaciones.objects.filter(puntoventa=puntoventa, status=True)
    if not secuencial_.exists():
        secuencia = SecuencialRecaudaciones(puntoventa=puntoventa)
        secuencia.save(request)
        return secuencia
    else:
        return secuencial_.first()

def secuencia_caja(request, anio):
    from administrativo.models import SecuenciaSesionCaja
    anioe = datetime.now().date()
    secuenciacaja = SecuenciaSesionCaja.objects.filter(status=True)
    if not secuenciacaja.exists():
        secuencia = SecuenciaSesionCaja(status=True)
        secuencia.save(request)
        return secuencia
    else:
        return secuenciacaja.first()

def conviert_html_to_pdf(template_src, context_dict):
    import io as StringIO
    from xhtml2pdf import pisa
    from django.template.loader import get_template
    from django.http import HttpResponse, JsonResponse
    template = get_template(template_src)
    html = template.render(context_dict).encode(encoding="UTF-8")
    result = StringIO.BytesIO()
    pisaStatus = pisa.CreatePDF(StringIO.BytesIO(html), result, link_callback=link_callback)
    if not pisaStatus.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return JsonResponse({"result": "bad", "mensaje": u"Problemas al ejecutar el reporte."})