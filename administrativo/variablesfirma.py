import os
from santaelena.settings import BASE_DIR


JAVA_18_HOME = 'C:/Program Files/Java/jdk-18.0.2.1/'
JR_RUN_SING_SIGNCLI = os.path.join(BASE_DIR, 'thirdparty', 'signcli')
SERVER_URL_SIGNCLI = 'http://127.0.0.1:8014'
SERVER_USER_SIGNCLI = 'root'
SERVER_PASS_SIGNCLI = 'magic.number.82'
PASSSWORD_SIGNCLI = 'Epunemi0968*'
ENVIO_SRI_PRUEBAS = 'https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl'
ENVIO_SRI_PRODUCCION = 'https://cel.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantes?wsdl'
AUTORIZACION_SRI_PRUEBAS = 'https://celcer.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl'
AUTORIZACION_SRI_PRODUCCION = 'https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantes?wsdl'

jaxb_api = os.path.join(BASE_DIR, 'Java', 'libs', 'jaxb', 'jaxb-api-2.3.1.jar')
jaxb_impl = os.path.join(BASE_DIR, 'Java', 'libs', 'jaxb', 'jaxb-impl-2.3.1.jar')
activation = os.path.join(BASE_DIR, 'Java', 'libs', 'jaxb', 'activation-1.1.1.jar')
signcli_jar = os.path.join(JR_RUN_SING_SIGNCLI, 'SignCLI.jar')

classpath = f"{jaxb_api};{jaxb_impl};{activation};{signcli_jar}"