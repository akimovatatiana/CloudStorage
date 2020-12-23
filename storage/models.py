import os

from datetime import datetime

from django.contrib.auth.models import User
from django.db import models
from django.utils.encoding import uri_to_iri

from storage.functions import get_upload_path


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
        super().save(*args, **kwargs)

        if self.file:
            self.title = os.path.split(uri_to_iri(str(self.file.url)))[-1]

            super().save(update_fields=['title'])

    def extension(self):
        name, extension = os.path.splitext(self.file.name)

        return extension
