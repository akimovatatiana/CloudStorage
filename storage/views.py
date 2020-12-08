from os import path

from django.conf import settings
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views import View

from .forms import FileForm
from .models import File


def reformat_size(value):
    """
    Simple kb/mb/gb size snippet for templates:

    {{ product.file.size|sizify }}
    """
    # value = ing(value)
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
        files_list = File.objects.all()

        return render(self.request, 'storage/upload.html', {'files': files_list})

    def post(self, request):
        post = request.POST.copy()
        post.update({'title': str(request.FILES['file'])})

        form = FileForm(post, self.request.FILES)

        if form.is_valid():
            form_with_unique_filename = form.save()

            # Get unique filename from disk
            filename = path.split(str(form_with_unique_filename.file.url))[-1]
            form_with_unique_filename.title = filename

            form_with_unique_filename.save()

            file_path = str(settings.BASE_DIR) + form_with_unique_filename.file.url
            file_size = reformat_size(path.getsize(file_path))
            print(file_size)

            data = {'is_valid': True, 'name': form_with_unique_filename.file.name,
                    'url': form_with_unique_filename.file.url}
        else:
            data = {'is_valid': False}

        return JsonResponse(data)


def remove_file(request):
    pk = request.POST.get('pk', '')
    query = File.objects.get(pk=pk)
    query.delete()

    return redirect('upload')
