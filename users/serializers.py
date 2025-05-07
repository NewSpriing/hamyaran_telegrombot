from rest_framework import serializers
from .models import CustomUser, Address, FamilyMember, Document
from jdatetime import date, datetime
from django.core.exceptions import ValidationError

class DocumentSerializer(serializers.ModelSerializer):
    uploaded_at_jalali = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Document
        fields = ['id', 'family_member', 'file', 'description', 'uploaded_at', 'uploaded_at_jalali']
        extra_kwargs = {
            'uploaded_at': {'write_only': True}
        }

    def get_uploaded_at_jalali(self, obj):
        return datetime.fromgregorian(date=obj.uploaded_at.date()).strftime('%Y/%m/%d %H:%M:%S') if obj.uploaded_at else None

class FamilyMemberSerializer(serializers.ModelSerializer):
    birth_date_jalali = serializers.SerializerMethodField(read_only=True)
    age = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = FamilyMember
        fields = ['id', 'full_name', 'birth_date', 'birth_date_jalali', 'age', 'gender', 'medical_conditions', 'email', 'region', 'relationship']
        extra_kwargs = {
            'birth_date': {'write_only': True}
        }

    def get_birth_date_jalali(self, obj):
        return date.fromgregorian(date=obj.birth_date).strftime('%Y/%m/%d') if obj.birth_date else None

    def get_age(self, obj):
        return calculate_age(obj.birth_date)

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'title', 'full_address', 'latitude', 'longitude']

class CustomUserSerializer(serializers.ModelSerializer):
    family_members = FamilyMemberSerializer(many=True, read_only=True)
    addresses = AddressSerializer(many=True, read_only=True)
    birth_date_jalali = serializers.SerializerMethodField(read_only=True)
    age = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'phone_number', 'full_name', 'birth_date', 'birth_date_jalali', 'age', 'gender', 'medical_conditions', 'email', 'region', 'family_members', 'addresses']
        extra_kwargs = {
            'birth_date': {'write_only': True}
        }

    def get_birth_date_jalali(self, obj):
        return date.fromgregorian(date=obj.birth_date).strftime('%Y/%m/%d') if obj.birth_date else None

    def get_age(self, obj):
        return calculate_age(obj.birth_date)

def calculate_age(birth_date):
    """Calculates age from a birth date."""
    if not birth_date:
        return None
    today = date.today()
    birth_date = date.fromgregorian(date=birth_date)
    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age

class CreateCustomUserSerializer(serializers.ModelSerializer):
    birth_date_jalali = serializers.CharField(write_only=True, required=False, allow_blank=True, label='تاریخ تولد شمسی')

    class Meta:
        model = CustomUser
        fields = ['phone_number', 'full_name', 'birth_date', 'birth_date_jalali', 'gender', 'medical_conditions', 'email', 'region']

    def validate_birth_date_jalali(self, value):
        if value:
            try:
                jdate = date.parse(value)
                return date(jdate.year, jdate.month, jdate.day).togregorian()
            except ValueError:
                raise serializers.ValidationError("فرمت تاریخ تولد شمسی نامعتبر است. (مثال: 1370/02/15)")
        return None

    def create(self, validated_data):
        birth_date = validated_data.pop('birth_date_jalali', None)
        user = CustomUser.objects.create(birth_date=birth_date, **validated_data)
        return user