import json
from os import path

from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from django.utils.encoding import uri_to_iri

from cloud_storage import settings
from storage.models import File
from storage.functions import beautify_size, get_used_size


def get_used_size_json(request):
    files_list = File.objects.filter(user=request.user)
    used_size = beautify_size(get_used_size(files_list))

    data = {
        'size': used_size
    }

    dump = json.dumps(data)

    return HttpResponse(dump, content_type='application/json')