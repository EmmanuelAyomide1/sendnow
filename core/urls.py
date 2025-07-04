"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path

from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions


schema_view = get_schema_view(
    openapi.Info(
        title="SENDNOW API",
        default_version="v1",
        description="SendNow API version one",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="owoeyeemmanuel206@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    re_path(
        r'^swagger(?P<format>\.json|\.yaml)$',
        schema_view.without_ui(cache_timeout=0),
        name="swagger-json",
    ),
    path(
        "api/swagger-doc/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="swagger-ui",
    ),
    path(
        "api/swagger-redoc/",
        schema_view.with_ui("redoc", cache_timeout=0),
        name="swagger-redoc",
    ),
    path("admin/", admin.site.urls),
    path("api/v1/users/", include("users.urls"))
]
