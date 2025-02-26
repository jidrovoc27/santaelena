import os
import sys

sys.path.append('/var/lib/django/epunemi')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

