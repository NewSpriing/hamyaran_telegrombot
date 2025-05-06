from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomUserViewSet, AddressViewSet, FamilyMemberViewSet, DocumentViewSet

router = DefaultRouter()
router.register(r'profile', CustomUserViewSet, basename='profile')
router.register(r'addresses', AddressViewSet, basename='address')
router.register(r'family-members', FamilyMemberViewSet, basename='family-member')
router.register(r'documents', DocumentViewSet, basename='document')

urlpatterns = [
    path('', include(router.urls)),
]
