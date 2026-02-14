# process/signals.py
from django.db.models.signals import post_migrate
from django.contrib.auth import get_user_model
from django.dispatch import receiver

@receiver(post_migrate)
def create_default_superuser(sender, **kwargs):
    User = get_user_model()
    if not User.objects.filter(username="simple").exists():
        User.objects.create_superuser(
            username="simple",
            email="simple@gmail.com",
            password="YourStrongPassword123!"
        )
        print("Default superuser created")
