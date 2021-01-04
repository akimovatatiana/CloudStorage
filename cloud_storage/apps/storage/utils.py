import os
import mimetypes
import humanize
from django.core.cache.backends.base import DEFAULT_TIMEOUT

from django.core.cache import cache
from django.utils.encoding import uri_to_iri
from subscriptions.models import UserSubscription

from cloud_storage import settings
from cloud_storage.apps.storage.constants import mime_dict
from cloud_storage.apps.storage.models import File
from cloud_storage.apps.storage_subscriptions.models import StorageSubscription

CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)

SUBSCRIPTION_CACHE_KEY_PREFIX = 'subscription'
DATA_CACHE_KEY_PREFIX = 'data'
USED_SIZE_CACHE_KEY_PREFIX = 'used_size'


def get_cache_or_none(cache_key):
    if cache_key in cache:
        return cache.get(cache_key)
    else:
        return None


def generate_cache_key(request, key_prefix):
    return f'{key_prefix}:{request.user.id}'


def get_storage_data(request):
    data_cache_key = generate_cache_key(request, DATA_CACHE_KEY_PREFIX)
    data = get_cache_or_none(data_cache_key)

    if not data:
        data = get_storage_data_from_db(request)
        cache.set(data_cache_key, data)

    return data


def get_files_list(request):
    context = get_storage_data(request)

    return context['files_list']


def get_storage_capacity(request):
    user_subscription = get_user_subscription(request)
    capacity = 0

    if user_subscription:
        user_plan_id = user_subscription[0].subscription.plan_id

        storage_subscription = StorageSubscription.objects.filter(subscription=user_plan_id)[0]

        capacity = int(storage_subscription.size) / 1000

    return capacity


def get_user_subscription(request):
    subscription_cache_key = generate_cache_key(request, SUBSCRIPTION_CACHE_KEY_PREFIX)

    if subscription_cache_key in cache:
        user_subscription = cache.get(subscription_cache_key)
    else:
        user_subscription = get_user_subscription_from_db(request.user.id)
        if user_subscription:
            cache.set(subscription_cache_key, user_subscription)
        else:
            return None

    return user_subscription


def get_used_size(request, beautify=True):
    used_size_cache_key = generate_cache_key(request, USED_SIZE_CACHE_KEY_PREFIX)

    if used_size_cache_key in cache:
        used_size = cache.get(used_size_cache_key)

    else:
        files_list = get_files_list(request)
        size = get_used_size_from_db(files_list)
        cache.set(used_size_cache_key, size)

        used_size = size

    if beautify:
        used_size = beautify_size(used_size)

    return used_size


def get_files_list_from_db(request, sorted_by='-uploaded_at'):
    return File.objects.filter(user=request.user.id).order_by(sorted_by)


def get_storage_capacity_from_db(request):
    user_subscription = get_user_subscription_from_db(request.user)

    if user_subscription:
        user_plan_id = user_subscription[0].subscription.plan_id

        storage_subscriptions = StorageSubscription.objects.filter(subscription=user_plan_id)
        capacity = storage_subscriptions[0].size

        return capacity

    return 0


def get_storage_data_from_db(request):
    user_id = request.user.id

    files_list = File.objects.filter(user=user_id).order_by('-uploaded_at')
    capacity = int(get_storage_capacity_from_db(request) / 1000)

    data = {
        'files_list': files_list,
        'capacity': capacity,
    }

    return data


def get_used_size_from_db(files_list):
    used_size = 0
    for file in files_list:
        file_path = str(settings.BASE_DIR) + uri_to_iri(file.file.url)

        size = os.path.getsize(file_path)

        used_size += size

    return used_size


def get_user_subscription_from_db(user):
    return UserSubscription.objects.get_queryset().filter(user=user)


def get_mime_file_type(url):
    return mimetypes.guess_type(url)[0]


def get_file_type(content_type):
    for simple_file_type, mime_file_types in mime_dict.items():
        if content_type in mime_file_types:
            return simple_file_type.title()

    return content_type


def beautify_size(value):
    return humanize.naturalsize(value).upper()
