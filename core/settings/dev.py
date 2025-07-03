from .base import *

DEBUG = True

INSTALLED_APPS += [
    "django_seed"
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "sendnow",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "localhost",
        "PORT": 5432,
    },
}
