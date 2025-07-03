from email.policy import default
from pickle import FALSE
from .base import *

DEBUG = config("DEBUG", default=FALSE)

INSTALLED_APPS += [
    "corsheaders",
]

# DATABASE_URL = config("DATABASE_URL")

# DATABASES = {
#     "default": dj_database_url.parse(
#         DATABASE_URL,
#         conn_max_age=600,
#     ),
# }
