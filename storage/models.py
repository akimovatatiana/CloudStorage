from os import path

from django.db import models
from django.contrib.auth.models import User
from django.utils.encoding import uri_to_iri


def get_upload_path(instance, filename):
    return uri_to_iri(str(instance.user.id) + '/' + filename)


class File(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to=get_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    size = models.CharField(max_length=255)

    def extension(self):
        name, extension = path.splitext(self.file.name)

        return extension
