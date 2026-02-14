from django.contrib.auth import get_user_model

def create_superuser():
    User = get_user_model()
    if not User.objects.filter(username="simple").exists():
        User.objects.create_superuser(
            username="simple",
            email="simple@gmail.com",
            password="YourStrongPassword123!"
        )
        print("Superuser created")