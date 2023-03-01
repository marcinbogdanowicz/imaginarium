import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'imaginarium.settings')
app = Celery('imaginarium')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()