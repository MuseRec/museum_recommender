"""
WSGI config for museum_webapp project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/wsgi/
"""

import os
import sys

from django.core.wsgi import get_wsgi_application

sys.path.append('/var/www/django/recommender/')
sys.path.append('/var/www/django/recommender/museum_webapp/')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'museum_webapp.settings')

application = get_wsgi_application()
