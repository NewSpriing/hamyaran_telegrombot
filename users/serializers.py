from rest_framework import serializers
from .models import CustomUser, Address, FamilyMember, Document

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'family_member', 'file', 'description', 'uploaded_at']

class FamilyMemberSerializer(serializers.ModelSerializer):
    documents = DocumentSerializer(many=True, read_only=True)
    age = serializers.ReadOnlyField()

    class Meta:
        model = FamilyMember
        fields = ['id', 'full_name', 'birth_date', 'age', 'gender', 'medical_conditions', 'email', 'region', 'relationship', 'documents']

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'title', 'full_address', 'latitude', 'longitude']

class CustomUserSerializer(serializers.ModelSerializer):
    family_members = FamilyMemberSerializer(many=True, read_only=True)
    addresses = AddressSerializer(many=True, read_only=True)
    age = serializers.ReadOnlyField()

    class Meta:
        model = CustomUser
        fields = ['id', 'phone_number', 'full_name', 'birth_date', 'age', 'gender', 'medical_conditions', 'email', 'region', 'family_members', 'addresses']
        