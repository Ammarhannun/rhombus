import os
import pandas as pd
from django.conf import settings
from django.core.files.storage import default_storage
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.response import Response

from .models import Job
from .serializers import JobSerializer


@api_view(['POST'])
@parser_classes([MultiPartParser])
def get_columns(request):
    file = request.FILES.get('file')
    if not file:
        return Response({'error': 'No file provided.'}, status=status.HTTP_400_BAD_REQUEST)

    filename = file.name.lower()
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(file, nrows=0)
        elif filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file, nrows=0)
        else:
            return Response({'error': 'Only CSV and Excel files are supported.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'columns': list(df.columns)})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@parser_classes([MultiPartParser])
def create_job(request):
    from processing.tasks import run_job

    file = request.FILES.get('input_file')
    nl_prompt = request.data.get('nl_prompt', '').strip()
    replacement_value = request.data.get('replacement_value', '')
    target_columns = request.data.getlist('target_columns')
    original_filename = request.data.get('original_filename', file.name if file else '')

    if not file:
        return Response({'error': 'No file provided.'}, status=status.HTTP_400_BAD_REQUEST)
    if not nl_prompt:
        return Response({'error': 'nl_prompt is required.'}, status=status.HTTP_400_BAD_REQUEST)
    if not target_columns:
        return Response({'error': 'At least one target column is required.'}, status=status.HTTP_400_BAD_REQUEST)

    job = Job.objects.create(
        input_file=file,
        original_filename=original_filename,
        target_columns=target_columns,
        nl_prompt=nl_prompt,
        replacement_value=replacement_value,
    )

    task = run_job.delay(str(job.id))
    job.celery_task_id = task.id
    job.save(update_fields=['celery_task_id'])

    return Response({'job_id': str(job.id)}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def job_status(request, job_id):
    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        return Response({'error': 'Job not found.'}, status=status.HTTP_404_NOT_FOUND)
    return Response(JobSerializer(job).data)


@api_view(['GET'])
def job_results(request, job_id):
    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        return Response({'error': 'Job not found.'}, status=status.HTTP_404_NOT_FOUND)

    if job.status != Job.Status.SUCCESS:
        return Response({'error': 'Job is not complete yet.'}, status=status.HTTP_400_BAD_REQUEST)

    if not job.result_file:
        return Response({'error': 'No result file found.'}, status=status.HTTP_404_NOT_FOUND)

    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 100))

    result_path = job.result_file.path
    total_rows = job.total_rows
    start = (page - 1) * page_size

    chunk = pd.read_csv(result_path, skiprows=range(1, start + 1), nrows=page_size)
    columns = pd.read_csv(result_path, nrows=0).columns.tolist()

    return Response({
        'total_rows': total_rows,
        'page': page,
        'page_size': page_size,
        'total_pages': (total_rows + page_size - 1) // page_size,
        'columns': columns,
        'rows': chunk.to_dict(orient='records'),
    })


@api_view(['POST'])
def cancel_job(request, job_id):
    from config.celery import app as celery_app

    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        return Response({'error': 'Job not found.'}, status=status.HTTP_404_NOT_FOUND)

    if job.status in [Job.Status.SUCCESS, Job.Status.FAILED, Job.Status.CANCELLED]:
        return Response({'error': 'Job is already finished.'}, status=status.HTTP_400_BAD_REQUEST)

    if job.celery_task_id:
        celery_app.control.revoke(job.celery_task_id, terminate=True)

    job.status = Job.Status.CANCELLED
    job.save(update_fields=['status'])

    return Response({'status': 'cancelled'})
