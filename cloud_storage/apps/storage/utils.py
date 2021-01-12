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

SUBSCRIPTION_DATA_CACHE_KEY_PREFIX = 'subscription_data'
USER_FILES_CACHE_KEY_PREFIX = 'user_files'
USED_SIZE_CACHE_KEY_PREFIX = 'used_size'


def get_cache_or_none(cache_key):
    if cache_key in cache:
        return cache.get(cache_key)
    else:
        return None


def generate_cache_key(request, key_prefix):
    return f'{key_prefix}:{request.user.id}'


def get_user_files(request):
    user_files_cache_key = generate_cache_key(request, USER_FILES_CACHE_KEY_PREFIX)
    user_files = get_cache_or_none(user_files_cache_key)

    if not user_files:
        user_files = get_user_files_from_db(request)
        cache.set(user_files_cache_key, user_files, CACHE_TTL)

    return user_files


def get_user_files_from_db(request, sorted_by='-uploaded_at'):
    return File.objects.filter(user=request.user.id).order_by(sorted_by)


def get_subscription_data(request):
    subscription_cache_key = generate_cache_key(request, SUBSCRIPTION_DATA_CACHE_KEY_PREFIX)
    subscription_data = get_cache_or_none(subscription_cache_key)

    if not subscription_data:
        user_subscription = get_user_subscription_from_db(request)
        capacity = get_storage_capacity_from_db(request)

        if user_subscription and capacity:
            subscription_data = {
                'subscription': user_subscription,
                'capacity': capacity
            }

            cache.set(subscription_cache_key, subscription_data, CACHE_TTL)

    return subscription_data


def get_user_subscription(request):
    subscription_data = get_subscription_data(request)

    return subscription_data['subscription'] if subscription_data else None


def get_user_subscription_from_db(request):
    return UserSubscription.objects.get_queryset().filter(user=request.user)


def get_storage_capacity(request):
    subscription_data = get_subscription_data(request)

    return subscription_data['capacity'] if subscription_data else 0


def get_storage_capacity_from_db(request):
    user_subscription = get_user_subscription_from_db(request)

    if user_subscription:
        user_plan_id = user_subscription[0].subscription.plan_id

        storage_subscriptions = StorageSubscription.objects.filter(subscription=user_plan_id)
        capacity = storage_subscriptions[0].size

        return capacity

    return 0


def get_used_size(request, beautify=True):
    used_size_cache_key = generate_cache_key(request, USED_SIZE_CACHE_KEY_PREFIX)
    used_size = get_cache_or_none(used_size_cache_key)

    if not used_size:
        used_size = get_used_size_from_db(request)
        cache.set(used_size_cache_key, used_size, CACHE_TTL)

    return beautify_size(used_size) if beautify else used_size


def get_used_size_from_db(request):
    user_files = get_user_files_from_db(request)
    used_size = 0

    for file in user_files:
        file_path = str(settings.BASE_DIR) + uri_to_iri(file.file.url)

        size = os.path.getsize(file_path)

        used_size += size

    return int(used_size)


def beautify_size(value):
    return humanize.naturalsize(value).upper()


def get_mime_file_type(url):
    return mimetypes.guess_type(url)[0]


def get_file_type(content_type):
    for simple_file_type, mime_file_types in mime_dict.items():
        if content_type in mime_file_types:
            return simple_file_type.title()

    return content_type

