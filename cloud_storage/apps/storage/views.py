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
from django.utils.decorators import method_decorator
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
        return self.object_list.count()

    def __len__(self):
        return self.count


class StorageView(View):
    @method_decorator(login_required())
    def get(self, request):
        subscription_data = get_subscription_data(self.request)

        if not subscription_data:
            return redirect('dfs_subscribe_list')

        capacity = subscription_data['capacity']

        user_files = get_user_files(self.request)
        used_size = get_used_size(self.request)

        file_filter = FileFilter(self.request.GET, queryset=user_files)

        page = self.request.GET.get('page', 1)

        paginator = CachedPaginator(file_filter.qs, 10)

        try:
            files = paginator.page(page)

        except PageNotAnInteger:
            files = paginator.page(1)

        except EmptyPage:
            files = paginator.page(paginator.num_pages)

        context = {
            'files': files,
            'capacity': capacity,
            'filter': file_filter,
            'used_size': used_size
        }

        return render(self.request, 'storage/overview.html', context)

    @method_decorator(login_required())
    def post(self, request):
        data = self._form_post_request_data()

        form = FileForm(files=self.request.FILES, data=data)

        if form.is_valid() and self._space_is_available():
            file_form = form.save()

            # Update storage data cache
            user_files = get_user_files(self.request)
            user_files |= user_files.filter(pk=file_form.pk)

            user_files_cache_key = generate_cache_key(self.request, USER_FILES_CACHE_KEY_PREFIX)
            cache.set(user_files_cache_key, user_files, CACHE_TTL)

            # Update storage used size cache
            used_size_cache_key = generate_cache_key(self.request, USED_SIZE_CACHE_KEY_PREFIX)
            cache.incr(used_size_cache_key, file_form.file.size)

            response = {'is_valid': True}

        else:
            response = {'is_valid': False}

        return JsonResponse(response)

    @method_decorator(login_required())
    def delete(self, request):
        user_files = get_user_files(self.request)

        used_size_cache_key = generate_cache_key(self.request, USED_SIZE_CACHE_KEY_PREFIX)
        used_size = get_used_size(self.request, beautify=False)

        request_data = QueryDict(self.request.body).get('files_id')

        files_id = [request_data] if str.isdigit(request_data) else json.loads(request_data)

        for file_id in files_id:
            file = File.objects.get(pk=file_id, user=self.request.user)

            if file:
                used_size -= file.file.size
                file.file.delete()
                file.delete()

                user_files = user_files.exclude(pk=file_id)

            else:
                raise Http404

        user_files_cache_key = generate_cache_key(self.request, USER_FILES_CACHE_KEY_PREFIX)
        cache.set(user_files_cache_key, user_files, CACHE_TTL)

        cache.set(used_size_cache_key, used_size, CACHE_TTL)

        response = HttpResponse({'success': 'OK'})

        return response

    def _form_post_request_data(self):
        title = str(self.request.FILES['file'])

        byte_size = self.request.FILES['file'].size

        content_type = get_file_type(self.request.FILES['file'].content_type)

        token = self.request.POST.get('csrfmiddlewaretoken', '')

        post_request_data = {
            'user': self.request.user,
            'title': title,
            'byte_size': byte_size,
            'type': content_type,
            'csrfmiddlewaretoken': token,
        }

        return post_request_data

    def _space_is_available(self):
        new_file_size = self.request.FILES['file'].size
        capacity_in_bytes = get_storage_capacity(self.request) * 1073741824

        used_size = get_used_size(self.request, beautify=False)

        new_size_in_bytes = new_file_size
        new_used_size = new_size_in_bytes + used_size

        return new_used_size <= capacity_in_bytes


class StorageStatsView(View):
    @method_decorator(login_required())
    def get(self, request):
        subscription_data = get_subscription_data(request)

        if not subscription_data:
            return redirect('dfs_subscribe_list')

        capacity = subscription_data['capacity']

        user_files = get_user_files(self.request)
        used_size = get_used_size(self.request)

        files_count = user_files.count()

        largest_file_size = 0
        largest_file_title = ""

        types_dict = {}

        for file in user_files:
            size = file.file.size

            if size > largest_file_size:
                largest_file_title = file.title
                largest_file_size = size

            if file.type in types_dict:
                types_dict[file.type] += 1

            else:
                types_dict[file.type] = 1

        largest_file_size = beautify_size(largest_file_size)

        return render(self.request, 'storage/stats.html', {
            'capacity': capacity,
            'used_size': used_size,
            'files_count': files_count,
            'largest_file_title': largest_file_title,
            'largest_file_size': largest_file_size,
            'data': list(types_dict.values()),
            'labels': list(types_dict.keys())
        })


@login_required()
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
