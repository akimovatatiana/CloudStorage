from django.conf.urls import url

from cloud_storage.apps.storage import views

urlpatterns = [
    url('overview/', views.StorageView.as_view(), name='overview'),
    url('stats/', views.StorageStatsView.as_view(), name='stats'),
    url('download-compressed-files', views.download_compressed_files, name='download-compressed-files'),
]
