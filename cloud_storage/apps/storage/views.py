import mimetypes
import os
import posixpath
import zipfile
import json

from pathlib import Path

from os.path import basename

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage, Page
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, Http404, FileResponse, HttpResponseNotModified
from django.template import RequestContext
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


class CachedPaginator(Paginator):
    """A paginator that caches the results on a page by page basis."""

    def __init__(self, object_list, per_page, orphans=0, allow_empty_first_page=True, cache_key=None,
                 cache_timeout=300):
        super(CachedPaginator, self).__init__(object_list, per_page, orphans, allow_empty_first_page)

        self.cache_key = cache_key
        self.cache_timeout = cache_timeout

    @cached_property
    def count(self):
        """
            The original django.core.paginator.count attribute in Django1.8
            is not writable and cant be setted manually, but we would like
            to override it when loading data from cache. (instead of recalculating it).
            So we make it writable via @cached_property.
        """
        return super(CachedPaginator, self).count

    def set_count(self, count):
        """
            Override the paginator.count value (to prevent recalculation)
            and clear num_pages and page_range which values depend on it.
        """
        self.count = count
        # if somehow we have stored .num_pages or .page_range (which are cached properties)
        # this can lead to wrong page calculations (because they depend on paginator.count value)
        # so we clear their values to force recalculations on next calls
        try:
            del self.num_pages
        except AttributeError:
            pass
        try:
            del self.page_range
        except AttributeError:
            pass

    @cached_property
    def num_pages(self):
        """This is not writable in Django1.8. We want to make it writable"""
        return super(CachedPaginator, self).num_pages

    @cached_property
    def page_range(self):
        """This is not writable in Django1.8. We want to make it writable"""
        return super(CachedPaginator, self).page_range

    def page(self, number):
        """
        Returns a Page object for the given 1-based page number.

        This will attempt to pull the results out of the cache first, based on
        the requested page number. If not found in the cache,
        it will pull a fresh list and then cache that result + the total result count.
        """
        if self.cache_key is None:
            return super(CachedPaginator, self).page(number)

        # In order to prevent counting the queryset
        # we only validate that the provided number is integer
        # The rest of the validation will happen when we fetch fresh data.
        # so if the number is invalid, no cache will be setted
        # number = self.validate_number(number)
        try:
            number = int(number)
        except (TypeError, ValueError):
            raise PageNotAnInteger('That page number is not an integer')

        page_cache_key = "%s:%s:%s" % (self.cache_key, self.per_page, number)
        page_data = cache.get(page_cache_key)

        if page_data is None:
            page = super(CachedPaginator, self).page(number)
            # cache not only the objects, but the total count too.
            page_data = (page.object_list, self.count)
            cache.set(page_cache_key, page_data, self.cache_timeout)
        else:
            cached_object_list, cached_total_count = page_data
            self.set_count(cached_total_count)
            page = Page(cached_object_list, number, self)

        return page


class CacheMixin(object):
    cache_timeout = CACHE_TTL

    def get_cache_timeout(self):
        return self.cache_timeout

    @method_decorator(vary_on_cookie)
    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        return cache_page(self.get_cache_timeout())(super(CacheMixin, self).dispatch)(*args, **kwargs)


def flush_cache():
    get_redis_connection("default").clear()


class UploadView(View):
    def _get_storage_used_size(self, files_list):
        return beautify_size(get_used_size(files_list))

    def _get_context_from_db(self):
        user_id = self.request.user.id

        files_list = File.objects.filter(user=user_id).order_by('-uploaded_at')
        # used_size = beautify_size(get_used_size(files_list))
        capacity = int(get_storage_capacity(self.request) / 1000)

        data = {
            'files_list': files_list,
            # 'used_size': used_size,
            'capacity': capacity,
        }

        return data

    def _generate_cache_key(self, key_prefix):
        return f'{key_prefix}:{self.request.session.session_key}'

    # @method_decorator(cache_page(CACHE_TTL))
    # @method_decorator(vary_on_cookie)
    # @method_decorator(login_required)
    def get(self, request):
        subscription_cache_key = self._generate_cache_key("subscription")
        if subscription_cache_key in cache:
            user_subscription = cache.get(subscription_cache_key)
        else:
            user_subscription = get_user_subscription(request.user.id)
            cache.set(subscription_cache_key, user_subscription)

        if not user_subscription:
            return redirect('dfs_subscribe_list')

        data_cache_key = self._generate_cache_key("data")

        if data_cache_key in cache:
            context = cache.get(data_cache_key)
        else:
            context = self._get_context_from_db()
            cache.set(data_cache_key, context, CACHE_TTL)

        files_list = context['files_list']

        # user_subscription = get_user_subscription(request.user.id)
        # data = self._get_data_from_db()
        # used_size = beautify_size(get_used_size(files_list))

        used_size_cache_key = self._generate_cache_key("used_size")
        if used_size_cache_key in cache:
            used_size = cache.get(used_size_cache_key)
        else:
            used_size = beautify_size(get_used_size(files_list))
            cache.set(used_size_cache_key, used_size)

        file_filter = FileFilter(self.request.GET, queryset=files_list)

        page = self.request.GET.get('page', 1)
        paginator = Paginator(file_filter.qs, 10)
        # paginator = CachedPaginator(file_filter.qs, 10, cache_key=cache_key, cache_timeout=CACHE_TTL)
        # paginator_cache_key = "%s:%s:%s" % (cache_key, paginator.per_page, page)

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

        if form.is_valid() and is_space_available(request, size):
            file_form = form.save()

            data = {'is_valid': True, 'name': file_form.file.name,
                    'url': uri_to_iri(file_form.file.url)}
        else:
            data = {'is_valid': False}

        return JsonResponse(data)


@login_required()
def remove_file(request):
    file_id = request.POST.get('file_id', '')

    if file_id == '':
        files_id = json.loads(request.POST.get('files_id', ''))

        for pk in files_id:
            file = File.objects.get(pk=pk)
            file.file.delete()
            file.delete()
    else:
        file = File.objects.get(pk=file_id)

        file.file.delete()
        file.delete()

    flush_cache()

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
def get_storage_capacity(request):
    user_subscription = get_user_subscription(request.user)

    if user_subscription:
        user_plan_id = user_subscription[0].subscription.plan_id

        storage_subscriptions = StorageSubscription.objects.filter(subscription=user_plan_id)
        capacity = storage_subscriptions[0].size

        return capacity

    return 0


# TODO: Update accuracy

def is_space_available(request, size):
    capacity = get_storage_capacity(request)
    user_id = request.user.id

    files_list = File.objects.filter(user=user_id)
    used_size = get_used_size(files_list) / 1048576.0

    formatted_size = size / 1048576.0
    new_used_size = formatted_size + used_size

    return new_used_size <= capacity


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


# @login_required()
@cache_page(CACHE_TTL)
@vary_on_cookie
@login_required()
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
