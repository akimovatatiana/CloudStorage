import zipfile
import json

from os import path
from os.path import basename

from django.conf import settings
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse, Http404, FileResponse
from django.views import View
from django.utils.encoding import uri_to_iri

from .forms import FileForm
from .models import File

from subscriptions.models import UserSubscription
from storage_subscriptions.models import StorageSubscription


def beautify_size(value):
    if value < 512000:
        value = value / 1024.0
        ext = 'KB'
    elif value < 4194304000:
        value = value / 1048576.0
        ext = 'MB'
    else:
        value = value / 1073741824.0
        ext = 'GB'
    return '%s %s' % (str(round(value, 2)), ext)


def get_used_size(files_list):
    used_size = 0
    for file in files_list:
        file_path = str(settings.BASE_DIR) + uri_to_iri(file.file.url)

        size = path.getsize(file_path)

        used_size += size

    return used_size


def get_storage_capacity(request):
    user = request.user
    user_subscription = UserSubscription.objects.get_queryset().filter(user=user)

    if user_subscription:
        user_plan_id = user_subscription[0].subscription.plan_id

        storage_subscriptions = StorageSubscription.objects.filter(subscription=user_plan_id)
        max_size = storage_subscriptions[0].size

        return max_size

    return 100


def is_new_file_fit_in_storage(request):
    capacity = get_storage_capacity(request)
    user_id = request.user.id

    files_list = File.objects.filter(user=user_id)
    used_size = get_used_size(files_list) / 1048576.0

    new_file_size = request.FILES['file'].size / 1048576.0
    new_used_size = new_file_size + used_size

    return new_used_size <= capacity


class UploadView(View):
    def get(self, request):
        user_id = request.user.id

        if user_id is not None:
            files_list = File.objects.filter(user=user_id)
            used_size = beautify_size(get_used_size(files_list))
            capacity = get_storage_capacity(request)

            return render(self.request, 'storage/upload.html',
                          {'files': files_list,
                           'used_size': used_size,
                           'capacity': capacity}
                          )
        else:
            return redirect('dfs_subscribe_list')

    def post(self, request):
        post = request.POST.copy()
        post.update({'title': str(request.FILES['file']), 'size': '0 kb'})

        form = FileForm(post, self.request.FILES)

        if form.is_valid() and is_new_file_fit_in_storage(request):
            form_with_unique_filename = form.save()

            # Get unique filename from disk, add to form
            filename = path.split(uri_to_iri(str(form_with_unique_filename.file.url)))[-1]
            form_with_unique_filename.title = filename

            # Add file size to form
            file_path = str(settings.BASE_DIR) + uri_to_iri(form_with_unique_filename.file.url)
            file_size = beautify_size(path.getsize(file_path))
            form_with_unique_filename.size = file_size

            form_with_unique_filename.save()

            data = {'is_valid': True, 'name': form_with_unique_filename.file.name,
                    'url': uri_to_iri(form_with_unique_filename.file.url)}
        else:
            data = {'is_valid': False}

        return JsonResponse(data)


def remove_file(request):
    file_id = request.POST.get('file_id', '')

    if file_id == '':
        files_id = json.loads(request.POST.get('files_id', ''))

        for pk in files_id:
            file = File.objects.get(pk=pk)
            # file.file.delete()
            # file.delete()
            print('Dummy multi delete ' + str(file))
    else:
        file = File.objects.get(pk=file_id)
        print('Dummy single delete ' + str(file))

        # file.file.delete()
        # file.delete()

    return redirect('upload')


def download_file(request):
    user_id = request.user
    file_id = request.POST.get('file_id', '')
    user_file = File.objects.get(pk=file_id, user=user_id)

    if user_file:
        file_path = uri_to_iri(user_file.file.path)

        if path.exists(file_path):
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
        paths.append(path.join(settings.MEDIA_ROOT, uri_to_iri(file.file.path)))

    response = HttpResponse(content_type='application/zip')
    archive = zipfile.ZipFile(response, 'w')
    for file_path in paths:
        archive.write(file_path, basename(file_path))

    archive.close()

    response['Content-Disposition'] = 'attachment; filename={}'.format('cloud-archive.zip')

    return response
