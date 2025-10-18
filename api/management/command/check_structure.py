import os
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'In ra cấu trúc thư mục của dự án để gỡ lỗi trên server.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- BẮT ĐẦU CHIẾN DỊCH DO THÁM ---"))
        
        # BASE_DIR là thư mục gốc của dự án Django (nơi có manage.py)
        base_dir = settings.BASE_DIR
        self.stdout.write(f"Thư mục gốc của dự án (BASE_DIR): {base_dir}\n")

        # In ra cấu trúc thư mục
        for root, dirs, files in os.walk(base_dir):
            # Chỉ hiển thị các thư mục con tương đối so với thư mục gốc
            level = root.replace(str(base_dir), '').count(os.sep)
            indent = ' ' * 4 * (level)
            self.stdout.write(f'{indent}{os.path.basename(root)}/')
            
            sub_indent = ' ' * 4 * (level + 1)
            for f in files:
                # Chỉ in các file Python để cho gọn
                if f.endswith('.py'):
                    self.stdout.write(f'{sub_indent}{f}')
        
        self.stdout.write(self.style.SUCCESS("\n--- KẾT THÚC CHIẾN DỊCH DO THÁM ---"))