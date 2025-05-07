from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Order
from .serializers import OrderSerializer
import logging

logger = logging.getLogger(__name__)

class OrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows orders to be viewed, created, edited, and deleted.
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Return a list of all orders for the current user.
        """
        return Order.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        Create a new order.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        logger.info(f"Order created for user {request.user.id}.")
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a specific order.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        logger.info(f"Order {instance.id} retrieved.")
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """
        Update an existing order.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        logger.info(f"Order {instance.id} updated.")
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        Delete an order.
        """
        instance = self.get_object()
        self.perform_destroy(instance)
        logger.warning(f"Order {instance.id} deleted.")
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        """
        Create a new order instance.
        """
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        """
        Update an existing order instance.
        """
        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        """
        Delete an order instance.
        """
        instance.delete()