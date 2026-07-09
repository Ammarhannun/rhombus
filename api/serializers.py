from rest_framework import serializers
from .models import Job


class JobCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ['input_file', 'original_filename', 'target_columns', 'nl_prompt', 'replacement_value']


class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = '__all__'
