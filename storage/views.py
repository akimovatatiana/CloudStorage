from os import path

from django.conf import settings
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views import View

from .forms import FileForm
from .models import File

from subscriptions.models import UserSubscription
from storage_subscriptions.models import StorageSubscription


def beautify_size(value):
    if value < 512000:
        value = value / 1024.0
        ext = 'kb'
    elif value < 4194304000:
        value = value / 1048576.0
        ext = 'mb'
    else:
        value = value / 1073741824.0
        ext = 'gb'
    return '%s %s' % (str(round(value, 2)), ext)


def get_used_size(files_list):
    used_size = 0
    for file in files_list:
        file_path = str(settings.BASE_DIR) + file.file.url
        size = path.getsize(file_path)

        used_size += size

    return used_size


def get_storage_capacity(request):
    user = request.user
    user_subscription = UserSubscription.objects.get_queryset()
    user_plan_id = user_subscription.filter(user=user)[0].subscription.plan_id

    storage_subscriptions = StorageSubscription.objects.filter(subscription=user_plan_id)
    max_size = storage_subscriptions[0].size

    return max_size


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
            filename = path.split(str(form_with_unique_filename.file.url))[-1]
            form_with_unique_filename.title = filename

            # Add file size to form
            file_path = str(settings.BASE_DIR) + form_with_unique_filename.file.url
            file_size = beautify_size(path.getsize(file_path))
            form_with_unique_filename.size = file_size

            form_with_unique_filename.save()

            data = {'is_valid': True, 'name': form_with_unique_filename.file.name,
                    'url': form_with_unique_filename.file.url}
        else:
            data = {'is_valid': False}

        return JsonResponse(data)


def remove_file(request):
    pk = request.POST.get('pk', '')
    file = File.objects.get(pk=pk)
    file.file.delete()
    file.delete()

    return redirect('upload')
