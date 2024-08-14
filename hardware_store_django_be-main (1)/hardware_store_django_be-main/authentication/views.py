from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from authentication.serializers import CustomerSerializer, TechnicianSerializer, DeliveryGuySerializer, \
    RbacUserSerializer, CashierSerializer
from marketplace.models import Customer, UserRoles, Technician, DeliveryGuy, RbacUser, Cashier, Address


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def health_check(request):
    content = {
        'user': str(request.user),  # `django.contrib.auth.User` instance.
        'auth': str(request.auth),  # None
    }
    return Response(content)


# Create your views here.
@api_view(['POST'])
def signup(request, role=UserRoles.CUSTOMER):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']
        firstname = request.POST['firstname']
        lastname = request.POST['lastname']

        try:
            serializer = None
            if role == UserRoles.TECHNICIAN:
                user = Technician.objects.create_user(
                    username, email, password, first_name=firstname, last_name=lastname, phone=request.POST['phone'],
                    nic_no=request.POST['nic_no'], rate_per_hour=request.POST['rate_per_hour'])
                # for nic_image
                serializer = TechnicianSerializer(user, request.data)
                if serializer.is_valid():
                    serializer.save()
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            elif role == UserRoles.DELIVERY_GUY:
                user = DeliveryGuy.objects.create_user(
                    username, email, password, first_name=firstname, last_name=lastname, phone=request.POST['phone'],
                    nic_no=request.POST['nic_no'], vehicle_type=request.POST['vehicle_type'])
                # for nic_image
                serializer = DeliveryGuySerializer(user, request.data)
                if serializer.is_valid():
                    serializer.save()
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            elif role == UserRoles.CUSTOMER:
                user = Customer.objects.create_user(
                    username, email, password, first_name=firstname, last_name=lastname, phone=request.POST['phone'])
                serializer = CustomerSerializer(user)
                Address.objects.create(customer=user, address=request.data['address'])

            else:
                return Response({'error': 'invalid user type'}, status=status.HTTP_400_BAD_REQUEST)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as err:
            return Response({'error': str(err)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def account(request):
    role = request.user.role
    user_model_class = None
    serializer_class = None
    if role == UserRoles.TECHNICIAN:
        serializer_class = TechnicianSerializer
        user_model_class = Technician
    elif role == UserRoles.CUSTOMER:
        serializer_class = CustomerSerializer
        user_model_class = Customer
    elif role == UserRoles.DELIVERY_GUY:
        serializer_class = DeliveryGuySerializer
        user_model_class = DeliveryGuy
    elif role == UserRoles.ADMIN:
        serializer_class = RbacUserSerializer
        user_model_class = RbacUser
    elif role == UserRoles.CASHIER:
        serializer_class = CashierSerializer
        user_model_class = Cashier

    if request.method == 'GET':
        user = user_model_class.objects.get(id=request.user.id)
        serializer = serializer_class(user)
        return Response(serializer.data, status=200)
    elif request.method == 'PUT':
        user = user_model_class.objects.get(id=request.user.id)

        serializer = serializer_class(user, request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # address change
        Address.objects.update_or_create(customer=user, defaults={'address': request.data['address']})
        # Password change
        if request.data.get('password_changed') == 'true' and not user.check_password(request.data.get('old_password')):
            return Response({'error': 'Invalid old password'}, status=status.HTTP_400_BAD_REQUEST)

        if request.data.get('password_changed') == 'true':
            user.set_password(request.data['password'])
            user.save()

        serializer.save()
        return Response(status=status.HTTP_200_OK)

    elif request.method == 'DELETE':
        request.user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def logout(request):
    # Get the current user
    user = request.user

    # Delete the existing token for the user
    Token.objects.filter(user=user).delete()

    # You can customize the response as needed
    response_data = {
        'message': 'Logged out successfully.',
    }

    return Response(response_data, status=status.HTTP_200_OK)
