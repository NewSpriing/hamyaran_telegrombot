import logging
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import CustomUser, Address, FamilyMember, Document
from .serializers import CustomUserSerializer, AddressSerializer, FamilyMemberSerializer, DocumentSerializer, CreateCustomUserSerializer

logger = logging.getLogger(__name__)

class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CustomUser.objects.filter(id=self.request.user.id)

    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = CreateCustomUserSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                logger.info(f"User registered: {serializer.validated_data.get('phone_number')}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Error registering user: {e}", exc_info=True)
                return Response({"error": "Failed to register user."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning(f"Invalid user registration data: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        try:
            serializer.save(user=self.request.user)
            logger.info(f"Address created for user: {self.request.user.phone_number}")
        except Exception as e:
            logger.error(f"Error creating address: {e}", exc_info=True)
            raise

    def perform_update(self, serializer):
        try:
            serializer.save(user=self.request.user)
            logger.info(f"Address updated for user: {self.request.user.phone_number}")
        except Exception as e:
            logger.error(f"Error updating address: {e}", exc_info=True)
            raise

class FamilyMemberViewSet(viewsets.ModelViewSet):
    serializer_class = FamilyMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FamilyMember.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        try:
            serializer.save(user=self.request.user)
            logger.info(f"Family member created for user: {self.request.user.phone_number}")
        except Exception as e:
            logger.error(f"Error creating family member: {e}", exc_info=True)
            raise

    def perform_update(self, serializer):
        try:
            serializer.save(user=self.request.user)
            logger.info(f"Family member updated for user: {self.request.user.phone_number}")
        except Exception as e:
            logger.error(f"Error updating family member: {e}", exc_info=True)
            raise

class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        return Document.objects.filter(family_member__user=self.request.user)

    def perform_create(self, serializer):
        try:
            serializer.save()
            logger.info(f"Document created for family member: {serializer.instance.family_member.full_name}")
        except Exception as e:
            logger.error(f"Error creating document: {e}", exc_info=True)
            raise