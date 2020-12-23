import json

from django.http import HttpResponse

# Create your views here.

from cloud_storage.apps.storage.models import File
from cloud_storage.apps.storage.utils import beautify_size, get_used_size


def get_used_size_json(request):
    files_list = File.objects.filter(user=request.user)
    used_size = beautify_size(get_used_size(files_list))

    data = {
        'size': used_size
    }

    dump = json.dumps(data)

    return HttpResponse(dump, content_type='application/json')