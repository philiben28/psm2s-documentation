import os
import sys
os.environ['DJANGO_SECRET_KEY'] = 'tor7)zzv+4sfr#crz!tpq5ow+=q&2o=m@tr_+6l%7ddwf!56g8'

# Chemin absolu — évite la récursion
sys.path.insert(0, '/home/roda4402/psm2s_v2')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
