from django.db import models
from django.contrib.auth.models import User


# Create your models here.

class File(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='storage/data/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
