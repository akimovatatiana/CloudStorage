import json

from django.contrib.auth.models import User
from django.http import HttpResponse

# Create your views here.
from django.shortcuts import render

from cloud_storage.apps.storage.models import File
from cloud_storage.apps.storage.utils import beautify_size, get_used_size


def get_all_users(request):
    keys = User.objects.count() + 1
    users = []

    # Traverse all users by primary keys
    for pk in range(1, keys):
        user = User.objects.get(pk=pk)
        users.append(user)

    context = {
        "users": users
    }

    return render(request, "profile/users.html", context)


def get_used_size_json(request):
    files_list = File.objects.filter(user=request.user)
    used_size = beautify_size(get_used_size(files_list))

    data = {
        'size': used_size
    }

    dump = json.dumps(data)

    return HttpResponse(dump, content_type='application/json')