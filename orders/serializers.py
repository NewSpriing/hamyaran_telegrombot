from rest_framework import serializers
from .models import Order
from users.serializers import AddressSerializer, FamilyMemberSerializer
from services.serializers import ServiceSerializer
from users.models import Address, FamilyMember
from services.models import Service
import logging

logger = logging.getLogger(__name__)

class OrderSerializer(serializers.ModelSerializer):
    address = AddressSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)
    recipient = FamilyMemberSerializer(read_only=True, allow_null=True)  # Allow null recipient
    address_id = serializers.PrimaryKeyRelatedField(
        queryset=Address.objects.all(), source='address', write_only=True,
        label="آدرس"  # Added label
    )
    service_id = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.all(), source='service', write_only=True,
        label="خدمت"  # Added label
    )
    recipient_id = serializers.PrimaryKeyRelatedField(
        queryset=FamilyMember.objects.all(), source='recipient', write_only=True, allow_null=True,
        label="گیرنده خدمت"  # Added label
    )

    class Meta:
        model = Order
        fields = ['id', 'user', 'service', 'service_id', 'address', 'address_id', 'recipient', 'recipient_id', 'preferred_gender', 'special_conditions', 'scheduled_time', 'status', 'created_at']
        read_only_fields = ['user', 'status', 'created_at']
        extra_kwargs = {
            'preferred_gender': {'label': 'جنسیت ترجیحی'},
            'special_conditions': {'label': 'شرایط ویژه'},
            'scheduled_time': {'label': 'زمان برنامه ریزی شده'},
        }

    def create(self, validated_data):
        try:
            order = Order.objects.create(**validated_data)
            logger.info(f"Order {order.id} created.")
            return order
        except Exception as e:
            logger.error(f"Error creating order: {e}", exc_info=True)
            raise

    def update(self, instance, validated_data):
        try:
            order = super().update(instance, validated_data)
            logger.info(f"Order {instance.id} updated.")
            return order
        except Exception as e:
            logger.error(f"Error updating order {instance.id}: {e}", exc_info=True)
            raise