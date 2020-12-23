import os
import zipfile
import json
import django_filters

from os.path import basename

from django.conf import settings
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse, Http404
from django.views import View
from django.utils.encoding import uri_to_iri
from django import forms

from .forms import FileForm
from .utils import beautify_size, get_used_size, get_file_type
from .models import File

from subscriptions.models import UserSubscription
from cloud_storage.apps.storage_subscriptions.models import StorageSubscription


class UploadView(View):
    def get(self, request):
        user_id = request.user.id

        if user_id is not None:
            user_subscription = get_user_subscription(user_id)

            if not user_subscription:
                return redirect('dfs_subscribe_list')

            files_list = File.objects.filter(user=user_id).order_by('-uploaded_at')

            used_size = beautify_size(get_used_size(files_list))

            capacity = int(get_storage_capacity(request) / 1000)

            file_filter = FileFilter(request.GET, queryset=files_list)

            return render(self.request, 'storage/upload.html',
                          {'files': files_list,
                           'used_size': used_size,
                           'capacity': capacity,
                           'filter': file_filter,
                           }
                          )
        else:
            return redirect('dfs_subscribe_list')

    def post(self, request):
        title = str(request.FILES['file'])
        size = self.request.FILES['file'].size
        beautified_size = beautify_size(self.request.FILES['file'].size)
        content_type = get_file_type(self.request.FILES['file'].content_type)
        token = request.POST.get('csrfmiddlewaretoken', '')

        data = {
            'user': self.request.user,
            'title': title,
            'size': beautified_size,
            'type': content_type,
            'csrfmiddlewaretoken': token,
        }

        form = FileForm(files=request.FILES, data=data)

        if form.is_valid() and is_new_file_fit_in_storage(request, size):
            file_form = form.save()

            data = {'is_valid': True, 'name': file_form.file.name,
                    'url': uri_to_iri(file_form.file.url)}
        else:
            data = {'is_valid': False}

        return JsonResponse(data)


def remove_file(request):
    file_id = request.POST.get('file_id', '')

    if file_id == '':
        files_id = json.loads(request.POST.get('files_id', ''))

        for pk in files_id:
            file = File.objects.get(pk=pk)
            file.file.delete()
            file.delete()
            # print('Dummy multi delete ' + str(file))
    else:
        file = File.objects.get(pk=file_id)
        # print('Dummy single delete ' + str(file))

        file.file.delete()
        file.delete()

    return redirect('upload')


def download_file(request):
    user_id = request.user
    file_id = request.POST.get('file_id', '')
    user_file = File.objects.get(pk=file_id, user=user_id)

    if user_file:
        file_path = uri_to_iri(user_file.file.path)

        if os.path.exists(file_path):
            with open(file_path, 'rb') as file:
                filename = user_file.file.name

                response = HttpResponse(file.read(), content_type="application/octet-stream")
                response['Content-Disposition'] = 'attachment; filename=' + filename
                response['X-Sendfile'] = file_path

                return response

        raise Http404

    return redirect('upload')


def download_compressed_files(request):
    user = request.user
    files_id = json.loads(request.POST.get('files_id', ''))

    paths = []

    for file_id in files_id:
        file = File.objects.get(pk=file_id)
        paths.append(os.path.join(settings.MEDIA_ROOT, uri_to_iri(file.file.path)))

    response = HttpResponse(content_type='application/zip')
    archive = zipfile.ZipFile(response, 'w')

    for file_path in paths:
        archive.write(file_path, basename(file_path))

    archive.close()

    response['Content-Disposition'] = 'attachment; filename={}'.format('cloud-archive.zip')

    return response



def get_user_subscription(user):
    return UserSubscription.objects.get_queryset().filter(user=user)


def get_storage_capacity(request):
    user_subscription = get_user_subscription(request.user)

    if user_subscription:
        user_plan_id = user_subscription[0].subscription.plan_id

        storage_subscriptions = StorageSubscription.objects.filter(subscription=user_plan_id)
        capacity = storage_subscriptions[0].size

        return capacity

    return 0


# TODO: Update accuracy

def is_new_file_fit_in_storage(request, new_size):
    capacity = get_storage_capacity(request)
    user_id = request.user.id

    files_list = File.objects.filter(user=user_id)
    used_size = get_used_size(files_list) / 1048576.0

    new_file_size = new_size / 1048576.0
    new_used_size = new_file_size + used_size

    return new_used_size <= capacity


FILTER_CHOICES = (
    ('Image', 'Image'),
    ('Audio', 'Audio'),
    ('Video', 'Video'),
    ('Document', 'Document'),
    ('Table', 'Table Sheet'),
    ('Presentation', 'Presentation'),
)


class FileFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(label="", lookup_expr='icontains',
                                      widget=forms.TextInput(attrs={'autocomplete': 'off'}))
    type = django_filters.ChoiceFilter(label="", empty_label="All Types", choices=FILTER_CHOICES)

    class Meta:
        model = File
        fields = ['title', 'type']
        exclude = ['user', 'file']
