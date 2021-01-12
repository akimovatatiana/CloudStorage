import json

from django.http import HttpResponse

from cloud_storage.apps.storage.utils import get_used_size


def get_used_size_json(request):
    used_size = get_used_size(request, beautify=True)

    used_size_data = {
        'size': used_size
    }

    dump = json.dumps(used_size_data)

    return HttpResponse(dump, content_type='application/json')
