from django.urls import path

from . import views


urlpatterns = [
    path("items/<int:key>", views.items_view, name="item"),
    path("items/", views.items_view, name="items"),
    path("items/search/", views.search, name='search'),
    path("items/search/<str:value>", views.search, name='search'),

    path("cart/", views.my_cart, name="cart"),
    path("cart/item/<int:key>", views.cart_item_view, name="cart_item"),
    path("cart/payment/", views.payment, name="payment"),

    path("technicians/", views.technicians_view, name="payment"),
    path("technicians/<int:key>", views.technicians_view, name="payment"),

    path("item/<int:item_id>/feedbacks/", views.item_feedbacks_view, name="feedbacks"),
    path("item/<int:item_id>/feedbacks/<int:feedback_id>", views.item_feedbacks_view, name="feedback"),

    path("booking/", views.booking_view, name="booking"),
    path("booking/<int:key>", views.booking_view, name="booking"),

    path("account/purchased/", views.orders_view),

    path("admin_area/items/<int:key>", views.items_admin_view, name="item_admin"),
    path("admin_area/items/", views.items_admin_view, name="items_admin"),
    path("admin_area/outofstock/", views.out_of_stock_items),
    path("admin_area/instock/", views.in_stock_items),
    path("admin_area/cashiers/", views.cashiers_view),
    path("admin_area/cashiers/<int:key>", views.cashiers_view),
    path("admin_area/technicians/", views.admin_technicians_view),
    path("admin_area/technicians/<int:key>", views.admin_technicians_view),
    path("admin_area/delivery_guys/", views.admin_delivery_guy_view),
    path("admin_area/delivery_guys/<int:key>", views.admin_delivery_guy_view),
    path("admin_area/pos_orders/", views.bill_manage_view),
    path("admin_area/pos_orders/<int:key>", views.bill_manage_view),
    path("admin_area/approve/technician/<int:key>", views.approve_technician_view),
    path("admin_area/approve/delivery_guy/<int:key>", views.approve_delivery_guy_view),
    path("admin_area/feedbacks/", views.feedbacks_admin_view, name="feedback_admin"),
    path("admin_area/feedbacks/<int:key>", views.feedbacks_admin_view, name="feedbacks_admin"),
    path("admin_area/orders/", views.admin_orders_view, name="feedbacks_admin"),
    path("admin_area/orders/<int:key>", views.admin_orders_view, name="feedbacks_admin"),

    path("cashier/pos_orders/", views.billing_view),
    path("cashier/change_password/", views.cashier_change_password),

    path("technician/booking/", views.technician_request_view),
    path("technician/booking/<int:key>", views.technician_request_view),
    path("technician/booking_accept/<int:key>", views.technician_accept_view),
    path("technician/booking_started/<int:key>", views.technician_started_view),
    path("technician/booking_ended/<int:key>", views.technician_ended_view),
    path("technician/booking_decline/<int:key>", views.technician_decline_view),
    path("technician/work_summary/<int:key>", views.technician_work_summary_view),

    path("delivery_guy/deliveries/", views.delivery_guy_orders),
    path("delivery_guy/deliveries/<int:key>", views.delivery_guy_orders),
    path("delivery_guy/accept/order/<int:key>", views.delivery_guy_accept_order),
    path("delivery_guy/delivered/order/<int:key>", views.delivery_guy_delivered_order),
    path("delivery_guy/current/", views.current_delivery_view),
]

