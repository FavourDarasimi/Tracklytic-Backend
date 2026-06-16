import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tracklytic_Backend.settings')

app = Celery('Tracklytic_Backend')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
