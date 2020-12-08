from django.db import models

from subscriptions import models as subscription_models


# Create your models here.

class StorageSubscription(models.Model):
    subscription = models.ForeignKey(subscription_models.SubscriptionPlan, on_delete=models.CASCADE)
    size = models.IntegerField()
