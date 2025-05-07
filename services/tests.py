from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from .models import ServiceCategory, Service
from users.models import CustomUser  # Import your CustomUser model

class ServiceCategoryTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(phone_number='09123456789', full_name='Test User', gender='male')  # Create a test user
        self.client.force_authenticate(user=self.user)  # Authenticate the client
        self.category = ServiceCategory.objects.create(name='Test Category')

    def test_get_service_categories(self):
        url = reverse('categories-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_single_service_category(self):
        url = reverse('categories-detail', kwargs={'pk': self.category.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class ServiceTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(phone_number='09123456789', full_name='Test User', gender='male')  # Create a test user
        self.client.force_authenticate(user=self.user)  # Authenticate the client
        self.category = ServiceCategory.objects.create(name='Test Category')
        self.service = Service.objects.create(
            category=self.category,
            name='Test Service',
            description='Test Description',
            price=100,
            duration='01:00:00'
        )

    def test_get_services(self):
        url = reverse('services-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_single_service(self):
        url = reverse('services-detail', kwargs={'pk': self.service.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_services(self):
        url = reverse('services-list') + '?search=Test'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)