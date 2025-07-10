from django.contrib.auth import get_user_model
from django.db.models.signals import pre_save
from django.dispatch import receiver

from .utils import deleteImageInCloudinary


@receiver(pre_save, sender=get_user_model())
def handle_media_update(sender, instance, **kwargs):
    """
    Deletes old image and video from Cloudinary when updated.
    """
    try:
        if instance.id:
            old_instance = sender.objects.get(pk=instance.pk)

            if hasattr(instance, 'profile_picture') and old_instance.profile_picture != instance.profile_picture:
                deleteImageInCloudinary(old_instance.profile_picture)
                print("deleted successfully", old_instance.profile_picture)

            if hasattr(instance, 'video') and old_instance.video and old_instance.video != instance.video:
                deleteImageInCloudinary(old_instance.video)

    except Exception as e:
        print(f"Error in pre_save signal: {e}")
