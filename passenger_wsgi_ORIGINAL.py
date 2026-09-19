import os
import sys
os.environ['DJANGO_SECRET_KEY'] = '7x0r=z(*^o5ckhtb3%3p@&v*4p6$_ekmj@$avb&7lroi39972)'

# Chemin absolu — évite la récursion
sys.path.insert(0, '/home/roda4402/psm2s_v2')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
