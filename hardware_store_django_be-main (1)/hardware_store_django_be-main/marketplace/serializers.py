from rest_framework import serializers

from authentication.serializers import CustomerSerializer, TechnicianSerializer
from .models import Item, Cart, CartItem, TechnicianBooking, Feedback, OrderItem, Order, PosOrder, PosOrderItem


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = "__all__"


class CartItemSerializer(serializers.ModelSerializer):
    item = ItemSerializer(read_only=True)

    class Meta:
        model = CartItem
        fields = ['item', 'quantity']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(read_only=True, many=True)

    class Meta:
        model = Cart
        fields = ['id', 'customer', 'items']


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'item', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    address = serializers.CharField(source='customer.address.address', read_only=True)

    # customer = CustomerSerializer(read_only=True)
    # items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ['id', 'status', 'time', 'customer', 'address', 'total', 'delivery_fee']


class PosOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PosOrderItem
        fields = ["pos_order", "item", "quantity"]


class PosOrderSerializer(serializers.ModelSerializer):
    items = PosOrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = PosOrder
        fields = ['id', 'total', 'time', 'is_paid', 'cashier', 'items']


class TechnicianBookingSerializer(serializers.ModelSerializer):
    status = serializers.CharField()
    address = serializers.CharField(source='customer.address', read_only=True)
    customer = CustomerSerializer(read_only=True)
    technician = TechnicianSerializer(read_only=True)

    class Meta:
        model = TechnicianBooking
        fields = ['id', 'title', 'job_description', 'created_time', 'requested_rate', 'customer', 'technician',
                  'estimated_time', 'status', 'working_date', 'working_start_time', 'working_end_time', 'address']


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ['id', 'description', 'item', 'customer']


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
