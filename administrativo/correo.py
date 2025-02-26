from django.template.loader import get_template
import threading
from santaelena.settings import *
from django.core.mail.message import EmailMessage

class EmailThread(threading.Thread):
    def __init__(self, subject, html_content, recipient_list, recipient_list_cc, adjuntos, cuenta, adjuntosrender):
        self.subject = subject
        self.recipient_list = recipient_list
        self.recipient_list_cc = recipient_list_cc
        self.html_content = html_content
        self.adjuntos = adjuntos
        self.adjuntosrender = adjuntosrender
        self.cuenta = cuenta

        threading.Thread.__init__(self)

    def run(self):
        # if self.cuenta:
        #     msg = EmailMessage(self.subject, self.html_content, self.cuenta, self.recipient_list, bcc=self.recipient_list_cc)
        # else:
        #     msg = EmailMessage(self.subject, self.html_content, EMAIL_HOST_USER, self.recipient_list, bcc=self.recipient_list_cc)
        msg = EmailMessage(self.subject, self.html_content, DEFAULT_FROM_EMAIL, self.recipient_list, bcc=self.recipient_list_cc)
        msg.content_subtype = "html"
        if self.adjuntosrender:
            for adjunto in self.adjuntosrender:
                obj = Dict2Obj(adjunto)
                msg.attach(
                    obj.filename,
                    obj.content,
                    adjunto.get("mimetype")
                )
        if self.adjuntos:
            for adjunto in self.adjuntos:
                try:
                    if type(adjunto) is str:
                        msg.attach_file(adjunto)
                    else:
                        msg.attach_file(adjunto.file.name)
                except Exception as ex:
                    msg.attach_file(adjunto)
        msg.send()



CUENTAS_CORREOS = (
    (0, u'facturacion_epunemi@unemi.edu.ec'),
)

def send_html_mail(subject, html_template, data, recipient_list, recipient_list_cc, adjuntos=None, cuenta=None):
    try:
        if recipient_list.__len__() or recipient_list_cc.__len__():
            template = get_template(html_template)
            d = (data)
            html_content = template.render(d)
            EmailThread(subject, html_content, recipient_list, recipient_list_cc, adjuntos, cuenta).start() #subject.lower().capitalize()
    except Exception as ex:
        pass