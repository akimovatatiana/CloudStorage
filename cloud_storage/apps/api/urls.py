from django.contrib.auth import views
from django.conf.urls import url

from .views import *

urlpatterns = [
    url('used-size', get_used_size_json, name='get-used-size'),
    url('users/all/', get_all_users, name="all_users"),
]