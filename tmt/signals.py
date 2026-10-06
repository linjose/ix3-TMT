from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import Deck, Slide


@receiver(post_delete, sender=Slide)
def delete_slide_files(sender, instance, **kwargs):
    for field in (instance.image, instance.thumbnail):
        try:
            if field:
                field.delete(save=False)
        except Exception:
            pass


@receiver(post_delete, sender=Deck)
def delete_deck_file(sender, instance, **kwargs):
    try:
        if instance.original_file:
            instance.original_file.delete(save=False)
    except Exception:
        pass
