import json

from django.contrib.auth.models import User
from django.http import HttpResponse

# Create your views here.
from django.core.cache import cache
from django.shortcuts import render

from cloud_storage.apps.storage.models import File
from cloud_storage.apps.storage.utils import beautify_size, get_used_size_from_db, get_files_list
from cloud_storage.apps.storage.views import generate_cache_key, USED_SIZE_CACHE_KEY_PREFIX


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
    used_size_cache_key = generate_cache_key(request, USED_SIZE_CACHE_KEY_PREFIX)
    if used_size_cache_key in cache:
        used_size = beautify_size(cache.get(used_size_cache_key))
    else:
        files_list = get_files_list(request)
        used_size = beautify_size(get_used_size_from_db(files_list))

        cache.set(used_size_cache_key, used_size)

    data = {
        'size': used_size
    }

    dump = json.dumps(data)

    return HttpResponse(dump, content_type='application/json')
