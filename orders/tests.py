from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from .models import Order
from users.models import CustomUser, Address
from services.models import Service, ServiceCategory
import jdatetime  # Use jdatetime directly
from django.utils import timezone  # Import Django's timezone

class OrderTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(phone_number='09123456789', full_name='Test User', gender='male')
        self.client.force_authenticate(user=self.user)
        self.category = ServiceCategory.objects.create(name='Test Category')
        self.service = Service.objects.create(category=self.category, name='Test Service', price=100, duration='01:00:00')
        self.address = Address.objects.create(user=self.user, title='Test Address', full_address='Test Full Address')

    def test_create_order(self):
        url = reverse('order-list')
        # Convert jdatetime to datetime and make it timezone aware
        jalali_datetime = jdatetime.datetime(1402, 10, 11, 10, 0, 0)
        gregorian_datetime = jalali_datetime.togregorian()
        aware_datetime = timezone.make_aware(gregorian_datetime)
        data = {
            'service_id': self.service.id,
            'address_id': self.address.id,
            'scheduled_time': aware_datetime.isoformat(),
            'preferred_gender': 'any',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Order.objects.first().user, self.user)

    def test_get_order(self):
        # Convert jdatetime to datetime and make it timezone aware for creation
        jalali_datetime = jdatetime.datetime(1402, 10, 11, 10, 0, 0)
        gregorian_datetime = jalali_datetime.togregorian()
        aware_datetime = timezone.make_aware(gregorian_datetime)
        order = Order.objects.create(user=self.user, service=self.service, address=self.address, scheduled_time=aware_datetime)
        url = reverse('order-detail', kwargs={'pk': order.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], order.id)

    def test_update_order(self):
        # Convert jdatetime to datetime and make it timezone aware for creation
        jalali_datetime_create = jdatetime.datetime(1402, 10, 11, 10, 0, 0)
        gregorian_datetime_create = jalali_datetime_create.togregorian()
        aware_datetime_create = timezone.make_aware(gregorian_datetime_create)
        order = Order.objects.create(user=self.user, service=self.service, address=self.address, scheduled_time=aware_datetime_create)

        url = reverse('order-detail', kwargs={'pk': order.pk})
        data = {'status': 'confirmed'}
        response = self.client.patch(url, data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Order.objects.get(pk=order.pk).status, 'confirmed')

    def test_delete_order(self):
        # Convert jdatetime to datetime and make it timezone aware for creation
        jalali_datetime_create = jdatetime.datetime(1402, 10, 11, 10, 0, 0)
        gregorian_datetime_create = jalali_datetime_create.togregorian()
        aware_datetime_create = timezone.make_aware(gregorian_datetime_create)

        order = Order.objects.create(user=self.user, service=self.service, address=self.address, scheduled_time=aware_datetime_create)
        url = reverse('order-detail', kwargs={'pk': order.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Order.objects.count(), 0)