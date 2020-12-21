from django.conf.urls import url

from storage import views as storage_views

urlpatterns = [
    url('upload', storage_views.UploadView.as_view(), name='upload'),
    url('remove-file', storage_views.remove_file, name='remove-file'),
    url('download-file', storage_views.download_file, name='download-file'),
    url('download-selected-files', storage_views.download_compressed_files, name='download-selected-files')
]