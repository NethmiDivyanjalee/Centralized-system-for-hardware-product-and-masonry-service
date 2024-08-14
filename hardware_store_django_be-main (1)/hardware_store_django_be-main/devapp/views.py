import os
import random
from decimal import Decimal

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from helpers.vars import images_dir
from marketplace.models import Cart, RbacUser, UserRoles, Customer
from marketplace.models import Item


@api_view(['POST'])
def populate(request):
    # clear all users
    all_users = RbacUser.objects.all()
    for user in all_users:
        if not user.is_staff:
            user.delete()

    # clear all carts
    all_carts = Cart.objects.all()
    for cart in all_carts:
        cart.delete()

    # clear all items
    all_items = Item.objects.all()
    for item in all_items:
        item.delete()

    generated_data = {
        'users': [],
        'items': []
    }
    # populate users
    for i in range(6):
        try:
            user = Customer.objects.create_user(f"test_user{i}", f"test_user{i}@shop.aa", f"pass{i}",
                                                first_name=f"FirstName_{i}", last_name=f"LastName_{i}")
            user.phone = random.randint(1000000000, 9999999999)
            user.save()
            generated_data['users'].append(user.id)

        except Exception as err:
            return Response({'error': str(err)}, status=status.HTTP_400_BAD_REQUEST)

    # populate items
    for i in range(30):
        item = Item(name=f"test_item_{i}", description=f"test description {i}",
                    price=Decimal(random.uniform(10.0, 1000.0)),
                    image=os.path.join(images_dir, 'dummy_image.png'),
                    quantity=random.randint(3, 20))
        item.save()
        generated_data['items'].append(item.id)

    return Response(generated_data, status=status.HTTP_200_OK)
