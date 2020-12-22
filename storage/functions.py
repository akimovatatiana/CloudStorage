import os
import mimetypes
import humanize

from django.utils.encoding import uri_to_iri

from cloud_storage import settings
from storage.constants import mime_dict


def get_used_size(files_list):
    used_size = 0
    for file in files_list:
        file_path = str(settings.BASE_DIR) + uri_to_iri(file.file.url)

        size = os.path.getsize(file_path)

        used_size += size

    return used_size


def get_upload_path(instance, filename):
    return uri_to_iri(str(instance.user.id) + '/' + filename)


def get_mime_file_type(url):
    return mimetypes.guess_type(url)[0]


def get_file_type(content_type):
    # file_type = get_mime_file_type(url)

    for simple_file_type, mime_file_types in mime_dict.items():
        if content_type in mime_file_types:
            return simple_file_type.title()

    return content_type


def beautify_size(value):
    return humanize.naturalsize(value).upper()
