from rest_framework import serializers
from .models import ServiceCategory, Service

class ServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = ['id', 'name', 'parent']

class ServiceSerializer(serializers.ModelSerializer):
    category = ServiceCategorySerializer(read_only=True)

    class Meta:
        model = Service
        fields = ['id', 'name', 'description', 'price', 'duration', 'category']