from django.conf.urls import url

from cloud_storage.apps.storage import views as storage_views

urlpatterns = [
    url('overview', storage_views.UploadView.as_view(), name='overview'),
    url('remove-file', storage_views.remove_file, name='remove-file'),
    url('download-file', storage_views.download_file, name='download-file'),
    url('download-selected-files', storage_views.download_compressed_files, name='download-selected-files'),
    url('stats', storage_views.get_storage_stats, name='stats')
]