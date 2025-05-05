from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ServiceCategoryViewSet, ServiceViewSet

router = DefaultRouter()
router.register(r'categories', ServiceCategoryViewSet, basename='categories')
router.register(r'services', ServiceViewSet, basename='services')

urlpatterns = [
    path('', include(router.urls)),
]