from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.views import View

from .forms import FileForm
from .models import File


# @login_required
class UploadView(View):
    def get(self, request):
        files_list = File.objects.all()

        return render(self.request, 'storage/upload.html', {'files': files_list})

    def post(self, request):
        form = FileForm(self.request.POST, self.request.FILES)
        user_id = self.request.POST.get('user_id', '')
        if form.is_valid():
            file = form.save()
            data = {'is_valid': True, 'name': file.file.name, 'url': file.file.url}
        else:
            data = {'is_valid': False}

        return JsonResponse(data)


class ProgressBarUploadView(View):
    def get(self, request):
        files_list = File.objects.all()

        return render(self.request, 'storage/upload.html', {'files': files_list})

    def post(self, request):
        form = FileForm(self.request.POST, self.request.FILES)
        if form.is_valid():
            file = form.save()
            data = {'is_valid': True, 'name': file.file.name, 'url': file.file.url}
        else:
            data = {'is_valid': False}

        return JsonResponse(data)


class DragAndDropUploadView(View):
    def get(self, request):
        files_list = File.objects.all()

        return render(self.request, 'storage/upload.html', {'files': files_list})

    def post(self, request):
        form = FileForm(self.request.POST, self.request.FILES)
        if form.is_valid():
            file = form.save()
            data = {'is_valid': True, 'name': file.file.name, 'url': file.file.url}
        else:
            data = {'is_valid': False}

        return JsonResponse(data)
