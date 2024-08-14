from rest_framework import serializers

from marketplace.models import RbacUser, Technician, DeliveryGuy, Customer, Address


class RbacUserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(read_only=True)

    class Meta:
        model = RbacUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'phone']


class TechnicianSerializer(serializers.ModelSerializer):
    role = serializers.CharField(read_only=True)
    is_approved = serializers.BooleanField(read_only=True)

    class Meta:
        model = Technician
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'phone',
                  'nic_no', 'nic_image', 'rate_per_hour', 'is_approved', 'skill_category']


class DeliveryGuySerializer(serializers.ModelSerializer):
    role = serializers.CharField(read_only=True)
    is_approved = serializers.BooleanField(read_only=True)

    class Meta:
        model = DeliveryGuy
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'phone',
                  'nic_no', 'nic_image', 'vehicle_type', 'is_approved', 'current_delivery']


class AddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = Address
        fields = ['id', 'address', 'customer']


class CustomerSerializer(serializers.ModelSerializer):
    role = serializers.CharField(read_only=True)
    address = serializers.CharField(source='address.address', read_only=True)

    class Meta:
        model = Customer
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'phone', 'address']


class CashierSerializer(serializers.ModelSerializer):
    role = serializers.CharField(read_only=True)

    class Meta:
        model = RbacUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'phone']
