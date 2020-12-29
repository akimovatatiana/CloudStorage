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
import debug_toolbar
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include
from django.views.generic import TemplateView

from cloud_storage import settings

from cloud_storage.apps.storage.views import serve_protected_file
from cloud_storage.views import HomeView

urlpatterns = [
                  url('api/', include('cloud_storage.apps.api.urls')),
                  url('__debug__/', include(debug_toolbar.urls)),
                  url('admin/', admin.site.urls),
                  url('users/', include('cloud_storage.apps.users.urls')),
                  url('subscriptions/', include('subscriptions.urls')),
                  url('storage/', include('cloud_storage.apps.storage.urls')),
                  url('home', HomeView.as_view(), name='home'),
              ] + static(settings.MEDIA_URL, view=serve_protected_file, document_root=settings.MEDIA_ROOT)
