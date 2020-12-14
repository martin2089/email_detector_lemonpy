from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(self, *args, **options):
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@admin.com", "admin_lemon123")
        
        if not User.objects.filter(username="user_small_quota").exists():
            User.objects.create_user("user_small_quota", "sm4ll_1234")
        
        if not User.objects.filter(username="user_big_quota").exists():
            User.objects.create_user("user_big_quota", "b1gg_1234")
        
        if not User.objects.filter(username="dashboard").exists():
            User.objects.create_user("dashboard", "d4shb0ard123")
