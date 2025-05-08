from administrativo.custom_forms import FormModeloBase
from django import forms
from administrativo.funciones import ExtFileField
from django.forms.widgets import FileInput,DateTimeInput, CheckboxInput
from administrativo.models import *

from datetime import datetime

class MiPerfilUsuarioForm(FormModeloBase):
    telefono = forms.CharField(label=u"Teléfono", max_length=10, required=True, widget=forms.TextInput(attrs={'maxlength': '10',  'col': '6',  'onKeyPress': "return soloNumeros(event)"}))
    email = forms.CharField(label=u"Correo electronico", max_length=240, required=True, widget=forms.TextInput(attrs={'col': '6'}))
    nacimiento = forms.DateField(label=u"F. Nacimiento", initial=datetime.now().date(), required=True, widget=DateTimeInput({'col': '6'}))
    pais = forms.ModelChoiceField(label=u"País residencia", queryset=Pais.objects.filter(status=True), required=True, widget=forms.Select(attrs={'col': '6',}))
    provincia = forms.ModelChoiceField(label=u"Provincia residencia", queryset=Provincia.objects.filter(status=True), required=True, widget=forms.Select(attrs={'col': '6'},))
    canton = forms.ModelChoiceField(label=u"Canton residencia", queryset=Ciudad.objects.filter(status=True), required=True,  widget=forms.Select(attrs={'col': '6'},))
    direccion = forms.CharField(label=u"Dirección", widget=forms.Textarea(attrs={'rows': '5'}), required=True)

class AddProductoForm(FormModeloBase):
    nombre = forms.CharField(label=u'Nombre del producto', max_length=3000, required=True, widget=forms.TextInput(attrs={'col': '6', 'placeholder': 'Ingrese el nombre del producto...'}))
    #subcategoria = forms.ModelChoiceField(queryset=SubCategoriaProducto.objects.filter(status=True), required=False, label=u'SubCategoría', widget=forms.Select(attrs={'col': '4'}))
    precio = forms.DecimalField(label=u'Precio', max_digits=30, decimal_places=16, required=True, widget=forms.NumberInput(attrs={'col': '6', 'placeholder': 'Ingrese el precio del producto...'}))
    descripcion = forms.CharField(label=u'Descripción del producto', required=False,widget=forms.Textarea(attrs={'rows': '3', 'placeholder': 'Describa el producto...'}))
    imagenprincipal = ExtFileField(label=u'Imagen', required=False,help_text=u'Tamaño Maximo permitido 10Mb, en formato jpg, jpeg, png', ext_whitelist=(".jpg", ".jpeg", ".png"), max_upload_size=10485760, widget=FileInput({'accept':' image/jpeg, image/jpg, image/png'}))

    vigente = forms.BooleanField(label=u'Vigente', required=False, initial=True)
    def __str__(self):
        return u'%s' % self.nombre

    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'imagenprincipal', 'tiporubro', 'subcategoria', 'tipo', 'color', 'talla', 'material', 'stock', 'precio', 'vigente']

class ImportarProductoForm(FormModeloBase):
    archivo = ExtFileField(label=u'Archivo', required=False,help_text=u'Tamaño Maximo permitido 10Mb, en formato excel', ext_whitelist=(".xlx", ".xlsx", ".xlxs"), max_upload_size=10485760, widget=FileInput({}))

class ImportarPacienteForm(FormModeloBase):
    archivo = ExtFileField(label=u'Archivo', required=False,help_text=u'Tamaño Maximo permitido 10Mb, en formato excel', ext_whitelist=(".xlx", ".xlsx", ".xlxs"), max_upload_size=10485760, widget=FileInput({}))

class AddDescripcionForm(FormModeloBase):
    descripcion = forms.CharField(label=u'Descripción', max_length=800, widget=forms.TextInput(attrs={'class': 'imp-100'}), required=True)

class AddSubCategoriaForm(FormModeloBase):
    descripcion = forms.CharField(label=u'Descripción', max_length=800, widget=forms.TextInput(attrs={'class': 'imp-100'}), required=True)
    categoria = forms.ModelChoiceField(queryset=CategoriaProducto.objects.filter(status=True), required=True,label=u'Categoría',widget=forms.Select(attrs={'col': '12'}))
    imagen = ExtFileField(label=u'Imagen', required=False,help_text=u'Tamaño Maximo permitido 10Mb, en formato jpg, jpeg, png', ext_whitelist=(".jpg", ".jpeg", ".png"), max_upload_size=10485760, widget=FileInput({'accept':' image/jpeg, image/jpg, image/png'}))

class EspecificacionProductoForm(FormModeloBase):
    producto = forms.CharField(label=u'Producto', max_length=800, required=False, widget=forms.TextInput(attrs={'col': '4', 'disabled': 'disabled'}))
    tipoespecificacion = forms.ModelChoiceField(queryset=TipoEspecificacion.objects.filter(status=True), required=False, label=u'Tipo de Especificación', widget=forms.Select(attrs={'col': '4'}))
    valor = forms.CharField(label=u'Valor de la Especificación', max_length=800, required=False, widget=forms.TextInput(attrs={'col': '4', 'placeholder': 'Ingrese el valor de la especificación...'}))
    orden = forms.IntegerField(label=u'Orden', initial=1, required=False, widget=forms.TextInput(attrs={'col': '4', 'placeholder': 'Ingrese el orden del valor'}))

class AddStockForm(FormModeloBase):
    producto = forms.ModelChoiceField(queryset=Producto.objects.filter(status=True, vigente=True), required=True, label=u'Producto', widget=forms.Select(attrs={'col': '6'}))
    cantidad = forms.IntegerField(label=u'Cantidad', initial=0, required=True, widget=forms.TextInput(attrs={'col': '6', 'decimal': '0'}))
    #especificaciones = forms.ModelMultipleChoiceField(label=u'Especificaciones', queryset=EspecificacionProducto.objects.filter(status=True), required=True)

class AddPromocionForm(FormModeloBase):
    producto = forms.ModelChoiceField(queryset=Producto.objects.filter(status=True, vigente=True), required=True, label=u'Producto', widget=forms.Select(attrs={'col': '12'}))
    fecha_inicio = forms.DateField(label=u"F. Inicio", initial=datetime.now().date(), required=True, widget=DateTimeInput({'col': '6'}))
    fecha_vencimiento = forms.DateField(label=u"F. Vencimiento", initial=datetime.now().date(), required=True, widget=DateTimeInput({'col': '6'}))
    estado = forms.BooleanField(label=u'Estado', required=False, initial=True, widget=CheckboxInput(attrs={'col': '12'}))
    # cantidad_total = forms.IntegerField(label=u'Cantidad', initial=0, required=True, widget=forms.TextInput(attrs={'col': '6', 'decimal': '0'}))
    #tipo_promocion = forms.ChoiceField(label=u'Tipo de Promoción', choices=TIPO_PROMOCION, widget=forms.Select(attrs={'col': '6'}), required=True)
    descuento_porcentual = forms.DecimalField(label=u'Descuento Porcentual', max_digits=5, decimal_places=2, required=False, widget=forms.NumberInput(attrs={'col': '6', 'placeholder': 'Descuento porcentual (%)...'}))
    descuento_fijo = forms.DecimalField(label=u'Descuento Fijo', max_digits=30, decimal_places=2, required=False, widget=forms.NumberInput(attrs={'col': '6', 'placeholder': 'Descuento fijo ($)...'}))
    regalo = forms.BooleanField(label=u'Regalo', required=False, initial=True, widget=CheckboxInput(attrs={'col': '6', 'data-switchery':True}))

class ImagenesProductoForm(forms.ModelForm):
    class Meta:
        model = ImagenProducto
        fields = ['imagen']
        widgets = {
            'imagen': forms.ClearableFileInput(attrs={'multiple': False})
        }

class ImagenProductoForm(forms.ModelForm):
    class Meta:
        model = ImagenProducto
        fields = ['imagen']
        widgets = {
            'imagen': forms.ClearableFileInput()
        }

class SubirArchivo(FormModeloBase):
    archivo = ExtFileField(label=u'Archivo', required=True, help_text=u'Tamaño Maximo permitido 4Mb, en formato jpg, png, jpeg', ext_whitelist=(".jpg", ".png", ".jpeg"), max_upload_size=16194304, widget=forms.FileInput(attrs={'class': 'dropify', 'col': '12'}))

class RegistroForm(FormModeloBase):
    cedula = forms.CharField(label=u"Cédula", max_length=10, required=True, widget=forms.TextInput(attrs={'col': '6',  'onKeyPress': "return soloNumeros(event)"}))
    passsena = forms.CharField(label=u"Contraseña", max_length=500, required=True, widget=forms.PasswordInput(attrs={'col': '6', 'autocomplete': 'off'}))
    nombres = forms.CharField(label=u"Nombres", max_length=500, required=True, widget=forms.TextInput(attrs={'col': '12'}))
    apellido1 = forms.CharField(label=u"1er Apellido", max_length=500, required=True, widget=forms.TextInput(attrs={'col': '6'}))
    apellido2 = forms.CharField(label=u"2do Apellido", max_length=500, required=True,  widget=forms.TextInput(attrs={'col': '6'}))
    telefono = forms.CharField(label=u"Teléfono", max_length=10, required=True, widget=forms.TextInput(attrs={'maxlength': '10',  'col': '6',  'onKeyPress': "return soloNumeros(event)"}))
    email = forms.CharField(label=u"Correo Electronico", max_length=240, required=True, widget=forms.TextInput(attrs={'col': '6'}))
    pais = forms.ModelChoiceField(label=u"País residencia", queryset=Pais.objects.filter(status=True), required=True, widget=forms.Select(attrs={'col': '6'}))
    provincia = forms.ModelChoiceField(label=u"Provincia residencia", queryset=Provincia.objects.filter(status=True), required=True, widget=forms.Select(attrs={'col': '6'}))
    canton = forms.ModelChoiceField(label=u"Canton residencia", queryset=Ciudad.objects.filter(status=True), required=True,  widget=forms.Select(attrs={'col': '12'}))
    direccion = forms.CharField(label=u"Dirección", max_length=100, required=True, widget=forms.TextInput(attrs={}))

class AdministrativosForm(FormModeloBase):
    nombres = forms.CharField(label=u"Nombres", max_length=1000, widget=forms.TextInput(attrs={'class':'form-control','col': '12'}))
    apellido1 = forms.CharField(label=u"1er Apellido", max_length=1000, widget=forms.TextInput(attrs={'class':'form-control', 'col': '6'}))
    apellido2 = forms.CharField(label=u"2do Apellido", max_length=1000, required=True,
                                widget=forms.TextInput(attrs={'class':'form-control', 'col': '6'}))
    identificacion = forms.CharField(label=u"Identificación", max_length=13, required=True,
                             widget=forms.TextInput(attrs={'class': 'imp-identificacion form-control', 'col': '6'}))
    nacionalidad = forms.CharField(label=u"Nacionalidad", max_length=100, required=True,
                                   widget=forms.TextInput(attrs={'class': 'form-control', 'col': '12'}))
    nacimiento = forms.DateField(label=u"Fecha Nacimiento", initial=datetime.now().date(),
                                 widget=DateTimeInput(format='%d-%m-%Y', attrs={'class': 'selectorfecha form-control', 'col': '6'}),
                                 required=True)
    sexo = forms.ModelChoiceField(label=u"Sexo", queryset=Sexo.objects.filter(status=True),
                                  widget=forms.Select(attrs={'class':'form-control', 'col': '6'}))
    telefono = forms.CharField(label=u"Teléfono Movil", max_length=100, required=True,
                               widget=forms.TextInput(attrs={'class': 'imp-25 form-control', 'col': '6'}))
    telefono_conv = forms.CharField(label=u"Teléfono Fijo", max_length=100, required=False,
                                    widget=forms.TextInput(attrs={'class': 'imp-25 form-control', 'col': '6'}))
    email = forms.CharField(label=u"Correo Electronico", max_length=1000, required=True,
                            widget=forms.TextInput(attrs={'class': 'imp-50 form-control'}))
    pais = forms.ModelChoiceField(label=u"País residencia", queryset=Pais.objects.all(), required=False,
                                  widget=forms.Select(attrs={'class': 'form-control', 'col': '12'}))
    provincia = forms.ModelChoiceField(label=u"Provincia residencia", queryset=Provincia.objects.all(), required=False,
                                       widget=forms.Select(attrs={'class': 'form-control', 'col': '12'}))
    ciudad = forms.ModelChoiceField(label=u"Canton residencia", queryset=Ciudad.objects.all(), required=False,
                                    widget=forms.Select(attrs={'class': 'form-control', 'col': '12'}))
    parroquia = forms.ModelChoiceField(label=u"Parroquia residencia", queryset=Parroquia.objects.all(), required=False,
                                       widget=forms.Select(attrs={'class': 'form-control', 'col': '12'}))
    sector = forms.CharField(label=u"Sector", max_length=1000, required=False,
                             widget=forms.TextInput(attrs={'class': 'imp-50 form-control'}))
    direccion = forms.CharField(label=u"Calle Principal", max_length=1000, required=False,
                                widget=forms.TextInput(attrs={'class': 'imp-75 form-control'}))
    direccion2 = forms.CharField(label=u"Calle Secundaria", max_length=1000, required=False,
                                 widget=forms.TextInput(attrs={'class': 'imp-75 form-control'}))
    numeroresidencia = forms.CharField(label=u"Numero Domicilio", max_length=1000, required=False,
                                    widget=forms.TextInput(attrs={'class': 'imp-25 form-control'}))
    referencia = forms.CharField(label=u"Referencia", max_length=1000, required=False,
                                widget=forms.TextInput(attrs={'class': 'imp-75 form-control'}))


    pais = forms.ModelChoiceField(label=u"País nacimiento", queryset=Pais.objects.all(), required=False,
                                            widget=forms.Select(attrs={'class':'form-control', 'col': '12'}))
    provincia = forms.ModelChoiceField(label=u"Provincia nacimiento", queryset=Provincia.objects.all(),
                                                 required=False, widget=forms.Select(attrs={'class':'form-control', 'col': '12'}))
    ciudad = forms.ModelChoiceField(label=u"Canton nacimiento", queryset=Ciudad.objects.all(), required=False,
                                              widget=forms.Select(attrs={'class':'form-control', 'col': '12'}))
    parroquianacimiento = forms.ModelChoiceField(label=u"Parroquia nacimiento", queryset=Parroquia.objects.all(),
                                                 required=False, widget=forms.Select(attrs={'class':'form-control', 'col': '12'}))

class PacientesForm(FormModeloBase):
    nombres = forms.CharField(label=u"Nombres", max_length=1000, widget=forms.TextInput(attrs={'class':'form-control','col': '12'}))
    apellido1 = forms.CharField(label=u"1er Apellido", max_length=1000, widget=forms.TextInput(attrs={'class':'form-control', 'col': '6'}))
    apellido2 = forms.CharField(label=u"2do Apellido", max_length=1000, required=True,
                                widget=forms.TextInput(attrs={'class':'form-control', 'col': '6'}))
    identificacion = forms.CharField(label=u"Identificación", max_length=13, required=True,
                             widget=forms.TextInput(attrs={'class': 'imp-identificacion form-control', 'col': '6'}))
    nacionalidad = forms.CharField(label=u"Nacionalidad", max_length=100, required=True,
                                   widget=forms.TextInput(attrs={'class': 'form-control', 'col': '12'}))
    nacimiento = forms.DateField(label=u"Fecha Nacimiento", initial=datetime.now().date(),
                                 widget=DateTimeInput(format='%d-%m-%Y', attrs={'class': 'selectorfecha form-control', 'col': '6'}),
                                 required=True)
    sexo = forms.ModelChoiceField(label=u"Sexo", queryset=Sexo.objects.filter(status=True),
                                  widget=forms.Select(attrs={'class':'form-control', 'col': '6'}))
    telefono = forms.CharField(label=u"Teléfono Movil", max_length=100, required=True,
                               widget=forms.TextInput(attrs={'class': 'imp-25 form-control', 'col': '6'}))
    telefono_conv = forms.CharField(label=u"Teléfono Fijo", max_length=100, required=False,
                                    widget=forms.TextInput(attrs={'class': 'imp-25 form-control', 'col': '6'}))
    email = forms.CharField(label=u"Correo Electronico", max_length=1000, required=False,
                            widget=forms.TextInput(attrs={'class': 'imp-50 form-control'}))
    sector = forms.CharField(label=u"Sector", max_length=1000, required=False,
                             widget=forms.TextInput(attrs={'class': 'imp-50 form-control'}))
    direccion = forms.CharField(label=u"Calle Principal", max_length=1000, required=False,
                                widget=forms.TextInput(attrs={'class': 'imp-75 form-control'}))
    direccion2 = forms.CharField(label=u"Calle Secundaria", max_length=1000, required=False,
                                 widget=forms.TextInput(attrs={'class': 'imp-75 form-control'}))
    numeroresidencia = forms.CharField(label=u"Numero Domicilio", max_length=1000, required=False,
                                    widget=forms.TextInput(attrs={'class': 'imp-25 form-control'}))
    referencia = forms.CharField(label=u"Referencia", max_length=1000, required=False,
                                widget=forms.TextInput(attrs={'class': 'imp-75 form-control'}))

class GrupoUsuarioForm(forms.Form):
    grupo = forms.ModelChoiceField(label=u'Grupo', queryset=Group.objects.all().order_by('name'), required=False, widget=forms.Select(attrs={'class': 'imp-100'}))

    def grupos(self, lista):
        self.fields['grupo'].queryset = lista

class GrupoUsuarioMultipleForm(forms.Form):
    grupo = forms.ModelMultipleChoiceField(label=u'Grupo', queryset=Group.objects.all().order_by('name'), required=False)

    def grupos(self, lista):
        self.fields['grupo'].queryset = lista

class ModuloCategoriaForm(forms.Form):
    orden = forms.IntegerField(initial=0, required=True, label=u'Orden',
                                        widget=forms.TextInput(attrs={'formwidth': '100%'}))
    nombre = forms.CharField(label=u"Nombre", max_length=100, required=True,
                                   widget=forms.TextInput(attrs={'formwidth': '100%'}))
    icono = forms.CharField(label=u"Url del icono", max_length=100, required=True,
                             widget=forms.TextInput(attrs={'formwidth': '100%'}))


class ModuloForm(forms.Form):
    orden = forms.IntegerField(initial=0, required=True, label=u'Orden',
                                        widget=forms.TextInput(attrs={'formwidth': '100%'}))
    url = forms.CharField(label=u"Url", max_length=100, required=True,
                                   widget=forms.TextInput(attrs={'formwidth': '100%'}))
    nombre = forms.CharField(label=u"Nombre", max_length=100, required=True,
                                   widget=forms.TextInput(attrs={'formwidth': '100%'}))
    icono = forms.CharField(label=u"Url del icono", max_length=100, required=True,
                             widget=forms.TextInput(attrs={'formwidth': '100%'}))
    descripcion = forms.CharField(label=u"Descripcion", max_length=200, required=True,
                             widget=forms.TextInput(attrs={'formwidth': '100%'}))
    categoria = forms.ModelMultipleChoiceField(label=u'Categorias', required=False,
                                                 queryset=CategoriaModulo.objects.filter(status=True),
                                                 widget=forms.SelectMultiple(attrs={'formwidth': '100%'}))
    activo = forms.BooleanField(label=u'¿Activo?', required=False,
                                  widget=CheckboxInput(attrs={'formwidth': '30%'}))
    administrativo = forms.BooleanField(label=u'¿Administrativo?', required=False,
                                  widget=CheckboxInput(attrs={'formwidth': '30%'}))


class ModuloGrupoForm(forms.Form):
    nombre = forms.CharField(max_length=100, label=u'Nombre', required=True, widget=forms.TextInput(attrs={'class': 'imp-100', 'formwidth': '35%'}))
    descripcion = forms.CharField(max_length=200, label=u"Descripción", required=True, widget=forms.TextInput(attrs={'class': 'imp-100', 'formwidth': '65%'}))
    modulos = forms.ModelMultipleChoiceField(label=u'Módulos', required=False, queryset=Modulo.objects.filter(status=True).order_by('-pk'), widget=forms.CheckboxSelectMultiple(attrs={'class': 'js-switch', 'formwidth': '50%', 'separator': 'true', 'separatortitle': 'Relacione módulos y grupos', 'searchMultipleCheckbox': 'true'}))
    grupos = forms.ModelMultipleChoiceField(label=u'Grupos', required=False, queryset=Group.objects.all().order_by('-pk'), widget=forms.CheckboxSelectMultiple(attrs={'class': 'js-switch', 'formwidth': '50%', 'searchMultipleCheckbox': 'true'}))

    def deleteFields(self):
        del self.fields['modulos']
        del self.fields['grupos']

    def view(self):
        for field in self.fields:
            self.fields[field].widget.attrs['readonly'] = True
            self.fields[field].widget.attrs['disabled'] = True
            # if field in ['grupos', 'modulos']:
            #     self.fields[field].widget.attrs = {'checked': 'checked', 'readonly': 'readonly', 'style': 'display:none;'}
            #     self.fields[field].help_text = ''
    sagest = forms.BooleanField(label=u'¿Sagest?', required=False,
                                  widget=CheckboxInput(attrs={'formwidth': '100%'}))
    sga = forms.BooleanField(label=u'¿Sga?', required=False,
                                  widget=CheckboxInput(attrs={'formwidth': '100%'}))


class GrupoForm(forms.Form):
    nombre = forms.CharField(label=u"Nombre", max_length=40, widget=forms.TextInput(attrs={'class': 'imp-25'}))
    inicio = forms.DateField(label=u"Fecha Inicio", input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y', attrs={'class': 'selectorfecha'}))
    fin = forms.DateField(label=u"Fecha Fin", input_formats=['%d-%m-%Y'], widget=DateTimeInput(format='%d-%m-%Y', attrs={'class': 'selectorfecha'}))
    capacidad = forms.IntegerField(label=u"Capacidad", initial=30, widget=forms.TextInput(attrs={'class': 'imp-numbersmall', 'decimal': '0'}))
    costoinscripcion = forms.FloatField(label=u"Costo inscripción", initial=0, widget=forms.TextInput(attrs={'class': 'imp-moneda', 'decimal': '2'}))
    observaciones = forms.CharField(label=u"Observaciones", max_length=200, required=False)

class GrupoPermisoForm(forms.Form):
    name = forms.CharField(max_length=100, label=u'Nombre', required=True, widget=forms.TextInput(attrs={'class': 'imp-100', 'formwidth': '100%'}))

    def view(self):
        for field in self.fields:
            self.fields[field].widget.attrs['readonly'] = True
            self.fields[field].widget.attrs['disabled'] = True


class TipoOtroRubroForm(forms.Form):
    nombre = forms.CharField(label=u'Nombre', max_length=250, required=False,
                             widget=forms.TextInput(attrs={'formwidth': '100%'}))
    tiporubro = forms.ChoiceField(choices=TIPO_RUBRO, required=False, label=u'Tipo Rubro', widget=forms.Select())
    ivaaplicado = forms.ModelChoiceField(IvaAplicado.objects.filter(status=True), required=False, label=u'Iva Aplicado',
                                         widget=forms.Select(attrs={'formwidth': '50%'}))
    valor = forms.DecimalField(label=u"Valor por defecto", required=False, initial="0.00",
                               widget=forms.TextInput(attrs={'class': 'imp-moneda', 'decimal': '2'}))
    activo = forms.BooleanField(initial=False, label=u'Activo', required=False)
    requierefactura = forms.BooleanField(initial=False, label=u'No Emitir Factura', required=False)

class LugarRecaudacionForm(forms.Form):
    nombre = forms.CharField(label=u'Nombre', widget=forms.TextInput(attrs={'class': 'imp-100'}))
    puntoventa = forms.ModelChoiceField(PuntoVenta.objects.filter(status=True), required=False, label=u'Punto de Venta', widget=forms.Select(attrs={'class': 'imp-50'}))
    persona = forms.CharField(required=False, label=u'Persona', widget=forms.Select(attrs={'class': 'imp-50', 'style': "width: 100%"}))
    activo = forms.BooleanField(initial=True, label=u'Activo', required=False)

class PuntoVentaForm(FormModeloBase):
    nombreestablecimiento = forms.CharField(label=u'Nombre', max_length=500, widget=forms.TextInput(attrs={'col': '12'}), required=True)
    direccion = forms.CharField(label=u'Dirección', max_length=500, widget=forms.TextInput(attrs={'col': '12'}), required=True)
    establecimiento = forms.CharField(label=u'Establecimiento', max_length=500, widget=forms.TextInput(attrs={'col': '6'}), required=True)
    puntoventa = forms.CharField(label=u'Punto de Venta', max_length=500, widget=forms.TextInput(attrs={'col': '6'}), required=True)
    activo = forms.BooleanField(initial=False, widget=forms.CheckboxInput(attrs={'col':'6'}), label=u'Activo?', required=False)
    facturaelectronica = forms.BooleanField(initial=False, widget=forms.CheckboxInput(attrs={'col':'6'}), label=u'Emite Facturación Electroncia?', required=False)
    imprimirfactura = forms.BooleanField(initial=False, widget=forms.CheckboxInput(attrs={'col':'6'}), label=u'Imprime Facturas?', required=False)

class SecuencialRecaudacionesForm(FormModeloBase):
    puntoventa = forms.ModelChoiceField(label=u"Puntos de Ventas", queryset=PuntoVenta.objects.filter(status=True, activo=True).order_by('establecimiento'), required=True,  widget=forms.Select(attrs={'col': '12'}))
    comprobante = forms.IntegerField(initial=0, label=u'Secuencia Comprobantes', required=False, widget=forms.TextInput(attrs={'col': '6', 'class': 'imp-numbersmall', 'decimal': '0'}))
    cajero = forms.IntegerField(initial=0, label=u'Secuencia Cajero', required=False, widget=forms.TextInput(attrs={'col': '6', 'class': 'imp-numbersmall', 'decimal': '0'}))

class VentaForm(FormModeloBase):
    persona = forms.CharField(required=False, label=u'Persona', widget=forms.Select(attrs={'class': 'form-control', 'col': '12'}))
    rubro = forms.ModelChoiceField(TipoOtroRubro.objects.filter(status=True), required=False, label=u'Rubro', widget=forms.Select(attrs={'class': 'form-control', 'col': '9'}))

class FacturaForm(FormModeloBase):
    persona = forms.CharField(required=False, label=u'Persona', widget=forms.Select(attrs={'class': 'form-control', 'col': '12'}))
    rubro = forms.ModelChoiceField(TipoOtroRubro.objects.filter(status=True), required=False, label=u'Rubro', widget=forms.Select(attrs={'class': 'form-control', 'col': '9'}))

class SalidaRecaudacionForm(FormModeloBase):
    concepto = forms.CharField(required=False, label=u'Concepto', widget=forms.TextInput(attrs={'class': 'form-control', 'col': '6'}))
    valor = forms.DecimalField(label=u"Valor", required=False, initial="0.00", widget=forms.TextInput(attrs={'class': 'imp-moneda', 'decimal': '2', 'col': '6'}))
