from rest_framework.permissions import BasePermission

from marketplace.models import UserRoles, DeliveryGuy, Technician


class AllowGetIsAuthenticated(BasePermission):
    """
    The request is permitted only if the method is POST
    """

    def has_permission(self, request, view):
        if request.method == 'GET' or request.user and request.user.is_authenticated:
            return True
        return False


class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == UserRoles.CUSTOMER)


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == UserRoles.ADMIN)


class IsTechnician(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == UserRoles.TECHNICIAN)


class IsCashier(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == UserRoles.CASHIER)


class IsDeliveryGuy(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == UserRoles.DELIVERY_GUY)


class IsDeliveryGuyApproved(BasePermission):
    def has_permission(self, request, view):
        try:
            user = DeliveryGuy.objects.get(id=request.user.id)
            return bool(
                request.user and request.user.is_authenticated and request.user.role == UserRoles.DELIVERY_GUY and user.is_approved)
        except Exception as err:
            return False
class IsTechnicianApproved(BasePermission):
    def has_permission(self, request, view):
        try:
            user = Technician.objects.get(id=request.user.id)
            return bool(
                request.user and request.user.is_authenticated and request.user.role == UserRoles.TECHNICIAN and user.is_approved)
        except Exception as err:
            return False
