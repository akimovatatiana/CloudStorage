from os import path

from django.conf import settings
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views import View

from .forms import FileForm
from .models import File


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


class UploadView(View):
    def get(self, request):
        user_id = request.user.id

        if user_id is not None:
            files_list = File.objects.filter(user=user_id)

            return render(self.request, 'storage/upload.html', {'files': files_list})
        else :
            return redirect('dfs_subscribe_list')

    def post(self, request):
        post = request.POST.copy()
        post.update({'title': str(request.FILES['file']), 'size': '0 kb'})

        form = FileForm(post, self.request.FILES)

        if form.is_valid():
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
