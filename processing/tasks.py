import os
from celery import shared_task
from django.conf import settings


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def run_job(self, job_id):
    from api.models import Job
    from processing.llm import generate_regex, validate_regex
    from processing.spark_engine import apply_regex_replacement

    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        return

    def set_progress(pct):
        job.progress = pct
        job.save(update_fields=['progress'])

    try:
        job.status = Job.Status.RUNNING
        job.progress = 0
        job.save(update_fields=['status', 'progress'])

        set_progress(5)

        pattern = generate_regex(job.nl_prompt)
        validate_regex(pattern)

        job.regex_pattern = pattern
        job.save(update_fields=['regex_pattern'])

        set_progress(15)

        input_path = job.input_file.path
        result_dir = os.path.join(settings.MEDIA_ROOT, 'results')
        os.makedirs(result_dir, exist_ok=True)
        output_path = os.path.join(result_dir, f'{job_id}_result.csv')

        total_rows = apply_regex_replacement(
            input_path=input_path,
            output_path=output_path,
            columns=job.target_columns,
            pattern=pattern,
            replacement=job.replacement_value,
            progress_callback=set_progress,
        )

        relative_path = os.path.relpath(output_path, settings.MEDIA_ROOT)
        job.result_file = relative_path
        job.total_rows = total_rows
        job.status = Job.Status.SUCCESS
        job.progress = 100
        job.save(update_fields=['result_file', 'total_rows', 'status', 'progress'])

    except Exception as exc:
        if self.request.retries >= self.max_retries:
            job.status = Job.Status.FAILED
            job.error_message = str(exc)
            job.save(update_fields=['status', 'error_message'])
        else:
            job.status = Job.Status.QUEUED
            job.save(update_fields=['status'])
            raise self.retry(exc=exc)
