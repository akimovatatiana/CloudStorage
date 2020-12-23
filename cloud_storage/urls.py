"""CloudStorage URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
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

from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from cloud_storage import settings

from cloud_storage.apps.storage.views import serve_protected_file

urlpatterns = [
                  path('admin/', admin.site.urls),
                  path('subscriptions/', include('subscriptions.urls')),
                  path('users/', include('cloud_storage.apps.users.urls')),
                  path('storage/', include('cloud_storage.apps.storage.urls')),
                  path('api/', include('cloud_storage.apps.api.urls')),
                  # path(r'^media/(?P<file>.*)$', serve_protected_file, name='serve_protected_file'),
                  # path(r'^media/(?P<path>.*)$', serve_protected_file, {'document_root': settings.MEDIA_ROOT}),

              ] + static(settings.MEDIA_URL, view=serve_protected_file, document_root=settings.MEDIA_ROOT)
