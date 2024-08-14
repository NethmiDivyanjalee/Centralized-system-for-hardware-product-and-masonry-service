import math
from decimal import Decimal

from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from authentication.serializers import CashierSerializer, TechnicianSerializer, DeliveryGuySerializer
from helpers.common_messages import not_exist_msg
from helpers.functions import process_payment
from .models import Item, Cart, CartItem, Order, Customer, Cashier, PosOrder, TechnicianBooking, Feedback, Technician, \
    DeliveryGuy, BookingStates, OrderStates
from .permission_classes import IsAdmin, IsCustomer, IsTechnician, IsDeliveryGuy, IsCashier, IsDeliveryGuyApproved, \
    IsTechnicianApproved
from .serializers import ItemSerializer, CartSerializer, PosOrderSerializer, TechnicianBookingSerializer, \
    FeedbackSerializer, OrderSerializer, PosOrderItemSerializer, ChangePasswordSerializer


@api_view(['GET'])
def items_view(request, key=None):
    if key is None:
        item_list = Item.objects.all()
        serializer = ItemSerializer(item_list, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        try:
            item = Item.objects.get(id=key)
        except Item.DoesNotExist as err:
            return Response({'error': str(err)}, status=status.HTTP_404_NOT_FOUND)
        serializer = ItemSerializer(item)
        return Response(serializer.data)


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated, IsAdmin])
def items_admin_view(request, key=None):
    if key is None:
        if request.method == 'GET':
            item_list = Item.objects.all()
            serializer = ItemSerializer(item_list, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == 'POST':
            serializer = ItemSerializer(data=request.data)
            if serializer.is_valid():
                item = serializer.save()
                return Response(ItemSerializer(item).data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_400_BAD_REQUEST)
    else:
        try:
            item = Item.objects.get(id=key)
        except Item.DoesNotExist as err:
            return Response({'error': str(err)}, status=status.HTTP_404_NOT_FOUND)
        if request.method == 'GET':
            serializer = ItemSerializer(item)
            return Response(serializer.data)
        elif request.method == 'PUT':
            serializer = ItemSerializer(item, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)

            print(serializer.errors)
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        elif request.method == 'DELETE':
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def search(request, value=""):
    if request.method == 'GET':
        if value == '*':
            all_items = Item.objects.all()
            serializer = ItemSerializer(all_items, many=True)
            return Response(serializer.data, status=200)

        searched_items = Item.objects.filter(name__icontains=value)
        serializer = ItemSerializer(searched_items, many=True)
        return Response(serializer.data, status=200)


# Create your views here.
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsCustomer])
def my_cart(request):
    cart = None
    try:
        cart = Cart.objects.get(customer__username=request.user.username)
    except Cart.DoesNotExist as err:
        # create cart if not exist
        cart = Cart(customer=Customer.objects.get(username=request.user))
        cart.save()
    except Exception as err:
        Response(data={'error': err.__str__()}, status=status.HTTP_400_BAD_REQUEST)
    serializer = CartSerializer(instance=cart)
    return Response(data=serializer.data, status=status.HTTP_200_OK)


@api_view(['POST', 'DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsCustomer])
def cart_item_view(request, key):
    if request.method == 'POST':
        cart = None
        try:
            # get the cart
            cart = Cart.objects.get(customer__username=request.user.username)
        except Cart.DoesNotExist as err:
            # create cart if not exist
            cart = Cart(customer=Customer.objects.get(username=request.user.username))
            cart.save()

        # add item
        item = None
        try:
            item = Item.objects.get(id=key)
            if item.quantity <= 0:
                raise Exception("Item out of stock.")
        except Exception as err:
            return Response(data={'error': err.__str__()}, status=status.HTTP_404_NOT_FOUND)

        cart_item = cart.items.filter(item=item).first()
        if cart_item is None:
            cart.items.create(cart=cart, item=item, quantity=1)
            cart.save()
        else:
            # if in cart increase qty
            if cart_item.quantity >= item.quantity:
                return Response({'errors': 'Item out of stock'}, status=status.HTTP_400_BAD_REQUEST)
            cart_item.quantity = cart_item.quantity + 1
            cart_item.save()
        return Response(status=status.HTTP_200_OK)

    elif request.method == 'DELETE':
        item, cart = None, None
        try:
            cart = Cart.objects.get(customer__username=request.user.username)
            item = Item.objects.get(id=key)
        except Cart.DoesNotExist or Item.DoesNotExist:
            return Response(data=not_exist_msg, status=status.HTTP_404_NOT_FOUND)

        cart_item = cart.items.filter(item=item).first()
        if cart_item is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        elif cart_item.quantity > 1:
            cartItem = CartItem.objects.get(item=item)
            cartItem.quantity = cartItem.quantity - 1
            cartItem.save()
        else:
            cartItem = CartItem.objects.get(item=item)
            cartItem.delete()
        return Response(status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsCustomer])
def payment(request):
    cart = Cart.objects.get(customer__username=request.user.username)

    # validating cart
    if cart.items.count() == 0:
        return Response({'errors': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

    cart_items = cart.items.all()
    for cart_item in cart_items:
        item = Item.objects.get(id=cart_item.item.id)
        if cart_item.quantity > item.quantity:
            # Item is out of stock
            return Response({'errors': f'Requested quantity is not available in item: {item} '},
                            status=status.HTTP_400_BAD_REQUEST)

    # process payment
    total = sum(item.item.price * item.quantity for item in cart.items.all())
    delivery_fee = total * Decimal(0.1)
    if process_payment(total):
        # change items to SOLD
        for cart_item in cart.items.all():
            stock_item = Item.objects.get(id=cart_item.item.id)
            stock_item.quantity = stock_item.quantity - cart_item.quantity
            stock_item.save()

        # placing an order for the payment
        new_order = Order.objects.create(customer_id=request.user.id, total=total, delivery_fee=delivery_fee)
        for cart_item in cart.items.all():
            new_order.items.create(
                item=cart_item.item,
                quantity=cart_item.quantity
            )

        # clear cart
        cart.delete()

        return Response(status=status.HTTP_200_OK)
    # failed payment
    return Response(status=status.HTTP_400_BAD_REQUEST)


def validate_item_price(item_id, price):
    """
    Validates an item's price with price in the db and returns True or False accordingly
    """
    db_item = Item.objects.get(id=item_id)

    print(price)
    print(db_item.price)
    if float(price) == float(db_item.price):
        print('hit')
        return True

    return False


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def orders_view(request):
    try:
        orders = Order.objects.filter(customer_id=request.user.id)
        serializer = OrderSerializer(orders, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
    except Exception as error:
        return Response({'errors': str(error)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAdmin])
def out_of_stock_items(request):
    items = Item.objects.filter(quantity=0)
    serializer = ItemSerializer(items, many=True)
    return Response(data=serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAdmin])
def in_stock_items(request):
    items = Item.objects.exclude(quantity=0)
    serializer = ItemSerializer(items, many=True)
    return Response(data=serializer.data, status=status.HTTP_200_OK)


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAdmin])
def cashiers_view(request, key=None):
    try:
        if request.method == 'POST':
            cashier = Cashier.objects.create_user(username=request.POST['username'], password=request.POST['password'])
            # for other attributes
            serializer = CashierSerializer(cashier, request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'GET':
            if not key:
                cashiers = Cashier.objects.all()
                serializer = CashierSerializer(cashiers, many=True)
                return Response(serializer.data)
            else:
                cashier = Cashier.objects.get(id=key)
                serializer = CashierSerializer(cashier)
                return Response(serializer.data)

        if request.method == 'PUT':
            cashier = Cashier.objects.get(id=key)
            serializer = CashierSerializer(cashier, request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            cashier = Cashier.objects.get(id=key)
            cashier.delete(keep_parents=False)
            return Response(key, status=status.HTTP_204_NO_CONTENT)
    except Exception as error:
        return Response({'errors': str(error)}, status=status.HTTP_400_BAD_REQUEST)
    pass


@api_view(['GET', 'DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAdmin])
def admin_technicians_view(request, key=None):
    try:
        if request.method == 'GET':
            if not key:
                technicians = Technician.objects.all()
                serializer = TechnicianSerializer(technicians, many=True)
                return Response(serializer.data)
            else:
                technicians = Technician.objects.get(id=key)
                serializer = TechnicianSerializer(technicians)
                return Response(serializer.data)

        if request.method == 'DELETE':
            technicians = Technician.objects.get(id=key)
            technicians.delete(keep_parents=False)
            return Response(key, status=status.HTTP_204_NO_CONTENT)
    except Exception as error:
        return Response({'errors': str(error)}, status=status.HTTP_400_BAD_REQUEST)
    pass


@api_view(['GET', 'DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAdmin])
def admin_delivery_guy_view(request, key=None):
    try:
        if request.method == 'GET':
            if not key:
                delivery_guy = DeliveryGuy.objects.all()
                serializer = DeliveryGuySerializer(delivery_guy, many=True)
                return Response(serializer.data)
            else:
                delivery_guy = DeliveryGuy.objects.get(id=key)
                serializer = DeliveryGuySerializer(delivery_guy)
                return Response(serializer.data)

        if request.method == 'DELETE':
            delivery_guy = DeliveryGuy.objects.get(id=key)
            delivery_guy.delete(keep_parents=False)
            return Response(key, status=status.HTTP_204_NO_CONTENT)
    except Exception as error:
        return Response({'errors': str(error)}, status=status.HTTP_400_BAD_REQUEST)
    pass


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsCashier])
def billing_view(request):
    try:
        # validate items
        for item in request.data['items']:
            if Item.objects.get(id=item['item']).quantity < item['quantity']:
                return Response({'errors': f'Item: {item["item"]} out of stock'}, status=status.HTTP_400_BAD_REQUEST)

        total = sum([Item.objects.get(id=item['item']).price * item['quantity'] for item in request.data['items']])
        serializer = PosOrderSerializer(data=request.data, partial=True)

        if serializer.is_valid():
            order = serializer.save(cashier=Cashier.objects.get(id=request.user.id), total=total)
            for item in request.data['items']:
                item['pos_order'] = order.id
                item_serializer = PosOrderItemSerializer(data=item)
                if item_serializer.is_valid():
                    item_serializer.save()

                    # change stocks
                    current_item = Item.objects.get(id=item['item'])
                    current_item.quantity -= item['quantity']
                    current_item.save()
                else:
                    return Response(item_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            return Response(serializer.data)
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as error:
        return Response({'errors': str(error)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsCashier])
def cashier_change_password(request):
    try:
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        cashier = Cashier.objects.get(id=request.user.id)
        if not cashier.check_password(serializer.data.get('old_password')):
            return Response({"detail": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        cashier.set_password(serializer.data.get("new_password"))
        cashier.save()
        return Response({'detail': 'Password changes successfully'})
    except Exception as error:
        return Response({'errors': str(error)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE', 'GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAdmin])
def bill_manage_view(request, key=None):
    try:
        if request.method == 'GET':
            if not key:
                pos_orders = PosOrder.objects.all()
                serializer = PosOrderSerializer(pos_orders, many=True)
                return Response(serializer.data)
            else:
                pos_order = PosOrder.objects.get(id=key)
                serializer = PosOrderSerializer(pos_order)
                return Response(serializer.data)

        if request.method == 'DELETE':
            pos_order = PosOrder.objects.get(id=key)
            pos_order.delete()
            return Response(key, status=status.HTTP_204_NO_CONTENT)
    except Exception as error:
        return Response({'errors': str(error)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAdmin])
def approve_technician_view(request, key):
    try:
        technician = Technician.objects.get(id=key)
        technician.is_approved = True
        technician.save()
        return Response(status=status.HTTP_200_OK)

    except Exception as error:
        return Response({'errors': str(error)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAdmin])
def approve_delivery_guy_view(request, key):
    try:
        delivery_guy = DeliveryGuy.objects.get(id=key)
        delivery_guy.is_approved = True
        delivery_guy.save()
        return Response(status=status.HTTP_200_OK)

    except Exception as error:
        return Response({'errors': str(error)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST', 'PUT', 'DELETE', 'GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsCustomer])
def booking_view(request, key=None):
    try:
        if request.method == 'POST':
            customer = Customer.objects.get(id=request.user.id)
            technician = Technician.objects.get(id=int(request.data['technician']))
            serializer = TechnicianBookingSerializer(data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save(customer=customer, technician=technician)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'GET':
            if not key:
                bookings = TechnicianBooking.objects.filter(customer_id=request.user.id).all()
                serializer = TechnicianBookingSerializer(bookings, many=True)
                return Response(serializer.data)
            else:
                booking = TechnicianBooking.objects.filter(customer_id=request.user.id).get(id=key)
                serializer = TechnicianBookingSerializer(booking)
                return Response(serializer.data)

        if request.method == 'PUT':
            booking = TechnicianBooking.objects.filter(customer_id=request.user.id).get(id=key)
            request.data['customer'] = request.user.id
            if booking.status == BookingStates.TECHNICIAN_ACCEPTED:
                request.data['status'] = BookingStates.CUSTOMER_ACCEPTED
            elif booking.status == BookingStates.TECHNICIAN_COMPLETED:
                request.data['status'] = BookingStates.CUSTOMER_APPROVED

            serializer = TechnicianBookingSerializer(booking, request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            booking = TechnicianBooking.objects.filter(customer_id=request.user.id).get(id=key)
            booking.delete()
            return Response(key, status=status.HTTP_204_NO_CONTENT)
    except Exception as error:
        return Response({'errors': str(error)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAdmin])
def feedbacks_admin_view(request, key=None):
    try:
        if request.method == 'GET':
            if not key:
                feedbacks = Feedback.objects.all()
                serializer = FeedbackSerializer(feedbacks, many=True)
                return Response(serializer.data)
            else:
                feedback = Feedback.objects.get(id=key)
                serializer = FeedbackSerializer(feedback)
                return Response(serializer.data)

        if request.method == 'DELETE':
            feedback = Feedback.objects.get(id=key)
            feedback.delete()
            return Response(key, status=status.HTTP_204_NO_CONTENT)

    except Exception as error:
        return Response({'errors': str(error)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST', 'DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsCustomer])
def item_feedbacks_view(request, item_id, feedback_id=None):
    try:
        if request.method == 'GET':
            if not feedback_id:
                feedbacks = Item.objects.get(id=item_id).feedbacks
                serializer = FeedbackSerializer(feedbacks, many=True)
                return Response(serializer.data)
            else:
                feedback = Feedback.objects.get(id=feedback_id)
                serializer = FeedbackSerializer(feedback)
                return Response(serializer.data)
        if request.method == 'POST':
            serializer = FeedbackSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(customer_id=request.user.id, item_id=item_id)
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            feedback = Feedback.objects.filter(customer_id=request.user.id).get(id=feedback_id)
            feedback.delete()
            return Response(feedback_id, status=status.HTTP_204_NO_CONTENT)

    except Exception as error:
        return Response({'errors': str(error)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsTechnician])
def technician_request_view(request, key=None):
    try:
        if not key:
            booking_requests = TechnicianBooking.objects.filter(technician_id=request.user.id).all()
            serializer = TechnicianBookingSerializer(booking_requests, many=True)
            return Response(serializer.data)
        else:
            booking_request = TechnicianBooking.objects.get(id=key)
            serializer = TechnicianBookingSerializer(booking_request)
            return Response(serializer.data)

    except Exception as error:
        return Response({'errors': str(error)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsTechnicianApproved])
def technician_accept_view(request, key):
    try:
        # request.data should contain only estimated_time, working_date, requested_rate
        data = {
            'estimated_time': request.data['estimated_time'],
            'working_date': request.data['working_date'],
            'requested_rate': request.data['requested_rate'],
        }
        booking_request = TechnicianBooking.objects.get(id=key)
        if booking_request.status != BookingStates.PENDING:
            return Response({'errors': 'Invalid current state to accept'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = TechnicianBookingSerializer(booking_request, data, partial=True)
        if serializer.is_valid():
            if any(value is None for value in data.values()):
                return Response({'errors': 'One or more of estimated_time, working_date or requested_rate'
                                           ' validation failed'}, status=status.HTTP_400_BAD_REQUEST)

            serializer.save(status=BookingStates.TECHNICIAN_ACCEPTED)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as error:
        return Response({'errors': str(error)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsTechnicianApproved])
def technician_started_view(request, key):
    try:
        # request.data should contain only working_start_time, working_end_time
        data = {
            'working_start_time': timezone.now(),
        }
        booking_request = TechnicianBooking.objects.get(id=key)

        if booking_request.status != BookingStates.CUSTOMER_ACCEPTED:
            return Response({'errors': "Customer hasn't accepted yet"})

        serializer = TechnicianBookingSerializer(booking_request, data, partial=True)
        if serializer.is_valid():
            serializer.save(status=BookingStates.TECHNICIAN_WORK_STARTED)
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as error:
        return Response({'errors': str(error)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsTechnicianApproved])
def technician_ended_view(request, key):
    try:
        # request.data should contain only working_start_time, working_end_time
        data = {
            'working_end_time': timezone.now(),
        }
        booking_request = TechnicianBooking.objects.get(id=key)

        serializer = TechnicianBookingSerializer(booking_request, data, partial=True)
        if serializer.is_valid():
            serializer.save(status=BookingStates.TECHNICIAN_COMPLETED)
            booking_request.save()

            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as error:
        return Response({'errors': str(error)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsTechnicianApproved])
def technician_decline_view(request, key):
    try:
        booking_request = TechnicianBooking.objects.get(id=key)
        booking_request.status = BookingStates.TECHNICIAN_DECLINED
        booking_request.save()
        return Response()

    except Exception as error:
        return Response({'errors': str(error)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsTechnicianApproved])
def technician_work_summary_view(request, key):
    try:
        booking_request = TechnicianBooking.objects.get(id=key)

        if booking_request.status != BookingStates.CUSTOMER_APPROVED:
            return Response({'errors': 'Customer should be approved prior to summary generation for works'},
                            status=status.HTTP_400_BAD_REQUEST)

        # creating summary details
        worked_time = math.floor(
            (booking_request.working_end_time - booking_request.working_start_time).total_seconds() / 3600)
        total = worked_time * booking_request.requested_rate

        return Response({'worked_time': worked_time, 'rate': booking_request.requested_rate, 'total': total})

    except Exception as error:
        return Response({'errors': str(error)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsDeliveryGuy])
def delivery_guy_orders(request, key=None):
    try:
        if not key:
            available_orders = Order.objects.filter(Q(status=OrderStates.PAID) | Q(status=OrderStates.DELIVERED))
            serializer = OrderSerializer(available_orders, many=True)
            return Response(serializer.data)
        else:
            order = Order.objects.get(id=key)
            serializer = OrderSerializer(order)
            return Response(serializer.data)

    except Exception as error:
        return Response({'errors': str(error)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsDeliveryGuyApproved])
def delivery_guy_accept_order(request, key):
    try:
        current_user = DeliveryGuy.objects.get(id=request.user.id)

        if current_user.current_delivery is not None:
            return Response({'errors': 'Please completed the current delivery before accepting new'},
                            status=status.HTTP_400_BAD_REQUEST)

        order = Order.objects.get(id=key)
        if order.status == OrderStates.DELIVERED:
            return Response({'errors': 'Cannot accept a delivered order'}, status=status.HTTP_400_BAD_REQUEST)

        # update order status
        order.status = OrderStates.AWAITING_DELIVERY
        order.save()

        # add order to delivery_guy's delivery
        current_user.current_delivery = order
        current_user.save()
        return Response()

    except Exception as error:
        return Response({'errors': str(error)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsDeliveryGuyApproved])
def delivery_guy_delivered_order(request, key):
    try:
        # update order status
        order = Order.objects.get(id=key)
        order.status = OrderStates.DELIVERED
        order.save()
        # remove order to delivery_guy's delivery
        current_user = DeliveryGuy.objects.get(id=request.user.id)
        current_user.current_delivery = None
        current_user.save()
        return Response()

    except Exception as error:
        return Response({'errors': str(error)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsDeliveryGuy])
def current_delivery_view(request):
    try:
        current_delivery = DeliveryGuy.objects.get(id=request.user.id).current_delivery
        if current_delivery is None:
            return Response({'errors': 'No current delivery'}, status=status.HTTP_404_NOT_FOUND)
        serializer = OrderSerializer(current_delivery)
        return Response(serializer.data)

    except Exception as error:
        return Response({'errors': str(error)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsCustomer])
def technicians_view(request, key=None):
    try:
        if not key:
            technicians = Technician.objects.filter(is_approved=True)
            serializer = TechnicianSerializer(technicians, many=True)
            return Response(serializer.data)
        else:
            technician = Technician.objects.get(id=key)
            serializer = TechnicianSerializer(technician)
            return Response(serializer.data)

    except Exception as err:
        return Response({'errors': str(err)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAdmin])
def admin_orders_view(request, key=None):
    try:
        if not key:
            cashiers = Order.objects.all()
            serializer = OrderSerializer(cashiers, many=True)
            return Response(serializer.data)
        else:
            cashier = Order.objects.get(id=key)
            serializer = OrderSerializer(cashier)
            return Response(serializer.data)

    except Exception as error:
        return Response({'errors': str(error)}, status=status.HTTP_400_BAD_REQUEST)
    pass
