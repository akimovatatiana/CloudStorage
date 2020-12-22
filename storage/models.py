from datetime import datetime
from os import path

from django.contrib.auth.models import User
from django.db import models
from django.utils.encoding import uri_to_iri

import mimetypes


def get_upload_path(instance, filename):
    return uri_to_iri(str(instance.user.id) + '/' + filename)


def get_mime_file_type(url):
    return mimetypes.guess_type(url)[0]


mime_dict = {
    "text": ["text/plain"],
    "image": ["image/png", "image/jpeg", "image/jpg", "image/gif", "image/svg+xml", "image/apng", "image/avif",
              "image/heic"],
    "audio": ["audio/wave", "audio/wav", "audio/x-wav", "audio/x-pn-wav", "audio/webm", "audio/ogg", "audio/mpeg",
              "audio/midi", "audio/3gpp", "audio/3gpp2"],
    "video": ["video/x-msvideo", "video/mpeg", "video/ogg", "video/mp2t", "video/webm", "video/3gpp", "video/3gpp2"],
    "document": ["application/msword",
                 "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                 "application/vnd.openxmlformats-officedocument.wordprocessingml.template",
                 "application/vnd.ms-word.document.macroEnabled.12",
                 "application/vnd.ms-word.template.macroEnabled.12"],
    "table": ["application/vnd.ms-excel",
              "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
              "application/vnd.openxmlformats-officedocument.spreadsheetml.template",
              "application/vnd.ms-excel.sheet.macroEnabled.12",
              "application/vnd.ms-excel.template.macroEnabled.12",
              "application/vnd.ms-excel.addin.macroEnabled.12",
              "application/vnd.ms-excel.sheet.binary.macroEnabled.12"],
    "presentation": ["application/vnd.ms-powerpoint",
                     "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                     "application/vnd.openxmlformats-officedocument.presentationml.template",
                     "application/vnd.openxmlformats-officedocument.presentationml.slideshow",
                     "application/vnd.ms-powerpoint.addin.macroEnabled.12",
                     "application/vnd.ms-powerpoint.presentation.macroEnabled.12",
                     "application/vnd.ms-powerpoint.template.macroEnabled.12",
                     "application/vnd.ms-powerpoint.slideshow.macroEnabled.12"],
    "archive": ["application/x-freearc", "application/x-bzip", "application/x-bzip2", "application/gzip",
                "application/java-archive", "application/vnd.rar", "application/x-tar", "application/zip",
                "application/x-7z-compressed"]
}


class File(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to=get_upload_path)
    uploaded_at = models.DateTimeField(default=datetime.now)
    type = models.CharField(max_length=255, default="none")
    size = models.CharField(max_length=255)

    class Meta:
        ordering = ['uploaded_at']

    def save(self, *args, **kwargs):
        if self.file:
            self.type = self.file_type()

        super().save(*args, **kwargs)

    def file_type(self):
        file_type = get_mime_file_type(self.file.url)

        for simple_file_type, mime_file_types in mime_dict.items():
            if file_type in mime_file_types:
                return simple_file_type.title()

        return file_type

    def extension(self):
        name, extension = path.splitext(self.file.name)

        return extension
