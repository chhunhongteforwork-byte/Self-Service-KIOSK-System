import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

def create_admin():
    User = get_user_model()
    username = 'chhunhong'
    password = 'chhunhong'
    email = 'admin@kiosk.com'

    if not User.objects.filter(username=username).exists():
        print(f"Creating superuser {username}...")
        User.objects.create_superuser(username, email, password)
        print("Superuser created successfully!")
    else:
        print(f"Superuser {username} already exists. Updating password...")
        user = User.objects.get(username=username)
        user.set_password(password)
        user.is_superuser = True
        user.is_staff = True
        user.save()
        print("Password updated successfully!")

if __name__ == "__main__":
    create_admin()
