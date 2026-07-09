from django.contrib import admin
from .models import Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['id', 'status', 'progress', 'original_filename', 'created_at']
    list_filter = ['status']
    readonly_fields = ['id', 'celery_task_id', 'created_at', 'updated_at']
