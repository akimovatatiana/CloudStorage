import mimetypes
import os
import posixpath
import zipfile
import json
from math import ceil

from pathlib import Path

from os.path import basename

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage, Page
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, Http404, FileResponse, HttpResponseNotModified
from django.utils._os import safe_join
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.utils.http import http_date
from django.views import View
from django.utils.encoding import uri_to_iri
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.vary import vary_on_cookie
from django.views.static import was_modified_since, directory_index
from django_redis import get_redis_connection

from .filters import FileFilter
from .forms import FileForm
from .utils import beautify_size, get_used_size, get_file_type, get_user_subscription
from .models import File

from cloud_storage.apps.storage_subscriptions.models import StorageSubscription

CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)

SUBSCRIPTION_CACHE_KEY_PREFIX = 'subscription'
DATA_CACHE_KEY_PREFIX = 'data'
USED_SIZE_CACHE_KEY_PREFIX = 'used_size'


class CachedPaginator(Paginator):
    @cached_property
    def count(self):
        return len(self.object_list)


def flush_cache():
    get_redis_connection('default').clear()


def get_cache_or_none(request, cache_key):
    if cache_key in cache:
        return cache.get(cache_key)
    else:
        return None


def generate_cache_key(request, key_prefix):
    return f'{key_prefix}:{request.session.session_key}'



@login_required()
def get_storage_capacity(request):
    user_subscription = get_user_subscription(request.user)

    if user_subscription:
        user_plan_id = user_subscription[0].subscription.plan_id

        storage_subscriptions = StorageSubscription.objects.filter(subscription=user_plan_id)
        capacity = storage_subscriptions[0].size

        return capacity

    return 0

# TODO: Update accuracy

def space_is_available(request, size):
    capacity = get_storage_capacity(request)
    user_id = request.user.id

    files_list = File.objects.filter(user=user_id)
    used_size = get_used_size(files_list) / 1048576.0

    formatted_size = size / 1048576.0
    new_used_size = formatted_size + used_size

    return new_used_size <= capacity


class UploadView(View):
    def _get_context_from_db(self):
        user_id = self.request.user.id

        files_list = File.objects.filter(user=user_id).order_by('-uploaded_at')
        capacity = int(get_storage_capacity(self.request) / 1000)

        data = {
            'files_list': files_list,
            'capacity': capacity,
        }

        return data

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

    def get(self, request):
        subscription_cache_key = generate_cache_key(request, SUBSCRIPTION_CACHE_KEY_PREFIX)
        if subscription_cache_key in cache:
            user_subscription = cache.get(subscription_cache_key)
        else:
            user_subscription = get_user_subscription(request.user.id)
            cache.set(subscription_cache_key, user_subscription)

        if not user_subscription:
            return redirect('dfs_subscribe_list')

        data_cache_key = generate_cache_key(request, DATA_CACHE_KEY_PREFIX)

        if data_cache_key in cache:
            context = cache.get(data_cache_key)
        else:
            context = self._get_context_from_db()
            cache.set(data_cache_key, context, CACHE_TTL)

        files_list = context['files_list']

        # user_subscription = get_user_subscription(request.user.id)
        # data = self._get_data_from_db()
        # used_size = beautify_size(get_used_size(files_list))

        used_size_cache_key = generate_cache_key(request, USED_SIZE_CACHE_KEY_PREFIX)
        if used_size_cache_key in cache:
            used_size = cache.get(used_size_cache_key)
        else:
            used_size = beautify_size(get_used_size(files_list))
            cache.set(used_size_cache_key, used_size)

        file_filter = FileFilter(self.request.GET, queryset=files_list)

        page = self.request.GET.get('page', 1)
        paginator = CachedPaginator(file_filter.qs, 10)

        try:
            files = paginator.page(page)
        except PageNotAnInteger:
            files = paginator.page(1)
        except EmptyPage:
            files = paginator.page(paginator.num_pages)

        context['files'] = files
        context['filter'] = file_filter
        context['used_size'] = used_size

        return render(self.request, 'storage/overview.html', context)

    def post(self, request):
        data = self._form_post_request_data()
        form = FileForm(files=request.FILES, data=data)

        if form.is_valid() and space_is_available(request, request.FILES['file'].size):
            file_form = form.save()

            data_cache_key = generate_cache_key(request, DATA_CACHE_KEY_PREFIX)
            cached_files = get_cache_or_none(request, data_cache_key)

            cached_files['files_list'] |= cached_files['files_list'].filter(pk=file_form.pk)
            cache.set(data_cache_key, cached_files)

            data = {'is_valid': True, 'name': file_form.file.name,
                    'url': uri_to_iri(file_form.file.url)}
        else:
            data = {'is_valid': False}

        return JsonResponse(data)


@login_required()
def remove_file(request):
    file_id = request.POST.get('file_id', '')

    data_cache_key = generate_cache_key(request, DATA_CACHE_KEY_PREFIX)
    cached_files = get_cache_or_none(request, data_cache_key)

    if file_id == '':
        files_id = json.loads(request.POST.get('files_id', ''))

        if cached_files:
            for pk in files_id:
                file = File.objects.get(pk=pk)
                file.file.delete()
                file.delete()
                cached_files['files_list'] = cached_files['files_list'].exclude(pk=pk)

        else:
            for pk in files_id:
                file = File.objects.get(pk=pk)
                file.file.delete()
                file.delete()
    else:
        file = File.objects.get(pk=file_id)
        file.file.delete()
        file.delete()

        if cached_files:
            cached_files['files_list'] = cached_files['files_list'].exclude(pk=file_id)
            cache.set(data_cache_key, cached_files)

    return redirect('overview')


@login_required()
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

    return redirect('overview')


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

    if request.user.id != user_file.user_id:
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


# @cache_page(CACHE_TTL)
# @vary_on_cookie
# @login_required()
def get_storage_stats(request):
    user_id = request.user.id
    user_subscription = get_user_subscription(user_id)

    if not user_subscription:
        return redirect('dfs_subscribe_list')

    files_list = File.objects.filter(user=user_id)

    used_size = beautify_size(get_used_size(files_list))
    files_count = files_list.count()

    largest_file_size = 0
    largest_file_title = ""

    types_dict = {}

    for file in files_list:
        file_path = str(settings.BASE_DIR) + uri_to_iri(file.file.url)

        size = os.path.getsize(file_path)

        if size > largest_file_size:
            largest_file_title = file.title
            largest_file_size = size

        if file.type in types_dict:
            types_dict[file.type] += 1
        else:
            types_dict[file.type] = 1

    largest_file_size = beautify_size(largest_file_size)

    return render(request, 'storage/stats.html', {
        'used_size': used_size,
        'files_count': files_count,
        'largest_file_title': largest_file_title,
        'largest_file_size': largest_file_size,
        'data': list(types_dict.values()),
        'labels': list(types_dict.keys())
    })
