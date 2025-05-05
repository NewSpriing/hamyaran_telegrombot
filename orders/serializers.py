from rest_framework import serializers
from .models import Order
from users.serializers import AddressSerializer, FamilyMemberSerializer
from services.serializers import ServiceSerializer
from users.models import Address, FamilyMember
from services.models import Service


class OrderSerializer(serializers.ModelSerializer):
    address = AddressSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)
    recipient = FamilyMemberSerializer(read_only=True)
    address_id = serializers.PrimaryKeyRelatedField(
        queryset=Address.objects.all(), source='address', write_only=True
    )
    service_id = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.all(), source='service', write_only=True
    )
    recipient_id = serializers.PrimaryKeyRelatedField(
        queryset=FamilyMember.objects.all(), source='recipient', write_only=True, allow_null=True
    )

    class Meta:
        model = Order
        fields = ['id', 'user', 'service', 'service_id', 'address', 'address_id', 'recipient', 'recipient_id', 'preferred_gender', 'special_conditions', 'scheduled_time', 'status', 'created_at']
        read_only_fields = ['user', 'status', 'created_at']
