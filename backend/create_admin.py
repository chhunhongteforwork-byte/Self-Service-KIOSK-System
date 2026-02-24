import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import sys
from django.conf import settings
from django.contrib.auth import get_user_model

def create_admin():
    User = get_user_model()
    
    # Read environment variables
    env_username = os.environ.get('DJANGO_ADMIN_USERNAME')
    env_password = os.environ.get('DJANGO_ADMIN_PASSWORD')
    env_email = os.environ.get('DJANGO_ADMIN_EMAIL', 'admin@kiosk.com')
    
    # Determine behavior if credentials are not provided
    if not env_username or not env_password:
        if settings.DEBUG:
            print("WARNING: Admin credentials not provided in environment.")
            print("DEBUG=True detected. Falling back to default 'chhunhong' superuser for local development.")
            username = 'chhunhong'
            password = 'chhunhong'
            email = env_email
        else:
            print("WARNING: Skipping superuser creation.")
            print("Reason: DJANGO_ADMIN_USERNAME and DJANGO_ADMIN_PASSWORD are required when DEBUG=False.")
            sys.exit(0)
    else:
        username = env_username
        password = env_password
        email = env_email

    if not User.objects.filter(username=username).exists():
        print(f"Creating superuser {username}...")
        User.objects.create_superuser(username, email, password)
        print("Superuser created successfully!")
    else:
        print(f"Superuser {username} already exists. Updating permissions...")
        user = User.objects.get(username=username)
        # Optionally update password if provided via ENV (meaning they explicitly set it)
        if env_password:
            user.set_password(password)
            print("Password updated successfully!")
            
        user.is_superuser = True
        user.is_staff = True
        user.save()
        print(f"User {username} permissions verified.")

if __name__ == "__main__":
    create_admin()
