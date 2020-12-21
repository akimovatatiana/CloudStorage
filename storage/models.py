from datetime import datetime
from os import path

from django.contrib.auth.models import User
from django.db import models
from django.utils.encoding import uri_to_iri

import mimetypes


def get_upload_path(instance, filename):
    return uri_to_iri(str(instance.user.id) + '/' + filename)


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
        return mimetypes.guess_type(self.file.url)[0]

    def extension(self):
        name, extension = path.splitext(self.file.name)

        return extension
