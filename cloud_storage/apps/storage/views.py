import posixpath
import zipfile
import json

from pathlib import Path

from os.path import basename

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage, Page
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, Http404, FileResponse, HttpResponseNotModified, QueryDict
from django.utils._os import safe_join
from django.utils.functional import cached_property
from django.utils.http import http_date
from django.views import View
from django.views.static import was_modified_since, directory_index

from .filters import FileFilter
from .forms import FileForm
from .utils import *
from .models import File


class CachedPaginator(Paginator):
    @cached_property
    def count(self):
        return len(self.object_list)


class StorageView(View):
    def get(self, request):
        user_subscription = get_user_subscription(self.request)

        if not user_subscription:
            return redirect('dfs_subscribe_list')

        data = get_storage_data(self.request)

        capacity = data['capacity']

        files_list = data['files_list']

        used_size = get_used_size(self.request, files_list)

        file_filter = FileFilter(self.request.GET, queryset=files_list)

        page = self.request.GET.get('page', 1)

        paginator = CachedPaginator(file_filter.qs, 10)

        try:
            files = paginator.page(page)

        except PageNotAnInteger:
            files = paginator.page(1)

        except EmptyPage:
            files = paginator.page(paginator.num_pages)

        context = {'files': files, 'capacity': capacity, 'filter': file_filter, 'used_size': used_size}

        return render(self.request, 'storage/overview.html', context)

    def post(self, request):
        data = self._form_post_request_data()

        form = FileForm(files=self.request.FILES, data=data)

        if form.is_valid() and self._space_is_available():
            file_form = form.save()

            # Update storage data cache
            data = get_storage_data(self.request)
            data['files_list'] |= data['files_list'].filter(pk=file_form.pk)

            data_cache_key = generate_cache_key(self.request, DATA_CACHE_KEY_PREFIX)
            cache.set(data_cache_key, data)

            # Update storage used size cache
            used_size_cache_key = generate_cache_key(self.request, USED_SIZE_CACHE_KEY_PREFIX)
            cache.incr(used_size_cache_key, file_form.file.size)

            response = {'is_valid': True, 'name': file_form.file.name,
                        'url': uri_to_iri(file_form.file.url), 'size': file_form.file.size}
        else:
            response = {'is_valid': False}

        return JsonResponse(response)

    def delete(self, request):
        data_cache_key = generate_cache_key(self.request, DATA_CACHE_KEY_PREFIX)
        cached_data = get_cache_or_none(data_cache_key)

        files_list = cached_data['files_list']

        used_size_cache_key = generate_cache_key(self.request, USED_SIZE_CACHE_KEY_PREFIX)
        cached_used_size = cache.get(used_size_cache_key)

        request_data = QueryDict(self.request.body).get('files_id')

        files_id = [request_data] if str.isdigit(request_data) else json.loads(request_data)

        for file_id in files_id:
            file = File.objects.get(pk=file_id, user=self.request.user)

            if file:
                cached_used_size -= file.file.size
                file.file.delete()
                file.delete()

                cached_data['files_list'] = files_list.exclude(pk=file_id)

            else:
                raise Http404

        cache.set(data_cache_key, cached_data)
        cache.set(used_size_cache_key, cached_used_size)

        response = HttpResponse({'success': 'OK'})

        return response

    def _form_post_request_data(self):
        title = str(self.request.FILES['file'])

        beautified_size = beautify_size(self.request.FILES['file'].size)

        content_type = get_file_type(self.request.FILES['file'].content_type)

        token = self.request.POST.get('csrfmiddlewaretoken', '')

        return {
            'user': self.request.user,
            'title': title,
            'size': beautified_size,
            'type': content_type,
            'csrfmiddlewaretoken': token,
        }

    def _space_is_available(self):
        new_file_size = self.request.FILES['file'].size
        capacity_in_bytes = get_storage_capacity(self.request) * 1073741824

        files_list = get_files_list(self.request)
        used_size = get_used_size(self.request, files_list, beautify=False)

        new_size_in_bytes = new_file_size
        new_used_size = new_size_in_bytes + used_size

        return new_used_size <= capacity_in_bytes


class StorageStatsView(View):
    def get(self, request):
        user_subscription = get_user_subscription(self.request)

        if not user_subscription:
            return redirect('dfs_subscribe_list')

        files_list = get_files_list(self.request)

        capacity = get_storage_capacity(self.request)

        used_size = get_used_size(self.request, files_list)

        files_count = files_list.count()

        largest_file_size = 0
        largest_file_title = ""

        types_dict = {}

        for file in files_list:
            size = file.file.size

            if size > largest_file_size:
                largest_file_title = file.title
                largest_file_size = size

            if file.type in types_dict:
                types_dict[file.type] += 1

            else:
                types_dict[file.type] = 1

        largest_file_size = beautify_size(largest_file_size)

        return render(request, 'storage/stats.html', {
            'capacity': capacity,
            'used_size': used_size,
            'files_count': files_count,
            'largest_file_title': largest_file_title,
            'largest_file_size': largest_file_size,
            'data': list(types_dict.values()),
            'labels': list(types_dict.keys())
        })


def download_file(request):
    file_id = request.POST.get('file_id', '')
    user_file = File.objects.get(pk=file_id, user=request.user)

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

    return redirect('overview')


def download_compressed_files(request):
    user = request.user
    files_id = json.loads(request.POST.get('files_id', ''))

    paths = []

    for file_id in files_id:
        file = File.objects.get(pk=file_id, user_id=user.id)
        paths.append(os.path.join(settings.MEDIA_ROOT, uri_to_iri(file.file.path)))

    response = HttpResponse(content_type='application/zip')
    archive = zipfile.ZipFile(response, 'w')

    for file_path in paths:
        archive.write(file_path, basename(file_path))

    archive.close()

    response['Content-Disposition'] = 'attachment; filename={}'.format('cloud-archive.zip')

    return response


@login_required()
def serve_protected_file(request, path, document_root=None, show_indexes=False):
    user_file = get_object_or_404(File, file=path)

    if user_file.user_id != request.user.id:
        raise Http404

    path = posixpath.normpath(path).lstrip('/')
    fullpath = Path(safe_join(document_root, path))

    if fullpath.is_dir():
        if show_indexes:
            return directory_index(path, fullpath)

        raise Http404("Directory indexes are not allowed here.")

    if not fullpath.exists():
        raise Http404('“%(path)s” does not exist' % {'path': fullpath})

    # Respect the If-Modified-Since header.
    statobj = fullpath.stat()
    if not was_modified_since(request.META.get('HTTP_IF_MODIFIED_SINCE'),
                              statobj.st_mtime, statobj.st_size):
        return HttpResponseNotModified()

    content_type, encoding = mimetypes.guess_type(str(fullpath))
    content_type = content_type or 'application/octet-stream'

    response = FileResponse(fullpath.open('rb'), content_type=content_type)
    response["Last-Modified"] = http_date(statobj.st_mtime)

    if encoding:
        response["Content-Encoding"] = encoding

    return response
