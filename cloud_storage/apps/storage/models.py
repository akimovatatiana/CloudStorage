import os
import json

from datetime import datetime

from django.contrib.auth.models import User
from django.db import models
from django.utils.encoding import uri_to_iri


def get_upload_path(instance, filename):
    return uri_to_iri(str(instance.user.id) + '/' + filename)


class File(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to=get_upload_path)
    uploaded_at = models.DateTimeField(default=datetime.now)
    type = models.CharField(max_length=255, default="none")
    byte_size = models.PositiveIntegerField()

    class Meta:
        ordering = ['uploaded_at']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.file:
            self.title = os.path.split(uri_to_iri(str(self.file.url)))[-1]
            self.byte_size = self.file.file.size

            super().save(update_fields=['title', 'byte_size'])

    def extension(self):
        name, extension = os.path.splitext(self.file.name)

        return extension

    def beautified_size(self):
        from cloud_storage.apps.storage.utils import beautify_size

        return beautify_size(self.byte_size)
