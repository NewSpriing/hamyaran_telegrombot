from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import CustomUser, Address, FamilyMember, Document
from .serializers import CustomUserSerializer, AddressSerializer, FamilyMemberSerializer, DocumentSerializer
from rest_framework.parsers import MultiPartParser, FormParser

class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CustomUser.objects.filter(id=self.request.user.id)

    @action(detail=False, methods=['post'])
    def register(self, request):
        telegram_id = request.data.get('telegram_id')
        full_name = request.data.get('full_name')
        phone_number = request.data.get('phone_number')
        age = request.data.get('age')
        gender = request.data.get('gender')
        medical_conditions = request.data.get('medical_conditions')
        email = request.data.get('email')
        region = request.data.get('region')

        if CustomUser.objects.filter(telegram_id=telegram_id).exists():
            return Response({'error': 'کاربر قبلاً ثبت‌نام کرده است'}, status=400)

        user = CustomUser.objects.create(
            telegram_id=telegram_id,
            full_name=full_name,
            phone_number=phone_number,
            age=age,
            gender=gender,
            medical_conditions=medical_conditions,
            email=email,
            region=region
        )
        return Response(CustomUserSerializer(user).data)

class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

class FamilyMemberViewSet(viewsets.ModelViewSet):
    serializer_class = FamilyMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FamilyMember.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        return Document.objects.filter(family_member__user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(family_member_id=self.request.data.get('family_member_id'))
        