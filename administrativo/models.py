#IMPORTACIÓN DJANGO
from django.db import models
from django.db.models.functions import Coalesce
from django.db.models import Sum, F, FloatField
from django.contrib.auth.models import User, Group
from administrativo.choices import *
from django.utils import timezone
from django.core.cache import cache

#IMPORTACIÓN SGA
from administrativo.funciones import ModeloBase


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

    def crear_perfil(self, administrativo=None, cliente=None):
        if administrativo:
            perfil = PerfilUsuario(persona=self, administrativo=administrativo)
            perfil.save()
        elif cliente:
            perfil = PerfilUsuario(persona=self, cliente=cliente)
            perfil.save()

    def creacion_persona(self, nombresistema,persona):
        lista = ['sistemas@epunemi.gob.ec']
        perfil = PerfilUsuario.objects.filter(persona=self).order_by('-id')[0]
        send_html_mail("Creación de Persona",
                       "emails/creacionpersona.html",
                       {'sistema': nombresistema, 'd': self, 'perfil': perfil, 't': miinstitucion(),'persona':persona},
                       lista, [], coneccion=conectar_cuenta(CUENTAS_CORREOS[4][1]))

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
        if self.lugarrecaudacion_set.filter(origenrecaudacion=1).values("id").exists():
            return self.lugarrecaudacion_set.filter(origenrecaudacion=1)[0]
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
        
class PerfilUsuario(ModeloBase):
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE)
    administrativo = models.ForeignKey(Administrativo, blank=True, null=True, verbose_name=u'Administrativo', on_delete=models.CASCADE)
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


