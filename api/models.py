import uuid
from django.db import models


class Job(models.Model):
    class Status(models.TextChoices):
        QUEUED = 'QUEUED', 'Queued'
        RUNNING = 'RUNNING', 'Running'
        SUCCESS = 'SUCCESS', 'Success'
        FAILED = 'FAILED', 'Failed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    progress = models.IntegerField(default=0)

    input_file = models.FileField(upload_to='uploads/')
    original_filename = models.CharField(max_length=255)
    target_columns = models.JSONField(default=list)
    nl_prompt = models.TextField()
    replacement_value = models.CharField(max_length=500)

    regex_pattern = models.TextField(blank=True, default='')

    result_file = models.FileField(upload_to='results/', blank=True, null=True)
    total_rows = models.IntegerField(default=0)

    error_message = models.TextField(blank=True, default='')
    celery_task_id = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Job {self.id} [{self.status}]'
