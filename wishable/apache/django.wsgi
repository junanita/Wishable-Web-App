import os
import sys

path = '/home/ubuntu/team9/wishable/webapps/'

sys.path.append(path)
sys.path.append('/home/ubuntu/team9/wishable/')

os.environ['DJANGO_SETTINGS_MODULE'] = 'webapps.settings'
#import django.core.handlers.wsgi
#application = django.core.handlers.wsgi.WSGIHandler()
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

