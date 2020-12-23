from django.contrib.auth import views
from django.conf.urls import url

from .views import *

urlpatterns = [
    url('used-size', get_used_size_json, name='get-used-size')
]