import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    
    help = 'Tạo một superuser tự động từ các biến môi trường.'

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        if not all([username, email, password]):
            self.stdout.write(self.style.ERROR('Thiếu các biến môi trường: DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, DJANGO_SUPERUSER_PASSWORD'))
            return

        # Kiểm tra xem user đã tồn tại chưa
        if not User.objects.filter(username=username).exists():
            self.stdout.write(self.style.SUCCESS(f'Đang tạo tài khoản superuser cho {username} ({email})'))
            User.objects.create_superuser(email=email, username=username, password=password)
        else:
            self.stdout.write(self.style.WARNING(f'Tài khoản superuser "{username}" đã tồn tại.'))