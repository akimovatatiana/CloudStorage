from django.conf.urls import url

from storage import views as storage_views

urlpatterns = [
    url(r'^upload/$', storage_views.UploadView.as_view(), name='upload'),
]