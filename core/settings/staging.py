from .base import *

DEBUG = config("DEBUG", cast=bool)


ALLOWED_HOSTS = [
    "localhost",
    "sendnow-kcxx.onrender.com",
    ".render.com",
    ".now.sh",
    ".onrender.com",
    "127.0.0.1",
]


# CORS CONFIGURATION
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
    "https://sendnow-amber.vercel.app",
    "https://send-now-six.vercel.app",
]

CORS_ORIGIN_WHITELIST = (
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
    "http://localhost:8000",
    "https://sendnow-amber.vercel.app",
    "https://send-now-six.vercel.app",
)

CSRF_TRUSTED_ORIGINS = [
    "https://sendnow-amber.vercel.app",
    "https://send-now-six.vercel.app",
    "https://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
]


INSTALLED_APPS += [
    "corsheaders",
]


MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
] + MIDDLEWARE
