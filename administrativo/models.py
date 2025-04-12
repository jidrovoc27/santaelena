import datetime
from datetime import datetime
from decimal import Decimal

#IMPORTACIÓN DJANGO
from django.db import models
from django.db.models.functions import Coalesce
from django.db.models import Sum, F, FloatField, Q
from django.contrib.auth.models import User, Group
from administrativo.choices import *
from django.utils import timezone
from django.core.cache import cache

#IMPORTACIÓN SGA
from administrativo.funciones import ModeloBase, null_to_decimal, null_to_numeric, convertir_fecha, miempresa


unicode = str


class CategoriaModulo(ModeloBase):
    orden = models.IntegerField(default=0, verbose_name='Orden')
    nombre = models.CharField(default='', max_length=1000, verbose_name=u'Nombre')
    icono = models.CharField(default='', max_length=100, verbose_name=u'Icono')

    def mismodulos(self, persona, ids_modulos_favoritos):
        ids_modulos_favoritos = [] if not ids_modulos_favoritos else ids_modulos_favoritos
        misgrupos = ModuloGrupo.objects.filter(grupos__in=persona.usuario.groups.all()).values_list('id', flat=True)
        return self.modulo_set.exclude(id__in=ids_modulos_favoritos).values('id', 'icono', 'nombre', 'descripcion',
                                                                            'url').filter(Q(modulogrupo__in=misgrupos),
                                                                                          activo=True,
                                                                                          sagest=True).distinct().order_by(
            'orden')

    def __str__(self):
        return u'%s' % (self.nombre)

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.strip()
        super(CategoriaModulo, self).save(*args, **kwargs)


class Modulo(ModeloBase):
    categoria = models.ManyToManyField(CategoriaModulo, verbose_name=u'Categoria')
    orden = models.IntegerField(default=0, verbose_name='Orden')
    url = models.CharField(default='', max_length=100, verbose_name=u'URL')
    nombre = models.CharField(default='', max_length=1000, verbose_name=u'Nombre')
    icono = models.CharField(default='', max_length=100, verbose_name=u'Icono')
    descripcion = models.CharField(default='', max_length=200, verbose_name=u'Descripción')
    activo = models.BooleanField(default=True, verbose_name=u'Activo')
    administrativo = models.BooleanField(default=False, verbose_name=u'Activo para administrativos')
    submodulo = models.BooleanField(default=False, blank=True, null=True, verbose_name=u'Es submódulo?')

    def __str__(self):
        return u'%s (/%s)' % (self.nombre, self.url)

    class Meta:
        verbose_name = u"Modulo"
        verbose_name_plural = u"Modulos"
        ordering = ['nombre']
        unique_together = ('url',)

    def grupo_prioridad(self):
        return self.modulogrupo_set.all().order_by('prioridad')[0]

    def save(self, *args, **kwargs):
        self.url = self.url.strip()
        self.nombre = self.nombre.strip()
        self.icono = self.icono.strip()
        self.descripcion = self.descripcion.strip()
        super(Modulo, self).save(*args, **kwargs)


class ModuloGrupo(ModeloBase):
    nombre = models.CharField(default='', max_length=100, verbose_name=u' Nombre')
    descripcion = models.CharField(default='', max_length=200, verbose_name=u'Descripción')
    modulos = models.ManyToManyField(Modulo, verbose_name=u'Modulos')
    grupos = models.ManyToManyField(Group, verbose_name=u'Grupos')
    prioridad = models.IntegerField(default=0, verbose_name=u'Prioridad')

    def __str__(self):
        return u'%s' % self.nombre

    class Meta:
        verbose_name = u'Grupo de modulos'
        verbose_name_plural = u"Grupos de modulos"
        ordering = ['nombre']
        unique_together = ('nombre',)

    def modulos_activos(self):
        return self.modulos.filter(activo=True)

    def modules(self):
        return self.modulos.all()

    def groups(self):
        return self.grupos.all()

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.strip().capitalize()
        self.descripcion = self.descripcion.strip().capitalize()
        super(ModuloGrupo, self).save(*args, **kwargs)


class Sexo(ModeloBase):
    nombre = models.CharField(default='', max_length=100, verbose_name=u'Nombre')

    def __str__(self):
        return u'%s' % self.nombre

    class Meta:
        verbose_name = u"Sexo"
        verbose_name_plural = u"Sexos"
        unique_together = ('nombre',)

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper()
        super(Sexo, self).save(*args, **kwargs)


class Pais(ModeloBase):
    nombre = models.CharField(default='', max_length=100, verbose_name=u"Nombre")
    nacionalidad = models.CharField(default='', max_length=100, verbose_name=u"Nacionalidad")

    @staticmethod
    def flexbox_query(q, extra=None):
        if extra:
            return eval('Pais.objects.filter(Q(nombre__contains="%s")).filter(%s).distinct()[:25]' % (q, extra))
        return Pais.objects.filter(Q(nombre__contains=q)).distinct()[:25]

    def flexbox_repr(self):
        return self.__str__()

    def __str__(self):
        return u'%s' % self.nombre

    class Meta:
        verbose_name = u"País"
        verbose_name_plural = u"Paises"
        ordering = ['nombre']
        unique_together = ('nombre',)

    def en_uso(self):
        return self.provincia_set.values('id').all().exists()

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper()
        super(Pais, self).save(*args, **kwargs)


class Region(ModeloBase):
    nombre = models.CharField(default='', max_length=100, verbose_name=u"Nombre")

    def __str__(self):
        return u'%s' % self.nombre

    class Meta:
        verbose_name = u"Región"
        verbose_name_plural = u"Regiones"
        ordering = ['nombre']
        unique_together = ('nombre',)


class Provincia(ModeloBase):
    pais = models.ForeignKey(Pais, blank=True, null=True, verbose_name=u'País', on_delete=models.CASCADE)
    nombre = models.CharField(default='', max_length=100, verbose_name=u"Nombre")

    @staticmethod
    def flexbox_query(q, extra=None):
        if extra:
            return eval('Provincia.objects.filter(Q(nombre__contains="%s")).filter(%s).distinct()[:25]' % (q, extra))
        return Provincia.objects.filter(Q(nombre__contains=q)).distinct()[:25]

    def flexbox_repr(self):
        return self.__str__()

    def __str__(self):
        return u'%s' % self.nombre

    class Meta:
        verbose_name = u"Provincia"
        verbose_name_plural = u"Provincias"
        ordering = ['nombre']
        unique_together = ('nombre', 'pais')

    def en_uso(self):
        return self.ciudad_set.values('id').all().exists()

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper()
        super(Provincia, self).save(*args, **kwargs)


class Ciudad(ModeloBase):
    provincia = models.ForeignKey(Provincia, blank=True, null=True, verbose_name=u'Provincia', on_delete=models.CASCADE)
    nombre = models.CharField(default='', max_length=100, verbose_name=u"Nombre")

    @staticmethod
    def flexbox_query(q, extra=None):
        if extra:
            return eval('Canton.objects.filter(Q(nombre__contains="%s")).filter(%s).distinct()[:25]' % (q, extra))
        return Ciudad.objects.filter(Q(nombre__contains=q)).distinct()[:25]

    def flexbox_repr(self):
        return self.__str__()

    def __str__(self):
        return f'{self.nombre}'

    def nombre_largo_2(self):
        if self.provincia and self.provincia.pais:
            return f'{self.nombre.title()} - {self.provincia.nombre.title()} - {self.provincia.pais.nombre.title()}'
        elif self.provincia:
            return f'{self.nombre.title()} - {self.provincia.nombre.title()}'
        else:
            return f'{self.nombre.title()}'

    def nombre_largo(self):
        if self.provincia and self.provincia.pais:
            return f'{self.nombre.title()}, {self.provincia.nombre.title()}, {self.provincia.pais.nombre.title()}'
        elif self.provincia:
            return f'{self.nombre.title()}, {self.provincia.nombre.title()}'
        else:
            return f'{self.nombre.title()}'

    class Meta:
        verbose_name = u"Canton"
        verbose_name_plural = u"Cantones"
        ordering = ['nombre']
        unique_together = ('nombre', 'provincia')

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper()
        super(Ciudad, self).save(*args, **kwargs)


class Parroquia(ModeloBase):
    ciudad = models.ForeignKey(Ciudad, blank=True, null=True, verbose_name=u'Provincia', on_delete=models.CASCADE)
    nombre = models.CharField(default='', max_length=100, verbose_name=u"Nombre")

    def __str__(self):
        return u'%s' % self.nombre

    class Meta:
        verbose_name = u"Parroquia"
        verbose_name_plural = u"Parroquia"
        ordering = ['nombre']
        unique_together = ('nombre', 'ciudad')

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper()
        super(Parroquia, self).save(*args, **kwargs)


class Persona(ModeloBase):
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    nombres = models.CharField(default='', max_length=100, verbose_name=u'Nombre')
    apellido1 = models.CharField(default='', max_length=50, verbose_name=u"1er Apellido")
    apellido2 = models.CharField(default='', max_length=50, verbose_name=u"2do Apellido")
    identificacion = models.CharField(default='', max_length=20, verbose_name=u"Cedula", blank=True)
    tipodocumento = models.IntegerField(choices=TIPO_IDENTIFICACION, default=1, blank=True, null=True,
                                        verbose_name=u"Tipo Documento")
    tipopersona = models.IntegerField(choices=TIPO_PERSONA, default=1, null=True, blank=True,
                                      verbose_name=u"Tipo de persona")
    nacionalidad = models.CharField(default='', max_length=100, verbose_name=u'Nacionalidad')
    nacimiento = models.DateField(blank=True, null=True, verbose_name=u"Fecha de nacimiento o constitución")
    sexo = models.ForeignKey(Sexo, on_delete=models.PROTECT, blank=True, null=True, verbose_name=u'Sexo')
    telefono = models.CharField(default='', max_length=50, verbose_name=u"Teléfono móvil")
    telefono_conv = models.CharField(default='', max_length=50, verbose_name=u"Teléfono fijo")
    correo = models.CharField(default='', max_length=200, verbose_name=u"Correo electronico personal")
    pais = models.ForeignKey(Pais, on_delete=models.PROTECT, blank=True, null=True, related_name='+',
                             verbose_name=u'País de nacimiento')
    provincia = models.ForeignKey(Provincia, on_delete=models.PROTECT, blank=True, null=True, related_name='+',
                                  verbose_name=u"Provincia de nacimiento")
    ciudad = models.ForeignKey(Ciudad, on_delete=models.PROTECT, blank=True, null=True, related_name='+',
                               verbose_name=u"Ciudad de nacimiento")
    parroquia = models.ForeignKey(Parroquia, on_delete=models.PROTECT, blank=True, null=True, related_name='+',
                                  verbose_name=u"Parroquia de nacimiento")
    sector = models.CharField(default='', max_length=300, verbose_name=u"Sector de residencia")
    direccion = models.CharField(default='', max_length=300, verbose_name=u"Calle principal")
    direccion2 = models.CharField(default='', max_length=300, verbose_name=u"Calle secundaria")
    numeroresidencia = models.CharField(default='', max_length=15, verbose_name=u"Numero")
    referencia = models.CharField(default='', max_length=100, verbose_name=u"Referencia")

    def __str__(self):
        return u'%s %s %s' % (self.apellido1, self.apellido2, self.nombres)

    class Meta:
        verbose_name = u"Persona"
        verbose_name_plural = u"Personal"
        ordering = ['apellido1', 'apellido2', 'nombres']
        unique_together = ('identificacion',)

    def tiene_perfil(self):
        return self.perfilusuario_set.values("id").exists()

    @staticmethod
    def flexbox_query(q, extra=None):
        if ' ' in q:
            s = q.split(" ")
            if extra:
                return eval(
                    'Persona.objects.filter(Q(apellido1__contains="%s") & Q(apellido2__contains="%s")).filter(%s).distinct()[:25]' % (
                        s[0], s[1], extra))
            return Persona.objects.filter(Q(apellido1__contains=s[0]) & Q(apellido2__contains=s[1])).distinct()[:25]
        if extra:
            return eval(
                'Persona.objects.filter(Q(nombres__contains="%s") | Q(apellido1__contains="%s") | Q(apellido2__contains="%s") | Q(identificacion__contains="%s")).filter(%s).distinct()[:25]' % (
                    q, q, q, q, extra))
        return Persona.objects.filter(Q(nombres__contains=q) | Q(apellido1__contains=q) | Q(apellido2__contains=q) | Q(
            cedula__contains=q)).distinct()[:25]

    def flexbox_repr(self):
        return self.cedula + " - " + self.nombre_completo_inverso() + " - " + self.id.__str__()

    def flexbox_alias(self):
        return [self.cedula, self.nombre_completo()]

    def tiene_perfilusuario(self):
        return self.perfilusuario_set.values("id").exists()

    def crear_perfil(self, administrativo=None, cliente=None, paciente=None):
        if administrativo:
            perfil = PerfilUsuario(persona=self, administrativo=administrativo)
            perfil.save()
        if paciente:
            perfil = PerfilUsuario(persona=self, paciente=paciente)
            perfil.save()
        elif cliente:
            perfil = PerfilUsuario(persona=self, cliente=cliente)
            perfil.save()

    def creacion_persona(self, nombresistema,persona):
        lista = ['santaelena@outlook.com']
        perfil = PerfilUsuario.objects.filter(persona=self).order_by('-id')[0]

    def tiene_multiples_perfiles(self):
        return self.perfilusuario_set.values("id").count() > 1

    def mis_perfilesusuarios(self):
        return self.perfilusuario_set.all()

    def mis_perfilesusuarios_app(self, app):
        if app == 'administrativo':
            return self.perfilusuario_set.all().order_by('id')
        else:
            return self.perfilusuario_set.all().order_by('id')

    def mis_perfilesadministrativo(self):
        return self.perfilusuario_set.filter(administrativo__isnull=False)

    def perfilusuario_principal(self, perfiles, app):
        if app == 'administrativo':
            if perfiles.values("id").filter(administrativo__isnull=False, administrativo__activo=True).exists():
                return perfiles.filter(administrativo__isnull=False, administrativo__activo=True)[0]
        return None

    def perfilusuario_administrativo(self):
        if self.perfilusuario_set.values("id").filter(administrativo__isnull=False,
                                                      administrativo__activo=True).exists():
            return self.perfilusuario_set.filter(administrativo__isnull=False, administrativo__activo=True)[0]
        return None

    def puede_recibir_pagos(self):
        if self.lugarrecaudacion_set.values("id").exists():
            lr = self.lugarrecaudacion_set.all()[0]
            if lr.sesioncaja_set.values("id").filter(abierta=True).exists():
                lr = lr.sesioncaja_set.filter(abierta=True)[0]
                return lr.fecha == datetime.now().date()
        return False

    def es_cajero_online(self):
        return self.lugarrecaudacion_set.filter(available=True, activo=True, cajaonline=True).exists()

    def es_administrador(self):
        return self.usuario.groups.values("id").filter(id=1).exists()

    def es_administrativo(self):
        return self.perfilusuario_set.values("id").filter(administrativo__isnull=False).exists()

    def es_clienteexterno(self):
        return self.perfilusuario_set.values("id").filter(cliente__isnull=False).exists()

    def es_administrativo_perfilactivo(self):
        return self.perfilusuario_set.values("id").filter(administrativo__isnull=False,
                                                          administrativo__activo=True).exists()

    def direccion_completa(self):
        return u"%s %s %s %s %s %s %s" % ((self.provincia.nombre + ",") if self.provincia else "",
                                          (self.ciudad + ",") if self.ciudad else "",
                                          (self.parroquia.nombre + ",") if self.parroquia else "",
                                          (self.sector + ",") if self.sector else "",
                                          (self.direccion + ",") if self.direccion else "",
                                          (self.direccion2 + ",") if self.direccion2 else "",
                                          self.num_direccion)

    def direccion_corta(self):
        return u"%s %s %s" % (
            (self.direccion + ",") if self.direccion else "", (self.direccion2 + ",") if self.direccion2 else "",
            self.num_direccion)

    def activo(self):
        return self.usuario.is_active if self.usuario else False

    def ultima_sesioncaja(self):
        if self.lugarrecaudacion_set.values("id").exists():
            lr = self.lugarrecaudacion_set.all()[0]
            if lr.sesioncaja_set.values("id").filter(abierta=True).exists():
                return lr.sesioncaja_set.filter(abierta=True)[0]
        return None

    def caja(self):
        if self.lugarrecaudacion_set.values("id").exists():
            return self.lugarrecaudacion_set.all()[0]
        return None

    def ultima_fecha_caja(self):
        if self.caja():
            lr = self.caja()
            if lr.esta_abierta():
                return lr.sesion_caja().fecha
        return None

    def nombre_completo(self):
        return u'%s %s %s' % (self.nombres, self.apellido1, self.apellido2)

    def nombre_completo_inverso(self):
        return u'%s %s %s' % (self.apellido1, self.apellido2, self.nombres)

    def nombre_completo_simple(self):
        return u'%s %s' % (self.nombres, self.apellido1[0] if self.apellido1 else "")

    def nombre_iniciales(self):
        return u"%s" % (self.nombres[:3])

    def administrativo(self):
        if self.administrativo_set.values("id").exists():
            return self.administrativo_set.all()[0]
        return None

    def en_grupo(self, grupo):
        return self.usuario.groups.values("id").filter(id=grupo).exists()

    def en_grupos(self, lista):
        return self.usuario.groups.values("id").filter(id__in=lista).exists()

    def grupos(self):
        return self.usuario.groups.all().distinct()

    def lugar_recaudacion(self):
        lugar_rec = self.lugarrecaudacion_set.filter(status=True)
        if lugar_rec.values("id").exists():
            return lugar_rec.first()
        return None

    def mi_lugar_recaudacion(self):
        if self.lugarrecaudacion_set.values("id").filter(activo=True, puntoventa__activo=True,
                                                         origenrecaudacion=1).exists():
            return self.lugarrecaudacion_set.filter(activo=True, puntoventa__activo=True, origenrecaudacion=1)[0]
        return None

    def mi_lugar_recaudacion_unistore(self):
        lugar_recaudacion = self.lugarrecaudacion_set.filter(activo=True, puntoventa__activo=True,
                                                             origenrecaudacion=2).first()
        if lugar_recaudacion:
            return lugar_recaudacion
        return None


    def rubros_pendientes(self):
        return self.rubro_set.filter(cancelado=False, available=True).order_by('tipocuota', 'cuota', 'cancelado',
                                                                               'fechavence')

    def user_system(self):
        return False if self.usuario.groups.filter(id=1).exists() else True

    def save(self, *args, **kwargs):
        if self.tipopersona == 1 or self.tipopersona == 3:
            self.apellido1 = self.apellido1.upper().strip()
            self.apellido2 = self.apellido2.upper().strip()
        self.nombres = self.nombres.upper().strip()
        super(Persona, self).save(*args, **kwargs)

class Administrativo(ModeloBase):
    persona = models.ForeignKey(Persona, verbose_name=u"Persona", on_delete=models.CASCADE)
    fechaingreso = models.DateField(verbose_name=u'Fecha ingreso')
    activo = models.BooleanField(default=True, verbose_name=u"Activo")

    def __str__(self):
        return u'%s' % self.persona

    class Meta:
        verbose_name = u"Administrativo"
        verbose_name_plural = u"Administrativos"
        ordering = ['persona']
        unique_together = ('persona',)

    @staticmethod
    def flexbox_query(q, extra=None, limit=25):
        if ' ' in q:
            s = q.split(" ")
            return Administrativo.objects.filter(Q(persona__apellido1__contains=s[0]) & Q(persona__apellido2__contains=s[1])).distinct()[:limit]
        return Administrativo.objects.filter(Q(persona__nombres__contains=q) | Q(persona__apellido1__contains=q) | Q(persona__apellido2__contains=q) | Q(persona__identificacion__contains=q)).distinct()[:limit]

    def flexbox_repr(self):
        return self.persona.identificacion + " - " + self.persona.nombre_completo_inverso() + " - " + self.id.__str__()

    def flexbox_alias(self):
        return [self.persona.identificacion, self.persona.nombre_completo()]

class Paciente(ModeloBase):
    persona = models.ForeignKey(Persona, verbose_name=u"Persona", on_delete=models.CASCADE)
    fechaingreso = models.DateField(verbose_name=u'Fecha ingreso')
    activo = models.BooleanField(default=True, verbose_name=u"Activo")

    def __str__(self):
        return u'%s' % self.persona

    class Meta:
        verbose_name = u"Paciente"
        verbose_name_plural = u"Pacientes"
        ordering = ['persona']
        unique_together = ('persona',)

    @staticmethod
    def flexbox_query(q, extra=None, limit=25):
        if ' ' in q:
            s = q.split(" ")
            return Paciente.objects.filter(Q(persona__apellido1__contains=s[0]) & Q(persona__apellido2__contains=s[1])).distinct()[:limit]
        return Paciente.objects.filter(Q(persona__nombres__contains=q) | Q(persona__apellido1__contains=q) | Q(persona__apellido2__contains=q) | Q(persona__identificacion__contains=q)).distinct()[:limit]

    def flexbox_repr(self):
        return self.persona.identificacion + " - " + self.persona.nombre_completo_inverso() + " - " + self.id.__str__()

    def flexbox_alias(self):
        return [self.persona.identificacion, self.persona.nombre_completo()]

class Encargado(ModeloBase):
    persona = models.ForeignKey(Persona, verbose_name=u"Persona", on_delete=models.CASCADE)
    fechaingreso = models.DateField(verbose_name=u'Fecha ingreso')
    activo = models.BooleanField(default=True, verbose_name=u"Activo")

    def __str__(self):
        return u'%s' % self.persona

    class Meta:
        verbose_name = u"Administrativo"
        verbose_name_plural = u"Administrativos"
        ordering = ['persona']
        unique_together = ('persona',)

    @staticmethod
    def flexbox_query(q, extra=None, limit=25):
        if ' ' in q:
            s = q.split(" ")
            return Administrativo.objects.filter(Q(persona__apellido1__contains=s[0]) & Q(persona__apellido2__contains=s[1])).distinct()[:limit]
        return Administrativo.objects.filter(Q(persona__nombres__contains=q) | Q(persona__apellido1__contains=q) | Q(persona__apellido2__contains=q) | Q(persona__identificacion__contains=q)).distinct()[:limit]

    def flexbox_repr(self):
        return self.persona.identificacion + " - " + self.persona.nombre_completo_inverso() + " - " + self.id.__str__()

    def flexbox_alias(self):
        return [self.persona.identificacion, self.persona.nombre_completo()]

class PerfilUsuario(ModeloBase):
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE)
    administrativo = models.ForeignKey(Administrativo, blank=True, null=True, verbose_name=u'Administrativo', on_delete=models.CASCADE)
    paciente = models.ForeignKey(Paciente, blank=True, null=True, verbose_name=u'Paciente', on_delete=models.CASCADE)
    visible = models.BooleanField(default=True, verbose_name=u'Visible')

    def __str__(self):
        if self.es_administrativo():
            return u'%s' % "ADMINISTRATIVO"
        elif self.es_cliente():
            return u'%s' % "CLIENTE"
        else:
            return u'%s' % "OTRO PERFIL"

    class Meta:
        ordering = ['persona', ]
        # unique_together = ('persona', )

    def es_administrativo(self):
        if self.administrativo_id:
            return True if self.administrativo_id > 0 else False
        return False

    def es_cliente(self):
        if self.cliente_id:
            return True if self.cliente_id > 0 else False
        return False

    def activo(self):
        if self.es_administrativo():
            return self.administrativo.activo
        elif self.es_cliente():
            return self.cliente.activo
        return False

    def obtener_perfil(self):
        if self.es_cliente():
            return self.cliente
        elif self.es_administrativo():
            return self.administrativo
        return None

    def tipo(self):
        if self.es_cliente():
            return "CLIENTE"
        elif self.es_administrativo():
            return "ADMINISTRATIVO"
        else:
            return "NO DEFINIDO"

    def save(self, *args, **kwargs):
        super(PerfilUsuario, self).save(*args, **kwargs)

class Empresa(ModeloBase):
    nombre = models.CharField(default='', max_length=300, verbose_name=u'Nombre')
    nombrecomercial = models.CharField(default='', max_length=300, verbose_name=u'Nombre Comercial')
    ruc = models.CharField(default='', max_length=13, verbose_name=u'RUC')
    contribuyenteespecial = models.CharField(default='', max_length=13, verbose_name=u'Contribuyente Especial')
    direccion = models.CharField(default='', max_length=300, verbose_name=u'Dirección')
    telefono = models.CharField(default='', max_length=200, verbose_name=u'Telefonos')
    telefono_tics = models.CharField(default='', max_length=200, verbose_name=u'Telefono Tics')
    telwhats = models.CharField(default='', max_length=200, verbose_name=u'Whatsapp')
    correo = models.CharField(default='', max_length=200, verbose_name=u'Correo electronico')
    terminospagoonline = models.FileField(upload_to="terminoscondiciones", blank=True, null=True, verbose_name='Consulta Estudiante Términos y condiciones')
    mensajeventanapagos = models.TextField(blank=True, null=True, verbose_name="Mensaje para ventana pagos")
    proceso_facturacion = models.BooleanField(default=True, verbose_name=u"Proceso Factura")
    mision = models.TextField(blank=True, null=True, verbose_name='Misión')
    vision = models.TextField(blank=True, null=True, verbose_name='Visión')
    terminoscondiciones = models.TextField(blank=True, null=True, verbose_name='Terminos y Condiciones')
    logo = models.FileField(upload_to='configuracion/logo/', max_length=600, blank=True, null=True, verbose_name='Imagen 1920*718')
    logo_blanco = models.FileField(upload_to='configuracion/logo/', max_length=600, blank=True, null=True, verbose_name='Imagen 1920*718')
    habilitado_transferencia = models.BooleanField(default=True, verbose_name=u"Habilitar Transferencia/Deposito")
    habilitado_ptp = models.BooleanField(default=True, verbose_name=u"Habilitar Placetopay")
    produccion_ptp = models.BooleanField(default=True, verbose_name=u"Habilitar Entorno Producción Placetopay")
    cron_placetopay = models.BooleanField(default=False, verbose_name=u"Habilitar cron para finalizar sesiones pendientes de placetopay")
    cron_pruebaplacetopay = models.BooleanField(default=False, verbose_name=u"Habilitar cron prueba para finalizar sesiones pendientes de placetopay")
    habilitar_historial = models.BooleanField(default=True, verbose_name=u"Habilitar historial de transacciones PlaceToPay")

    class Meta:
        verbose_name = u"Dato de la institución"
        verbose_name_plural = u"Datos de la institución"

    def __str__(self):
        return u'%s' % self.nombre

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper().strip()
        self.direccion = self.direccion.strip().capitalize()
        self.telefono = self.telefono.upper().strip()
        self.correo = self.correo.lower().strip()
        super(Empresa, self).save(*args, **kwargs)

class ClienteTienda(ModeloBase):
    persona = models.ForeignKey(Persona, on_delete=models.PROTECT, blank=True, null=True, verbose_name=u"Persona")
    nombrecompleto = models.CharField(default='', max_length=200, verbose_name=u'Nombre completo')
    telefonocontacto = models.CharField(default='', max_length=50, verbose_name=u"Telefono contacto")

    def __str__(self):
        return u'%s' % self.nombrecompleto

    class Meta:
        verbose_name = u"Cliente de tienda virtual"
        verbose_name_plural = u"Clientes de tienda virtual"
        ordering = ['persona']
        unique_together = ('persona',)

    def save(self, *args, **kwargs):
        self.nombrecompleto = self.nombrecompleto.upper().strip()
        super(ClienteTienda, self).save(*args, **kwargs)

class CategoriaProducto(ModeloBase):
    descripcion = models.CharField(default='', max_length=800, null=True, blank=True, verbose_name=u"Descripción de la categoría")

    def __str__(self):
        return u'%s' % self.descripcion

    class Meta:
        verbose_name = u"Categoría producto"
        verbose_name_plural = u"Categorías producto"

    def get_subcategorias(self):
        return self.subcategoriaproducto_set.filter(status=True)

class SubCategoriaProducto(ModeloBase):
    descripcion = models.CharField(default='', max_length=800, null=True, blank=True, verbose_name=u"Descripción de la categoría")
    categoriaproducto = models.ForeignKey(CategoriaProducto, on_delete=models.PROTECT, blank=True, null=True, verbose_name=u"Categoría")
    imagen = models.ImageField(upload_to='tiendavirtual/subcategoria/', verbose_name=u'Imagen principal del producto', blank=True, null=True)

    def __str__(self):
        return u'%s' % self.descripcion

    class Meta:
        verbose_name = u"Subcategoría producto"
        verbose_name_plural = u"Subcategorías producto"

class Producto(ModeloBase):
    nombre = models.CharField(default='', max_length=800, null=True, blank=True, verbose_name=u"Nombre del producto")
    descripcion = models.TextField(default='', max_length=4000, null=True, blank=True, verbose_name=u"Descripción del producto")
    imagenprincipal = models.ImageField(upload_to='tiendavirtual', verbose_name=u'Imagen principal del producto', blank=True, null=True)
    subcategoria = models.ForeignKey(SubCategoriaProducto, on_delete=models.PROTECT, blank=True, null=True, verbose_name=u"SubCategoría")
    precio = models.DecimalField(max_digits=30, decimal_places=16, default=0)
    vigente = models.BooleanField(default=True, verbose_name=u'Vigente')

    def __str__(self):
        return u'%s' % self.nombre

    class Meta:
        verbose_name = u"Producto"
        verbose_name_plural = u"Productos"

    def get_stock_(self, especificaciones):
        producto = self
        stock = Stock.objects.filter(status=True, producto__status=True, producto=producto, producto__vigente=True, cantidad__gt=0, especificacion_producto__in=especificaciones)
        if stock.exists():
            stock = stock.first()
            return stock
        return None

    def get_total_salidas(self):
        kardex = KardexProducto.objects.filter(status=True, stock__producto=self, stock__status=True, movimiento=2).aggregate(total=Coalesce(Sum('cantidad'), 0, output_field=FloatField())).get('total')
        return kardex
    def get_total_ingresos(self):
        kardex = KardexProducto.objects.filter(status=True, stock__producto=self, stock__status=True, movimiento=1).aggregate(total=Coalesce(Sum('cantidad'), 0, output_field=FloatField())).get('total')
        return kardex

    def get_stock(self, talla_id):
        producto = self
        stock = Stock.objects.filter(status=True, producto=producto, producto__vigente=True, cantidad__gt=0, talla_id=talla_id)
        if stock.exists():
            stock = stock.first()
            return stock
        return stock

    def get_val_especificacion(self, tipoespecificacion):
        stock = Stock.objects.filter(status=True, especificacion_producto__especificacion_id=tipoespecificacion, producto=self).values_list('especificacion_producto__id', flat=True)
        especificacion = EspecificacionProducto.objects.filter(status=True, id__in=stock).order_by('valor')
        return especificacion


class TipoEspecificacion(ModeloBase):
    atributo = models.CharField(max_length=1000, verbose_name=u"Atributo (ej. Talla, Color, Capacidad)")

    def __str__(self):
        return u'%s' % (self.atributo)

class EspecificacionProducto(ModeloBase):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, blank=True, null=True, related_name='especificaciones', verbose_name=u"Producto")
    especificacion = models.ForeignKey(TipoEspecificacion, on_delete=models.CASCADE, blank=True, null=True, related_name='tipoespecificacion', verbose_name=u"Tipo especificación")
    valor = models.CharField(max_length=1000, blank=True, null=True, verbose_name=u"Valor (ej. L, Azul, 10kg)")
    orden = models.IntegerField(default=1, blank=True, null=True, verbose_name=u"Orden de la especificación")

    def __str__(self):
        return u'%s: %s' % (self.especificacion, self.valor)


class Stock(ModeloBase):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, blank=True, null=True, related_name='stocks', verbose_name=u"Stock")
    especificacion_producto = models.ManyToManyField(EspecificacionProducto, blank=True, related_name='stocks', verbose_name=u"Especificaciones del producto")
    cantidad_inicial = models.IntegerField(default=0, blank=True, null=True, verbose_name=u'Cantidad inicial')
    cantidad = models.IntegerField(default=0, blank=True, null=True, verbose_name=u'Cantidad disponible')

    def __str__(self):
        especificaciones = ", ".join([str(e) for e in self.especificacion_producto.all()])
        return u'%s - %s' % (self.producto.nombre, especificaciones)

    def get_cantidad_sesion(self, list_carrito):
        id_produc_stock = f"{self.producto.id}_{self.id}"
        cantidad = list_carrito[id_produc_stock]
        if cantidad:
            return cantidad
        return 0

    def get_total_producto(self, cantidad):
        return cantidad * self.producto.precio

    def get_especificaciones(self):
        return self.especificacion_producto.filter(status=True)

    def detalle_especificacion(self):
        detale = ''
        for especi in self.get_especificaciones():
            detale += f'{especi.especificacion.__str__()}: {especi.valor}'
        return detale


TIPO_MOVIMIENTO = (
    (1, u'INGRESO'),
    (2, u'EGRESO'),
)

class KardexProducto(ModeloBase):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, blank=True, null=True, related_name='stock', verbose_name=u"Stock")
    movimiento = models.IntegerField(choices=TIPO_MOVIMIENTO, default=2, verbose_name=u'Movimiento del kardex')
    cantidad = models.PositiveIntegerField(default=0, blank=True, null=True, verbose_name=u'Cantidad')
    costo = models.DecimalField(max_digits=30, decimal_places=16, default=0, verbose_name=u'Costo')
    total = models.DecimalField(max_digits=30, decimal_places=16, default=0, verbose_name=u'Costo total')
    observacion = models.CharField(max_length=2000, blank=True, null=True, verbose_name=u"Observación sobre el movimiento")

    def __str__(self):
        return u'%s' % (self.get_movimiento_display)

class ImagenProducto(ModeloBase):
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, blank=True, null=True, verbose_name=u"Producto")
    imagen = models.ImageField(upload_to='tiendavirtual/imagenproducto/', verbose_name=u'Imagen secundaria del producto', blank=True, null=True)

class TemplateBaseSetting(ModeloBase):
    name_system = models.CharField(max_length=500, default='', verbose_name=u'Nombre del Sistema')
    app = models.IntegerField(choices=APP_LABEL_TEMPLATE, default=2, verbose_name=u'Aplicación')
    use_menu_favorite_module = models.BooleanField(default=False, verbose_name=u"Usar modulo favorito")
    use_menu_notification = models.BooleanField(default=False, verbose_name=u"Usar notificación")
    use_menu_user_manual = models.BooleanField(default=False, verbose_name=u"Usar manual de usuario")
    use_api = models.BooleanField(default=False, verbose_name=u"Usar API")

    def __str__(self):
        return f"{self.name_system} - {self.get_app_display()}"

    def es_sga(self):
        return self.app == 1

    def es_sagest(self):
        return self.app == 2

    def save(self, *args, **kwargs):
        self.name_system = self.name_system.strip()
        super(TemplateBaseSetting, self).save(*args, **kwargs)

    class Meta:
        verbose_name = u'Ajuste de Plantilla Base'
        verbose_name_plural = u'Ajustes de Plantilla Base'
        ordering = ('app',)
        unique_together = ('name_system', 'app',)


class MenuFavoriteProfile(ModeloBase):
    setting = models.ForeignKey(TemplateBaseSetting, on_delete=models.CASCADE, verbose_name=u'Ajuste de plantilla')
    profile = models.ForeignKey('administrativo.PerfilUsuario', on_delete=models.CASCADE, verbose_name=u'Perfil Usuario')
    modules = models.ManyToManyField('administrativo.Modulo', verbose_name=u'Modulos')

    def __str__(self):
        return f"{self.setting.__str__()} - {self.profile.persona.__str__()} ({self.profile.__str__()})"

    def tiene_modulos(self):
        return self.modules.values("id").all().exists()

    def mis_modulos_id(self):
        if self.tiene_modulos():
            if self.setting.es_sga():
                return self.modules.filter(activo=True, status=True, sga=True).values_list('id', flat=True).distinct()
            elif self.setting.es_sagest():
                return self.modules.filter(activo=True, status=True, sagest=True).values_list('id',
                                                                                              flat=True).distinct()
            else:
                return None
        return None

    def mis_modulos(self):
        if self.tiene_modulos():
            if self.setting.es_sga():
                return self.modules.filter(activo=True, status=True, sga=True)
            elif self.setting.es_sagest():
                return self.modules.filter(activo=True, status=True, sagest=True)
            else:
                return None
        return None

    def save(self, *args, **kwargs):
        from administrativo.funciones import encrypt
        if self.profile:
            eMenuFavoriteProfilesEnCache = cache.get(f"module_favorites_perfilprincipal_id_{encrypt(self.profile.id)}")
            if not eMenuFavoriteProfilesEnCache is None:
                cache.delete(f"module_favorites_perfilprincipal_id_{encrypt(self.profile.id)}")
        super(MenuFavoriteProfile, self).save(*args, **kwargs)

    class Meta:
        verbose_name = u'Menu Favorito Perfil'
        verbose_name_plural = u'Menus Favorito Perfil'
        ordering = ('setting',)
        unique_together = ('setting', 'profile',)

class IvaAplicado(ModeloBase):
    descripcion = models.CharField(max_length=300, verbose_name=u'Nombre')
    porcientoiva = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'% IVA aplicado')
    codigo = models.IntegerField(default=0, verbose_name=u'Codigo')
    activo = models.BooleanField(default=True, verbose_name=u'Activo')

    def __str__(self):
        return u'%s' % self.descripcion

    class Meta:
        verbose_name = u"IVA aplicado"
        verbose_name_plural = u"IVA aplicados"

    def save(self, *args, **kwargs):
        self.descripcion = self.descripcion.upper().strip()
        super(IvaAplicado, self).save(*args, **kwargs)

class TipoOtroRubro(ModeloBase):
    nombre = models.CharField(default='', max_length=300, verbose_name=u'Nombre')
    valor = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'Valor')
    interface = models.BooleanField(default=False, verbose_name=u'Interface')
    activo = models.BooleanField(default=True, verbose_name=u'Activo')
    ivaaplicado = models.ForeignKey(IvaAplicado, on_delete=models.PROTECT, verbose_name=u'Iva Aplicado')
    requierefactura = models.BooleanField(default=True, verbose_name=u'No Emitir Factura')
    exportabanco = models.BooleanField(default=False, verbose_name=u'Exporta deudas a banco')
    tiporubro = models.IntegerField(choices=TIPO_RUBRO, default=1, verbose_name=u"Tipo de Rubro")

    def __str__(self):
        return u'%s' % (self.nombre)

    class Meta:
        verbose_name = u"Tipo otro rubro"
        verbose_name_plural = u"Tipos otros rubros"
        ordering = ['nombre']
        unique_together = ('nombre',)

    @staticmethod
    def flexbox_query(q, extra=None):
        return TipoOtroRubro.objects.filter(nombre__icontains=q).distinct()

    def flexbox_repr(self):
        return unicode(self.nombre)

    def typefile(self):
        if self.archivo:
            return self.archivo.name[self.archivo.name.rfind("."):]
        else:
            return None

    def en_uso(self):
        if self.rubro_set.exists():
            return True
        return False

    def mi_rubro(self):
        if self.rubro_set.exists():
            return self.rubro_set.all()[0]
        return None

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper().strip()
        super(TipoOtroRubro, self).save(*args, **kwargs)

class Rubro(ModeloBase):
    tipo = models.ForeignKey(TipoOtroRubro, on_delete=models.PROTECT, blank=True, null=True, verbose_name=u"Tipo")
    persona = models.ForeignKey('administrativo.Persona', on_delete=models.PROTECT, verbose_name=u'Cliente')
    relacionados = models.ForeignKey('self', on_delete=models.PROTECT, blank=True, null=True, verbose_name=u'Rubro')
    nombre = models.CharField(max_length=1000, verbose_name=u'Nombre')
    cuota = models.IntegerField(default=0, verbose_name=u'Cuota')
    tipocuota = models.IntegerField(choices=TIPO_CUOTA, default=3)
    fecha = models.DateField(verbose_name=u'Fecha emisión')
    fechavence = models.DateField(verbose_name=u'Fecha vencimiento')
    preciounitario = models.DecimalField(default=0, max_digits=30, decimal_places=2, blank=True, null=True, verbose_name=u'Precio unitario')
    valor = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'Valor')
    iva = models.ForeignKey(IvaAplicado, on_delete=models.PROTECT, verbose_name=u'IVA')
    valoriva = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'Valor IVA')
    valortotal = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'Valor total')
    saldo = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'Saldo')
    cancelado = models.BooleanField(default=False, verbose_name=u'Cancelado')
    observacion = models.TextField(default='', max_length=250, blank=True, null=True, verbose_name=u"Observación")
    valordescuento = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'Valor descuento')
    anulado = models.BooleanField(default=False, verbose_name=u'Anulados')

    def tiene_cantidad(self):
        if self.tipocuota == 4:
            return True
        return False

    def get_pagos(self):
        return self.pago_set.filter(available=True)

    def fechavence_str(self):
        return str(self.fechavence)

    def __str__(self):
        return u'%s' % self.nombre

    class Meta:
        verbose_name = u"Rubro de cobro"
        verbose_name_plural = u"Rubros de cobro"

    @staticmethod
    def flexbox_query(q, extra=None):
        return Rubro.objects.filter(nombre__contains=q).distinct()[:20]

    def flexbox_repr(self):
        return self.nombre

    def tiene_pagos(self):
        return self.pago_set.exists()

    def tiene_factura(self):
        try:
            return self.pago_set.all()[0].factura_set.exists()
        except:
            return False

    def tiene_recibocaja(self):
        try:
            return self.pago_set.all()[0].recibocaja_set.exists()
        except:
            return False

    def factura(self):
        return self.pago_set.all().order_by('-fecha')[0].factura().id

    def valor_total(self):
        return (float(self.valor))

    def valor_iva(self):
        if self.iva.porcientoiva:
            return null_to_decimal((float(self.valor) - null_to_decimal(self.valordescuento, 2)) * null_to_decimal(
                float(self.iva.porcientoiva), 2), 2)
        return 0

    def vencido(self):
        return not self.cancelado and self.fechavence < datetime.now().date()

    def rubro_vencido(self):
        return 'SÍ' if not self.cancelado and self.fechavence < datetime.now().date() else 'NO'

    def futuroavencer(self):
        return not self.cancelado and datetime.now().date() < self.fechavence

    def puede_eliminarse(self):
        return not self.cancelado and not self.pago_set.exists() and not self.rubronotadebito_set.exists()

    def tiene_adeuda(self):
        return self.total_pagado() < self.valor

    def valores_anulados(self):
        return null_to_numeric(
            self.pago_set.filter(factura__valida=False, available=True).aggregate(valor=Sum('valortotal'))['valor'], 2)

    def total_pagado(self):
        return null_to_decimal(
            self.pago_set.filter(status=True).distinct().aggregate(
                valor=Sum('valortotal'))['valor'], 2)

    def adeudado(self):
        return self.valortotal - self.total_pagado()

    def total_adeudado(self):
        sumapagado = null_to_decimal(self.total_pagado(), 2)
        # valornotacredito=null_to_decimal(self.valornotacredito,2)
        # return null_to_decimal((self.valor_total()  - sumapagado) + valornotacredito ,2)
        saldo = null_to_decimal((self.valor_total() - sumapagado), 2)
        try:
            if saldo == 0 and self.cancelado == False:
                self.cancelado = True
                self.save()
            if saldo < 0:
                saldo = 0
        except Exception as ex:
            print(ex)
        return saldo

    def tiene_recibo(self):
        return self.reciborubro_set.exists()

    def recibo(self):
        if self.tiene_recibo():
            return self.reciborubro_set.all()[0]
        return None

    def tiene_recibo_valido(self):
        if self.tiene_recibo():
            recibo = self.reciborubro_set.all()[0]
            return recibo.es_valido()
        return False

    def rubro_devolucion(self):
        return self.tipo_id == 2951

    def nombre_usuario(self):
        if self.usuario_creacion:
            if not self.usuario_creacion.is_superuser:
                return self.usuario_creacion
        return None

    def tiene_promocion(self):
        return (null_to_decimal(self.valordescuento, 2)) > 0

    def descuento_promocion(self):
        if self.tiene_promocion:
            return null_to_decimal(self.valordescuento, 2)
        else:
            return 0

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper().strip()
        self.observacion = self.observacion.upper().strip()
        if not self.id:
            if self.iva.porcientoiva:
                self.valoriva = self.valor_iva()
            else:
                self.valoriva = 0
        self.valortotal = self.valor_total()
        self.saldo = self.total_adeudado()
        if self.valor > 0:
            self.cancelado = (self.saldo == 0)
        super(Rubro, self).save(*args, **kwargs)

    def pedidoonlinependiente(self):
        if self.detallepedidoonline_set.filter(available=True,pedido__estado=1).exists():
            return True
        return False

class PuntoVenta(ModeloBase):
    nombreestablecimiento = models.CharField(default='', max_length=300, verbose_name=u'Nombre')
    establecimiento = models.CharField(default='', max_length=3, verbose_name=u'Establecimiento')
    puntoventa = models.CharField(default='', max_length=3, verbose_name=u'Punto de venta')
    activo = models.BooleanField(default=True, verbose_name=u'Activo')
    facturaelectronica = models.BooleanField(default=False, verbose_name=u'Factura electronica')
    imprimirfactura = models.BooleanField(default=False, verbose_name=u'Imprimir factura')
    direccion = models.CharField(default='', max_length=300, verbose_name=u'Direccion Establecimiento')

    def __str__(self):
        return u'%s - %s - %s' % (self.nombreestablecimiento, self.establecimiento, self.puntoventa)

    class Meta:
        verbose_name_plural = u"Puntos de venta"
        ordering = ['establecimiento']
        unique_together = ('establecimiento', 'puntoventa')

    def numeracion(self):
        return self.establecimiento + '-' + self.puntoventa

    def save(self, *args, **kwargs):
        self.nombreestablecimiento = self.nombreestablecimiento.upper().strip()
        self.establecimiento = self.establecimiento.upper().strip()
        self.puntoventa = self.puntoventa.upper().strip()
        super(PuntoVenta, self).save(*args, **kwargs)

class LugarRecaudacion(ModeloBase):
    persona = models.ForeignKey(Persona, on_delete=models.PROTECT, verbose_name=u'Persona')
    nombre = models.CharField(default='', max_length=100, verbose_name=u'Nombre')
    puntoventa = models.ForeignKey(PuntoVenta, on_delete=models.PROTECT, verbose_name=u'Punto de venta')
    activo = models.BooleanField(default=True, verbose_name=u'Activo')

    class Meta:
        verbose_name = u"Lugar de recaudación"
        verbose_name_plural = u"Lugares de recaudación"
        ordering = ['nombre']

    def __str__(self):
        return u'%s - %s' % (self.nombre, self.persona)

    def flexbox_repr(self):
        return self.persona.__str__()

    def esta_abierta(self):
        return SesionCaja.objects.filter(caja=self, abierta=True).exists()

    def sesion_caja(self):
        if SesionCaja.objects.filter(caja=self, abierta=True, fecha=datetime.now().date()).exists():
            return SesionCaja.objects.filter(caja=self, abierta=True).first()
        return None

    def sesion_fecha(self, fecha):
        if self.sesioncaja_set.filter(fecha=fecha).exists():
            return self.sesioncaja_set.filter(fecha=fecha)
        return None

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper().strip()
        super(LugarRecaudacion, self).save(*args, **kwargs)

class AnioEjercicio(ModeloBase):
    anioejercicio = models.IntegerField(default=0, verbose_name=u"Ejercicio")
    cerrado = models.BooleanField(default=False, verbose_name=u'Cerrado')

    def __str__(self):
        return u"%s" % self.anioejercicio

    @staticmethod
    def flexbox_query(q, extra=None):
        return AnioEjercicio.objects.filter(anioejercicio__icontains=q).distinct()

    def flexbox_repr(self):
        return u"%s" % self.anioejercicio

    def flexbox_alias(self):
        return [self.id, self.anioejercicio]

class SesionCaja(ModeloBase):
    caja = models.ForeignKey(LugarRecaudacion, on_delete=models.PROTECT, verbose_name=u'Caja')
    #anioejercicio = models.ForeignKey(AnioEjercicio, on_delete=models.PROTECT, verbose_name=u'Anio Ejercicio')
    fecha = models.DateField(verbose_name=u'Fecha')
    fondo = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'Fondo inicial')
    abierta = models.BooleanField(default=True, verbose_name=u'Abierta')
    numero = models.IntegerField(default=0, verbose_name=u'Numero arqueo')

    def __str__(self):
        return u'%s - %s' % (self.fecha.strftime("%d-%m-%Y"), self.caja)

    class Meta:
        verbose_name = u"Sesion de recaudación de caja"
        verbose_name_plural = u"Sesiones de recaudación de caja"
        ordering = ['caja', 'fecha']
        unique_together = ('caja', 'fecha',)

    @staticmethod
    def flexbox_query(q, extra=None):
        return SesionCaja.objects.filter(Q(caja__nombre__icontains=q) | Q(caja__persona__apellido1__icontains=q) | Q(
            caja__persona__apellido2__icontains=q) | Q(caja__persona__nombres__icontains=q) | Q(
            caja__persona__cedula__icontains=q)).distinct().order_by('-fecha', '-hora')[:20]

    def flexbox_repr(self):
        return self.caja.nombre + " " + self.fecha.strftime("%d-%m-%Y") + " " + str(self.id)

    def typefile(self):
        if self.archivo:
            return self.archivo.name[self.archivo.name.rfind("."):]
        else:
            return None

    def total_efectivo_recibo_sesion(self):
        return null_to_decimal(
            Pago.objects.filter(sesion=self, efectivo=True, recibocaja__isnull=False).distinct().aggregate(
                valor=Sum('valortotal'))['valor'], 2)

    def total_cheque_sesion(self):
        return null_to_decimal(
            Pago.objects.filter(sesion=self, pagocheque__isnull=False, factura__valida=True).distinct().aggregate(
                valor=Sum('valortotal'))['valor'], 2)

    def total_electronico_sesion(self):
        return null_to_decimal(Pago.objects.filter(sesion=self, pagodineroelectronico__isnull=False,
                                                   factura__valida=True).distinct().aggregate(valor=Sum('valortotal'))[
                                   'valor'], 2)

    def total_cuentasxcobrar_sesion(self):
        return null_to_decimal(Pago.objects.filter(sesion=self, pagocuentaporcobrar__isnull=False,
                                                   factura__valida=True).distinct().aggregate(valor=Sum('valortotal'))[
                                   'valor'], 2)

    def total_tarjeta_sesion(self):
        return null_to_decimal(
            Pago.objects.filter(sesion=self, pagotarjeta__isnull=False, factura__valida=True).distinct().aggregate(
                valor=Sum('valortotal'))['valor'], 2)

    def total_tarjeta_recibo_sesion(self):
        return null_to_decimal(
            Pago.objects.filter(sesion=self, pagotarjeta__isnull=False, recibocaja__isnull=False).distinct().aggregate(
                valor=Sum('valortotal'))['valor'], 2)

    def total_deposito_sesion(self):
        return null_to_decimal(Pago.objects.filter(sesion=self, pagotransferenciadeposito__isnull=False,
                                                   pagotransferenciadeposito__deposito=True,
                                                   factura__valida=True).exclude(
            pagotransferenciadeposito__recaudacionventanilla=True).distinct().aggregate(valor=Sum('valortotal'))[
                                   'valor'], 2)

    def total_deposito_recibo_sesion(self):
        return null_to_decimal(Pago.objects.filter(sesion=self, pagotransferenciadeposito__isnull=False,
                                                   pagotransferenciadeposito__deposito=True,
                                                   recibocaja__isnull=False).exclude(
            pagotransferenciadeposito__recaudacionventanilla=True).distinct().aggregate(valor=Sum('valortotal'))[
                                   'valor'], 2)

    def total_transferencia__recibocaja_sesion(self):
        return null_to_decimal(Pago.objects.filter(sesion=self, pagotransferenciadeposito__isnull=False,
                                                   pagotransferenciadeposito__deposito=False,
                                                   recibocaja__isnull=False).distinct().aggregate(valor=Sum('valortotal'))[
                                   'valor'], 2)

    def get_pagos_sesion(self):
        return Pago.objects.filter(status=True, sesion=self)

    def get_detallesalida_sesion(self):
        return DetalleSalidaRecaudacion.objects.filter(status=True, sesion=self)

    def total_recibocaja_sesion(self):
        return null_to_decimal(ComprobantePago.objects.filter(sesioncaja=self).distinct().aggregate(valor=Sum('valor'))['valor'], 2)

    def total_egresado_recibocaja_sesion(self):
        return null_to_decimal(SalidaRecaudacion.objects.filter(sesioncaja=self).distinct().aggregate(valor=Sum('valor'))['valor'], 2)

    def total_neto_recibocaja_sesion(self):
        return null_to_decimal(self.total_recibocaja_sesion() - self.total_egresado_recibocaja_sesion(), 2)

    def total_transferencia_sesion(self):
        return null_to_decimal(Pago.objects.filter(sesion=self, pagotransferenciadeposito__isnull=False,
                                                   pagotransferenciadeposito__deposito=False,
                                                   factura__valida=True).distinct().aggregate(valor=Sum('valortotal'))[
                                   'valor'], 2)

    def total_pagobecas(self):
        return null_to_decimal(Pago.objects.filter(sesion=self, pagobecas__isnull=False,
                               factura__valida=True).distinct().aggregate(valor=Sum('valortotal'))['valor'], 2)

    def total_notas_credito_sesion(self):
        return null_to_decimal(
            Pago.objects.filter(sesion=self, pagonotacredito__isnull=False, factura__valida=True).distinct().aggregate(
                valor=Sum('valortotal'))['valor'], 2)

    def cierre_sesion(self):
        if self.recaudacionfinalsesioncaja_set.exists():
            return self.recaudacionfinalsesioncaja_set.all().first()
        return None

    def save(self, *args, **kwargs):
        super(SesionCaja, self).save(*args, **kwargs)

class Banco(ModeloBase):
    nombre = models.CharField(default='', max_length=800, verbose_name=u'Nombre')
    tasaprotesto = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'Banco')
    codigo = models.CharField(max_length=10, default="", verbose_name=u"Código")
    codigoinstitucion = models.CharField(max_length=300, default="", verbose_name=u"Codigo institucion", blank=True, null=True)
    foto = models.FileField(upload_to='bancos', blank=True, null=True, verbose_name=u'Foto')
    imagen = models.ImageField(upload_to='bancos/iconos',verbose_name=u'Banco icono', blank=True, null=True)
    referencia = models.ImageField(upload_to='bancos/referencia',verbose_name=u'Banco referencia transferencia', blank=True, null=True)
    referenciadeposito = models.ImageField(upload_to='bancos/referencia',verbose_name=u'Banco referencia deposito', blank=True, null=True)
    textreferencia = models.CharField(max_length=200,verbose_name=u"Referencia transferencia", null=True, blank=True)
    textreferenciadeposito = models.CharField(max_length=200,verbose_name=u"Referencia deposito", null=True, blank=True)

    def __str__(self):
        return u'%s' % self.nombre

    class Meta:
        verbose_name = u"Banco"
        verbose_name_plural = u"Bancos"
        ordering = ['nombre']
        unique_together = ('nombre',)

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper().strip()
        self.codigo = self.codigo.upper().strip()
        super(Banco, self).save(*args, **kwargs)

class TipoCuentaBanco(ModeloBase):
    nombre = models.CharField(default='', max_length=100, verbose_name=u'Nombre')
    codigo = models.CharField(max_length=10, default="", verbose_name=u"Código")

    def __str__(self):
        return u'%s' % self.nombre

    class Meta:
        verbose_name = u"Tipo cuenta banco"
        verbose_name_plural = u"Tipos de cuentas de banco"
        ordering = ['nombre']
        unique_together = ('nombre',)

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper().strip()
        self.codigo = self.codigo.upper().strip()
        super(TipoCuentaBanco, self).save(*args, **kwargs)

class CuentaBanco(ModeloBase):
    banco = models.ForeignKey(Banco, on_delete=models.PROTECT, verbose_name=u'Banco')
    tipocuenta = models.ForeignKey(TipoCuentaBanco, on_delete=models.PROTECT, verbose_name=u'Tipo cuenta banco')
    numero = models.CharField(default='', max_length=50, verbose_name=u'Numero')
    representante = models.CharField(default='', max_length=100, verbose_name=u'Representante')
    saldo = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'Saldo')
    saldoinicial = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'Saldo')
    anio = models.IntegerField(default=2018, verbose_name=u"Año Inicio")
    mes = models.IntegerField(default=1, verbose_name=u"Mes Inicio")

    #DATOS EXTRAS
    excluir = models.BooleanField(default=False, verbose_name=u'Excluir cuenta')
    tipodocumento = models.IntegerField(choices=TIPO_IDENTIFICACION, default=1, blank=True, null=True)
    documento =  models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return u'%s - Cta:%s - #:%s' % (self.banco, self.tipocuenta, self.numero)

    class Meta:
        verbose_name = u"Cuenta de banco"
        verbose_name_plural = u"Cuentas bancarias"
        ordering = ['numero']
        unique_together = ('banco', 'tipocuenta', 'numero')

    @staticmethod
    def flexbox_query(q, extra=None):
        return CuentaBanco.objects.filter(numero__icontains=q).distinct()[:20]

    def flexbox_repr(self):
        return self.banco.nombre + " - " + self.tipocuenta + " - " + self.numero

    # def actualiza_saldo(self, request):
    #     self.saldo = null_to_decimal(self.detalleconciliacion_set.aggregate(valor=Sum('valor'))['valor'], 2)
    #     self.save(request)

    def total_recaudado(self, fecha):
        if self.recaudacionbanco_set.filter(fecha=convertir_fecha(fecha)).exists():
            recaudacion = self.recaudacionbanco_set.filter(fecha=convertir_fecha(fecha))[0]
            return recaudacion.valor
        return 0

    def save(self, *args, **kwargs):
        self.representante = self.representante.upper().strip()
        super(CuentaBanco, self).save(*args, **kwargs)

    def get_logo(self):
        if self.banco.imagen:
            return self.banco.imagen.url
        return ''

    def get_referencia_trans(self):
        if self.banco.referencia:
            return self.banco.referencia.url
        return ''

    def get_referencia_dep(self):
        if self.banco.referenciadeposito:
            return self.banco.referenciadeposito.url
        return ''

class Pago(ModeloBase):
    sesion = models.ForeignKey(SesionCaja, on_delete=models.PROTECT, blank=True, null=True, verbose_name=u'Sesion de caja')
    rubro = models.ForeignKey(Rubro, on_delete=models.PROTECT, verbose_name=u'Rubros')
    fecha = models.DateField(verbose_name=u'Fecha')
    preciounitario = models.DecimalField(default=0, max_digits=30, decimal_places=2, blank=True, null=True, verbose_name=u'Precio unitario')
    subtotal0 = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'Valor')
    subtotaliva = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'Valor')
    iva = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'IVA')
    valordescuento = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'Valor Total')
    valortotal = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'Valor Total')
    subtotal0_anterior = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'Valor anterior', blank=True, null=True)
    subtotaliva_anterior = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'Valor anterior', blank=True, null=True)
    iva_anterior = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'IVA anterior', blank=True, null=True)
    valordescuento_anterior = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'Valor Total anterior', blank=True, null=True)
    valortotal_anterior = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'Valor que tuvo antes de generar la nota de crédito', blank=True, null=True)
    efectivo = models.BooleanField(default=True, verbose_name=u'Pago en efectivo')
    archivo = models.FileField(upload_to='pagotransferenciadeposito/', blank=True, null=True,
                               verbose_name=u'Archivo Papeleta Banco')
    secuencia = models.IntegerField(default=1, verbose_name=u'Secuencia')

    def __str__(self):
        return u'Pago $%s' % self.valortotal

    class Meta:
        verbose_name = u"Pago"
        verbose_name_plural = u"Pagos"
        ordering = ['fecha']
        unique_together = ('fecha', 'rubro', 'valortotal')
        # unique_together = ('fecha','fecha_creacion','rubro' )

    def get_preciounitario(self):
        if self.preciounitario:
            return self.preciounitario
        elif self.subtotal0:
            return self.subtotal0
        return self.subtotaliva

    def subtotal(self):
        return self.subtotaliva if self.iva else self.subtotal0

    def total_sinimpuesto(self):
        return Decimal(self.subtotal0 + self.subtotaliva).quantize(Decimal('.01'))

    def tipo(self):
        if self.es_tarjeta():
            return "TARJETA"
        elif self.es_cheque():
            return "CHEQUE"
        elif self.es_deposito():
            return "DEPOSITO"
        elif self.es_transferencia():
            return "TRANSFERENCIA"
        elif self.es_electronico():
            return "DINERO ELECTRONICO"
        elif self.es_liquidacion():
            return "LIQUIDACION"
        elif self.es_cuentaporcobrar():
            return "CUENTAXCOBRAR"
        elif self.es_notacredito():
            return "NOTACREDITO"
        elif self.es_beca():
            return "BECAS"
        else:
            return "EFECTIVO"

    def formapagoid(self):
        if self.es_tarjeta():
            return 3
        elif self.es_cheque():
            return 2
        elif self.es_deposito():
            return 4
        elif self.es_transferencia():
            return 5
        elif self.es_electronico():
            return 6
        elif self.es_liquidacion():
            return 8
        elif self.es_cuentaporcobrar():
            return 7
        elif self.es_notacredito():
            return 9
        elif self.es_beca():
            return 10
        else:
            return 1

    def relacionado(self):
        if self.es_tarjeta():
            return self.pagotarjeta_set.all()[0]
        elif self.es_cheque():
            return self.pagocheque_set.all()[0]
        elif self.es_electronico():
            return self.pagodineroelectronico_set.all()[0]
        elif self.es_liquidacion():
            return self.pagoliquidacion_set.all()[0]
        elif self.es_cuentaporcobrar():
            return self.pagocuentaporcobrar_set.all()[0]
        elif self.es_deposito() or self.es_transferencia():
            return self.pagotransferenciadeposito_set.all()[0]
        elif self.es_notacredito():
            return self.pagonotacredito_set.all()[0]
        elif self.es_beca():
            return self.pagobecas_set.all()[0]
        return None

    def es_chequevista(self):
        if self.relacionado():
            return self.relacionado().a_vista()
        return None

    def es_tarjeta(self):
        return self.pagotarjeta_set.exists()

    def es_chequepostfechado(self):
        return not self.relacionado().a_vista() if self.relacionado() else None

    def es_cheque(self):
        return self.pagocheque_set.exists()

    def es_transferencia(self):
        return self.pagotransferenciadeposito_set.filter(deposito=False).exists()

    def es_deposito(self):
        return self.pagotransferenciadeposito_set.filter(deposito=True).exists()

    def deposito(self):
        return self.pagotransferenciadeposito_set.filter(deposito=True)[0] if self.es_deposito() else None

    def es_electronico(self):
        return self.pagodineroelectronico_set.exists()

    def es_liquidacion(self):
        return self.pagoliquidacion_set.exists()

    def liquidacion(self):
        if self.pagoliquidacion_set.exists():
            return self.pagoliquidacion_set.filter(available=True)[0]

    def es_cuentaporcobrar(self):
        return self.pagocuentaporcobrar_set.exists()

    def es_notacredito(self):
        return self.pagonotacredito_set.exists()

    def es_beca(self):
        return self.pagobecas_set.exists()

    def factura(self):
        if self.factura_set.exists():
            return self.factura_set.all()[0]
        return None

    def recibo(self):
        if self.recibocaja_set.exists():
            return self.recibocaja_set.all()[0]
        return None

class SecuenciaSesionCaja(ModeloBase):
    #anioejercicio = models.ForeignKey(AnioEjercicio, on_delete=models.PROTECT, verbose_name=u'Anio Ejercicio')
    secuenciacaja = models.IntegerField(default=0, verbose_name=u'Secuencia Caja')

class FormaDePago(ModeloBase):
    nombre = models.CharField(default='', max_length=100, verbose_name=u'Nombre')

    def __str__(self):
        return u'%s' % (self.nombre)

    class Meta:
        verbose_name = u"Forma de pago"
        verbose_name_plural = u"Formas de pago"
        ordering = ['nombre']
        unique_together = ('nombre',)

    @staticmethod
    def flexbox_query(q, extra=None):
        if ' ' in q:
            s = q.split(" ")
            return FormaDePago.objects.filter(nombre__contains=s[0]).distinct()[:25]
        return FormaDePago.objects.filter(nombre__contains=q).distinct()[:25]

    def flexbox_repr(self):
        return self.nombre + " - " + self.id.__str__()

    def flexbox_alias(self):
        return [self.nombre]

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper().strip()
        super(FormaDePago, self).save(*args, **kwargs)

class ComprobantePago(ModeloBase):
    puntoventa = models.ForeignKey(PuntoVenta, on_delete=models.PROTECT, verbose_name=u"Punto Venta", blank=True, null=True)
    sesioncaja = models.ForeignKey(SesionCaja, on_delete=models.PROTECT, verbose_name=u'Sesión de caja')
    persona = models.ForeignKey(Persona, on_delete=models.PROTECT, verbose_name=u"Persona Entrega")
    numero = models.IntegerField(default=0, verbose_name=u"Numero")
    numerocompleto = models.CharField(default='', max_length=20, verbose_name=u"Numero Completo")
    concepto = models.TextField(default='', verbose_name=u'Concepto')
    valor = models.DecimalField(default='0', max_digits=30, decimal_places=2, verbose_name=u'Valor')
    pagos = models.ManyToManyField(Pago, blank=True, verbose_name=u"Pagos")

    def __str__(self):
        return u'Recibo de caja $%s' % self.valor

    class Meta:
        verbose_name = u"Recibo de caja"
        verbose_name_plural = u"Recibos de caja"
        #ordering = ['persona']

    def save(self, *args, **kwargs):
        self.concepto = self.concepto.upper().strip()
        super(ComprobantePago, self).save(*args, **kwargs)


class SalidaRecaudacion(ModeloBase):
    puntoventa = models.ForeignKey(PuntoVenta, on_delete=models.PROTECT, verbose_name=u"Punto Venta", blank=True, null=True)
    sesioncaja = models.ForeignKey(SesionCaja, on_delete=models.PROTECT, verbose_name=u'Sesión de caja')
    numero = models.IntegerField(default=0, verbose_name=u"Numero")
    numerocompleto = models.CharField(default='', max_length=20, verbose_name=u"Numero Completo")
    concepto = models.TextField(default='', verbose_name=u'Concepto')
    valor = models.DecimalField(default='0', max_digits=30, decimal_places=2, verbose_name=u'Valor')

    def __str__(self):
        return u'Salida de dinero $%s' % self.valor

    class Meta:
        verbose_name = u"Salida recaudación"
        verbose_name_plural = u"Salidas recaudación"
        #ordering = ['persona']

    def save(self, *args, **kwargs):
        self.concepto = self.concepto.upper().strip()
        super(SalidaRecaudacion, self).save(*args, **kwargs)


class DetalleSalidaRecaudacion(ModeloBase):
    salida = models.ForeignKey(SalidaRecaudacion, on_delete=models.PROTECT, blank=True, null=True, verbose_name=u'Salida recaudación')
    sesion = models.ForeignKey(SesionCaja, on_delete=models.PROTECT, blank=True, null=True, verbose_name=u'Sesion de caja')
    fecha = models.DateField(verbose_name=u'Fecha')
    concepto = models.TextField(default='', verbose_name=u'Concepto')
    valor = models.DecimalField(default=0, max_digits=30, decimal_places=2, blank=True, null=True, verbose_name=u'Precio unitario')


class SecuencialRecaudaciones(ModeloBase):
    puntoventa = models.ForeignKey(PuntoVenta, on_delete=models.PROTECT, verbose_name=u'Punto e venta')
    factura = models.IntegerField(default=0, verbose_name=u'Secuencia Factura')
    comprobante = models.IntegerField(default=0, verbose_name=u'Secuencia Comprobantes')
    salidarecaudacion = models.IntegerField(default=1, verbose_name=u'Secuencia salida recaudación')
    cajero = models.IntegerField(default=1, verbose_name=u'Secuencia Cajero')

    def ultimafactura(self):
        ultimafactura = self.puntoventa.factura_set.filter(status=True).order_by('-id')
        return ultimafactura.first()

    class Meta:
        verbose_name = u"Secuencia de recaudacion"
        verbose_name_plural = u"Secuencias de recaudaciones"

    def save(self, *args, **kwargs):
        super(SecuencialRecaudaciones, self).save(*args, **kwargs)

class RecaudacionFinalSesionCaja(ModeloBase):
    sesion = models.ForeignKey(SesionCaja, on_delete=models.PROTECT, verbose_name=u'Sesion de caja')
    total = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'Total')
    comprobante = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'Total comprobantes')
    salidarecaudacion = models.DecimalField(default=0, max_digits=30, decimal_places=2, verbose_name=u'Total salida de efectivo')
    fecha = models.DateField(blank=True, null=True, verbose_name=u'Fecha')

    def __str__(self):
        return u'Total recaudado: %s' % self.sesion

    class Meta:
        verbose_name = u"Resumen cierre de sesion de caja"
        verbose_name_plural = u"Resumenes cierre de sesion de caja"
        unique_together = ('sesion',)

    def save(self, *args, **kwargs):
        super(RecaudacionFinalSesionCaja, self).save(*args, **kwargs)


class Perms(models.Model):
    class Meta:
        permissions = (
            ("puede_eliminar_grupos", "Puede eliminar grupos"),
            ("puede_eliminar_stock", "Puede eliminar stock"),
        )

