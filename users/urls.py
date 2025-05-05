from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomUserViewSet, AddressViewSet, FamilyMemberViewSet

router = DefaultRouter()
router.register(r'profile', CustomUserViewSet, basename='profile')
router.register(r'addresses', AddressViewSet, basename='addresses')
router.register(r'family-members', FamilyMemberViewSet, basename='family-members')

urlpatterns = [
    path('', include(router.urls)),
]
