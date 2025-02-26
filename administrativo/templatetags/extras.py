# -*- coding: UTF-8 -*-
from _decimal import Decimal

from babel.dates import format_date
from django import template

from santaelena.settings import TIPO_RESPUESTA_EVALUACION
from administrativo.funciones import fechaletra_corta, fields_model, field_default_value_model
from administrativo.models import MESES_CHOICES, Persona
from datetime import datetime, timedelta, date
from num2words import num2words

register = template.Library()

@register.simple_tag
def get_verbose_field_name(instance, field_name):
    return instance._meta.get_field(field_name).verbose_name.title()

@register.simple_tag
def ver_valor_dict(dicionario, llave):
    return dicionario[llave]

@register.filter
def divide(value, arg):
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except ValueError:
        return 0

@register.simple_tag
def get_total_departamentos(values, object):
    try:
        return object.totales_pac(values)
    except Exception as ex:
        return ""


def callmethod(obj, methodname):
    method = getattr(obj, methodname)
    if "__callArg" in obj.__dict__:
        ret = method(*obj.__callArg)
        del obj.__callArg
        return ret
    return method()


def args(obj, arg):
    if "__callArg" not in obj.__dict__:
        obj.__callArg = []
    obj.__callArg.append(arg)
    return obj


def suma(var, value=1):
    try:
        return var + value
    except Exception as ex:
        pass


def resta(var, value=1):
    return var - value

def restanumeros(var, value):
    return var - value

def multiplicanumeros(var, value):
    return Decimal(Decimal(var).quantize(Decimal('.01')) *  Decimal(value).quantize(Decimal('.01'))).quantize(Decimal('.01'))

def divide(value, arg):
    return int(value) / int(arg) if arg else 0


def porciento(value, arg):
    return round(value * 100 / float(arg), 2) if arg else 0


def calendarbox(var, dia):
    return var[dia]


def barraporciento(var, total):
    if int(total) == 0:
        return 0
    else:
        if TIPO_RESPUESTA_EVALUACION == 3:
            return int((int(var) / 3) * total)
        elif TIPO_RESPUESTA_EVALUACION == 1:
            return int((int(var) / 5) * total)
        elif TIPO_RESPUESTA_EVALUACION == 2:
            return int((int(var) / 10) * total)


def calendarboxdetails(var, dia):
    lista = var[dia]
    result = []
    for x in lista:
        b = [x.split(',')[0], x.split(',')[1]]
        result.append(b)
    return result


def calendarboxdetailsmostrar(var, dia):
    return var[dia]


def calendarboxdetails2(var, dia):
    lista = var[dia]
    result = []
    b = []
    for x in lista:
        b.append(x[0])
        b.append(x[1])
        b.append(x[2])
        b.append(x[3])
        result.append(b)
    return result


def times(number):
    return range(number)


def nombremescorto(fecha):
    if type(fecha) is str:
        return "%s" % fecha[:3].capitalize()
    else:
        return "%s %s" % (fecha.day, MESES_CHOICES[fecha.month - 1][1][:3].capitalize())

def substraer(value, rmostrar):
    return "%s" % value[:rmostrar]


def nombremes(fecha):
    if type(fecha) is int:
        return "%s" % MESES_CHOICES[fecha - 1][1]
    elif type(fecha) is str:
        return ""
    else:
        return "%s" % MESES_CHOICES[fecha.month - 1][1]


def fechapermiso(fecha):
    if datetime.now().date() >= fecha:
        return True
    else:
        return False


def entrefechas(finicio,ffin):
    if datetime.now().date() >= finicio and datetime.now().date() <= ffin :
        return True
    else:
        return False


def datename(fecha):
    return u"%s de %s del %s" % (str(fecha.day).rjust(2, "0"), nombremes(fecha=fecha).capitalize(), fecha.year)

def fecha_estructurada(fecha):
    if not fecha:
        return ''
    return u"%s de %s del %s" % (str(fecha.day).rjust(2, "0"), nombremes(fecha=fecha).capitalize(), fecha.year)


def nombrepersona(usuario):
    if Persona.objects.filter(usuario=usuario).exists():
        return Persona.objects.filter(usuario=usuario)[0]
    return None


def encrypt(value):
    myencrip = ""
    if type(value) is int:
        value = str(value)
    i = 1
    for c in value.zfill(20):
        myencrip = myencrip + chr(int(44450/350) - ord(c) + int(i/int(9800/4900)))
        i = i + 1
    return myencrip


def encrypt_alu(value):
    myencrip = ""
    if type(value) is int:
        value = str(value)
    i = 1
    for c in value.zfill(20):
        myencrip = myencrip + chr(int(44450/350) - ord(c) + int(i/int(14700/4900)))
        i = i + 1
    return myencrip

def is_int_or_char(value):
    try:
        if type(value) is int:
            return 1
        elif type(value) is str:
            return 2
        else:
            return 3
    except:
        return 3

def splitcadypre(string, sep):
    a= string.split(sep)
    b=int(a[0])
    return b

def splitcadyprestr(string, sep):
    a= string.split(sep)
    b=a[1]
    return b

def solo_caracteres(texto):
    acentos = [u'á', u'é', u'í', u'ó', u'ú', u'Á', u'É', u'Í', u'Ó', u'Ú', u'ñ', u'Ñ']
    alfabeto = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '.', '/', '#', ',', ' ']
    resultado = ''
    for letra in texto:
        if letra in alfabeto:
            resultado += letra
        elif letra in acentos:
            if letra == u'á':
                resultado += 'a'
            elif letra == u'é':
                resultado += 'e'
            elif letra == u'í':
                resultado += 'i'
            elif letra == u'ó':
                resultado += 'o'
            elif letra == u'ú':
                resultado += 'u'
            elif letra == u'Á':
                resultado += 'A'
            elif letra == u'É':
                resultado += 'E'
            elif letra == u'Í':
                resultado += 'I'
            elif letra == u'Ó':
                resultado += 'O'
            elif letra == u'Ú':
                resultado += 'U'
            elif letra == u'Ñ':
                resultado += 'N'
            elif letra == u'ñ':
                resultado += 'n'
        else:
            resultado += '?'
    return resultado


def ceros(numero, cantidad):
    return str(numero).zfill(cantidad)


def fechamayor(fecha1, fecha2):
    if fecha1.date() > fecha2:
        return True
    else:
        return False


def transformar_n_l(n):
    arreglo = ['PRIMERO', 'SEGUNDO', 'TERCERO', 'CUARTO', 'QUINTO', 'SEXTO', 'SEPTIMO', 'OCTAVO', 'NOVENO']
    return arreglo[n - 1] if n else "MALLA NO VIGENTE"


def transformar_mes(n):
    arreglo = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    return arreglo[n - 1] if n else "SIN MES"

def convertir_numero_a_palabra(numero):
    palabra = num2words(numero, lang='es')
    return palabra



def diaenletra(dia):
    arreglo = ['LUNES', 'MARTES', 'MIERCOLES', 'JUEVES', 'VIERNES', 'SABADO', 'DOMINGO']
    return arreglo[dia -1 ]

# NO TUVE MAS REMEDIO QUE HACER FUNCIONES MUERTAS PARA UN SOLO REPORTE PIDO MIL DISCULPAS A MIS ADMIRADORES ATT. CLOCKEM
def sumar_fm(value, lista):
    su = 0
    for l in lista:
        if value == l[0]:
            su += l[3]
    return su

def sumar_fh(value, lista):
    su = 0
    for l in lista:
        if value == l[0]:
            su += l[4]
    return su

def sumar_cm(value, lista):
    su = 0
    for l in lista:
        if value == l[1]:
            su += l[3]
    return su

def sumar_ch(value, lista):
    su = 0
    for l in lista:
        if value == l[1]:
            su += l[4]
    return su

def sumar_th(value, lista):
    su = 0
    for l in lista:
        su += l[4]
    return su


def sumar_tm(value, lista):
    su = 0
    for l in lista:
        su += l[3]
    return su


def sumar_pagineo(totalpagina, contador):
    suma = totalpagina + contador
    return suma
# AQUI TERMINA LAS FUNCIONES NO REUTILIZABLES :(

def rangonumeros(_min, args=None):
    _max, _step = None, None
    if args:
        if not isinstance(args, int):
            _max, _step = map(int, args.split(','))
        else:
            _max = args
    args = filter(None, (_min, _max+1, _step))
    return range(*args)

def splitcadena(string, sep):
    return string.split(sep)

def obtenernumerosdecadena(cadena):
    import re
    cadena = re.sub("\D", "", cadena)
    return cadena

def convertirentero(cadena):
    return int(cadena)

@register.simple_tag
def traducir_mes(value):
    return ' '.join(str(value).lower().replace('january', 'Ene') \
                    .replace('february', 'Feb') \
                    .replace('march', 'Mar') \
                    .replace('april', 'Abr') \
                    .replace('may', 'May') \
                    .replace('june', 'Jun') \
                    .replace('july', 'Jul') \
                    .replace('august', 'Ago') \
                    .replace('september', 'Sep') \
                    .replace('october', 'Oct') \
                    .replace('november', 'Nov') \
                    .replace('december', 'Dic').split(' ')[0:2])

@register.simple_tag
def traducir_mes_completo(value):
    return ' '.join((str(value).lower()).replace('january', 'Enero') \
                    .replace('february', 'Febrero') \
                    .replace('march', 'Marzo') \
                    .replace('april', 'Abril') \
                    .replace('may', 'Mayo') \
                    .replace('june', 'Junio') \
                    .replace('july', 'Julio') \
                    .replace('august', 'Agosto') \
                    .replace('september', 'Septiembre') \
                    .replace('october', 'Octubre') \
                    .replace('november', 'Noviembre') \
                    .replace('december', 'Diciembre').split(' ')[0:2])

@register.simple_tag
def traducir_fecha_completo(value):
    dia = str(value.day)
    mes = traducir_mes_completo(value.strftime("%B"))
    anio = str(value.year)
    return dia + ' de ' + str(mes) + ' del ' + anio


@register.simple_tag
def formatnamerubro(value):
    try:
        valor = str(value).lower().capitalize().replace('valor inscripcion', '').replace('valor matricula', '')
    except Exception as ex:
        valor = str(value).lower().capitalize()
    return valor

@register.simple_tag
def contador_lista(page, forloop_counter):
    return ((page.number - 1) * page.paginator.per_page) + forloop_counter


def realizo_busqueda(url_vars='', numero=1):
    return len(url_vars.split('&')) - numero > 1

def title2(texto=''):
    return " ".join([x.capitalize() if x.__len__() > 3 else x.lower() for x in f"{texto}".lower().split(' ')])

def fecha_natural(fecha=datetime.now().date()):
    # Para mostrar todo el formato usar:format='log'
    format_custom = "d 'de' MMMM 'del' y"
    return format_date(fecha, format=format_custom, locale='es')

def numero_ordinal(numero, femenino=False):
    ordinal = num2words(numero, ordinal=True, lang='es')
    if femenino:
        ordinal = ' '.join([p[:-1] + 'a' if p.endswith('o') else p for p in ordinal.split()])
    return ordinal

def iniciales(palabras):
    palabras = palabras.split()
    primera = palabras[0][0]
    total = len(palabras)
    if total >= 3:
       ante_ultima = palabras[total - 2][0]
    ultima = palabras[total - 1][0]
    iniciales = primera + ante_ultima + ultima
    return iniciales

@register.simple_tag
def palabra_genero(persona, masculino='el', femenino='la'):
    sexo = persona.sexo
    palabra = masculino if not sexo or sexo.id == 2 else femenino
    return palabra

def fecha_completa_limite_indicador(value):
    date = value
    dia = str(date.day)
    mes = traducir_mes_completo(date.strftime("%B"))
    anio = str(date.year)
    return dia + ' de ' + str(mes) + ' del ' + anio


def numero_a_texto(n):
    UNIDADES = {
        1: 'primer' if n == 1 else 'uno',
        2: 'segundo',
        3: 'tercer' if n == 3 else 'tres',
        4: 'cuarto',
        5: 'quinto',
        6: 'sexto',
        7: 'séptimo',
        8: 'octavo',
        9: 'noveno'
    }

    DECENAS = {
        1: 'décimo',
        2: 'vigésimo',
        3: 'trigésimo',
        4: 'cuadragésimo',
        5: 'quincuagésimo',
        6: 'sexagésimo',
        7: 'septuagésimo',
        8: 'octogésimo',
        9: 'nonagésimo'
    }

    if n <= 9:
        return UNIDADES[n]
    elif n % 10 == 0:
        return DECENAS[n // 10]
    else:
        decena = n // 10
        unidad = n % 10
        return f"{DECENAS[decena]} {UNIDADES[unidad]}"


def numero_anio_a_texto(anio):
    UNIDADES = ['', 'un', 'dos', 'tres', 'cuatro', 'cinco', 'seis', 'siete', 'ocho', 'nueve']
    DECENAS = ['', 'diez', 'veinte', 'treinta', 'cuarenta', 'cincuenta', 'sesenta', 'setenta', 'ochenta', 'noventa']
    CENTENAS = ['', 'ciento', 'doscientos', 'trescientos', 'cuatrocientos', 'quinientos', 'seiscientos', 'setecientos',
                'ochocientos', 'novecientos']
    ESPECIALES = {
        11: 'once',
        12: 'doce',
        13: 'trece',
        14: 'catorce',
        15: 'quince',
        16: 'dieciséis',
        17: 'diecisiete',
        18: 'dieciocho',
        19: 'diecinueve',
    }

    millares = anio // 1000
    centenas = (anio % 1000) // 100
    decenas = (anio % 100) // 10
    unidades = anio % 10

    texto = []

    # Millares
    if millares > 0:
        texto.append(UNIDADES[millares] + ' mil')

    # Centenas
    if centenas > 0:
        texto.append(CENTENAS[centenas])

    # Decenas y unidades
    resto = anio % 100
    if resto in ESPECIALES:
        texto.append(ESPECIALES[resto])
    else:
        if decenas > 0:
            if unidades == 0:
                texto.append(DECENAS[decenas])
            elif decenas == 2:
                texto.append(f"veinti{UNIDADES[unidades]}")
            else:
                texto.append(f"{DECENAS[decenas]} y {UNIDADES[unidades]}")
        elif unidades > 0:
            texto.append(UNIDADES[unidades])

    return ' '.join(texto)


@register.filter
def fecha_a_texto(fecha):
    MESES = dict(MESES_CHOICES)
    if not fecha:
        return ""

    try:
        if isinstance(fecha, str):
            fecha = datetime.strptime(fecha, '%Y-%m-%d').date()

        dia_texto = numero_a_texto(fecha.day)
        mes = MESES[fecha.month]
        anio_texto = numero_anio_a_texto(fecha.year)

        return f"{dia_texto} día del mes de {mes.lower()} del año {anio_texto}"
    except (ValueError, TypeError, KeyError):
        return ""


def numero_a_letras(numero):
    UNIDADES = ['', 'UN', 'DOS', 'TRES', 'CUATRO', 'CINCO', 'SEIS', 'SIETE', 'OCHO', 'NUEVE']
    DECENAS = ['', 'DIEZ', 'VEINTE', 'TREINTA', 'CUARENTA', 'CINCUENTA', 'SESENTA', 'SETENTA', 'OCHENTA', 'NOVENTA']
    DIEZ_A_VEINTE = ['DIEZ', 'ONCE', 'DOCE', 'TRECE', 'CATORCE', 'QUINCE', 'DIECISÉIS', 'DIECISIETE', 'DIECIOCHO',
                     'DIECINUEVE']
    CENTENAS = ['', 'CIENTO', 'DOSCIENTOS', 'TRESCIENTOS', 'CUATROCIENTOS', 'QUINIENTOS', 'SEISCIENTOS', 'SETECIENTOS',
                'OCHOCIENTOS', 'NOVECIENTOS']

    def convertir_grupo(n):
        centenas = n // 100
        decenas = (n % 100) // 10
        unidades = n % 10
        texto = ''

        if centenas == 1 and decenas == 0 and unidades == 0:
            return 'CIEN'

        if centenas > 0:
            texto = CENTENAS[centenas]

        if decenas == 1:
            texto = f"{texto} {DIEZ_A_VEINTE[unidades]}"
        elif decenas > 0:
            if unidades > 0:
                if decenas == 2:
                    texto = f"{texto} VEINTI{UNIDADES[unidades]}"
                else:
                    texto = f"{texto} {DECENAS[decenas]} Y {UNIDADES[unidades]}"
            else:
                texto = f"{texto} {DECENAS[decenas]}"
        elif unidades > 0:
            texto = f"{texto} {UNIDADES[unidades]}"

        return texto.strip()

    def convertir_millones(n):
        millones = n // 1000000
        resto = n % 1000000
        texto = ''

        if millones == 1:
            texto = 'UN MILLÓN'
        elif millones > 1:
            texto = f"{convertir_grupo(millones)} MILLONES"

        if resto > 0:
            texto = f"{texto} {convertir_miles(resto)}"

        return texto.strip()

    def convertir_miles(n):
        miles = n // 1000
        resto = n % 1000
        texto = ''

        if miles == 1:
            texto = 'MIL'
        elif miles > 1:
            texto = f"{convertir_grupo(miles)} MIL"

        if resto > 0:
            texto = f"{texto} {convertir_grupo(resto)}"

        return texto.strip()

    try:
        numero = float(numero)
        parte_entera = int(numero)
        parte_decimal = int(round((numero - parte_entera) * 100))

        if parte_entera == 0:
            texto_numero = "CERO"
        elif parte_entera == 1:
            texto_numero = "UN"
        else:
            if parte_entera < 1000:
                texto_numero = convertir_grupo(parte_entera)
            elif parte_entera < 1000000:
                texto_numero = convertir_miles(parte_entera)
            else:
                texto_numero = convertir_millones(parte_entera)

        texto_decimal = f"{parte_decimal:02d}"

        return f"{texto_numero} CON {texto_decimal}/100 DÓLARES"
    except:
        return "CERO CON 00/100 DÓLARES"


@register.filter
def moneda_a_texto(valor):
    if valor is None:
        return "CERO CON 00/100 DÓLARES"
    return numero_a_letras(valor)



register.filter('diaenletra', diaenletra)
register.filter('filedsmodel', fields_model)
register.filter('fielddefaultvaluemodel', field_default_value_model)
register.filter('ceros', ceros)
register.filter('fechamayor', fechamayor)
register.filter('fechaletra_corta', fechaletra_corta)
register.filter('times', times)
register.filter("call", callmethod)
register.filter("args", args)
register.filter("transformar_n_l", transformar_n_l)
register.filter("transformar_mes", transformar_mes)
register.filter("convertir_numero_a_palabra", convertir_numero_a_palabra)
register.filter("suma", suma)
register.filter("sumar_fm", sumar_fm)
register.filter("sumar_fh", sumar_fh)
register.filter("sumar_cm", sumar_cm)
register.filter("sumar_ch", sumar_ch)
register.filter("sumar_th", sumar_th)
register.filter("sumar_pagineo", sumar_pagineo)
register.filter("sumar_tm", sumar_tm)
register.filter("resta", resta)
register.filter("restanumeros", restanumeros)
register.filter("multiplicanumeros", multiplicanumeros)
register.filter("entrefechas", entrefechas)
register.filter("porciento", porciento)
register.filter("nombremescorto", nombremescorto)
register.filter("substraer", substraer)
register.filter("nombremes", nombremes)
register.filter("fechapermiso", fechapermiso)
register.filter("nombrepersona", nombrepersona)
register.filter("datename", datename)
register.filter("fecha_estructurada", fecha_estructurada)
register.filter("divide", divide)
register.filter("calendarbox", calendarbox)
register.filter("calendarboxdetails", calendarboxdetails)
register.filter("calendarboxdetails2", calendarboxdetails2)
register.filter("calendarboxdetailsmostrar", calendarboxdetailsmostrar)
register.filter("barraporciento", barraporciento)
register.filter("solo_caracteres", solo_caracteres)
register.filter("rangonumeros", rangonumeros)
register.filter("splitcadena", splitcadena)
register.filter("encrypt", encrypt)
register.filter("encrypt_alu", encrypt_alu)
register.filter("is_int_or_char", is_int_or_char)
register.filter("splitcadypre", splitcadypre)
register.filter("splitcadyprestr", splitcadyprestr)
register.filter("obtenernumerosdecadena", obtenernumerosdecadena)
register.filter("convertirentero", convertirentero)
register.filter("realizo_busqueda", realizo_busqueda)
register.filter("title2", title2)
register.filter("fecha_natural", fecha_natural)
register.filter("numero_ordinal", numero_ordinal)
register.filter("iniciales", iniciales)
register.filter("fecha_completa_limite_indicador", fecha_completa_limite_indicador)
