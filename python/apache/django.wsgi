import os
import sys

sys.path.append('/home/dirigible/python')

os.environ['DJANGO_SETTINGS_MODULE'] = 'dirigible.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

