from rest_framework import serializers
from .models import CustomUser, Address, FamilyMember

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'title', 'full_address', 'latitude', 'longitude', 'created_at']

class FamilyMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyMember
        fields = ['id', 'full_name', 'age', 'gender', 'medical_conditions', 'email', 'region', 'relationship', 'created_at']

class CustomUserSerializer(serializers.ModelSerializer):
    addresses = AddressSerializer(many=True, read_only=True)
    family_members = FamilyMemberSerializer(many=True, read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'telegram_id', 'full_name', 'phone_number', 'age', 'gender', 'medical_conditions', 'email', 'region', 'addresses', 'family_members']
        read_only_fields = ['telegram_id']
        