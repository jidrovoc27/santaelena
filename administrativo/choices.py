TIPO_PERSONA = (
    (1, u'NATURAL'),
    (2, u'JURÍDICA'),
)

TIPO_IDENTIFICACION = (
    (1, u'Cédula'),
    (2, u'Pasaporte'),
    (3, u'Ruc'),
)

TIPO_RUBRO = (
    (1, u'SERVICIO'),
    (2, u'BIEN'),
    (3, u'RENTA INVERSIONES')
)

TIPO_CUOTA = (
    (1, u'CANTIDAD'),
)

ESTADO_SESION_PLACETOPAY = (
    (1, u'Pendiente'),
    (2, u'Aprobado'),
    (3, u'Rechazado'),
    (4, u'Cancelado'),
)

ESTADO_PAGO_PLACETOPAY = (
    (1, "Aprobado"),
    (2, "Anulado"),
)

ORIGEN_SESION = (
    (1, u'TIENDA VIRTUAL'),
)

ORIGEN_RECAUDACION = (
    (1, u'TIENDA VIRTUAL'),
)

PRIORIDAD_NOTIFICACION = (
    (1, u'Alta'),
    (2, u'Media'),
    (3, u'Baja')
)

TIPO_NOTIFICACION = (
    (1, u'Mensaje'),
    (2, u'Proceso'),
    (3, u'Información')
)

ESTADO_PEDIDO = (
    (1, "PENDIENTE",),
    (2, "APROBADO",),
    (3, "RECHAZADO"),
    (4, "ANULADO",),
    (5, "REEMBOLSADO",),
)

METODO_PAGO = (
    (1, "Kushki"),
    (2, "Transferencia/Deposito"),
    (3, "Place To Pay"),
)

ESTADO_PROCESO = (
    (1, u'EN PROCESO'),
    (2, u'FINALIZADA'),
    (3, u'ANULADO'),
)

ESTADO_COMPROBANTE = (
    (1, u'PENDIENTE'),
    (2, u'FINALIZADA')
)

MESES_CHOICES = (
    (1, u'ENERO'),
    (2, u'FEBRERO'),
    (3, u'MARZO'),
    (4, u'ABRIL'),
    (5, u'MAYO'),
    (6, u'JUNIO'),
    (7, u'JULIO'),
    (8, u'AGOSTO'),
    (9, u'SEPTIEMBRE'),
    (10, u'OCTUBRE'),
    (11, u'NOVIEMBRE'),
    (12, u'DICIEMBRE')
)

TIPOS_PARAMETRO_VARIABLE = (
    (1, u'Texto'),
    (2, u'Numero Entero'),
    (3, u'Numero Decimal'),
    (4, u'Verdadero o Falso'),
    (5, u'Fecha'),
    (6, u'Lista')
)

MES_CHOICES = (
    (1, "Enero"),
    (2, "Febrero"),
    (3, "Marzo"),
    (4, "Abril"),
    (5, "Mayo"),
    (6, "Junio"),
    (7, "Julio"),
    (8, "Agosto"),
    (9, "Septiembre"),
    (10, "Octubre"),
    (11, "Noviembre"),
    (12, "Diciembre"),
)

ESTADO_FACTURA = (
    (1, u'PENDIENTE'),
    (2, u'FINALIZADA'),
)

TIPO_PAGO_FACTURA = (
    (1, u'EFECTIVO'),
    (20, u'CHEQUE'),
    (20, u'TRANSFERENCIA/DEPÓSITO'),
    (17, u'DINERO ELECTRÓNICO'),
    (19, u'TARJETA CRÉDITO'),
    (16, u'TARJETA DÉBITO'),
    (18, u'TARJETA PREPAGO'),
)


APP_LABEL = (
    (1, u'SGA'),
    (2, u'SAGEST'),
)

APP_LABEL_TEMPLATE = APP_LABEL