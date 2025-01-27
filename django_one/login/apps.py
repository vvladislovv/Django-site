from django.apps import AppConfig
from .db import init_db


class LoginConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'login'

    def ready(self):
        init_db()  # Initialize the database when the app is ready
