from django.contrib import admin

from .models import Item, Cart, CartItem, Customer, Technician, DeliveryGuy, Cashier, Order, \
    OrderItem, RbacUser, Address, TechnicianBooking

# Register your models here.
admin.site.register(Item)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(RbacUser)
admin.site.register(Customer)
admin.site.register(Cashier)
admin.site.register(Technician)
admin.site.register(DeliveryGuy)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Address)
admin.site.register(TechnicianBooking)
