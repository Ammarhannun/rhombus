from django.urls import path
from . import views

urlpatterns = [
    path('columns/', views.get_columns),
    path('jobs/', views.create_job),
    path('jobs/<uuid:job_id>/', views.job_status),
    path('jobs/<uuid:job_id>/results/', views.job_results),
    path('jobs/<uuid:job_id>/cancel/', views.cancel_job),
]
