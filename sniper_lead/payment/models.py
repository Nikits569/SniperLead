from django.db import models
from django.conf import settings

class UserSubscription(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) # юзер
    stripe_custom_id = models.CharField(max_length=255, blank=True, null=True) # id юзера
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True) # id подписки


    is_active = models.BooleanField(
        default=False
    )

    def __str__(self):
        return (
            f'{self.user.name} - {"Active" if self.is_active else "Inactive"}'
        )