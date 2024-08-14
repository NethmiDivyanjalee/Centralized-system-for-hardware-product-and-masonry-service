from django.contrib.auth.models import AbstractUser
from django.db import models

from helpers.vars import images_dir


# Choices
class OrderStates(models.TextChoices):
    PAID = 'PAID'
    AWAITING_DELIVERY = 'AWAITING_DELIVERY'
    DELIVERED = 'DELIVERED'


class UserRoles(models.TextChoices):
    CUSTOMER = 'customer',
    TECHNICIAN = 'technician',
    DELIVERY_GUY = 'delivery_guy',
    CASHIER = 'cashier',
    ADMIN = 'admin',


class JobStates(models.TextChoices):
    AVAILABLE = 'available'
    ALLOCATED = 'allocated'
    DONE = 'done'


class BookingStates(models.TextChoices):
    PENDING = 'PENDING'
    TECHNICIAN_ACCEPTED = 'TECHNICIAN_ACCEPTED'  # booking accepted by technician
    CUSTOMER_ACCEPTED = 'CUSTOMER_ACCEPTED'  # customer accepted technicians requested rates and date
    TECHNICIAN_DECLINED = 'TECHNICIAN_DECLINED'  # booking accepted by technician
    TECHNICIAN_WORK_STARTED = 'TECHNICIAN_WORK_STARTED'  # working started by technician
    TECHNICIAN_COMPLETED = 'TECHNICIAN_COMPLETED'  # working completed by technician
    CUSTOMER_APPROVED = 'CUSTOMER_APPROVED'  # customer accepted start and end times of technicians work. all done


# Models
class RbacUser(AbstractUser):
    role = models.CharField(max_length=20, choices=UserRoles, null=False)
    phone = models.CharField(max_length=20)


class Customer(RbacUser):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.role = UserRoles.CUSTOMER

    def __str__(self):
        return f"{self.id}: {self.first_name} {self.last_name}"

    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"


class Address(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, null=False, related_name='address')
    address = models.CharField(max_length=300, null=False)


class Technician(RbacUser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.role = UserRoles.TECHNICIAN

    rate_per_hour = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    is_approved = models.BooleanField(default=False, help_text="should be approved by admin")
    nic_no = models.CharField(max_length=10, null=False)
    nic_image = models.ImageField(upload_to=images_dir, null=False)
    skill_category = models.CharField(max_length=100, null=False)

    class Meta:
        verbose_name = "Technician"
        verbose_name_plural = "Technicians"

    def __str__(self):
        return f"{self.id}: {self.first_name} {self.last_name} - {self.skill_category} | Approval:{self.is_approved}"


class Cashier(RbacUser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.role = UserRoles.CASHIER

    def __str__(self):
        return f"{self.id}: {self.first_name} {self.last_name}"

    def delete(self, *args, **kwargs):
        # Override delete method to avoid trying to delete corresponding RbacUser instance
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name = "Cashier"
        verbose_name_plural = "Cashiers"


class Item(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to=images_dir, null=True)
    quantity = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.id}: {self.name} | {self.price} | qty: {self.quantity}  |" \
               f" {'In Stock' if self.quantity > 0 else 'Out of Stock'}"


class Feedback(models.Model):
    description = models.CharField(max_length=300, null=False)
    item = models.ForeignKey(Item, null=True, on_delete=models.CASCADE, related_name='feedbacks')
    customer = models.ForeignKey(Customer, null=True, on_delete=models.CASCADE, related_name='feedbacks')


class Cart(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, null=False, blank=False,
                                    related_name="cart")

    def __str__(self):
        return f"{self.id}: {self.customer.first_name} {self.customer.last_name}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null=False, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, null=False)
    quantity = models.IntegerField()

    class Meta:
        unique_together = ('cart', 'item')

    def __str__(self):
        return f"{self.id} | {self.item.id} - {self.item.name} qty: {self.quantity}"


class Order(models.Model):
    status = models.CharField(max_length=20, choices=OrderStates, default=OrderStates.PAID)
    time = models.DateTimeField(auto_now_add=True)
    customer = models.ForeignKey(Customer, null=False, on_delete=models.CASCADE, related_name='orders')
    total = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    def __str__(self):
        return f"{self.id}. {self.customer.__str__()} | {self.status}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=False, related_name="items")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, null=False)
    quantity = models.IntegerField()

    def __str__(self):
        return f"{self.id}. order {self.order.id} - item {self.item.name} | qty {self.quantity}"


class DeliveryGuy(RbacUser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.role = UserRoles.DELIVERY_GUY

    current_delivery = models.ForeignKey(Order, null=True, on_delete=models.SET_NULL, related_name="delivery_guy")
    nic_no = models.CharField(max_length=10, null=False)
    nic_image = models.ImageField(upload_to=images_dir, null=False)
    vehicle_type = models.CharField(max_length=100, null=False)
    is_approved = models.BooleanField(default=False, help_text="should be approved by admin")

    def __str__(self):
        return f"{self.id}: {self.first_name} {self.last_name} - {self.vehicle_type} | Approval:{self.is_approved}"

    class Meta:
        verbose_name = "Delivery Guy"
        verbose_name_plural = "Delivery Guys"


class TechnicianBooking(models.Model):
    title = models.CharField(max_length=50, null=False)
    job_description = models.CharField(max_length=300, null=False)
    created_time = models.DateTimeField(auto_now_add=True)

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=False)
    technician = models.ForeignKey(Technician, on_delete=models.CASCADE, null=False)

    status = models.CharField(max_length=30, choices=BookingStates, default=BookingStates.PENDING)

    estimated_time = models.IntegerField(null=True, help_text="assigned by technician in hours")
    working_date = models.DateField(null=True)
    requested_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    working_start_time = models.DateTimeField(null=True)
    working_end_time = models.DateTimeField(null=True)


class PosOrder(models.Model):
    time = models.DateTimeField(auto_now_add=True)
    cashier = models.ForeignKey(Cashier, on_delete=models.SET_NULL, null=True)

    total = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    is_paid = models.BooleanField(default=True)


class PosOrderItem(models.Model):
    pos_order = models.ForeignKey(PosOrder, on_delete=models.CASCADE, null=False, related_name="items")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, null=False)
    quantity = models.IntegerField()
