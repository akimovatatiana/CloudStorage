from django.db import models
from django.contrib.auth.models import User


def get_upload_path(instance, filename):
    return 'static/user_data/' + str(instance.user.id) + '/' + filename


class File(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to=get_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
