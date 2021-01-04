from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.core.cache.backends.base import DEFAULT_TIMEOUT

from cloud_storage import settings
from cloud_storage.apps.storage import views as storage_views

urlpatterns = [
    url('overview/', storage_views.StorageView.as_view(), name='overview'),
    url('stats/', storage_views.StorageStatsView.as_view(), name='stats'),
    url('download-file', storage_views.download_file, name='download-file'),
    url('download-compressed-files', storage_views.download_compressed_files, name='download-compressed-files'),
]
