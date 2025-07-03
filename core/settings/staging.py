from .base import *

DEBUG = config("DEBUG", cast=bool)


ALLOWED_HOSTS = [
    "localhost",
    ".render.com",
    ".now.sh",
    ".onrender.com",
    "127.0.0.1"
]


# CORS CONFIGURATION
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173"
    # "https://frontend.app",
]

CORS_ORIGIN_WHITELIST = (
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8000",
    # "https://frontend.app",
)

CSRF_TRUSTED_ORIGINS = [
    # "https://frontend.app",
    "https://localhost:3000",
    "http://localhost:5173"
]


INSTALLED_APPS += [
    "corsheaders",
]


MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
] + MIDDLEWARE
