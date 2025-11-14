from django.db.models.signals import post_save
from django.dispatch import receiver

from carts.models import Cart
from users.models import User


@receiver(post_save, sender=User)
def create_cart_for_new_user(sender, instance, created, **kwargs):
    if created:
        Cart.objects.create(user=instance)