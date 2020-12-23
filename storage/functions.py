import os
import mimetypes
import humanize

from django.utils.encoding import uri_to_iri
from subscriptions.models import UserSubscription

from cloud_storage import settings
from storage.constants import mime_dict
from storage_subscriptions.models import StorageSubscription


def get_used_size(files_list):
    used_size = 0
    for file in files_list:
        file_path = str(settings.BASE_DIR) + uri_to_iri(file.file.url)

        size = os.path.getsize(file_path)

        used_size += size

    return used_size


def get_upload_path(instance, filename):
    return uri_to_iri(str(instance.user.id) + '/' + filename)


def get_mime_file_type(url):
    return mimetypes.guess_type(url)[0]


def get_file_type(content_type):
    for simple_file_type, mime_file_types in mime_dict.items():
        if content_type in mime_file_types:
            return simple_file_type.title()

    return content_type


def beautify_size(value):
    return humanize.naturalsize(value).upper()

def get_user_subscription(user):
    return UserSubscription.objects.get_queryset().filter(user=user)


def get_storage_capacity(request):
    user_subscription = get_user_subscription(request.user)

    if user_subscription:
        user_plan_id = user_subscription[0].subscription.plan_id

        storage_subscriptions = StorageSubscription.objects.filter(subscription=user_plan_id)
        capacity = storage_subscriptions[0].size

        return capacity

    return 0
